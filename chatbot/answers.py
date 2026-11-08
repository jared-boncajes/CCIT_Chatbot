"""Extractive FAQ presentation. Department facts stay in the source JSON."""
import re
from chatbot.retriever import program_entities, tokens


def _sentences(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())


def _summary(record, question):
    answer = record['answer'].strip()
    category = record.get('category')
    if category in {'curriculum', 'prerequisites', 'ojt', 'organizations', 'community-service', 'activities'}:
        return answer
    if category in {'careers', 'faculty'} and re.search(r'\n\s*\d+\. ', answer):
        return re.sub(r'(?m)^\s*\d+\. ', '• ', answer)
    query = tokens(question)
    named = program_entities(question)
    if category == 'overview':
        meaning = re.fullmatch(r'FAITH-\s*(College of .+)', answer)
        if meaning:
            return 'CCIT stands for ' + meaning[1].rstrip('.') + '.'
    if category == 'academic_programs':
        programs = re.findall(r'Bachelor of Science in [^(]+\((?:BSIT|BSCS|BSEMC)\)', answer)
        if programs:
            if len(named) == 1:
                program = next((name for name in programs if f'({next(iter(named)).upper()})' in name), None)
                if program:
                    lead = '' if re.search(r"\bnot\b|n't\b", question, re.I) else 'Yes. '
                    return f'{lead}CCIT offers {program}.'
            graduate = next((s for s in _sentences(answer) if re.search(r'\bgraduate programs\b', s, re.I)), '')
            graduate = re.split(r',?\s+to support\b', graduate, maxsplit=1)[0].rstrip(' ,.')
            if 'graduate' in query and graduate:
                return graduate + '.'
            reply = 'CCIT offers:\n' + '\n'.join('• ' + name for name in programs)
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
            return '\n'.join('• ' + part for part in parts)
    if category in {'careers', 'faculty'} and ' - ' in answer:
        items = [part.strip(' ,.;-') for part in answer.split(' - ')[1:] if part.strip(' ,.;-')]
        source_programs = program_entities(record['question'])
        label = '/'.join(p.upper() for p in sorted(source_programs))
        title = ('Careers' if category == 'careers' else 'Faculty') + (f' for {label}' if label else '')
        return title + ':\n' + '\n'.join('• ' + item for item in items)
    if category == 'facilities':
        labs = list(dict.fromkeys(re.findall(r'\b(?:the|The) ([A-Z0-9][A-Za-z0-9 ]{0,40} Laboratory)\b', answer)))
        if labs:
            return 'CCIT laboratories:\n' + '\n'.join('• ' + lab for lab in labs)
    if category == 'dean' and ' is the current Dean' in answer:
        return answer.split(' is the current Dean', 1)[0] + ' is the CCIT dean.'
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


def _emphasize(text, record):
    """Mark key facts already present in the extractive reply, without adding facts."""
    phrases = re.findall(
        r'Bachelor of Science in [^(\n]+\((?:BSIT|BSCS|BSEMC)\)'
        r'|(?:Information Technology|Computer Science|Entertainment and Multimedia Computing) \((?:IT|CS|BSEMC)\)'
        r'|College of (?:Computer|Computing) and Information Technology(?: \(CCIT\))?'
        r'|(?:Course-Specific|50-TAG|DOST) Scholarship'
        r'|\d+% discount on tuition fees|Level [IVX]+ accreditation'
        r'|Master[’\']s and Doctorate degree in Information Technology'
        r'|Center of Excellence in Information Technology Education'
        r'|globally competent, committed,? and compassionate IT professionals'
        r'|academic performance in senior high school'
        r'|CCITITE|CCIT Camp|CCIT Night', text,
    )
    if record.get('category') in {'careers', 'faculty', 'facilities'}:
        phrases.extend(re.findall(r'^• (.+)$', text, re.M))
    if record.get('category') == 'dean' and ' is the CCIT dean.' in text:
        phrases.append(text.split(' is the CCIT dean.', 1)[0])
    if not phrases:
        return text
    pattern = '|'.join(re.escape(phrase) for phrase in sorted(set(phrases), key=len, reverse=True))
    return re.sub(pattern, lambda match: '**' + match[0] + '**', text)


def format_faq(records, question):
    parts = []
    for record in records:
        summary = _summary(record, question)
        if len(records) > 1 and record.get('category') in {'bsit', 'bscs', 'bsemc'}:
            summary = record['category'].upper() + ': ' + summary
        parts.append(_emphasize(summary, record))
    return '\n\n'.join(parts)


def source_metadata(records, knowledge):
    """Keep source review information in the API, separate from the visible reply."""
    sources = []
    details = []
    has_unconfirmed_source = False
    has_overview = False
    for record in records:
        if record.get('currency_status') == 'confirmed':
            currency = 'confirmed'
        else:
            currency = 'unconfirmed'
            has_unconfirmed_source = True
        if record.get('category') == 'overview':
            has_overview = True
        sources.append({
            'id': record['id'],
            'title': record['question'],
            'source': record.get('source', 'About CCIT'),
            'reviewed_at': record.get('reviewed_at'),
            'currency_status': currency,
            'verification_scope': record.get('verification_scope', 'Checked against the supplied source only.'),
        })
        details.append({'id': record['id'], 'title': record['question'], 'answer': record['answer']})

    warnings = []
    if has_unconfirmed_source:
        warnings.append('Current department details have not been independently confirmed.')
    overview_answers = []
    for record in knowledge:
        if record.get('category') == 'overview':
            overview_answers.append(record['answer'])
    overview = ' '.join(overview_answers)
    if has_overview and 'College of Computer and' in overview and 'College of Computing and' in overview:
        warnings.append('The source uses both “College of Computer” and “College of Computing” in the college name. Confirm the official wording with CCIT.')
    return sources, details, warnings
