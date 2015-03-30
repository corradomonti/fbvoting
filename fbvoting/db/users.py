import logging
from collections import defaultdict
from operator import itemgetter

from fbvoting.rediscache import redis_cached
from fbvoting.lib import ignore_errors
import fbvoting.conf as conf
from fbvoting.apis.fb import get_graph_api
from db import mongodb, exists
from categories import categories
from fbvoting.mylogging import report

logger = logging.getLogger(__name__)

@ignore_errors
def store_people_info(user_id, store_his_friends=conf.STORE_NAMES_OF_FRIENDS):
    assert type(user_id) in (int, long)
    
    try:
        api = get_graph_api()
        user = api[user_id]()
        doc = {'_id': user_id, 'name': user.name, 'link': user.link}
    
        mongodb.users.save(doc) # save = upsert
    
        try:
            if not exists(mongodb.friends, {'_id': user_id }):
    
                try:
                    friends = user.friends()
                except:
                    logger.info('I cannot get a friend list from user '+str(user_id)+'.')
                    return
    
                friends = [long(friend['id']) for friend in friends['data']]
                mongodb.friends.insert({'_id': user_id, 'friends': friends})
    
                report.mark('saved-friend-list')
    
                if store_his_friends:
                    logger.info('I am storing also friend information')
                    for friend in friends:
                        store_people_info(friend, store_his_friends=False)
        except Exception as exc:
            logger.error('Was not able to save a friend list. ' + exc.message)
    except Exception as exc:
        logger.error('Was not able to store user info. ' + exc.message)



def userid_to_name(user_id):
    assert type(user_id) in (int, long)
    db_results = list(mongodb.users.find(
            {'_id': user_id},
            limit=1,
            fields=('name',)
        ))
    if db_results:
        return db_results[0]['name']
    else:
        try:
            api = get_graph_api()   
            store_people_info(user_id)
            user = api[user_id]()
            return user['name']
        except:
            logger.exception('Was not able to get name for id ' + str(user_id))
            return "Unknown"


_category_fields = dict([(category, 1) for category in categories()] + [('_id', 0)])

def get_rank_and_percentiles(user_id):
    """
    Return a dict made of
    {"Jazz": {"score": <points>, "perc": <rounded percentile>}, ...}
    """
    assert type(user_id) in (int, long)
    results = list(mongodb.userrank.find(
            {'_id': user_id},
            limit=1, fields=_category_fields
        ))
    if results:
        return results[0]
    else:
        logger.warn("We were asked for ranking of user %i, but I dunno him!", user_id)
        return {}


categories = categories()

@redis_cached
def get_guru_friends(user_id):
    """ Return a list of tuples like (category, friend_id, percentile) of the
        friends of the given user, with at most one per category, ranked by their
        score in their respective category.
    """
    try:
        user = get_graph_api()[user_id]()
        friends = user.friends()
    except:
        return []
    
    friends = [long(friend['id']) for friend in friends['data']]
    ranks = list(mongodb.userrank.find(
            {'_id': {'$in': friends}}
        ))
    
    if ranks:
        best_friends = []
        for cat in categories:
            best_friend = max(ranks, key=lambda rank: rank.get(cat, {}).get('score', 1))
            if best_friend.get(cat, {}).get('score') > 1:
                best_friends.append( (cat, best_friend['_id'], best_friend[cat]['perc']) )
        
        return sorted(best_friends, key=itemgetter(2))
    else:
        return []
    
    


def users_with_missing_votes():
    all_categories = set(categories())
    n_categories = len(all_categories)
    
    query = mongodb.graph.aggregate([ {'$match': {"rm": {'$ne': True}}} , { '$group': {'_id': "$from", 'votes': {'$addToSet': "$category"}} } ])['result']
    user2votes = defaultdict(set, [(item['_id'], set(item['votes'])) for item in query])
    
    query = mongodb.advices.aggregate([ {'$match': {"rm": {'$ne': True}}} , { '$group': {'_id': "$user", 'votes': {'$addToSet': "$category"}} } ])['result']
    
    for item in query:
        user2votes[item['_id']] |= set(item['votes'])
    
    for user, votes in user2votes.items():
        if 0 < len(votes) < n_categories:
            yield user, all_categories - votes



