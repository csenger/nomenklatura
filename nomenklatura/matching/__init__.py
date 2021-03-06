import logging

from nomenklatura.core import db
from nomenklatura.model import Value

from nomenklatura.matching.normalize import normalize
from nomenklatura.matching.levenshtein import levenshtein
from nomenklatura.matching.fw import fw

log = logging.getLogger(__name__)

ALGORITHMS = {
        'levenshtein': levenshtein,
        'fuzzywuzzy': fw
    }

def get_algorithms():
    algorithms = []
    for name, fn in ALGORITHMS.items():
        algorithms.append((name, fn.__doc__))
    return algorithms

def get_candidates(dataset):
    candidates = set()
    for value in Value.all(dataset, eager_links=dataset.match_links):
        candidate = normalize(value.value, dataset)
        candidates.add(candidate)
        yield candidate, value
        if dataset.match_links:
            for link in value.links_static:
                candidate = normalize(link.key, dataset)
                if candidate in candidates:
                    continue
                candidates.add(candidate)
                yield candidate, value

def match(text, dataset, query=None):
    import time
    begin = time.time()
    choices = _match(text, dataset, query=query)
    duration = time.time() - begin
    log.info("Matching %s candidates took: %sms",
            len(choices), duration*1000)
    return choices

def _match(text, dataset, query=None):
    query = '' if query is None else query.strip().lower()
    text_normalized = normalize(text, dataset)
    matches = []
    func = ALGORITHMS.get(dataset.algorithm, levenshtein)
    for candidate, value in get_candidates(dataset):
        if len(query) and query not in candidate.lower():
            continue
        score = func(text_normalized, candidate)
        matches.append((candidate, value, score))
    matches = sorted(matches, key=lambda (c,v,s): s, reverse=True)
    values = []
    matches_uniq = []
    for c,v,s in matches:
        if v in values:
            continue
        values.append(v)
        matches_uniq.append((c,v,s))
    return matches_uniq


