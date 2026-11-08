"""Build the v3 corpus with source questions in train and frozen authored holdouts.

Run from any directory: python tools/build_dataset.py
No answers, keywords, IDs, or split metadata become question text features.
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chatbot.intent_model import clean_question
from research.dataset import FIELDS, load_dataset


def key(question):
    return ' '.join(re.findall(r"[a-z0-9]+(?:'[a-z]+)?", clean_question(question)))


def build():
    # 1. Read the active answers and the fixed holdout questions.
    records = json.loads((ROOT / 'data/knowledge.json').read_text(encoding='utf-8'))
    holdouts_path = ROOT / 'data/holdouts.json'
    holdouts = json.loads(holdouts_path.read_text(encoding='utf-8'))['examples']
    ids = {r['id'] for r in records}
    if set(holdouts) != ids:
        raise ValueError('Holdouts must cover exactly the active knowledge IDs')

    # 2. Group supplied question variants and resolve shared titles.
    candidates = defaultdict(list)
    for record in records:
        candidates[key(record['question'])].append((record['id'], record['question'], 'canonical'))
        for question in record['alternative_questions']:
            candidates[key(question)].append((record['id'], question, 'alternative'))

    rows, excluded, used = [], [], {}

    def add(label, question, split, provenance):
        normalized = key(question)
        if normalized in used:
            raise ValueError(f'Duplicate or overlapping split question: {question}')
        used[normalized] = (label, split)
        number = 1
        for row in rows:
            if row['faq_id'] == label and row['split'] == split:
                number += 1
        rows.append(dict(sample_id=f'{label}-V3-{split.upper()}-{number:02}',
                         question=question, faq_id=label, split=split,
                         language='English', provenance=provenance))

    for normalized, entries in sorted(candidates.items()):
        canonical = [entry for entry in entries if entry[2] == 'canonical']
        owners = {entry[0] for entry in entries}
        if len({entry[0] for entry in canonical}) > 1:
            raise ValueError('Conflicting canonical FAQ questions')
        if len(owners) > 1 and not canonical:
            excluded.append({'question': entries[0][1], 'labels': sorted(owners),
                             'reason': 'Shared alternative has no unique target'})
            continue
        chosen = canonical[0] if canonical else entries[0]
        if len(owners) > 1:
            excluded.append({'question': chosen[1], 'labels': sorted(owners),
                             'kept_label': chosen[0], 'reason': 'Canonical title takes precedence over broader alternatives'})
        add(chosen[0], chosen[1], 'train',
            f'User-supplied database_v3.json {chosen[2]} question; authorship not independently established')

    # 3. Add the separate validation and test questions without reshuffling.
    for label in sorted(holdouts):
        for split in ('validation', 'test'):
            if len(holdouts[label][split]) != 2:
                raise ValueError('Expected two frozen authored questions per holdout split')
            for question in holdouts[label][split]:
                add(label, question, split, ('AI-authored constructed question; frozen before expanded chair evaluation; not a student transcript' if int(label.split('-')[1]) >= 219 else 'AI-authored constructed question; frozen before v3 evaluation; not a student transcript'))

    # 4. Save the CSV and an audit of the counts, conflicts, and fingerprint.
    output = ROOT / 'data/questions.csv'
    with output.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    cleaned, profile = load_dataset(output, ids)
    if set(r['faq_id'] for r in cleaned) != ids:
        raise ValueError('Every active FAQ needs examples')
    audit = {'source': 'database_v3.json', 'classes': len(ids),
             'dataset_sha256': profile['sha256'], 'split_counts': profile['split_counts'],
             'training_examples_per_class': dict(sorted(Counter(r['faq_id'] for r in rows if r['split'] == 'train').items())),
             'source_question_conflicts': excluded,
             'protocol': 'All uniquely labeled supplied canonical/alternative questions train the model. Newly AI-authored holdouts are frozen separately before the first experiment. Never retune using test results. Shared templates and AI authorship limit external validity.'}
    (ROOT / 'data/dataset_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: audit[k] for k in ('classes', 'dataset_sha256', 'split_counts')}, indent=2))


if __name__ == '__main__':
    build()
