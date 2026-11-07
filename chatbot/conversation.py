"""A short program reference, never client-supplied facts or system prompts."""
import re
from chatbot.retriever import PROGRAMS, intents, program_entities, tokens

PENDING_TOPICS = {'description', 'academic_programs', 'careers', 'faculty', 'accreditation'}


def read_context(value):
    if value is None:
        return {'programs': []}
    if not isinstance(value, dict) or set(value) - {'programs', 'pending_topic'}:
        raise ValueError('Invalid conversation context')
    programs = value.get('programs', [])
    if not isinstance(programs, list) or len(programs) > 3 or any(not isinstance(p, str) or p not in PROGRAMS for p in programs):
        raise ValueError('Invalid conversation context')
    pending = value.get('pending_topic')
    if pending is not None and (not isinstance(pending, str) or pending not in PENDING_TOPICS):
        raise ValueError('Invalid conversation context')
    result = {'programs': sorted(set(programs))}
    if pending:
        result['pending_topic'] = pending
    return result


def resolve_question(message, context):
    named = program_entities(message)
    if named:
        if context.get('pending_topic') and not (tokens(message) - PROGRAMS - {'programs'}):
            topic = context['pending_topic']
            label = 'programs offer' if topic == 'academic_programs' else topic
            message = f'{message} {label}'
        return message, {'programs': sorted(named)}, False
    refers = bool(re.search(r'\b(?:(?:this|that|same)\s+(?:program|course|degree)|its|it|them|these programs|those programs|nito|niyan|ito|iyan)\b', message, re.I))
    short_followup = bool(re.match(r'\s*(?:and\b|how about\b|what about\b|paano naman\b)', message, re.I)) and bool(set(intents(message)) & {'careers', 'faculty', 'accreditation', 'description'})
    if refers or short_followup:
        previous = context['programs']
        if not previous or (len(previous) > 1 and re.search(r'\b(?:this|that|it|its)\b', message, re.I)):
            pending = next((topic for topic in intents(message) if topic in PENDING_TOPICS), 'description')
            return message, {**context, 'pending_topic': pending}, True
        return f"{message} ({', '.join(p.upper() for p in previous)})", context, False
    return message, {'programs': []}, False


def is_private_question(message):
    sensitive = re.search(r'\b(?:grades?|grado|marka|password|student records?|transcript|gpa)\b', message, re.I)
    personal = re.search(r"\b(?:my|his|her|their|your|student|aking|ko|ni|nya|namin|kaniya|kanyang|show|see|forgot|reset)\b|\b\w+'s\b", message, re.I)
    return bool(sensitive and personal)
