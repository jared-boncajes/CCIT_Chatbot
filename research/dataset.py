"""CSV validation, cleaning and descriptive statistics without runtime dependencies."""
import csv
import hashlib
import re
import statistics
from collections import Counter
from pathlib import Path

from chatbot.intent_model import clean_question, features

FIELDS = ('sample_id', 'question', 'faq_id', 'split', 'language', 'provenance')
SPLITS = {'train', 'validation', 'test'}
LANGUAGES = {'english': 'English', 'filipino': 'Filipino', 'taglish': 'Taglish'}


def count_values(rows, field):
    """Count a categorical column for a table or bar chart."""
    counts = Counter()
    for row in rows:
        counts[row[field]] += 1
    return dict(sorted(counts.items()))


def load_dataset(path, allowed_labels):
    """Read a CSV, keep valid rows, and return the observed cleaning statistics."""
    path = Path(path)
    quality = Counter(input_rows=0, missing_rows_removed=0, duplicate_rows_removed=0,
                      invalid_rows_removed=0, normalized_rows=0)
    rows, seen, identifiers = [], {}, set()
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS) <= set(reader.fieldnames or []):
            raise ValueError('CSV needs columns: ' + ', '.join(sorted(FIELDS)))
        for number, raw in enumerate(reader, 2):
            quality['input_rows'] += 1
            has_missing_value = False
            for field in FIELDS:
                value = raw.get(field)
                if not isinstance(value, str) or not value.strip():
                    has_missing_value = True
                    break
            if has_missing_value:
                quality['missing_rows_removed'] += 1
                continue
            row = {}
            for field in FIELDS:
                row[field] = raw[field].strip()
            row['question'] = clean_question(row['question'])
            row['faq_id'] = row['faq_id'].upper()
            row['split'] = row['split'].casefold()
            row['language'] = LANGUAGES.get(row['language'].casefold(), '')
            if row['faq_id'] not in allowed_labels:
                raise ValueError(f'Unknown FAQ label on CSV line {number}')
            valid_split = row['split'] in SPLITS
            valid_language = bool(row['language'])
            valid_question = len(row['question']) <= 1000 and bool(features(row['question']))
            if not valid_split or not valid_language or not valid_question:
                quality['invalid_rows_removed'] += 1
                continue
            # Match the token sequence used by the classifier, including word order.
            key = ' '.join(re.findall(r"[a-z0-9]+(?:'[a-z]+)?", row['question']))
            if key in seen:
                previous = seen[key]
                if previous['faq_id'] != row['faq_id']:
                    raise ValueError(f'Conflicting labels on CSV line {number}')
                if previous['split'] != row['split']:
                    raise ValueError(f'Train/validation/test leakage on CSV line {number}')
                quality['duplicate_rows_removed'] += 1
                continue
            if row['sample_id'] in identifiers:
                raise ValueError(f'Repeated sample ID on CSV line {number}')
            identifiers.add(row['sample_id'])
            for field in FIELDS:
                if row[field] != raw[field]:
                    quality['normalized_rows'] += 1
                    break
            seen[key] = row
            rows.append(row)
    labels = set()
    for row in rows:
        labels.add(row['faq_id'])
    if len(labels) < 2:
        raise ValueError('At least two FAQ classes are required')
    for split in sorted(SPLITS):
        split_labels = set()
        for row in rows:
            if row['split'] == split:
                split_labels.add(row['faq_id'])
        if split_labels != labels:
            raise ValueError(f'Every class needs examples in the {split} split')
    lengths = []
    for row in rows:
        lengths.append(sum(features(row['question']).values()))
    q1, _, q3 = statistics.quantiles(lengths, n=4, method='inclusive')
    upper = q3 + 1.5 * (q3 - q1)
    quality.update(retained_rows=len(rows), token_length_outliers=sum(length > upper for length in lengths))
    profile = {
        'filename': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'quality': dict(quality), 'class_counts': count_values(rows, 'faq_id'),
        'split_counts': count_values(rows, 'split'),
        'language_counts': count_values(rows, 'language'),
        'token_lengths': {'minimum': min(lengths), 'maximum': max(lengths),
                          'mean': statistics.mean(lengths), 'median': statistics.median(lengths),
                          'stdev': statistics.stdev(lengths), 'q1': q1, 'q3': q3, 'upper_fence': upper},
        'notes': [
            'See row provenance for source-supplied and constructed examples; these are not established student conversations.',
            'Missing/invalid rows and within-split duplicate questions are removed; conflicts and cross-split duplicates stop the run.',
            'NFKC, whitespace and case normalization are applied. FAQ/split/language labels are categorical; FAQ labels are targets, never input features.',
            'Token-length outliers are described, not removed: long legitimate questions remain useful. No numeric outlier clipping or missing-text imputation is appropriate.',
            'The vocabulary is fitted only on training questions. Stopwords and negations are retained; unseen terms are ignored.',
            'Language tags are approximate authoring metadata, not independent language annotations. They are excluded from classifier features.',
        ],
    }
    return rows, profile
