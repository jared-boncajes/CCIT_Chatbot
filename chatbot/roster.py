"""Resolve named student leaders from the supplied, dated roster."""
import re

from chatbot.retriever import normalize, program_entities, tokens


def is_roster_request(question):
    query = tokens(question)
    roles = {'representatives', 'officers', 'president', 'vice_president', 'secretary', 'treasurer', 'auditor', 'leaders'}
    actions = {'join', 'become', 'apply', 'positions', 'position', 'structure', 'contact', 'touch', 'reach', 'recruitment', 'elections', 'election', 'when', 'where', 'benefits'}
    return bool(query & roles) and not bool(query & actions)


def roster_records(records):
    return [r for r in records if r.get('category') == 'organizations'
            and 'Class Representatives:' in r['answer']]


def selectors(question):
    from chatbot.scope import curriculum_year
    year = curriculum_year(question)
    text = normalize(question)
    short = re.search(r'\b(?:bscs|bsit|bsemc|cs|it|emc)\s*([1-9])([a-z])?\b', text)
    section = re.search(r'\b([1-9])(?:st|nd|rd|th)?\s*(?:year|yr)?\s*[- ]?([a-z])\b', text)
    # A standalone suffix such as "3A" is a section, not a subject code.
    attached = re.search(r'\b([1-9])([a-z])\b', text)
    section = attached or section
    if short:
        year = int(short[1])
    ordinal = re.search(r'\b([1-9])(?:st|nd|rd|th)\b', text)
    if not year and ordinal:
        year = int(ordinal[1])
    if section:
        year = int(section[1])
    return program_entities(question), year, (section[2].upper() if section else (short[2].upper() if short and short[2] else None))


def entries(record):
    body = record['answer'].split('Class Representatives:', 1)[1]
    return [dict(name=match[1].strip(), program=match[2].casefold(),
                 year=int(match[3]), section=match[4] or '', text=match[0].strip())
            for match in re.finditer(r'([^\n•:,]+?)\s*\((BSIT|BSCS|BSEMC)\s+([1-4])([A-Z]?)\)', body)]


def selected_entries(record, question):
    programs, year, section = selectors(question)
    return [e for e in entries(record) if (not programs or e['program'] in programs)
            and (not year or e['year'] == year) and (not section or e['section'] == section)]


def focus_roster(records, question):
    """Pass the requested source names to both FAQ formatting and AI generation.

    Original records remain intact for source metadata and full-answer details.
    """
    if not is_roster_request(question):
        return records
    focused = []
    for record in records:
        if record not in roster_records([record]):
            focused.append(record)
            continue
        year_label = re.search(r'Academic Year (\d{4}-\d{4})', record['answer'])
        period = f' (A.Y. {year_label[1]})' if year_label else ''
        if {'representatives', 'officers'} <= tokens(question):
            focused.append(record)
            continue
        if 'representatives' in tokens(question):
            if 'fsc' in tokens(question):
                line = next((line for line in record['answer'].splitlines() if line.startswith('• FSC - FACTS Representative:')), '')
                focused.append({**record, 'answer': 'FACTS representative to FSC' + period + ':\n' + line})
                continue
            chosen = selected_entries(record, question)
            answer = 'FACTS class representatives' + period + ':\n' + '\n'.join('• ' + e['text'] for e in chosen)
        else:
            executive = record['answer'].split('Class Representatives:', 1)[0]
            roles = tokens(question) & {'president', 'vice_president', 'secretary', 'treasurer', 'auditor'}
            lines = [line for line in executive.splitlines() if line.startswith('• ')]
            if roles:
                labels = {'vice_president': 'vice president', **{r: r for r in roles if r != 'vice_president'}}
                lines = [line for line in lines if any(line[2:].split(':', 1)[0].casefold() == labels[r]
                         or (r == 'vice_president' and 'vice president' in line.split(':', 1)[0].casefold()) for r in roles)]
            answer = 'FACTS executive officers' + period + ':\n' + '\n'.join(lines)
        focused.append({**record, 'answer': answer})
    return focused
