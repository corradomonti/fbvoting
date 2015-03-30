import logging, random

from flask import render_template, abort, Markup, abort

from fbvoting.mylogging import report
import fbvoting.apis.fb as fbapi
from fbvoting.db.directvote import get_next_uncompleted_category
from fbvoting.db.feedback import find_success_of_advices
from fbvoting.directvote import dbdocs2str
import fbvoting.conf as conf

import commons

logger = logging.getLogger(__name__)


def build_home():
    try:
        fbapi.set_cookie_from_signed_request()
        return build_complete_home()
    except fbapi.FBException:
        logger.debug("Could not set cookie from signed request.")
        return build_empty_home()    


def build_complete_home():
    data = commons.get_base_data()
    data['already_logged'] = True
    data.update(get_intro_data())
    return render_template('empty.html', **data)


def build_empty_home():
    data = commons.get_base_data()
    data['already_logged'] = False
    data['js_on_loaded'] = Markup("""
        $("#intro-container").load(personal("ajax/intro"),
            function( response, status, xhr ) {
                if ( status != "success"  && xhr.status != 0) {
                    var msg = "There is a problem communicating to Facebook from our server. ";
                    msg+= "Please, try again or <a href='/about#contacts'>contact us</a>.";
                    $("#intro-container").html( msg );
                    $("#intro-container").addClass("alert-message block-message");
                } else {
                    $('#fb-error-msg').hide();
                }
                update_links();
            }
        );
    """)
    return render_template('empty.html', **data)


def get_intro_data():
    try:
        logger.debug("Trying to build intro data.")
        user_id = fbapi.get_user_id()
        user_name = fbapi.get_graph_api().me().first_name
        
        completed_votes = get_next_uncompleted_category(user_id) is None
        
        if completed_votes:
            button = """
                <a class="btn primary large" href="recommendation">
                    Start listening &raquo;
                </a>
                
                <a class="btn large" href="profile">
                    See your stats &raquo;
                </a>
                
                """
        else:
            button = """
                <a class="btn primary large" href="votes">
                    Start voting &raquo;
                </a>
                <br />
                <a class="btn" href="chart">
                    Listen to music &raquo;
                </a>
                
                """
        
        logger.debug("Introduction built for user id %i with name %s.", user_id, user_name)
        
        return {
            'your_name': user_name,
            'button': Markup(button),
            'ego_petting_msg': ego_petting_msg(user_id),
            'app_link': conf.FB_APP_LINK
        }
        
    except Exception as e:
        logger.exception("Exception while building intro message. " + e.message)
        abort(500)

def build_intro():
    return render_template('bits/intro.html', **get_intro_data())



def ego_petting_msg(userid):
    vote_success = find_success_of_advices(userid, only_above=1)
    if vote_success:
        category, vote, n_listenings = random.choice(vote_success)
        report.mark('ego-petting-msg')
        return Markup("""
<p><div class="alert-message block-message success row span8">
    <div class="column span">
        <img width="80" height="80" class="circled" src="/static/images/categories/%s.jpg">
    </div>
    <div class="column span6"><h4>
        Your <a href="votes/%s">%s vote</a> <em>%s</em>
                has been listened %i times!
    </h4></div>
</div></div></p>
            """ % (category, category, category, dbdocs2str([vote]), n_listenings))
    else:
        return ''
    

