import functools, json, logging, socket, urllib2
from ssl import SSLError

from flask import request, Markup, render_template

from werkzeug.contrib.fixers import ProxyFix
from werkzeug.contrib.profiler import ProfilerMiddleware
from werkzeug.debug import DebuggedApplication


import fbvoting.apis.fb as fbapi
import fbvoting.rediscache
import fbvoting.pagebuilders.commons
import fbvoting.pagebuilders.buildhome
from fbvoting.mylogging import report

logger = logging.getLogger(__name__)

def configure_app(my_app):
    # configuring the environment
    fbvoting.db.categories.bootstrap_categories()
    socket.setdefaulttimeout(10)
    
    # configuring flask
    if fbvoting.conf.Config.PROFILE:
        my_app.wsgi_app = ProfilerMiddleware(my_app.wsgi_app, restrictions = [30])
    my_app.wsgi_app = ProxyFix(my_app.wsgi_app)
    my_app.config.from_object('fbvoting.conf.Config')
    my_app.secret_key =  fbvoting.conf.MY_SECRET_KEY
    my_app.jinja_env.filters['json'] = lambda v: Markup(json.dumps(v))
    fbvoting.rediscache.redis_store.init_app(my_app)
    my_debugged_app = DebuggedApplication(my_app)
    
    #logging
    fbvoting.mylogging.configure_logging(add_handler_to=[my_app.logger])
    
    return my_app, my_debugged_app




###### decorators ######

def refresh_token(func):
    
    def handle_rotten_token():
        data = fbvoting.pagebuilders.commons.get_base_data()
        url = request.path
        logger.debug('A rotten token has been identified: redirecting to auth, and then to %s.', url)
        report.mark('rotten-token')
        data['already_logged']  = False
        data['js_on_loaded'] = Markup("""
            var url = new Url("%s");
            url.query.token = FB.getAuthResponse().accessToken;
            window.location.replace(url.toString());
        """  % url)
        return render_template('empty.html', **data)
    
    
    @functools.wraps(func)
    def checking_token_func(*a, **ka):
        try:
            return func(*a, **ka)
        except fbapi.FBException:
            return handle_rotten_token()
        except SSLError:
            return handle_rotten_token()
        except urllib2.HTTPError as err:
            if err.code == 400:
                return handle_rotten_token()
            else:
                raise err
    
    return checking_token_func
