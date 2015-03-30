
import urllib2, urllib, json, logging, base64
import hmac, hashlib

import flask
from flask import session, request
from facegraph import Graph

from fbvoting.conf import FB_APP_ID, FB_APP_SECRET
from fbvoting.lib import add_GET_params
from fbvoting.mylogging import report
from fbmock import mocking_false, mocking_api

logger = logging.getLogger(__name__)

class FBException(Exception):
    def __init__(self, msg="Something bad happened in Facebook authentication."):
        Exception.__init__(self, "Cannot login on FB." + msg)

def set_cookie_from_signed_request():
    try:
        logger.debug("Trying to get OAuth token from Signed Request.")
        sr = _parse_signed_request()
        token, user_id =  [sr[f] for f in ('oauth_token', 'user_id')]
        session['oauth_token'] = token
        session['user_id'] = int(user_id)
        logger.debug("An OAuth token has been set for user %s in cookies.", user_id)
    except:
        raise FBException()


def store_oauth_token(token):
    logger.debug("AUTH: setting OAuth token in cookies")
    
    if not token:
        raise FBException ("store_auth_token called, but no OAuth token has been provided.")
    
    session['oauth_token'] = token
    logger.debug("An OAuth token has been set in cookies from auth page")
    
    if 'user_id' in session:
        del session['user_id']
    
    report.mark('auth')
    return 'OK'

def fb_oauth_token(no_signed_request=False):
    token_from_cookie = session.get('oauth_token')
    if token_from_cookie:
        logger.debug("Oauth token found in cookies")
        return token_from_cookie
    elif flask.has_request_context():
        if 'token' in request.args:
            logger.debug("Oauth token found in GET arguments.")
            return request.args['token']
        elif not no_signed_request:
            logger.debug("Looking for OAuth token it via Signed Request.")
            return _parse_signed_request()['oauth_token']
        else:
            raise FBException("No OAuth token in cookies, neither in GET arguments.")
    else:
        raise FBException("No OAUth token in cookies and no request context.")


def _parse_signed_request():
    # reference: https://developers.facebook.com/docs/facebook-login/using-login-with-games
    
    if request.path != "/":
        raise FBException("Signed request avaiable only in url '/', not '%s'" % request.path )
    
    if request.method != "POST":
        raise FBException("Signed request avaiable only in POST mode, not %s." % request.method)
    
    signed_request = request.form.get('signed_request')
    
    if not signed_request:
        logger.error("I expected a signed_request in POST, but there was none (url=%s, method=%s).", request.path, request.method)
        raise FBException()
    
    
    # padding: in this way len is always a multiple of 4, as in base64 specs
    padded = lambda s : s + "=" * ((4 - (len(s) % 4 )) % 4)
    
    encoded_sign, encoded_data = signed_request.encode('utf-8', 'ignore').split('.')
    user_data = json.loads(base64.urlsafe_b64decode(padded(encoded_data)))
    
    # check
    if user_data.get('algorithm', '').upper() != 'HMAC-SHA256':
        logger.error('FB used an unknown algorithm for signing request!! Cannot verify anything.')
        raise FBException()
    else:
        expected_sign = hmac.new(FB_APP_SECRET, msg=encoded_data, digestmod=hashlib.sha256).digest()

        if base64.urlsafe_b64decode(padded(encoded_sign)) != expected_sign:
            logger.error("Wrong FB signature on signed requests. Possible man-in-the-middle. Cannot continue.")
            raise FBException()

    logger.debug("Signed Request correctly parsed.")
    return user_data


def get_user_id(with_signed_req=False):
    try:
        if 'user_id' in session:
            return int(session['user_id'])
        else:
            logger.debug("Asked for user id, and was not already set in cookies. Let's find it.")
            if with_signed_req:
                try:
                    logger.debug("Trying to find user id with Signed Request")
                    user_id = int(_parse_signed_request()['user_id'])
                    logger.debug("User id found with Signed Request")
                    session['user_id'] = user_id
                    return int(user_id)
                except:
                    logger.exception("Cannot use Signed Request to get user id!")
            
            logger.debug("Trying to find user id with API")
            user_id = get_graph_api().me().id
            logger.debug("User id found with API request")
            session['user_id'] = user_id
            return int(user_id)
    except:
        raise FBException()

@mocking_false
def is_token_gone_rotten():
    try:
        _ = get_graph_api(no_signed_request=True).me().id # can i do this?
        return False    # then f**k you.
    except FBException:
        logger.debug("Rotten OAuth token identified with FBException")
        return True     # no ok sorry
    except urllib2.HTTPError as err:
        if err.code == 400:
            logger.debug("Rotten OAuth token identified with HTTPError 400")
            return True # i said i am sorry
        else:
            logger.exception('FB answered badly')
            raise err   # there is no need to do this, please


@mocking_false
def ensure_token_is_valid():
    if is_token_gone_rotten():
        raise FBException()

    

def get_application_token():
    params = urllib.urlencode({
        'client_id':FB_APP_ID,
        'client_secret': FB_APP_SECRET,
        'grant_type': 'client_credentials'
    })
    response = urllib2.urlopen('https://graph.facebook.com/oauth/access_token', data=params).read()
    
    if '=' not in response:
        raise Exception("Could not obtain an application token.", response)
    value, token = response.split('=')
    if value != 'access_token':
        raise Exception("Could not obtain an application token.", response)
    
    return token

def get_application_token_api():
    api = Graph(get_application_token())
    api.DEFAULT_TIMEOUT = 10
    return api


@mocking_api    
def get_graph_api(**oauth_token_args):
    api = Graph(fb_oauth_token(**oauth_token_args))
    api.DEFAULT_TIMEOUT = 10
    return api


@mocking_false
def has_app_installed(user_id):
    assert type(user_id) in (int, long)
    
    permissions = get_application_token_api()[user_id].permissions()['data']
    for permission in permissions:
        if permission.get('installed') == 1:
            return True
    
    return False

def _fql_query(fql_code):
    url = add_GET_params(
        'https://graph.facebook.com/fql',
        {'q': fql_code, 'access_token': fb_oauth_token()}
    )
    response = json.load(urllib2.urlopen(url))
    return response['data']

@mocking_false
def can_we_write_to_wall_of(user_id):
    return _fql_query(
        "SELECT can_post FROM user WHERE uid = %i" % user_id
        )[0]["can_post"]
