# -*- coding: utf-8 -*-
import logging

from flask import Flask, redirect, request, jsonify, render_template, session
import requests

import fbvoting.pagebuilders.buildhome
import fbvoting.pagebuilders.buildoverview
import fbvoting.pagebuilders.buildprofile
import fbvoting.pagebuilders.buildfriends
import fbvoting.pagebuilders.buildrank
import fbvoting.pagebuilders.buildvote
import fbvoting.pagebuilders.builderrors
import fbvoting.pagebuilders.ajaxfeedback
import fbvoting.pagebuilders.jsonchart
import fbvoting.pagebuilders.commons

from fbvoting.mylogging import report, report_view
from fbvoting.apis.youtube import youtube_search
from fbvoting.lib import add_GET_params, url_for, as_full_url
from fbvoting.serverutils import refresh_token
from fbvoting.serverutils import configure_app
from fbvoting.admininterface import activate_admin_interface
from fbvoting.apis.fb import store_oauth_token

logger = logging.getLogger(__name__)

requests = requests.session()
app, debugged_app = configure_app(Flask(__name__))
route = lambda url: app.route(url, methods=['GET', 'POST'])
activate_admin_interface(route)

#### HANDLING LOGIN ####

@route('/auth')
def store_auth_token():
    return store_oauth_token(request.form.get('token'))


#### PAGES ####

@route('/')
@report_view
def index():
    return fbvoting.pagebuilders.buildhome.build_home()

@route('/ajax/intro')
@report_view
def home_intro():
    return fbvoting.pagebuilders.buildhome.build_intro()


@route('/profile')
@refresh_token
@report_view
def egoboost():
    return fbvoting.pagebuilders.buildprofile.build_profile()

@route('/friends')
@refresh_token
@report_view
def friends():
    return fbvoting.pagebuilders.buildfriends.build_friends()

@route('/votes')
@report_view
@refresh_token
def overview():
    return fbvoting.pagebuilders.buildoverview.build_overview()


@route('/votes/<category>')
@refresh_token
@report_view
def vote(category):
    return fbvoting.pagebuilders.buildvote.build_vote(category)


@app.route('/savevote', methods=["POST"])
def savevote():
    parameters = fbvoting.pagebuilders.buildvote.savevote(request.form)
    url = request.args.get('next', url_for('overview'))
    if not url.startswith('https'):
        url = as_full_url(url)
    url = add_GET_params(url, parameters)
    if 'token' in request.args:
        url = add_GET_params(url, {'token': request.args['token']} )
    report.mark('saved-vote')
    return redirect(url)


@route('/recommendation')
@refresh_token
@report_view
def recommendation():
    return fbvoting.pagebuilders.buildrank.build_recommendation_overview()


@route('/chart')
@refresh_token
@report_view
def chart():
    return fbvoting.pagebuilders.buildrank.build_chart_overview()
    
@route('/chart/<category>')
@refresh_token
@report_view
def category_chart(category):
    if request.args.get('query'):
        return fbvoting.pagebuilders.buildrank.build_category_chart_from_query(category, request.args.get('query'))
    else:
        return fbvoting.pagebuilders.buildrank.build_category_chart(category,
                    int(request.args.get('page', 0)),
                    playfirst=bool(request.args.get('playfirst'))
                    )
    

@route('/recommendation/<category>')
@refresh_token
@report_view
def category_recommendation(category):
    page = int(request.args.get('page', 0))
    return fbvoting.pagebuilders.buildrank.build_category_recommendation(category, page, 
                    playfirst=bool(request.args.get('playfirst')))

@route('/about')
@report_view
def about():
    data = fbvoting.pagebuilders.commons.get_base_data()
    data['active_section'] = 'about'
    data['activate_fb'] = False
    return render_template('about.html', **data)

#### ajax ####

@route('/ajax/check-token/')
def check_token_in_cookies():
    return jsonify({'results': 'oauth_token' in session})

@route('/ajax/musicbrainz/log/update')
def musicbrainz_logger():
    fbvoting.apis.musicbrainz.log_update()
    return "OK\n"



@route('/ajax/musicbrainz/check/')
def musicbrainz_check_if_exist():
    return jsonify({'results': fbvoting.pagebuilders.buildvote.check_with_suggestion(request.form)})

@route('/ajax/musicbrainz/search/artist')
def musicbrainz_search_artist():
    query = request.args.get('q','')
    return jsonify( {'query': query, 'suggestions':
        fbvoting.apis.musicbrainz.search_artists(query)
    } )

@route('/ajax/musicbrainz/search/song')
def musicbrainz_search_song():
    query = request.args.get('q','')
    return jsonify( {'query': query, 'suggestions':
        fbvoting.apis.musicbrainz.search_songs(
            query,
            request.args.get('artist'),
            category=request.args.get('category','')
        )
    } )

@route('/ajax/youtube/search')
def ajax_youtube_search():
    return jsonify({ 'results': youtube_search(
            request.args['q'],
            max_results=request.args.get('max-results', 4)
    ) } )

@route('/ajax/rank/<rank_type>/<category>')
def ajax_ranks(rank_type, category):
    return jsonify({
        'results': fbvoting.pagebuilders.jsonchart.get_ranks(rank_type, category,
                    page=int(request.args.get('page', 0)))
    })

@route('/feedback/put/<category>/<song>')
def feedback(category, song):
    return fbvoting.pagebuilders.ajaxfeedback.put_feedback(category, song, request.args)

@route('/feedback/get/<category>/<song>')
def get_rating(category, song):
    return fbvoting.pagebuilders.ajaxfeedback.get_rating(category, song)

## ERROR PAGES ##

for error_code in (404, 500):
    app.error_handler_spec[None][error_code] = lambda _ : fbvoting.pagebuilders.builderrors.build_error(error_code)

###############

logger.info("FBVoting server is now ready.")
if fbvoting.conf.DEBUG:
    logger.warn("We are in DEBUG mode.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=fbvoting.conf.PORT)
