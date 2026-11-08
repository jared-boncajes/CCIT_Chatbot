"""Task-specific closed-set classification metrics and auditable predictions."""

def classification_metrics(actual, predicted, labels):
    if len(actual) != len(predicted) or not actual:
        raise ValueError('Nonempty, equally sized actual and predicted labels are required')
    per_class = []
    for label in labels:
        # Count each type of mistake separately so the formulas are visible.
        tp = 0
        fp = 0
        fn = 0
        support = 0
        for actual_label, predicted_label in zip(actual, predicted):
            if actual_label == label:
                support += 1
                if predicted_label == label:
                    tp += 1
                else:
                    fn += 1
            elif predicted_label == label:
                fp += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append({'faq_id': label, 'support': support,
                          'precision': precision, 'recall': recall, 'f1': f1})

    columns = list(labels)
    if 'ABSTAIN' in predicted:
        columns.append('ABSTAIN')
    confusion_matrix = []
    for actual_label in labels:
        line = []
        for predicted_label in columns:
            count = 0
            for actual_item, predicted_item in zip(actual, predicted):
                if actual_item == actual_label and predicted_item == predicted_label:
                    count += 1
            line.append(count)
        confusion_matrix.append(line)

    correct = 0
    for actual_label, predicted_label in zip(actual, predicted):
        if actual_label == predicted_label:
            correct += 1
    return {
        'samples': len(actual), 'correct': correct,
        'accuracy': correct / len(actual),
        'macro_precision': sum(row['precision'] for row in per_class) / len(labels),
        'macro_recall': sum(row['recall'] for row in per_class) / len(labels),
        'macro_f1': sum(row['f1'] for row in per_class) / len(labels),
        'per_class': per_class, 'confusion_labels': columns,
        'confusion_matrix': confusion_matrix,
    }


def evaluate(model, rows, labels):
    predictions = []
    for row in rows:
        ranked = model.predict(row['question'])
        if ranked:
            predicted = ranked[0]['faq_id']
            score = ranked[0]['score']
        else:
            predicted = 'ABSTAIN'
            score = 0
        predictions.append({**row, 'predicted': predicted, 'correct': predicted == row['faq_id'],
                            'score': score})
    actual_labels = []
    predicted_labels = []
    languages = set()
    for row in predictions:
        actual_labels.append(row['faq_id'])
        predicted_labels.append(row['predicted'])
        languages.add(row['language'])
    metrics = classification_metrics(actual_labels, predicted_labels, labels)

    language_results = {}
    for language in sorted(languages):
        language_results[language] = {'samples': 0, 'correct': 0}
        for row in predictions:
            if row['language'] == language:
                language_results[language]['samples'] += 1
                if row['correct']:
                    language_results[language]['correct'] += 1
    metrics['by_language'] = language_results
    return metrics, predictions
