import itertools, logging
from operator import itemgetter
from uuid import uuid4 as uuid

from fbvoting.db.chart import find_rank, get_chart_elements_higher_than, get_sorted_chart_elements_lower_than
from personalranks import get_personal_ranks
from fbvoting.conf import MIXING_FACTOR
from fbvoting.rediscache import redis_cached

logger = logging.getLogger(__name__)

# k * p + (1 - k) * q
# gives the same ranking as
# (k / (1-k)) * p + q
# therefore:

PERSONAL_COEFF = MIXING_FACTOR / (1 - MIXING_FACTOR)
NORMALIZING_FACTOR = PERSONAL_COEFF + 1 # maximum score (for p = 1 and q = 1)

@redis_cached
def mixed_ranks_list(user_id, category):
    assert type(user_id) in (int, long)
    assert type(category) in (str, unicode)
    
    logger.debug("Mixing global and personal ranks for " + str((user_id, category)) + "...")
    
    # compute personal rankings
    personal_chart = get_personal_ranks(user_id, category)
    if not personal_chart:
        return float('inf'), [], []
    
    # mix those rankings with the global ones for the same items
    mixed_chart = []
    for voted_item, personal_rank_value in personal_chart.items():
        mixed_rank = find_rank(voted_item, category)
        if mixed_rank is None:
            mixed_rank = {'_id': uuid(), 'rank': 0, 'advice': voted_item}
        mixed_rank['rank'] += PERSONAL_COEFF * personal_rank_value
        mixed_chart.append(mixed_rank)
    
    # ids of ranks that have been changed
    changed_ids = map(itemgetter('_id'), mixed_chart)
    # i can delete ids now
    for doc in mixed_chart:
        del doc['_id']
    
    # minimum of the changed rankings: those below do not need to be re-sorted
    min_new_rank = min(map(itemgetter('rank'), mixed_chart))
    
    # now, I'll extract the part of the global ranks that need to be sorted...
    new_chart = list(get_chart_elements_higher_than(min_new_rank,
                    category, exclude_ids = changed_ids))
    # and I'll mix this list with the changed one, and sort 'em.
    new_chart = sorted(new_chart + mixed_chart, key = itemgetter('rank'), reverse=True)
    
    logger.debug("Recomputed personal ranks for " + str((user_id, category)) + ".")
    
    return min_new_rank, changed_ids, new_chart


def _normalize(db_obj):
    db_obj['rank'] /= NORMALIZING_FACTOR
    return db_obj

def recommendation_iterator(user_id, category):
    assert type(user_id) in (int, long)
    assert type(category) in (str, unicode)
    
    min_new_rank, changed_ids, new_chart = mixed_ranks_list(user_id, category)
    
    # finally, I'll attach all the other items in the global ranks
    unchanged_chart = get_sorted_chart_elements_lower_than(min_new_rank, category, exclude_ids = changed_ids)
    
    iterator = itertools.chain(new_chart, unchanged_chart)
    
    return itertools.imap(_normalize, iterator)

