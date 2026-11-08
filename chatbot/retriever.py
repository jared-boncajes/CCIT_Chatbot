"""Lightweight, phrase-aware retrieval for a small, reviewed FAQ collection."""
import math
import re
import unicodedata
from collections import Counter
from difflib import get_close_matches
from functools import lru_cache

PROGRAMS = {'bsit', 'bscs', 'bsemc'}
MINIMUM_COVERAGE = .6
MODEL_RANK_BONUS = .25
MODEL_MIN_RANK_SCORE = .5
PHRASES = [
    (r'\bpre[ -]reqs?\b', 'prerequisites'),
    (r'\bco[ -]reqs?\b', 'corequisites'),
    (r'\b(cs|it|emc)([1-4])([ab]?)\b', r'\1 \2\3'),
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
    'rep': 'representatives', 'reps': 'representatives', 'representative': 'representatives',
    'officer': 'officers', 'org': 'organizations', 'orgs': 'organizations',
    'pres': 'president', 'prez': 'president', 'vp': 'vice_president',
    'sec': 'secretary', 'treas': 'treasurer',
    'subj': 'subjects', 'subjs': 'subjects', 'prof': 'faculty', 'profs': 'faculty',
    'yr': 'year', 'yrs': 'year',
    'prereq': 'prerequisites', 'prereqs': 'prerequisites',
    'coreq': 'corequisites', 'coreqs': 'corequisites',
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
    'dean': {'dean'}, 'faculty': {'faculty', 'chair'}, 'careers': {'careers', 'graduates'},
    'facilities': {'facilities'}, 'accreditation': {'accreditation', 'pacucoa', 'level'},
    'dost': {'dost'}, 'activities': {'activities', 'camp', 'night', 'frequency'},
}
INTENT_VOCABULARY = set(ALIASES) | set(ALIASES.values()) | {term for group in INTENT_TERMS.values() for term in group}
INTENT_VOCABULARY |= {'prerequisite', 'prerequisites', 'corequisite', 'corequisites', 'curriculum', 'subjects'}

EXTENDED_INTENTS = {
    'prerequisites': r'\b(?:pre[ -]?requisites?|co[ -]?requisites?)\b|\btake before\b|\bbefore (?:taking|enrolling|studying)\b|\benrollment requirements? (?:of|for)\b',
    'ojt': r'\b(?:ojt|internship|practicum)\b',
    'curriculum': r'\b(?:curricul(?:um|a)|subjects|study plan|checklist)\b',
    'organizations': r'\b(?:facts|organizations?|officers?|representatives?|adviser)\b',
    'community-service': r'\b(?:community service|comserve|skip|not attend|no attendance)\b',
}


# Explicit texting forms apply to every topic, without guessing arbitrary names,
# unknown degree codes, or missing facts. Preserve negations and course numbers.
SHORTHAND = {
    'whats': 'what is', 'wats': 'what is', 'wat': 'what', 'wht': 'what',
    'whos': 'who is', 'hu': 'who', 'whre': 'where', 'wher': 'where',
    'pls': 'please', 'plz': 'please', 'abt': 'about', 'ab': 'about',
    'dept': 'department', 'dep': 'department', 'depmt': 'department',
    'chrmn': 'chair', 'chairperson': 'chair', 'chairman': 'chair',
    'schlrshp': 'scholarship', 'schlrshps': 'scholarships',
    'prgrm': 'program', 'prgrms': 'programs', 'fclty': 'faculty',
    'faclty': 'faculty', 'crriclm': 'curriculum',
    'schlrship': 'scholarship', 'schlrships': 'scholarships',
    'scholarshp': 'scholarship', 'scholarshps': 'scholarships',
    'curric': 'curriculum', 'curr': 'curriculum', 'prereqs': 'prerequisites',
    'req': 'requirements', 'reqs': 'requirements', 'r': 'are', 'u': 'you',
    'ur': 'your', 'n': 'and', 'sinoo': 'sino', 'cno': 'sino', 'cnong': 'sino',
    'anu': 'ano', 'anung': 'anong', 'pde': 'pwede', 'pano': 'paano',
    'grdes': 'grades', 'pwd': 'password', 'dpt': 'department', 'fac': 'faculty', 'hrs': 'hours', 'hr': 'hours',
}


def expand_shorthand(text):
    text = unicodedata.normalize('NFKC', text).replace('’', "'")
    text = re.sub(r"\b(what|who|where|how)'?s\b", r'\1 is', text, flags=re.I)
    text = re.sub(r"\b(dont|cant|isnt|arent|wont)\b", lambda m: {
        'dont': 'do not', 'cant': 'cannot', 'isnt': 'is not',
        'arent': 'are not', 'wont': 'will not'}[m[0].lower()], text, flags=re.I)
    text = re.sub(r'\bpre[ -]reqs?\b', 'prerequisites', text, flags=re.I)
    text = re.sub(r'\bco[ -]reqs?\b', 'corequisites', text, flags=re.I)
    text = re.sub(r'\bcollege of (?:computing|computer) and information technology\b', 'CCIT', text, flags=re.I)
    text = re.sub(r'\b[a-zA-Z]+\b', lambda m: SHORTHAND.get(m[0].lower(), m[0]), text)
    # Lowercase it is a degree only beside an explicit program/role term.
    text = re.sub(r'\bit(?=\s+(?:department|program|chair|faculty)\b)', 'bsit', text)
    text = re.sub(r'\bchair\s+(?:(?:of|for)\s+)?it\b', 'chair bsit', text)
    text = re.sub(r'\b(heads?|namumuno)\b(?=.{0,80}\b(?:program|bsit|bscs|bsemc|computer science|information technology|multimedia)\b)', 'chair', text, flags=re.I)
    return text


def normalize(text):
    text = expand_shorthand(text)
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
    """Turn a sentence into a set of meaningful, consistently named words."""
    words = re.findall(r'[a-z0-9_]+', normalize(text))
    result = set()
    for word in words:
        if word not in STOP:
            result.add(_canonical_word(word))
    return result


def program_entities(text):
    query = tokens(text)
    named = query & PROGRAMS
    # Lowercase "it" is usually a pronoun. Beside a representative lookup,
    # however, it is the common IT program abbreviation.
    if 'representatives' in query and re.search(r'\bit(?:\s+[1-4](?:st|nd|rd|th)?[a-z]?(?:\s*(?:year|yr))?)?\s+(?:reps?|representatives?)\b', normalize(text)):
        named.add('bsit')
    return named


def intents(text):
    """Identify requested topics using the documented keyword lists above."""
    text = normalize(text)
    if (tokens(text) & {'prerequisite', 'prerequisites', 'corequisite', 'corequisites'}
            or re.search(EXTENDED_INTENTS['prerequisites'], text, re.I)):
        return ['prerequisites']
    if tokens(text) & {'representatives', 'officers', 'president', 'vice_president', 'secretary', 'treasurer', 'auditor', 'organizations'}:
        return ['organizations']
    if 'subjects' in tokens(text):
        return ['curriculum']
    for category in ('community-service', 'prerequisites', 'ojt', 'organizations', 'curriculum'):
        if re.search(EXTENDED_INTENTS[category], text, re.I):
            return [category]
    query = tokens(text)
    found = []
    for name, terms in INTENT_TERMS.items():
        if name != 'academic_programs' and query & terms:
            found.append(name)
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


def retrieve(question, records, model=None):
    """Filter sources first, then rank eligible records by topic and word support."""
    from chatbot.scope import scope_candidates
    records, clarification, _ = scope_candidates(question, records)
    if clarification or not records:
        return []
    # Authored question variants are explicit source support, including questions
    # whose wording predates the generic detail guards below. Prefer canonical
    # titles when an alternative also appears in a broader overview record.
    key = normalize(question).strip(' ?.\n')
    for field in ('question', 'alternative_questions'):
        exact = []
        for record in records:
            if record.get('verification_status') != 'verified':
                continue
            variants = [record['question']] if field == 'question' else record.get(field, [])
            if any(normalize(variant).strip(' ?.\n') == key for variant in variants):
                exact.append(record)
        if len(exact) == 1:
            return exact
    for record in records:
        if record.get('verification_status') != 'verified' or not _supported_detail(question, record):
            continue
        if 'chair' not in tokens(record['question']):
            continue
        person = record['answer'].split(' is the Department Chair')[0]
        name_words = tokens(person) - {'dr'}
        name_words = {word for word in name_words if len(word) > 1}
        query_names = tokens(question) - {'role', 'position', 'hold'}
        if len(name_words & query_names) >= 2 and query_names <= (name_words | {'chair'}):
            return [record]
    # Step 1: recognize the words, program abbreviations and requested topics.
    query = tokens(question)
    if not query:
        if 'ccit' in normalize(question) and (normalize(question).strip(' ?.') == 'ccit' or re.search(r'\b(?:about|what is|what\'s)\b', normalize(question))):
            question, query = 'What is CCIT all about?', {'overview'}
        else:
            return []
    # Step 2: exclude unreviewed sources and missing facts before scoring anything.
    reviewed = []
    for record in records:
        if record.get('verification_status') == 'verified':
            if _supported_detail(question, record):
                reviewed.append(record)
    if not reviewed:
        return []
    # Learned intent scores can rank source-supported candidates, but cannot
    # bypass the detail, topic, program, coverage or exact-question checks.
    probabilities = {}
    if model:
        for prediction in model.predict(question):
            # Diffuse closed-set predictions should not displace lexical
            # retrieval. This majority-score gate is a ranking heuristic,
            # not a calibrated confidence or factual-verification threshold.
            if prediction['score'] > MODEL_MIN_RANK_SCORE:
                probabilities[prediction['faq_id']] = prediction['score']
    requested_programs = query & PROGRAMS
    topics = intents(question)
    comparison = bool(requested_programs and (len(requested_programs) > 1 or query & {'difference', 'compare', 'versus', 'vs'}))
    if comparison and not set(topics) & {'faculty', 'careers', 'accreditation', 'dost'}:
        topics = ['description']
    # Step 3: count how many eligible documents contain each word.
    # Rarer matching words receive a little more weight in the ranking.
    documents = {}
    for record in reviewed:
        keywords = ' '.join(record.get('keywords', []))
        document_text = record['question'] + ' ' + keywords + ' ' + record['answer'] + ' ' + ' '.join(record.get('alternative_questions', []))
        documents[record['id']] = tokens(document_text)
    df = Counter()
    for words in documents.values():
        df.update(words)

    chosen = []
    chosen_ids = set()
    # Step 4: score candidates separately for each requested topic.
    for topic in topics or [None]:
        candidates = []
        for record in reviewed:
            category = record.get('category')
            if category == 'prerequisites':
                # Prerequisite answers mention other courses; those must never
                # select the wrong target course. Preserve + and - in codes.
                codes = re.findall(r'\b[A-Za-z][A-Za-z0-9-]*[0-9+][A-Za-z0-9+]*', question)
                target = re.search(r'requirements of (\S+)', record['question'])
                if codes and target and target[1].casefold() not in {c.casefold() for c in codes}:
                    continue
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
            matches = set()
            for word in relevant:
                if word in terms:
                    matches.add(word)
                elif len(word) >= 5:
                    if get_close_matches(word, terms, n=1, cutoff=.88):
                        matches.add(word)
            coverage = len(matches) / len(relevant)
            if coverage < MINIMUM_COVERAGE:
                continue
            title = tokens(record['question'] + ' ' + ' '.join(record.get('keywords', [])) + ' ' + ' '.join(record.get('alternative_questions', [])))
            score = 0
            for word in matches:
                rarity_weight = 1 + math.log((len(reviewed) + 1) / (df[word] + 1))
                if word in title:
                    title_weight = 2
                else:
                    title_weight = 1
                score += rarity_weight * title_weight
            score /= max(len(relevant), 1)
            score += MODEL_RANK_BONUS * probabilities.get(record['id'], 0)
            if (topic == 'scholarships'
                    and not query & {'eligibility', 'requirements'} and re.search(r'\d+%', record['answer'])):
                score += 2
            if normalize(question).strip(' ?.\n') == normalize(record['question']).strip(' ?.\n'):
                score += 10
            candidates.append((score, record))
        ranked = sorted(candidates, key=lambda pair: pair[0], reverse=True)
        # Step 5: keep one answer per topic, except explicit program comparisons
        # and requests for several program faculty/career lists.
        if topic == 'description' and len(requested_programs) > 1:
            selected = []
            for program in sorted(requested_programs):
                for score, record in ranked:
                    if record.get('category') == program:
                        selected.append(record)
                        break
        elif topic in {'faculty', 'careers'} and not requested_programs:
            selected = []
            for score, record in ranked[:3]:
                selected.append(record)
        else:
            selected = []
            if ranked:
                selected.append(ranked[0][1])
        for record in selected:
            if record['id'] not in chosen_ids:
                chosen.append(record)
                chosen_ids.add(record['id'])
    return chosen[:4]
