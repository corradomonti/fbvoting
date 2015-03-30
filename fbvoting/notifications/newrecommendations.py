import threading, urllib2, logging
from random import random

from fbvoting.conf import NOTIFICATION_DEPTH, NOTIFICATION_CHANCE    
import fbvoting.apis.fb as fbapi
import fbvoting.db.delegatevote
#from fbvoting.dbutils import userid_to_name

from fbvoting.mylogging import report

logger = logging.getLogger(__name__)

app_api = fbapi.get_application_token_api()

class DelegatorsNotifier(threading.Thread):
    def __init__(self, user_id, category):
        threading.Thread.__init__(self, name=("NotifyDelegatorsOf%iIn%s" % (user_id, category)))
        self.user = user_id
        self.category = category
    
    def run(self, ):
        try:
            delegators = fbvoting.db.delegatevote.find_who_delegated_to(self.user, category=self.category, depth=NOTIFICATION_DEPTH)
            
            msg = "Your delegate for %s has contributed: you might have new recommendations!" % self.category
            href = "recommendation/" + self.category
            for delegator in delegators:
                try:
                    if fbapi.has_app_installed(delegator): # it should have, but let's be sure
                        if random() < NOTIFICATION_CHANCE:
                            app_api[delegator].notifications.post(template=msg, href=href)
                            report.mark('delegator-notified')
                        else:
                            report.mark('skipped-notification')
                    else:
                        report.mark('delegator-with-no-app') # disinstalled?
                except Exception as e:
                    if type(e) is urllib2.HTTPError:
                        logger.error("Cannot notify delegator %i: FB returned error %i %s.", delegator, e.code, str(e.read()))
                    else:
                        logger.exception("Error in notifying delegator %i", delegator)
        except:
            logger.exception("Error in notification thread %s", self.name)
