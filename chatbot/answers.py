"""Extractive FAQ presentation. Department facts stay in the source JSON."""
import re
from chatbot.retriever import program_entities, tokens


def _sentences(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())


def _summary(record, question):
    answer = record['answer'].strip()
    category = record.get('category')
    query = tokens(question)
    named = program_entities(question)
    if category == 'academic_programs':
        programs = re.findall(r'Bachelor of Science in [^(]+\((?:BSIT|BSCS|BSEMC)\)', answer)
        if programs:
            if len(named) == 1:
                program = next((name for name in programs if f'({next(iter(named)).upper()})' in name), None)
                if program:
                    lead = '' if re.search(r"\bnot\b|n't\b", question, re.I) else 'Yes. '
                    return f'{lead}The supplied document lists {program} as an undergraduate program.'
            graduate = next((s for s in _sentences(answer) if re.search(r'\bgraduate programs\b', s, re.I)), '')
            graduate = re.split(r',?\s+to support\b', graduate, maxsplit=1)[0].rstrip(' ,.')
            if 'graduate' in query and graduate:
                return graduate + '.'
            reply = 'Programs listed in the supplied document:\n' + '\n'.join('• ' + name for name in programs)
            if graduate:
                reply += '\n\n' + graduate + '.'
            return reply
    if category == 'scholarships' and re.search(r'\d+%', answer):
        sentence = next((s for s in _sentences(answer) if re.search(r'\d+%', s)), '')
        parts = re.split(r',?\s+while\s+(?:the\s+)?', sentence)
        if len(parts) > 1:
            parts = [part.strip(' .') + '.' for part in parts]
            if '50tag' in query and 'course_specific' not in query:
                parts = [part for part in parts if '50-TAG' in part]
            elif 'course_specific' in query and '50tag' not in query:
                parts = [part for part in parts if 'Course-Specific' in part]
            return 'Scholarship discounts listed in the document:\n' + '\n'.join('• ' + part for part in parts)
    if category in {'careers', 'faculty'} and ' - ' in answer:
        items = [part.strip(' ,.;-') for part in answer.split(' - ')[1:] if part.strip(' ,.;-')]
        source_programs = program_entities(record['question'])
        label = '/'.join(p.upper() for p in sorted(source_programs))
        title = ('Careers' if category == 'careers' else 'Faculty') + (f' for {label}' if label else '')
        return title + ' listed in the document:\n' + '\n'.join('• ' + item for item in items)
    if category == 'facilities':
        labs = list(dict.fromkeys(re.findall(r'\b(?:the|The) ([A-Z0-9][A-Za-z0-9 ]{0,40} Laboratory)\b', answer)))
        if labs:
            return 'Laboratories listed in the document:\n' + '\n'.join('• ' + lab for lab in labs)
    if category == 'dean' and ' is the current Dean' in answer:
        return 'The supplied document lists ' + answer.split(' is the current Dean', 1)[0] + ' as the CCIT dean.'
    if category == 'goals':
        return re.sub(r'\s+([1-7])\.\s+', r'\n\1. ', answer)
    sentences = _sentences(answer)
    if category == 'accreditation' and named:
        supported = [s for s in sentences if program_entities(s) & named]
        if supported:
            return ' '.join(supported)
    if len(answer) > 320 and len(sentences) > 2:
        return ' '.join(sentences[:2])
    return answer


def format_faq(records, question):
    parts = []
    for record in records:
        summary = _summary(record, question)
        if len(records) > 1 and record.get('category') in {'bsit', 'bscs', 'bsemc'}:
            summary = record['category'].upper() + ': ' + summary
        parts.append(summary)
    return '\n\n'.join(parts)


def source_metadata(records, knowledge):
    sources = [{
        'id': r['id'], 'title': r['question'], 'source': r.get('source', 'About CCIT'),
        'reviewed_at': r.get('reviewed_at'), 'currency_status': 'confirmed' if r.get('currency_status') == 'confirmed' else 'unconfirmed',
        'verification_scope': r.get('verification_scope', 'Checked against the supplied source only.'),
    } for r in records]
    details = [{'id': r['id'], 'title': r['question'], 'answer': r['answer']} for r in records]
    warnings = []
    if any(source['currency_status'] == 'unconfirmed' for source in sources):
        warnings.append('Current department details have not been independently confirmed.')
    overview = ' '.join(r['answer'] for r in knowledge if r.get('category') == 'overview')
    if any(r.get('category') == 'overview' for r in records) and 'College of Computer and' in overview and 'College of Computing and' in overview:
        warnings.append('The source uses both “College of Computer” and “College of Computing” in the college name. Confirm the official wording with CCIT.')
    return sources, details, warnings
