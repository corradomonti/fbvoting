from collections import defaultdict
import logging

from fbvoting.db.directvote import get_direct_votes
from fbvoting.db.delegatevote import get_delegate
from fbvoting.directvote import dbdoc2comparable

from fbvoting.conf import DUMP_FACTOR, RANK_THRESHOLD


logger = logging.getLogger(__name__)

def get_personal_ranks(user_id, category):
    """ Returns a dictionary advice -> rank.
    Advice is result of dbdoc2comparable, and input of find_rank. """
    assert type(user_id) in (int, long)
    assert type(category) in (str, unicode)
    
    logger.debug("Recomputing personal ranks for " + str((user_id, category)) + ".")
    
    delegate = get_delegate(user_id, category)
    current_rank = 1.0
    ranks = defaultdict(float)
    
    while delegate is not None:
        
        for advice in get_direct_votes(delegate, category):
            ranks[dbdoc2comparable(advice)] += current_rank
        
        current_rank *= DUMP_FACTOR
        
        if current_rank < RANK_THRESHOLD:
            break
        else:
            delegate = get_delegate(delegate, category)
    
    if not ranks:
        return {}
    
    # max-normalization
    max_norm = max(ranks.values())
    normalized_ranks = {}
    for advice, score in ranks.items():
        normalized_ranks[advice] = score / max_norm
    
    
    return normalized_ranks

