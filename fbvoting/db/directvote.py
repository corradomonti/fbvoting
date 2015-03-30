import logging
from operator import itemgetter
from collections import defaultdict

from pymongo import ASCENDING

from db import mongodb, get_id_if_exists
from delegatevote import get_delegate, get_delegates_of
from categories import categories
from fbvoting.mylogging import report
from fbvoting.conf import TEST_USER_IDS

logger = logging.getLogger(__name__)

_DV_ORDER = [ ('_id', ASCENDING)]

def assign_direct_votes(user_id, category, votes):
    """ After this operation, the only valid votes in the db
        will be those contained in votes. """
    assert type(user_id) in (long, int)
    assert type(category) in (str, unicode)
    assert type(votes) is list
    
    ids_to_preserve = set()
    votes_to_add = []
    
    # translating to db documents, and finding unchanged votes
    for vote in votes:    
        if vote is not None:
            report.mark('direct-vote')
            vote_doc = {
                    'user': user_id,
                    'category': category,
                    'advice': vote,
                }
            existing_id = get_id_if_exists(mongodb.advices, vote_doc)
            if existing_id:
                ids_to_preserve.add(existing_id)
            else:
                votes_to_add.append(vote_doc)

    # marking old votes as removed
    mongodb.advices.update(
        {'user': user_id, 'category': category, '_id': {"$nin": list(ids_to_preserve)}},
        {"$set": {'rm': True}},
        multi=True
    )
    
    # adding new votes
    if votes_to_add:
        mongodb.advices.insert(votes_to_add)


def get_direct_votes_of(userid):
    """ returns the dictionary of category -> list of advice for that user,
        only for categories fo which it exists. """ 
    assert type(userid) in (long, int)
    
    votes = defaultdict(list)
    for doc in mongodb.advices.find({"user": userid, 'rm': {'$ne': True}}, sort=_DV_ORDER):
        votes[ doc["category"] ].append( doc['advice'] )
    
    return dict(votes)

    
def get_direct_votes(userid, category):
    """ Return the list of votes of this user in this category. """
    assert type(userid) in (long, int)
    assert type(category) in (str, unicode)
    
    return map(
        itemgetter('advice'),
        mongodb.advices.find({
            'user': userid, 'category': category, 'rm': {'$ne': True}},
            sort=_DV_ORDER)
    )

def get_categories_with_direct_votes(userid):
    assert type(userid) in (long, int)
    
    return set(
        map(itemgetter('category'),
            mongodb.advices.find(
                {'user': userid, 'rm': {'$ne': True}},
                fields={'category':1, '_id': 0}
            )
        )
    )
    

def has_direct_or_delegate_vote(userid, category):
    return get_direct_votes(userid, category) or get_delegate(userid, category) is not None



def get_next_uncompleted_category(userid, considered_completed=None, delegates=None):
    assert considered_completed is None or type(considered_completed) in (str, unicode)
    assert type(userid) in (long, int)
    assert delegates is None or type(delegates) is dict
    
    direct_votes = get_categories_with_direct_votes(userid)
    
    if delegates is None:
        delegates = get_delegates_of(userid)
    
    try:
        return next(cat for cat in categories()
            if not (cat in direct_votes or cat in delegates or cat == considered_completed) )
    except StopIteration:
        return None



def count_all_nontest_votes(category=None):
    assert category is None or category in categories()
    
    query = {"user": {'$nin': TEST_USER_IDS}, 'rm': {'$ne': True}}
    if category:
        query["category"] = category
    count = mongodb.advices.find(query, fields=("_id", )).count()
    assert type(count) in (int, long)
    return count


def replace_all_videos(old_video, new_video):
    logger.warn("Replacing all videos id from %s to %s", old_video, new_video)
    result = mongodb.advices.update({"advice.video": old_video}, {"$set" : {"advice.video": new_video, "chg": True}}, multi=True, fsync=True, upsert=False)
    logger.warn("%i videos updated.", result.get('n'))
    return result

