"""Require explicit subjects/programs before ranking narrowly scoped answers."""
import re

from chatbot.retriever import intents, normalize, program_entities, tokens

CODE_PATTERN = r'\b[a-z][a-z0-9-]*[0-9+][a-z0-9+]*'


def subject_codes(text, known_codes=()):
    codes = set(re.findall(CODE_PATTERN, text.casefold()))
    for code in known_codes:
        if re.search(r'(?<![\w+-])' + re.escape(code) + r'(?![\w+-])', text, re.I):
            codes.add(code.casefold())
    return codes


def curriculum_year(text):
    if text.strip() in {'1', '2', '3', '4'}:
        return int(text.strip())
    match = re.search(r'\b(?:([1-4])(?:st|nd|rd|th)?\s*(?:year|yr)|(?:year|yr)\s*([1-4]))\b', text, re.I)
    if match:
        return int(match[1] or match[2])
    for year, word in enumerate(('first', 'second', 'third', 'fourth'), 1):
        if re.search(rf'\b{word}[ -]year\b', text, re.I) or text.strip().casefold() == word:
            return year
    for year, word in enumerate(('freshm[ae]n', 'sophomores?', 'juniors?', 'seniors?'), 1):
        if re.search(rf'\b{word}\b', text, re.I):
            return year
    return None


def course_identity(record):
    return re.search(r'requirements of (\S+) \((.+)\) in the (\S+) curriculum', record['question'])


def scope_candidates(question, records):
    """Return eligible records, an optional clarification, and bounded selectors.

    Identity comes from the record's question, never incidental answer mentions
    or a classifier prediction. Unknown explicit selectors produce no match.
    """
    from chatbot.retriever import expand_shorthand
    question = expand_shorthand(question)
    topics = intents(question)
    named = program_entities(question)
    query = tokens(question)
    pending = {}
    reviewed = [r for r in records if r.get('verification_status') == 'verified']
    if not reviewed:
        return records, None, pending
    if 'chair' in query:
        chairs = [r for r in reviewed if 'chair' in tokens(r['question'])]
        if not named:
            return [], 'Which department chair do you mean: BSIT, BSCS, or BSEMC?', {'pending_topic': 'chair'}
        return [r for r in chairs if program_entities(r['question']) == named], None, {}
    identities = [(r, course_identity(r)) for r in reviewed if r.get('category') == 'prerequisites']
    identities = [(r, match) for r, match in identities if match]
    known_codes = {match[1].casefold() for _, match in identities}
    codes = subject_codes(question, known_codes)
    unknown_programs = set(re.findall(r'\bbs[a-z]{1,6}\b', normalize(question))) - {'bsit', 'bscs', 'bsemc'}
    if unknown_programs:
        return [], None, {}

    generic = query - {'help', 'details', 'need', 'needed', 'know', 'want'}
    prompts = {
        'requirements': 'Which requirements do you mean: a subject prerequisite, OJT, scholarships, or enrollment? Please include the subject or program.',
        'hours': 'Which hours do you mean: OJT, laboratory access, or community service? Please include the program or activity.',
        'contact': 'Who would you like to contact: FACTS, a faculty member, or the department office?',
        'schedule': 'Which schedule do you mean? Please name the activity, laboratory, or deadline.',
    }
    if len(generic) == 1 and next(iter(generic)) in prompts:
        topic = next(iter(generic))
        return [], prompts[topic], {'pending_topic': topic}
    if 'hours' in generic and not topics and not codes:
        return [], prompts['hours'], {'pending_topic': 'hours'}
    from chatbot.roster import is_roster_request, roster_records, selectors, selected_entries
    if is_roster_request(question):
        candidates = roster_records(reviewed)
        if 'representatives' in query and 'officers' not in query:
            programs, year, section = selectors(question)
            if (year and year not in range(1, 5)) or (not year and re.search(r'\b(?:[5-9](?:st|nd|rd|th)?|fifth|sixth)\s*(?:year|yr)\b', question, re.I)):
                return [], None, {}
            if year and not programs:
                pending = {'pending_topic': 'representatives', 'pending_year': year}
                if section:
                    pending['pending_section'] = section
                return [], 'Which program are those class representatives for: BSCS, BSIT, or BSEMC?', pending
            candidates = [r for r in candidates if selected_entries(r, question)]
        return candidates, None, {}
    if codes and (not topics or topics == ['description']):
        if not codes <= known_codes:
            return [], None, {}
        return [], 'What would you like to know about that subject: its prerequisites or where it appears in the curriculum? Please include your program.', {}

    if topics == ['prerequisites']:
        pending['pending_topic'] = 'prerequisites'
        if codes:
            if codes - known_codes:
                return [], None, {}
            candidates = [r for r, match in identities if match[1].casefold() in codes]
            if not candidates:
                return [], None, {}
        else:
            # Subject names may be abbreviated, but topic words alone cannot
            # establish a course. Two identifying words/numbers are required.
            subject = query - {'prerequisite', 'prerequisites', 'corequisite', 'corequisites',
                               'co', 'pre', 'requisite', 'requisites', 'requirements', 'required',
                               'subject', 'subjects', 'programs', 'curriculum', 'before', 'enroll',
                               'enrolling', 'need', 'needed', 'must', 'complete', 'completed',
                               'concurrent', 'alongside', 'rules', 'under', 'degree', 'taking'} - named
            if 'bsemc' in named:
                subject.discard('da')
            candidates = [r for r, match in identities
                          if subject and subject <= tokens(match[2])
                          and (len(subject) >= 2 or subject == tokens(match[2]))]
            if not candidates:
                if subject:
                    return [], None, {}
                return [], 'Which subject do you mean? Please provide its course code or name and your program (BSCS, BSIT, or BSEMC).', pending
        if named:
            candidates = [r for r in candidates if program_entities(r['question']) == named]
        if not candidates:
            return [], None, {}
        targets = {course_identity(r)[1] for r in candidates}
        if len(targets) != 1:
            return [], 'Which specific subject do you mean? Please provide one course code and your program.', pending
        pending['pending_subject'] = next(iter(targets))
        if len(candidates) > 1:
            return [], 'Which program is this subject for: BSCS, BSIT, or BSEMC?', pending
        return candidates, None, {}

    if topics == ['curriculum']:
        subject_list = 'subjects' in query and not re.search(r'\bcurricul(?:um|a)|study plan|checklist\b', question, re.I)
        pending['pending_topic'] = 'subjects' if subject_list else 'curriculum'
        year = curriculum_year(question)
        if not year and re.search(r'\b(?:\d+(?:st|nd|rd|th)?|fifth|sixth)\s*(?:year|yr)\b', question, re.I):
            return [], None, {}
        if year:
            pending['pending_year'] = year
        if not named:
            return [], 'Which program do you mean: BSCS, BSIT, or BSEMC? You can also include the year level.', pending
        if len(named) != 1:
            return [], 'Please choose one program for the curriculum or subject list: BSCS, BSIT, or BSEMC.', pending
        candidates = [r for r in reviewed if r.get('category') == 'curriculum'
                      and program_entities(r['question']) == named]
        if year:
            candidates = [r for r in candidates if curriculum_year(r['question']) == year]
        elif subject_list:
            return [], 'Which year level do you mean: first, second, third, or fourth year?', pending
        else:
            candidates = [r for r in candidates if curriculum_year(r['question']) is None]
        return candidates, None, {}

    if topics == ['ojt']:
        placement = query & {'company', 'companies', 'placement', 'find', 'finding', 'help', 'assist', 'assistance'}
        if not placement and not named:
            return [], 'Which program are you asking about: BSCS, BSIT, or BSEMC? If you mean help finding an OJT company, please say so.', {'pending_topic': 'ojt'}
        candidates = [r for r in reviewed if r.get('category') == 'ojt']
        if placement:
            candidates = [r for r in candidates if not program_entities(r['question'])]
        else:
            candidates = [r for r in candidates if program_entities(r['question']) == named]
        return candidates, None, {}

    if topics == ['organizations'] and query & {'contact', 'email', 'phone', 'social', 'media', 'facebook'}:
        # Participation records may mention contacting an officer in passing;
        # a directory request must use the dedicated contact record.
        return [r for r in reviewed if r.get('category') == 'organizations'
                and 'contact' in tokens(r['question'])], None, {}

    # General topic requests use their overview instead of arbitrarily choosing
    # an event, laboratory procedure or student officer mentioned in the answer.
    if generic and generic <= {'activities', 'campus', 'student'} and not re.search(r'non[ -]academic', question, re.I):
        return [r for r in reviewed if r.get('category') == 'activities'
                and 'what events does ccit organize' in r['question'].casefold()], None, {}
    if generic and generic <= {'facts', 'organizations', 'organization', 'student'}:
        return [r for r in reviewed if r.get('category') == 'organizations'
                and 'what student organization' in r['question'].casefold()], None, {}
    if generic and generic <= {'community', 'service', 'comserve'}:
        return [], 'Do you mean the consequences of missing an event, or how to render community service hours?', {'pending_topic': 'community-service'}
    return records, None, {}
