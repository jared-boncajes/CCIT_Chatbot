"""Load a labeled CSV, run EDA and a validation-selected FAQ classifier experiment.

Usage: python analyze.py --dataset data/question_dataset.csv
Install optional research dependencies with requirements-research.txt first.
No AI API key, student transcript, or network call is used.
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from chatbot.intent_model import IntentModel, features, knowledge_fingerprint
from research.dataset import load_dataset
from research.evaluation import classification_metrics, evaluate

ROOT = Path(__file__).resolve().parent
CONFIGURATIONS = [(1, 1.0), (1, 0.5), (2, 1.0), (2, 0.5)]


def better_configuration(candidate, current_best):
    """Apply the same four selection rules in an easy-to-read order."""
    if current_best is None:
        return True
    if candidate['macro_f1'] != current_best['macro_f1']:
        return candidate['macro_f1'] > current_best['macro_f1']
    if candidate['accuracy'] != current_best['accuracy']:
        return candidate['accuracy'] > current_best['accuracy']
    if candidate['ngram_max'] != current_best['ngram_max']:
        return candidate['ngram_max'] < current_best['ngram_max']
    return abs(1 - candidate['alpha']) < abs(1 - current_best['alpha'])


def save_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def figures(output, report, rows):
    import os
    import tempfile
    # Managed environments may have a read-only home. Use a task-owned cache.
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'ccit-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    output.mkdir(parents=True, exist_ok=True)

    def finish(fig, name):
        fig.tight_layout()
        fig.savefig(output / name, dpi=180, facecolor='white')
        plt.close(fig)

    profile = report['dataset']
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(profile['class_counts'].keys(), profile['class_counts'].values(), color='#a71917')
    ax.set(title='Constructed examples per FAQ intent', ylabel='Examples', xlabel='FAQ ID')
    ax.tick_params(axis='x', rotation=70)
    if len(profile['class_counts']) > 30:
        ax.set_xticks(range(0, len(profile['class_counts']), 10))
    finish(fig, 'class_distribution.png')

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist([sum(features(row['question']).values()) for row in rows], bins=12,
            color='#a71917', edgecolor='white')
    ax.set(title='Question lengths after preprocessing', xlabel='Tokens per question', ylabel='Examples')
    finish(fig, 'question_lengths.png')

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(profile['language_counts'].keys(), profile['language_counts'].values(), color=['#a71917', '#cc7470', '#713431'])
    ax.set(title='Approximate authoring-language distribution', ylabel='Examples')
    finish(fig, 'language_distribution.png')

    fig, ax = plt.subplots(figsize=(8, 4))
    experiments = report['experiments']
    ax.bar([row['name'] for row in experiments], [100 * row['macro_f1'] for row in experiments], color='#a71917')
    ax.set(title='Validation experiment (test set excluded from selection)', ylabel='Macro F1 (%)', ylim=(0, 105))
    for index, row in enumerate(experiments):
        ax.text(index, 100 * row['macro_f1'] + 1, f"{100 * row['macro_f1']:.1f}", ha='center')
    finish(fig, 'validation_experiment.png')

    matrix, labels = report['test']['confusion_matrix'], report['test']['confusion_labels']
    fig, ax = plt.subplots(figsize=(10, 9))
    image = ax.imshow(matrix, cmap='Reds', vmin=0)
    ax.set(xticks=range(len(labels)), yticks=range(len(profile['class_counts'])),
           xticklabels=labels, yticklabels=list(profile['class_counts']),
           xlabel='Predicted FAQ ID', ylabel='Actual FAQ ID', title='Selected model: frozen test-set confusion matrix')
    ax.tick_params(axis='x', rotation=90)
    if len(labels) > 30:
        ticks = list(range(0, len(labels), 10))
        ax.set_xticks(ticks, [labels[i] for i in ticks])
        ax.set_yticks(ticks, [labels[i] for i in ticks])
    for i, line in enumerate(matrix):
        for j, value in enumerate(line):
            if value and len(labels) <= 30:
                ax.text(j, i, str(value), ha='center', va='center', color='white' if value > 1 else 'black', fontsize=8)
    fig.colorbar(image, ax=ax, label='Questions')
    finish(fig, 'test_confusion.png')


def run(dataset_path, output, make_figures=True):
    # 1. Load the source labels and clean the separate question CSV.
    knowledge = json.loads((ROOT / 'data/knowledge.json').read_text(encoding='utf-8'))
    allowed_labels = set()
    for record in knowledge:
        allowed_labels.add(record['id'])
    rows, profile = load_dataset(dataset_path, allowed_labels)

    # 2. Respect the existing split column. Do not mix the test rows into training.
    splits = {'train': [], 'validation': [], 'test': []}
    label_set = set()
    for row in rows:
        splits[row['split']].append(row)
        label_set.add(row['faq_id'])
    labels = sorted(label_set)
    metadata = {'knowledge_sha256': knowledge_fingerprint(knowledge), 'dataset_sha256': profile['sha256'],
                'training_sample_ids': [row['sample_id'] for row in splits['train']]}
    # 3. Train four configurations and choose using validation results only.
    experiments = []
    best_model = None
    selected = None
    for ngram_max, alpha in CONFIGURATIONS:
        model = IntentModel.fit(splits['train'], alpha=alpha, ngram_max=ngram_max, metadata=metadata)
        metrics, _ = evaluate(model, splits['validation'], labels)
        result = {'name': f"{'Unigrams' if ngram_max == 1 else 'Uni+bigrams'} / a={alpha:g}",
                  'ngram_max': ngram_max, 'alpha': alpha,
                  **{key: metrics[key] for key in ['samples', 'correct', 'accuracy', 'macro_precision', 'macro_recall', 'macro_f1']}}
        experiments.append(result)
        if better_configuration(result, selected):
            best_model = model
            selected = result

    # 4. Evaluate the winner and a majority baseline on the frozen test partition.
    model = best_model
    test, predictions = evaluate(model, splits['test'], labels)
    counts = model.class_counts
    majority = sorted(counts)[0]
    for label in sorted(counts):
        if counts[label] > counts[majority]:
            majority = label
    baseline = classification_metrics([row['faq_id'] for row in splits['test']], [majority] * len(splits['test']), labels)
    report = {
        'schema_version': 1, 'executed_at': datetime.now(timezone.utc).isoformat(),
        'dataset': profile, 'labels': {row['id']: row['question'] for row in knowledge if row['id'] in labels},
        'protocol': 'Use the fixed splits in the selected CSV; actual per-class and split counts are reported in the dataset profile. Fit vocabulary/counts on train only; choose among four fixed configurations on validation macro F1, then accuracy, then simpler n-grams, then alpha closest to 1. Evaluate only the selected configuration and a majority baseline on the frozen test set. Do not tune using test results.',
        'algorithm': 'Multinomial Naive Bayes implemented in standard Python; bag-of-words counts with optional adjacent bigrams and additive smoothing.',
        'experiments': experiments, 'selected': selected, 'test': test,
        'baseline': {'name': 'Training majority class (alphabetical tie break)', 'predicted_label': majority, **baseline},
        'errors': [row for row in predictions if not row['correct']],
        'limitations': [
            f'This corpus covers {len(labels)} source FAQs. See row provenance for supplied versus AI-authored questions; no observed student inquiries are established.',
            'Related phrasing and parallel templates can remain across splits even after exact duplicate/leakage rejection.',
            'The fixed test set is small; no independent annotators, usability study or population-level accuracy claim.',
            'Closed-set single-intent evaluation excludes unknown, private, ambiguous and multi-intent questions; application guards handle these separately.',
            'Normalized NB scores are not calibrated probabilities of correctness. Strong scores do not establish source support.',
            'The original 95 question checks are development regression checks, not this classifier test set.',
            'Department facts may be outdated. No successful live Gemini/OpenAI generation or end-user deployment is established by these results.',
        ],
    }
    # 5. Save evidence and the model. Flask later reads these saved files.
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    model.save(output / 'model.json')
    save_csv(output / 'prepared_dataset.csv', rows)
    save_csv(output / 'test_predictions.csv', predictions)
    save_csv(output / 'experiments.csv', experiments)
    if make_figures:
        figures(output / 'figures', report, rows)
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'data/question_dataset.csv')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'research/results')
    parser.add_argument('--no-figures', action='store_true', help='Run numerical analysis without optional Matplotlib')
    args = parser.parse_args()
    try:
        report = run(args.dataset, args.output_dir, not args.no_figures)
    except (OSError, ValueError, ImportError) as error:
        parser.exit(2, f'Analysis stopped: {error}\n')
    print(json.dumps({'retained_rows': report['dataset']['quality']['retained_rows'],
                      'splits': report['dataset']['split_counts'], 'selected': report['selected'],
                      'test_accuracy': report['test']['accuracy'], 'test_macro_f1': report['test']['macro_f1'],
                      'test_correct': report['test']['correct'], 'test_samples': report['test']['samples'],
                      'output_dir': str(args.output_dir)}, indent=2))


if __name__ == '__main__':
    main()
