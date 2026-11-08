"""Multinomial Naive Bayes, implemented with standard Python for explainability.

The local classifier predicts FAQ IDs, not department facts. Chat retrieval still
requires a reviewed source and passes the existing unsupported-detail guards.
JSON artifacts contain counts, not executable pickle objects.
"""
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


def clean_question(text):
    text = unicodedata.normalize('NFKC', text).casefold().replace('’', "'")
    return ' '.join(text.split())


def features(text, ngram_max=1):
    # Keep program IDs, numbers, question words and negations. Do not stem names.
    words = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", clean_question(text))
    result = Counter(words)
    if ngram_max == 2:
        for index in range(len(words) - 1):
            pair = words[index] + ' ' + words[index + 1]
            result[pair] += 1
    return result


def knowledge_fingerprint(records):
    """A changed source gets a different hash, so an old model can be ignored."""
    source_rows = []
    for record in records:
        source_rows.append((record['id'], record['question'], record['answer']))
    source_rows.sort()
    source_text = json.dumps(source_rows, ensure_ascii=False)
    return hashlib.sha256(source_text.encode()).hexdigest()


class IntentModel:
    """Store training counts and use them to rank FAQ labels for a question."""

    def __init__(self, artifact):
        if not isinstance(artifact, dict):
            raise ValueError('Unsupported intent model artifact')
        if artifact.get('schema_version') != 1 or artifact.get('ngram_max') not in (1, 2):
            raise ValueError('Unsupported intent model artifact')
        self.artifact = artifact
        self.alpha = float(artifact['alpha'])
        if not math.isfinite(self.alpha) or self.alpha <= 0:
            raise ValueError('Smoothing must be positive')
        self.ngram_max = artifact['ngram_max']
        self.class_counts = artifact['class_counts']
        self.term_counts = artifact['term_counts']
        if not isinstance(self.class_counts, dict) or not isinstance(self.term_counts, dict):
            raise ValueError('Invalid model structure')
        if not isinstance(artifact['vocabulary'], list):
            raise ValueError('Invalid model structure')
        for counts in self.term_counts.values():
            if not isinstance(counts, dict):
                raise ValueError('Invalid model structure')
        self.vocabulary = set(artifact['vocabulary'])
        if not self.vocabulary or len(self.class_counts) < 2:
            raise ValueError('Model needs a vocabulary and at least two classes')
        if set(self.term_counts) != set(self.class_counts):
            raise ValueError('Invalid model counts or vocabulary')
        for count in self.class_counts.values():
            if type(count) is not int or count <= 0:
                raise ValueError('Invalid model counts or vocabulary')
        for term in self.vocabulary:
            if not isinstance(term, str) or not term:
                raise ValueError('Invalid model counts or vocabulary')
        for counts in self.term_counts.values():
            for term, count in counts.items():
                if type(count) is not int or count <= 0 or term not in self.vocabulary:
                    raise ValueError('Invalid model counts or vocabulary')

        # Precompute the parts of the Bayes equation that are constant per class.
        total = sum(self.class_counts.values())
        self.log_priors = {}
        self.denominators = {}
        for label, count in self.class_counts.items():
            self.log_priors[label] = math.log(count / total)
            total_terms = sum(self.term_counts[label].values())
            self.denominators[label] = total_terms + self.alpha * len(self.vocabulary)

    @classmethod
    def fit(cls, rows, alpha=1.0, ngram_max=1, metadata=None):
        """Learn by counting examples and words in each FAQ class."""
        class_counts = Counter()
        term_counts = {}
        vocabulary = set()
        for row in rows:
            label = row['faq_id']
            counts = features(row['question'], ngram_max)
            class_counts[label] += 1
            if label not in term_counts:
                term_counts[label] = Counter()
            term_counts[label].update(counts)
            vocabulary.update(counts)

        artifact = {
            'schema_version': 1,
            'alpha': alpha,
            'ngram_max': ngram_max,
            'class_counts': dict(class_counts),
            'term_counts': term_counts,
            'vocabulary': sorted(vocabulary),
            'metadata': metadata or {},
        }
        return cls(artifact)

    def predict(self, question):
        """Apply the learned counts; return labels from highest to lowest score."""
        counts = features(question, self.ngram_max)
        known = {}
        for term, count in counts.items():
            if term in self.vocabulary:
                known[term] = count
        if not known:
            return []  # No evidence: avoid selecting an arbitrary equal-prior class.

        # score = log(class prior) + sum(question count * log(word likelihood)).
        scores = {}
        for label in sorted(self.class_counts):
            terms = self.term_counts[label]
            denominator = self.denominators[label]
            word_score = 0.0
            for term, count in known.items():
                likelihood = (terms.get(term, 0) + self.alpha) / denominator
                word_score += count * math.log(likelihood)
            scores[label] = self.log_priors[label] + word_score

        # Subtract the largest log score before exponentiating to avoid overflow.
        peak = max(scores.values())
        weights = {}
        for label, score in scores.items():
            weights[label] = math.exp(score - peak)
        total = sum(weights.values())
        predictions = []
        for label, value in weights.items():
            predictions.append({'faq_id': label, 'score': value / total})

        # Alphabetical label order breaks equal-score ties consistently.
        predictions.sort(key=lambda item: (-item['score'], item['faq_id']))
        return predictions

    def save(self, path):
        model_text = json.dumps(self.artifact, ensure_ascii=False, indent=2)
        Path(path).write_text(model_text + '\n', encoding='utf-8')


def load_model(path, records):
    """Ignore absent/stale/invalid artifacts; keep ordinary retrieval available."""
    try:
        artifact = json.loads(Path(path).read_text(encoding='utf-8'))
        if artifact['metadata']['knowledge_sha256'] != knowledge_fingerprint(records):
            return None
        model = IntentModel(artifact)
        if set(model.class_counts) != {record['id'] for record in records}:
            return None
        return model
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
        return None
