"""Lightweight, phrase-aware retrieval for a small, reviewed FAQ collection."""
import math
import re
import unicodedata
from collections import Counter
from difflib import get_close_matches
from functools import lru_cache

PROGRAMS = {'bsit', 'bscs', 'bsemc'}
PHRASES = [
    (r'\bcourse[\s-]+specific\b', 'course_specific'),
    (r'\bprogram[\s-]+specific scholarships?\b', 'scholarships'),
    (r'\b50[\s-]*tag\b', '50tag'),
    (r'\b(?:bachelor of science in |bs )?entertainment and multimedia(?: computing)?\b', 'bsemc'),
    (r'\b(?:bachelor of science in |bs )?computer science\b', 'bscs'),
    (r'\b(?:bachelor of science in |bs )?information technology\b', 'bsit'),
    (r'\bfinancial (?:aid|assistance|support)\b', 'scholarships'),
    (r'\bcareer opportunities\b', 'careers'),
    (r'\bgame (?:development|design|developer)\b', 'game_development'),
    (r'\bnon[\s-]+academic(?: programs?)?\b', 'activities'),
    (r'\bhow often\b', 'frequency'),
    (r'\bhow long\b', 'duration'),
    (r'\bin charge of\b', 'dean'),
    (r'\bpag[\s-]*(?:aaral|aralan)\b', 'programs'),
    (r'\banu[\s-]*anong\b', 'ano'),
]
ALIASES = {
    'course': 'programs', 'courses': 'programs', 'program': 'programs',
    'degree': 'programs', 'degrees': 'programs', 'kurso': 'programs', 'kursong': 'programs',
    'offered': 'offer', 'offers': 'offer', 'offering': 'offer', 'inooffer': 'offer', 'inaalok': 'offer',
    'study': 'programs', 'studying': 'programs', 'studies': 'programs', 'kunin': 'programs', 'pursue': 'programs',
    'take': 'programs', 'cs': 'bscs', 'emc': 'bsemc',
    'bachelor': 'undergraduate', 'bachelors': 'undergraduate',
    'scholarship': 'scholarships', 'scholar': 'scholarships', 'scholars': 'scholarships', 'iskolar': 'scholarships',
    'discounts': 'discount', 'qualifications': 'eligibility', 'qualification': 'eligibility',
    'qualified': 'eligibility', 'qualify': 'eligibility', 'requirements': 'requirements',
    'dekan': 'dean', 'dekana': 'dean', 'head': 'dean', 'heads': 'dean',
    'teachers': 'faculty', 'teacher': 'faculty', 'teaches': 'faculty', 'professors': 'faculty', 'guro': 'faculty',
    'instructor': 'faculty', 'instructors': 'faculty', 'professor': 'faculty', 'namumuno': 'dean',
    'jobs': 'careers', 'job': 'careers', 'career': 'careers', 'graduates': 'graduates', 'graduating': 'graduates',
    'laboratory': 'facilities', 'laboratories': 'facilities', 'lab': 'facilities', 'labs': 'facilities',
    'facility': 'facilities', 'accredited': 'accreditation', 'accreditations': 'accreditation',
    'events': 'activities', 'activity': 'activities', 'objectives': 'goals', 'goal': 'goals',
    'trabaho': 'careers', 'work': 'careers', 'focuses': 'focus', 'purpose': 'mission',
    'masters': 'graduate', 'master': 'graduate', 'doctorate': 'graduate', 'phd': 'graduate',
    'emails': 'email', 'contacts': 'contact', 'deadlines': 'deadline', 'fees': 'fee',
}
STOP = set('''what which who is are was were the a an does do did can could would will i you we they
    sa ang mga ano anong ba may meron po sino ng nang na ni kong ko pwede pwedeng bang
    about please tell me of in at for have has any available after from this that these those
    it its guys college ccit faith colleges and or also there on to as with by how get much
    then studying description explain information of today dr m between all show list s
    inyo ninyo puwede puwedeng pagkatapos department'''.split())
# These terms identify intent. Other query words still need source support.
INTENT_TERMS = {
    'overview': {'meaning', 'stands', 'overview', 'about'},
    'vision': {'vision'}, 'mission': {'mission'}, 'goals': {'goals'},
    'academic_programs': {'programs', 'offer', 'study', 'graduate'},
    'scholarships': {'scholarships', 'discount', '50tag', 'course_specific', 'eligibility'},
    'dean': {'dean'}, 'faculty': {'faculty'}, 'careers': {'careers', 'graduates'},
    'facilities': {'facilities'}, 'accreditation': {'accreditation', 'pacucoa', 'level'},
    'dost': {'dost'}, 'activities': {'activities', 'camp', 'night', 'frequency'},
}
INTENT_VOCABULARY = set(ALIASES) | set(ALIASES.values()) | {term for group in INTENT_TERMS.values() for term in group}


def normalize(text):
    text = re.sub(r'\bIT\b', 'bsit', text)
    text = unicodedata.normalize('NFKC', text).casefold().replace('’', "'")
    # The college's name contains Information Technology; that alone is not
    # evidence that a statement concerns the BSIT degree or its program staff.
    text = re.sub(r'\bcollege of (?:computing|computer) and information technology\b', 'ccit', text)
    for pattern, replacement in PHRASES:
        text = re.sub(pattern, replacement, text)
    return text


@lru_cache(maxsize=4096)
def _canonical_word(word):
    # Cache only bounded word normalization, never conversations or answers.
    # Abbreviations are deliberately too short for intent typo correction.
    if word not in INTENT_VOCABULARY and len(word) >= 6:
        close = get_close_matches(word, INTENT_VOCABULARY, n=1, cutoff=.9)
        if close:
            word = close[0]
    return ALIASES.get(word, word)


def tokens(text):
    words = re.findall(r'[a-z0-9_]+', normalize(text))
    return {_canonical_word(word) for word in words if word not in STOP}


def program_entities(text):
    return tokens(text) & PROGRAMS


def intents(text):
    query = tokens(text)
    found = [name for name, terms in INTENT_TERMS.items()
             if name != 'academic_programs' and query & terms]
    if re.search(r'\b(?:meaning|stands? for|all about)\b', normalize(text)) or normalize(text).strip(' ?.') == 'ccit':
        if 'overview' not in found:
            found.insert(0, 'overview')
    # DOST acceptance is a separate source from general scholarships.
    if 'dost' in found:
        found = [name for name in found if name != 'scholarships']
    program_request = bool(query & INTENT_TERMS['academic_programs'])
    dependent = {'faculty', 'careers', 'accreditation', 'dost', 'activities', 'vision', 'mission', 'goals'}
    if (program_request and not (set(found) & dependent)
            and not (set(found) == {'scholarships'} and not (query & {'programs', 'study', 'graduate'}))):
        found.insert(0, 'academic_programs')
    if not found and query & PROGRAMS:
        found = ['description']
    if found == ['overview'] and query & PROGRAMS:
        found = ['description']
    if not found and query & {'game_development', 'animation', 'multimedia'}:
        found = ['description']
    if 'academic_programs' in found and query & PROGRAMS and not (query & {'offer', 'graduate'}):
        found = ['description' if name == 'academic_programs' else name for name in found]
    if 'academic_programs' in found and query & {'game_development', 'animation', 'multimedia'}:
        found = ['description' if name == 'academic_programs' else name for name in found]
    if found == ['description'] and query & PROGRAMS and re.search(r'^(?:do|does)\b|\bis there\b|\b(?:can|may|meron|offer|offered|available|study|kunin)\b', normalize(text).strip()):
        found = ['academic_programs']
    return list(dict.fromkeys(found))


def _supported_detail(question, record):
    """A broad topic match cannot establish a missing fee, deadline or contact."""
    query = tokens(question)
    answer = record['answer']
    body = tokens(record['question'] + ' ' + answer + ' ' + ' '.join(record.get('keywords', [])))
    unsupported_modifiers = query & {'online', 'hybrid', 'distance', 'weekend', 'evening', 'free', 'best', 'worst', 'ranking', 'guaranteed', 'everyone', 'automatic'}
    if not unsupported_modifiers <= body:
        return False
    years = {word for word in query if re.fullmatch(r'20\d{2}', word)}
    if not years <= body:
        return False
    if query & {'phone', 'email', 'contact', 'address', 'location', 'office'}:
        if not (body & (query & {'phone', 'email', 'contact', 'address', 'location', 'office'})):
            return False
    if query & {'deadline', 'tomorrow', 'bukas', 'schedule', 'meeting', 'hours', 'open', 'opening', 'time', 'oras', 'birthday', 'salary', 'age', 'duration'}:
        if not (query & {'deadline', 'tomorrow', 'bukas', 'schedule', 'meeting', 'hours', 'open', 'opening', 'time', 'oras', 'birthday', 'salary', 'age', 'duration'}) <= body:
            return False
    if 'where' in query and record.get('category') != 'careers' and not body & {'located', 'location', 'address'}:
        return False
    if query & {'tuition', 'fee', 'cost', 'price', 'amount', 'magkano', 'bayad'} and not query & {'scholarships', 'discount', '50tag', 'course_specific'}:
        if not re.search(r'(?:₱|PHP\s*|pesos\s*)\d', answer, re.I):
            return False
    if query & {'enrollment', 'enroll', 'admission', 'forms', 'form', 'application', 'apply', 'paano'}:
        required = query & {'enrollment', 'enroll', 'forms', 'form', 'application', 'apply', 'paano'}
        if required and not required <= body:
            return False
        if 'requirements' in query and record.get('category') not in {'admissions', 'enrollment'}:
            return False
    # Unsupported program abbreviations must not fuzzy-match an offered degree.
    unknown_programs = set(re.findall(r'\bbs[a-z]{1,6}\b', normalize(question))) - PROGRAMS
    if unknown_programs - body:
        return False
    return True


def _record_category(record):
    return record.get('category')


def retrieve(question, records):
    query = tokens(question)
    if not query:
        if 'ccit' in normalize(question) and (normalize(question).strip(' ?.') == 'ccit' or re.search(r'\b(?:about|what is|what\'s)\b', normalize(question))):
            question, query = 'What is CCIT all about?', {'overview'}
        else:
            return []
    reviewed = [r for r in records if r.get('verification_status') == 'verified' and _supported_detail(question, r)]
    if not reviewed:
        return []
    requested_programs = query & PROGRAMS
    topics = intents(question)
    comparison = bool(requested_programs and (len(requested_programs) > 1 or query & {'difference', 'compare', 'versus', 'vs'}))
    if comparison and not set(topics) & {'faculty', 'careers', 'accreditation', 'dost'}:
        topics = ['description']
    documents = {r['id']: tokens(r['question'] + ' ' + ' '.join(r.get('keywords', [])) + ' ' + r['answer']) for r in reviewed}
    df = Counter(word for words in documents.values() for word in words)
    chosen = []
    for topic in topics or [None]:
        candidates = []
        for record in reviewed:
            category = _record_category(record)
            if topic == 'description':
                allowed = requested_programs or ({'bsemc'} if query & {'game_development', 'animation', 'multimedia'} else PROGRAMS)
                if category and category not in allowed:
                    continue
            elif topic and category and category != topic:
                continue
            terms = documents[record['id']]
            if requested_programs and topic != 'academic_programs' and not requested_programs <= terms:
                # For comparisons, one description per requested program is needed.
                if not (topic == 'description' and category in requested_programs):
                    continue
            relevant = set(query)
            for other in topics:
                if other != topic:
                    relevant -= INTENT_TERMS.get(other, set())
            if topic == 'description':
                relevant -= {'difference', 'compare', 'versus', 'vs', 'programs', 'study', 'offer'}
                relevant -= requested_programs - ({category} if category in PROGRAMS else requested_programs)
            elif topic not in {'academic_programs', None}:
                relevant -= {'programs', 'offer', 'study', 'graduates'}
            if topic == 'careers':
                relevant.discard('where')
            if not relevant:
                relevant = query
            matches = {word for word in relevant if word in terms or (
                len(word) >= 5 and get_close_matches(word, terms, n=1, cutoff=.88))}
            coverage = len(matches) / len(relevant)
            if coverage < .6:
                continue
            title = tokens(record['question'] + ' ' + ' '.join(record.get('keywords', [])))
            score = sum((1 + math.log((len(reviewed) + 1) / (df[word] + 1))) * (2 if word in title else 1) for word in matches)
            score /= max(len(relevant), 1)
            if (topic == 'scholarships' and query & {'course_specific', '50tag', 'discount'}
                    and not query & {'eligibility', 'requirements'} and re.search(r'\d+%', record['answer'])):
                score += 2
            if normalize(question).strip(' ?.\n') == normalize(record['question']).strip(' ?.\n'):
                score += 10
            candidates.append((score, record))
        ranked = sorted(candidates, key=lambda pair: pair[0], reverse=True)
        if topic == 'description' and len(requested_programs) > 1:
            selected = []
            for program in sorted(requested_programs):
                match = next((r for _, r in ranked if r.get('category') == program), None)
                if match:
                    selected.append(match)
        elif topic in {'faculty', 'careers'} and not requested_programs:
            selected = [r for _, r in ranked[:3]]
        else:
            selected = [ranked[0][1]] if ranked else []
        for record in selected:
            if record['id'] not in {r['id'] for r in chosen}:
                chosen.append(record)
    return chosen[:4]
