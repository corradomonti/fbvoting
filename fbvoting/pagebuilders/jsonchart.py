from itertools import islice

from flask import abort

from fbvoting.db.chart import chart_iterator
from fbvoting.recommendation.mixedchart import recommendation_iterator
from fbvoting.apis.fb import get_user_id
from fbvoting.directvote import attach_cover_to_dbdoc

HOW_MANY_PER_PAGE = 3

class RankType(object):
    CHART = "chart"
    RECOMMENDATION = "recommendation"

rankTypes = set([RankType.CHART, RankType.RECOMMENDATION])


def get_ranks(rank_type, category, page=0, attach_cover=True):
    assert type(category) in (str, unicode)
    assert type(page) is int
    
    if rank_type == RankType.CHART:
        iterator = chart_iterator(category)
    elif rank_type == RankType.RECOMMENDATION:
        iterator = recommendation_iterator(get_user_id(), category)
    else:
        abort(404)
    
    start = page * HOW_MANY_PER_PAGE
    stop = start + HOW_MANY_PER_PAGE
    
    ranks = list(islice(iterator, start, stop))
    for position, item in enumerate(ranks, start+1):
        item['position'] = position
        if attach_cover:
            attach_cover_to_dbdoc(item['advice'])
    
    return ranks
