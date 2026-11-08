"""A short program reference, never client-supplied facts or system prompts."""
import re
from chatbot.retriever import PROGRAMS, intents, program_entities, tokens

PENDING_TOPICS = {'description', 'academic_programs', 'careers', 'faculty', 'accreditation'}


def read_context(value):
    """Accept only program names and an optional topic awaiting clarification."""
    if value is None:
        return {'programs': []}
    if not isinstance(value, dict):
        raise ValueError('Invalid conversation context')
    for key in value:
        if key not in {'programs', 'pending_topic'}:
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
    return result


def resolve_question(message, context):
    """Add the previous program name to a follow-up, or ask the user to choose."""
    named = program_entities(message)
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
