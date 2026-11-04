"""Conservative lexical retrieval; only reviewed records may support answers."""
import re
from difflib import get_close_matches

ALIASES = {'courses':'programs','course':'programs','degrees':'programs','kurso':'programs','alok':'offer','iskolar':'scholarships','scholarship':'scholarships','guro':'faculty','teachers':'faculty','laboratories':'facilities','labs':'facilities','jobs':'careers','career':'careers','teacher':'faculty','teachers':'faculty','dekan':'dean','scholar':'scholarships'}
STOP = set('what which who is are the a an does do can i you sa ang mga ano ba ccit about please tell me of in at for have any available offer offers after graduating pursue from program students it guys may meron po sino ang mga does college'.split())

def tokens(text):
    text = re.sub(r'computer science', 'bscs', text, flags=re.I)
    text = re.sub(r'information technology', 'bsit', text, flags=re.I)
    text = re.sub(r'entertainment and multimedia(?: computing)?', 'bsemc', text, flags=re.I)
    return {ALIASES.get(t,t) for t in re.findall(r'[a-z0-9]+', text.lower())} - STOP

def retrieve(question, records):
    query = tokens(question)
    ranked = []
    anchors = {'bscs','bsit','bsemc','dost','faculty','careers','dean','mission','vision','goals','facilities','accreditation','activities'}
    for record in records:
        if record.get('verification_status') != 'verified':
            continue
        if 'programs' in query and not (query & {'activities','bsit','bscs','bsemc','careers','faculty'}) and record.get('category') not in (None,'academic_programs'):
            continue
        terms = tokens(record['question'] + ' ' + ' '.join(record.get('keywords', [])))
        if (query & anchors) - terms:
            continue
        matched = sum(t in terms or bool(get_close_matches(t, terms, n=1, cutoff=.88)) for t in query)
        score = matched / max(len(query), 1)
        if matched and score >= .6:
            ranked.append((score, record))
    return [r for _, r in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:3]]
