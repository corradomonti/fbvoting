import re, logging
from numbers import Number
from itertools import imap

import pymongo

from fbvoting.db.db import mongodb
from fbvoting.rediscache import redis_cached

logger = logging.getLogger(__name__)

sorting_order = [('rank', pymongo.DESCENDING), ('_id', pymongo.ASCENDING)]

@redis_cached
def _get_norm(category):
    return mongodb.chartnorm.find({"_id": category}, limit=1)[0]['norm']


def _normalizator(category):
    norm = _get_norm(category)
    def _norm_rank(db_obj):
        db_obj['rank'] /= norm
        return db_obj
    return _norm_rank


def chart_iterator(category):
    """ Returns an iterator over documents such as {'advice': ..., 'rank': ...}
    sorted by rank. """
    assert type(category) in (str, unicode)
    
    collection = mongodb['chart-' + category]
    db_cursor = collection.find(
                    sort=sorting_order,
                    fields= {'advice': 1, 'rank':1, '_id': 0}
                )
    
    return imap(_normalizator(category), db_cursor)

def get_chart_elements_higher_than(min_rank, category, exclude_ids=None):
    """ Return an iterator over doc such as {'advice':x, 'rank': y} for all
    documents with rank higher than min_rank. """
    assert isinstance(min_rank, Number)
    assert type(category) in (str, unicode)
    assert type(exclude_ids) in (None, list, tuple)
    
    min_rank = min_rank * _get_norm(category) # un-normalizing
    
    query = {"rank" : {"$gte": min_rank}}
    if exclude_ids:
        query["_id"] = {"$nin": exclude_ids}
    
    db_cursor = mongodb['chart-' + category].find(query,
                                fields= {'advice': 1, 'rank':1, '_id': 0})
    return imap(_normalizator(category), db_cursor)


def get_sorted_chart_elements_lower_than(max_rank, category, exclude_ids=None):
    """ Return an iterator over doc such as {'advice':x, 'rank': y} for all
    documents with rank lower than max_rank, sorted by their rank. """
    assert isinstance(max_rank, Number)
    assert type(category) in (str, unicode)
    assert type(exclude_ids) in (None, list, tuple)
    
    max_rank = max_rank * _get_norm(category) # un-normalizing
    
    query = {"rank" : {"$lt": max_rank}}
    if exclude_ids:
        query["_id"] = {"$nin": exclude_ids}
        
    db_cursor = mongodb['chart-' + category].find(query, sort=sorting_order,
                            fields= {'advice': 1, 'rank':1, '_id': 0})
    return imap(_normalizator(category), db_cursor)

def count(category):
    assert type(category) in (str, unicode)
    return mongodb['chart-' + category].count()


def find_rank(partial_dbdoc, category):
    """ Given a dbdoc like ( ("author": ...), ("song": ...) )
    find a case insensitive match in the chart, and returns
    the mongo document of that match (a dict with keys
    'advice', 'rank', '_id'). If it does not exist in the chart, returns None. """
    
    assert type(category) in (str, unicode)
    assert type(partial_dbdoc) is tuple

    query = dict([("advice."+key, re.compile(re.escape(value), re.IGNORECASE)) for (key, value) in partial_dbdoc])
    
    results = list(mongodb['chart-' + category].find(query, limit=1))
    
    if results:
        return _normalizator(category)(results[0])
    else:
        return None


@redis_cached
def find_position(video_id, category):
    """ Returns the number of elements that come before
    the specified video. """
    assert type(video_id) in (str, unicode)
    assert type(category) in (str, unicode)
    
    collection = mongodb['chart-' + category]
    
    matching_docs = list(collection.find(
                    {"advice.video": video_id},
                    sort=sorting_order,
                    fields= {'rank':1, '_id': 1},
                    limit=1
                ))
    
    if matching_docs:
        rank_of_video = matching_docs[0]["rank"]
        id_of_video = matching_docs[0]["_id"]
    else:
        return None
    
    n_with_more_rank = collection.find(
            {"rank": {"$gt": rank_of_video}},
            fields={'_id':1}
        ).count()
    
    n_of_ties_before = collection.find(
        {"rank": rank_of_video, "_id": {"$lt": id_of_video}},
        fields={'_id':1}
    ).count()
    
    return n_with_more_rank + n_of_ties_before
    
    

