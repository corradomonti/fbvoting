import logging
from math import floor

from flask import render_template

from fbvoting.apis.fb import get_user_id
from fbvoting.db.users import get_guru_friends
import commons

logger = logging.getLogger(__name__)

def build_friends():
    
    data = commons.get_base_data()
    data.update({
        'active_section': 'friends',
        'best_friends': map(append_inv_decile, get_guru_friends(get_user_id()))
    })
    
    return render_template('friends.html', **data)


def append_inv_decile(item):
    item = list(item)
    item.append(int(floor((100 - item[2]) / 10)))
    return item


