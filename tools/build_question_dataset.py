"""Materialize the frozen, constructed examples as an ordinary CSV dataset."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    raw = json.loads((ROOT / 'data/question_examples.json').read_text(encoding='utf-8'))
    with (ROOT / 'data/question_dataset.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['sample_id', 'question', 'faq_id', 'split', 'language', 'provenance'], lineterminator='\n')
        writer.writeheader()
        for faq_id, examples in raw['examples'].items():
            assert len(examples) == 12
            for index, question in enumerate(examples):
                filipino = index in {6, 7, 9, 11}
                mixed = filipino and bool(re.search(r'\b(?:scholarship|college|academic|BSIT|BSCS|BSEMC|faculty|career|programa|dean|DOST|computing|vision|mission|course|night|camp|performance|initials)\b', question, re.I))
                writer.writerow({
                    'sample_id': f'{faq_id}-Q{index + 1:02}', 'question': question, 'faq_id': faq_id,
                    'split': 'train' if index < 8 else 'validation' if index < 10 else 'test',
                    'language': 'Taglish' if mixed else 'Filipino' if filipino else 'English',
                    'provenance': 'AI-assisted constructed example; not a student transcript',
                })
    print('Wrote 264 constructed examples: 176 train, 44 validation, 44 test.')


if __name__ == '__main__':
    main()
