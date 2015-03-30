from operator import itemgetter

from db import exists, mongodb
from categories import categories
from users import store_people_info
from fbvoting.mylogging import report
from fbvoting.conf import TEST_USER_IDS

def assign_delegate(user_id, category, vote, do_store_people_info=True):
    """ vote can be None -- meaning no vote. Returns True if the vote has changed,
    False otherwise."""
    assert type(user_id) in (long, int)
    assert type(category) in (str, unicode)
    assert vote is None or type(vote) in (long, int)
    
    
    if vote is not None:
        report.mark('delegate-vote')
        vote_doc = {
            'from': user_id,
            'category': category,
            'to': vote
        }
        if exists(mongodb.graph, vote_doc):
            return False
    
    # mark all past votes as removed
    mongodb.graph.update(
        {'from': user_id, 'category': category},
        {"$set": {'rm': True}},
        multi=True
    )
    
    # assing new vote
    if vote is not None:
        mongodb.graph.insert(vote_doc)
        if do_store_people_info:
            store_people_info(vote)
    
    return True
    
    



def get_delegates_of(userid):
    """ returns the dictionary of category -> delegate for that user,
         only for categories fo which it exists. """ 
    assert type(userid) in (long, int)
    return dict([
                ( doc["category"], doc['to'] )
                for doc in mongodb.graph.find({
                    "from": userid,
                    'rm': {'$ne': True}
                })
            ])


def delegation_category_and_date_generator(userid):
    assert type(userid) in (long, int)
    
    for doc in mongodb.graph.find({"to": userid, 'rm': {'$ne': True}}, fields=("category", )):
        yield doc["category"], doc['_id'].generation_time


def count_nominations_for(userid, category=None):
    assert type(userid) in (long, int)
    assert category is None or category in categories()
    
    query = {"to": userid, 'rm': {'$ne': True}}
    if category:
        query["category"] = category
    count = mongodb.graph.find(query, fields=("_id", )).count()
    assert type(count) in (int, long)
    return count
    

def count_all_nontest_nominations(category=None):
    assert category is None or category in categories()
    
    query = {"from": {'$nin': TEST_USER_IDS}, 'rm': {'$ne': True}}
    if category:
        query["category"] = category
    count = mongodb.graph.find(query, fields=("_id", )).count()
    assert type(count) in (int, long)
    return count
    
    
def find_who_delegated_to(userid, category, depth=1):
    assert type(userid) in (long, int)
    assert category in categories()
    assert type(depth) is int
    
    delegated = set((userid, ))
    results = set()
    
    for _ in range(depth):
        query = {"to": {'$in': tuple(delegated)}, 'rm': {'$ne': True}, "category": category}
        delegators = mongodb.graph.find(query, fields={"from":True,"_id":False})
        delegators = set(map(itemgetter('from'), delegators))
        if not delegators:
            break
        else:
            new_delegators = delegators - results
            delegated = new_delegators
            results |= delegators
    
    assert all([type(u) in (int, long) for u in results])
    return results

def get_delegate(userid, category):
    assert type(userid) in (long, int)
    assert type(category) in (str, unicode)
    votes = list(mongodb.graph.find({'from': userid, 'category': category, 'rm': {'$ne': True}}, limit=1))
    return votes[0]['to'] if votes else None

