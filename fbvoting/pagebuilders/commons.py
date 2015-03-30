import logging

from flask import request, render_template, Markup

import fbvoting.conf as conf
from fbvoting.db.categories import categories
from fbvoting.notifications.beennominated import DelayedNotificationABC
from fbvoting.apis.fbmock import should_we_mock
from fbvoting.apis.fb import fb_oauth_token

logger = logging.getLogger(__name__)

def build_messages():
    messages = []
    
    if request.args.get('success-vote'):
        category = request.args['success-vote']
        if category in categories():
            messages.append(
                Markup(render_template(
                    'bits/success-vote.html',
                    category=category
                    ))
            )
    
    return messages

def get_base_data():
    """ data neeeded by base.html """
    
    try:
        token = fb_oauth_token()
    except:
        token = None
    
    return {
        'domain': conf.DOMAIN,
        'app_id': conf.FB_APP_ID,
        'app_name': conf.APP_NAME,
        'app_link': conf.FB_APP_LINK,
        'description': conf.DESCRIPTION,
        'active_section': 'main',
        'categories': categories(),
        'messages': build_messages(),
        'notifications': DelayedNotificationABC.retrieve_all(),
        'FBAPI_SCOPE': conf.FB_APP_SCOPE,
        'activate_fb': not should_we_mock(),
        'token': token
    }
    
    

