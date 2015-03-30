import pymongo

import fbvoting.conf as conf

def get_mongo_db():
    mongo = pymongo.MongoClient(conf.MONGO_URI)
    db_name = pymongo.uri_parser.parse_uri(conf.MONGO_URI)['database']
    return mongo[db_name]

mongodb = get_mongo_db()


def exists(collection, attr, not_consider_removed=True):
    assert type(collection) is pymongo.collection.Collection
    assert type(attr) is dict
    
    query = dict(rm={'$ne': True}, **attr) if not_consider_removed else attr
    
    return bool(list(collection.find(query, ('_id',), limit=1)))


def get_id_if_exists(collection, attr, not_consider_removed=True):
    """ Returns the id object if the specified document (supposed unique)
        exists, or None if it does not.
    """
    assert type(collection) is pymongo.collection.Collection
    assert type(attr) is dict
    
    query = dict(rm={'$ne': True}, **attr) if not_consider_removed else attr
    results = list(collection.find(query, ('_id',), limit=1))
    return results[0]['_id'] if results else None
    


    


