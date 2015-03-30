import abc, json, logging

from flask import session, Markup

import fbvoting.apis.fb as fbapi
from fbvoting.conf import APP_HOMEPAGE, DESCRIPTION, DOMAIN
from fbvoting.lib import ignore_errors
import fbvoting.db.delegatevote
#from fbvoting.dbutils import userid_to_name

from fbvoting.mylogging import report

logger = logging.getLogger(__name__)

app_api = fbapi.get_application_token_api()

class DelayedNotificationABC(object):
    __metaclass__ = abc.ABCMeta
    
    def store(self, ):
        notifications = session.get('notifications', list())
        notifications.append(self)
        session['notifications'] = notifications
    
    @abc.abstractmethod
    def get_js_code(self, ):
        return NotImplemented
    
    @staticmethod
    def retrieve_all():
        if 'notifications' in session:
            report.mark('notification-returned')
            code = '\n'.join([n.get_js_code() for n in session['notifications']])
            del session['notifications']
            
            return Markup("""
                <script>
                    $('body').on( "onFacebookLoaded", function() {
                        """+code+"""
                    })
                </script>
                """)
        
        return ''


class NotifyToDelegateWall(DelayedNotificationABC):
    def __init__(self, delegate_id, from_id, category):
        self.category = category
        self.from_id = from_id
        self.delegate_id = delegate_id
    
    def get_js_code(self, ):
        message = "I've nominated you as %s guru on Liquid FM! Share your expertise!" % self.category
        picture = '%s/static/images/categories/%s.jpg' % (DOMAIN, self.category)
        return """
            FB.ui({
                method: 'feed',
                link: '%s',
                caption: %s,
                to: %i,
                description: %s,
                picture: '%s'
            }, function(response){});
        """ % (APP_HOMEPAGE, json.dumps(DESCRIPTION), self.delegate_id, json.dumps(message), picture)


#class NotifyOnMyWall(DelayedNotificationABC):
#    def __init__(self, delegate_id, from_id, category):
#        self.category = category
#        self.from_id = from_id
#        self.delegate_id = delegate_id
#    
#    def get_js_code(self, ):
#        name = userid_to_name(self.delegate_id)
#        message = "I've nominated %s as %s music guru on Liquid FM!" % (name, self.category)
#        return """
#            FB.ui({
#                method: 'feed',
#                link: '%s',
#                caption: %s,
#                description: '%s',
#            }, function(response){});
#        """ % (APP_HOMEPAGE, json.dumps(message), DESCRIPTION)

    



def do_impersonal_notify(count):
    if count < 5:
        return True
    if count < 50:
        return count % 5 == 0
    if count < 100:
        return count % 10 == 0
    else:
        return count % 50 == 0


@ignore_errors
def new_delegate(notified_user, from_id, category, personal_allowed):
    assert type(notified_user) in (int, long) and type(from_id) in (int, long)
    assert type(category) in (str, unicode)
    assert type(personal_allowed) is bool # delegator agrees to share its identity
    
    if personal_allowed:
        if fbapi.has_app_installed(notified_user):
            # FB notification
            report.mark('notification')
            msg = "@[%i] has nominated you as %s music guru! Find out more!" % (from_id, category)
            link = "profile"
            app_api[notified_user].notifications.post(template=msg, href=link )
        else:
            # tries to write on its wall
            if fbapi.can_we_write_to_wall_of(notified_user):
                report.mark('personal-wall-post')
                NotifyToDelegateWall(notified_user, from_id, category).store()
            else:
                pass #NotifyOnMyWall(notified_user, from_id, category).store()
    else:
        if fbapi.has_app_installed(notified_user):
            # FB notification from "n friends"
            count =  fbvoting.db.delegatevote.count_nominations_for(notified_user, category=category)
            if count == 1:
                report.mark('wall-post')
                msg = "One of your friends has nominated you as %s music guru! Find out more!" % category
                app_api[notified_user].notifications.post(template=msg, href="profile" )
                
            elif do_impersonal_notify(count):
                report.mark('wall-post')
                msg = "%i of your friends have nominated you as %s music guru! Find out more!" % (count, category)
                app_api[notified_user].notifications.post(template=msg, href="profile" )
