"""A short program reference, never client-supplied facts or system prompts."""
import re
from chatbot.retriever import PROGRAMS, intents, program_entities, tokens

PENDING_TOPICS = {'description', 'academic_programs', 'careers', 'faculty', 'accreditation', 'prerequisites', 'curriculum', 'subjects', 'ojt', 'representatives'}
SCOPED_TOPICS = {'prerequisites', 'curriculum', 'subjects', 'ojt', 'representatives'}
GENERIC_TOPICS = {'requirements', 'hours', 'contact', 'schedule', 'community-service'}
PENDING_TOPICS |= GENERIC_TOPICS


def read_context(value):
    """Accept only program names and an optional topic awaiting clarification."""
    if value is None:
        return {'programs': []}
    if not isinstance(value, dict):
        raise ValueError('Invalid conversation context')
    for key in value:
        if key not in {'programs', 'pending_topic', 'pending_subject', 'pending_year', 'pending_section', 'topic'}:
            raise ValueError('Invalid conversation context')
    programs = value.get('programs', [])
    if not isinstance(programs, list) or len(programs) > 3:
        raise ValueError('Invalid conversation context')
    for program in programs:
        if not isinstance(program, str) or program not in PROGRAMS:
            raise ValueError('Invalid conversation context')
    pending = value.get('pending_topic')
    if pending is not None and (not isinstance(pending, str) or pending not in PENDING_TOPICS):
        raise ValueError('Invalid conversation context')
    result = {'programs': sorted(set(programs))}
    if pending:
        result['pending_topic'] = pending
    subject = value.get('pending_subject')
    if subject is not None:
        if pending != 'prerequisites' or not isinstance(subject, str) or len(subject) > 32 or not re.fullmatch(r'[A-Za-z][A-Za-z0-9+-]*', subject):
            raise ValueError('Invalid subject context')
        result['pending_subject'] = subject
    year = value.get('pending_year')
    if year is not None:
        if pending not in {'curriculum', 'subjects', 'representatives'} or type(year) is not int or year not in range(1, 5):
            raise ValueError('Invalid year context')
        result['pending_year'] = year
    section = value.get('pending_section')
    if section is not None:
        if pending != 'representatives' or not isinstance(section, str) or not re.fullmatch(r'[A-Z]', section):
            raise ValueError('Invalid section context')
        result['pending_section'] = section
    if value.get('topic') is not None:
        if value['topic'] != 'representatives':
            raise ValueError('Invalid topic context')
        result['topic'] = value['topic']
    return result


def resolve_question(message, context):
    """Add the previous program name to a follow-up, or ask the user to choose."""
    named = program_entities(message)
    from chatbot.scope import curriculum_year, subject_codes
    pending = context.get('pending_topic')
    current_topics = set(intents(message))
    if context.get('topic') == 'representatives' and not pending:
        # Retain the roster topic for selector follow-ups, not unrelated questions.
        selector_words = tokens(message) - named - {'and', 'year', 'yr', 'first', 'second', 'third', 'fourth', '1st', '2nd', '3rd', '4th', '1', '2', '3', '4'}
        if not selector_words and (named or curriculum_year(message)):
            previous = named or set(context['programs'])
            message += ' representatives'
            if not named and len(previous) == 1:
                message += ' ' + next(iter(previous)).upper()
            return message, {'programs': sorted(previous)}, False
    generic_replies = {
        'contact': {'facts', 'department', 'office', 'faculty'},
        'hours': {'ojt', 'facilities', 'community', 'service'},
        'requirements': {'scholarships', 'ojt', 'enrollment', 'prerequisites'},
        'schedule': {'camp', 'night', 'codequest', 'artventure', 'activities', 'facilities'},
        'community-service': {'render', 'complete', 'missing', 'event', 'activities', 'consequences'},
    }
    if pending in GENERIC_TOPICS and tokens(message) and (not current_topics or tokens(message) <= generic_replies.get(pending, set())):
        return message + ' ' + pending.replace('-', ' '), {'programs': sorted(named)}, False
    if pending in SCOPED_TOPICS:
        answer_year = curriculum_year(message)
        program_reply = bool(named and not (tokens(message) - named - {'programs', 'da'}))
        # Only selector replies or the same topic continue a clarification.
        # A fresh question such as "Who is the dean?" discards pending state.
        selector_reply = bool(subject_codes(message) or curriculum_year(message))
        selector_reply |= program_reply
        selector_reply |= tokens(message) <= {'hours', 'company', 'companies', 'placement'}
        if selector_reply or pending in current_topics or not current_topics:
            previous = named or set(context['programs'])
            if pending not in current_topics:
                message += ' ' + pending
            if not named and len(previous) == 1:
                message += ' ' + next(iter(previous)).upper()
            if context.get('pending_subject') and program_reply:
                message += ' ' + context['pending_subject']
            year = answer_year or context.get('pending_year')
            if year and not curriculum_year(message):
                message += ' year ' + str(year)
            if context.get('pending_section') and year:
                message += f' {year}{context["pending_section"]}'
            return message, {'programs': sorted(previous)}, False
    if current_topics & SCOPED_TOPICS and not named and len(context['programs']) == 1:
        message += ' ' + context['programs'][0].upper()
        return message, {'programs': context['programs']}, False
    if named:
        extra_words = tokens(message) - PROGRAMS - {'programs'}
        if context.get('pending_topic') and not extra_words:
            topic = context['pending_topic']
            if topic == 'academic_programs':
                label = 'programs offer'
            else:
                label = topic
            message = f'{message} {label}'
        return message, {'programs': sorted(named)}, False

    reference_pattern = r'\b(?:(?:this|that|same)\s+(?:program|course|degree)|its|it|them|these programs|those programs|nito|niyan|ito|iyan)\b'
    followup_pattern = r'\s*(?:and\b|how about\b|what about\b|paano naman\b)'
    refers = bool(re.search(reference_pattern, message, re.I))
    followup_topics = {'careers', 'faculty', 'accreditation', 'description'}
    starts_like_followup = bool(re.match(followup_pattern, message, re.I))
    short_followup = starts_like_followup and bool(set(intents(message)) & followup_topics)
    if refers or short_followup:
        previous = context['programs']
        singular_reference = re.search(r'\b(?:this|that|it|its)\b', message, re.I)
        if not previous or (len(previous) > 1 and singular_reference):
            pending = 'description'
            for topic in intents(message):
                if topic in PENDING_TOPICS:
                    pending = topic
                    break
            next_context = context.copy()
            next_context['pending_topic'] = pending
            return message, next_context, True

        program_names = []
        for program in previous:
            program_names.append(program.upper())
        resolved = message + ' (' + ', '.join(program_names) + ')'
        return resolved, context, False
    return message, {'programs': []}, False


def is_private_question(message):
    """Detect requests for personal grades/passwords; no record database exists."""
    sensitive = re.search(r'\b(?:grades?|grado|marka|password|student records?|transcript|gpa)\b', message, re.I)
    personal = re.search(r"\b(?:my|his|her|their|your|student|aking|ko|ni|nya|namin|kaniya|kanyang|show|see|forgot|reset)\b|\b\w+'s\b", message, re.I)
    return bool(sensitive and personal)
