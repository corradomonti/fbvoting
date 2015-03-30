import logging

from flask import render_template, abort, url_for, make_response

import fbvoting.conf
from fbvoting.apis.fb import get_user_id
import fbvoting.db.directvote
import fbvoting.db.delegatevote
import fbvoting.notifications.beennominated
import fbvoting.notifications.newrecommendations
from fbvoting.db.categories import categories, song_for
import fbvoting.directvote as dv
import fbvoting.apis.musicbrainz as musicbrainz
from fbvoting.rediscache import void_cache
from fbvoting.recommendation.mixedchart import mixed_ranks_list
import commons

logger = logging.getLogger(__name__)

def build_vote(category):
    if category not in categories():
        abort(404)
    
    userid = get_user_id()
    
    data = commons.get_base_data()
    data.update({
        'active_section': 'voting',
        'category': category,
        'song': song_for(category),
        'userid': userid,
        'directvoteform': dv.DIRECT_VOTE,
        'N_ITEMS': fbvoting.conf.N_ITEMS
    })
    
    # finding next page url
    next_cat = fbvoting.db.directvote.get_next_uncompleted_category(userid, considered_completed=category)
    data['next_page'] = (
                ('/votes/' + next_cat) if next_cat is not None
                else url_for('overview'))
    
    # filling already existing data
    advices = fbvoting.db.directvote.get_direct_votes(userid, category)
    if advices:
        data['directvotes'] = list(enumerate(advices))
    
    delegate = fbvoting.db.delegatevote.get_delegate(userid, category)
    if delegate:
        data['delegate'] = delegate
    
    
    return render_template('vote.html', **data)



def savevote(form):
    if form['category'] not in categories():
        abort(400)
    
    if not bool(form['changed']):
        return {}
    
    user_id = int(form['userid'])
    category = form['category']
    
    if get_user_id() != user_id: # fraud detection
        logger.warn("Fraud detection: user %s tried to pretend to be user %s",
            get_user_id(), user_id)
        abort(403)
    
    direct_votes = dv.form2dbdocs(form)
    if direct_votes and not all([dv.validate(direct_vote) for direct_vote in direct_votes]):
        make_response('One of the submitted votes does not seem to be a valid song.', 406)
    
    delegate = int(form['delegate_id']) if form.get('delegate_id') else None
    
    if not direct_votes and not delegate: # empty vote
        abort(404)
    
    fbvoting.db.directvote.assign_direct_votes(user_id, category, direct_votes)
    changed_delegate = fbvoting.db.delegatevote.assign_delegate(user_id, category, delegate)
    
    if delegate and changed_delegate:        
        fbvoting.notifications.beennominated.new_delegate(delegate, user_id, category, bool(form.get('notify')))
        void_cache(mixed_ranks_list, user_id, category)
    
    fbvoting.notifications.newrecommendations.DelegatorsNotifier(user_id, category).start()
    
    return {'success-vote': category}


def check_with_suggestion(form):
    for i in range(fbvoting.conf.N_ITEMS):
        if form.get('dv-song' + str(i)):
            author, song = [form.get(s + str(i)) for s in (dv.Author.input_id, dv.Song.input_id) ]
            is_ok, is_artist_wrong, best_match = musicbrainz.check_existence_of(author, song, category=form.get('category'))
            if not is_ok:
                wrong_field = (dv.Author.input_id if is_artist_wrong else dv.Song.input_id) + str(i)
                error_msg = "<strong>We don\'t know %s n. %i! </strong>" % ('artist' if is_artist_wrong else 'song', i+1)
                if best_match:
                    error_msg += """
                        Maybe you meant
                        <strong>
                            <a class="suggestion" href="javascript:;"
                                onclick="correct('%s', '%s', %i);">
                                %s
                            </a>
                        </strong>?
                    """ % (
                        dv.Author.input_id if is_artist_wrong else dv.Song.input_id,
                        best_match.replace("'", r"\'"),
                        i,
                        best_match
                    )
                return False, error_msg, wrong_field
    
    return True, ""

