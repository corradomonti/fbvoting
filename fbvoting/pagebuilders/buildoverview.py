from operator import itemgetter

from flask import render_template

from fbvoting.conf import ORDERED_VOTE, DOMAIN
from fbvoting.apis.fb import get_user_id
import fbvoting.db.users
import fbvoting.db.directvote
import fbvoting.db.delegatevote
from fbvoting.db.categories import categories
from fbvoting.directvote import dbdocs2html, dbdocs2str
import commons

def build_overview():
    
    userid = get_user_id()
    fbvoting.db.users.store_people_info(userid)
    
    direct_votes = fbvoting.db.directvote.get_direct_votes_of(userid)
    delegates = fbvoting.db.delegatevote.get_delegates_of(userid)
    
    votes = [                                       # tuples of...
            (cat,                                       # category name
            (cat in direct_votes or cat in delegates),  # vote assigned
            dbdocs2html(direct_votes.get(cat), category=cat), # html to display all direct votes
            delegates.get(cat))                         # delegate, or None
        for cat in categories()]
    
    
    completed = all(map(itemgetter(1), votes))
    next_vote = fbvoting.db.directvote.get_next_uncompleted_category(userid, delegates=delegates)
    
    share_messages = dict([
            (c, share_message(c, direct_votes.get(c), delegates.get(c)))
            for c in categories()
        ])
    
    data = commons.get_base_data()
    data.update({
        'userid': userid,
        'active_section': 'voting',
        'DOMAIN': DOMAIN,
        "votes": votes,
        "next_vote": next_vote,
        "completed": completed,
        "share_messages": share_messages,
        "votable": [next_vote] if (ORDERED_VOTE and not completed) else categories()
    })
    
    return render_template('overview.html', **data)

def share_message(category, direct_votes, delegate):
    msg = ""
    
    if delegate:
        msg+= "I've nominated " + fbvoting.db.users.userid_to_name(delegate)
        msg+= " as " + category + " music guru on Liquid FM! "
        if direct_votes:
            msg+= "Also, "
    
    if direct_votes:
        msg+="I've voted for " + dbdocs2str(direct_votes)
        msg+=" as the best " + category + " tune"
        if len(direct_votes) > 1:
            msg+="s"
        if not delegate:
            msg+=" on Liquid FM"
        msg+="!"
    
    return msg



