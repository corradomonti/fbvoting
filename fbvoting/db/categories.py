from operator import itemgetter
import logging

from fbvoting.lib import cached
from db import mongodb

logger = logging.getLogger(__name__)

@cached
def categories():
    return map(itemgetter("_id"), mongodb.categories.find().sort("order", 1))


def bootstrap_categories():
    if 'categories' not in mongodb.collection_names():
        logging.info('Bootstrapping categories')
        mongodb.categories.insert([
            {'_id': 'Classical',    'order': 0, 'item': 'work'},
            {'_id': 'Electronic',   'order': 1, 'item': 'track'},
            {'_id': 'Folk',         'order': 2},
            {'_id': 'HipHop',       'order': 3},
            {'_id': 'Indie',        'order': 4, 'item': 'tune'},
            {'_id': 'Jazz',         'order': 5, 'item': 'tune'},
            {'_id': 'Metal',        'order': 6, 'item': 'track'},
            {'_id': 'Pop',          'order': 7},
            {'_id': 'Rock',         'order': 8}
        ])

@cached
def song_for(category):
    return mongodb.categories.find_one({"_id": category}).get('item', 'song')
