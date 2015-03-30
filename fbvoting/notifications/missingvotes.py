import logging
from random import choice

import fbvoting.apis.fb as fbapi
from fbvoting.db.users import users_with_missing_votes
import fbvoting.db.notifications as db

logger = logging.getLogger(__name__)


def send_notifications():
    logger.info("Notifications about missing votes: querying db...")
    notificationType = db.NotificationType.missing_votes
    logger.info("Notifications about missing votes: db has been queried.")
    
    app_api = fbapi.get_application_token_api()
    n_sent, n_skipped = 0, 0
    
    for user, missing_votes in users_with_missing_votes():
        logger.debug('user %s has missing votes %s', user, missing_votes)
        
        if db.is_last_notification_expired(user, notificationType):
            logger.debug('user %s has notification expired: we can send one', user)
            if fbapi.has_app_installed(user):
                category = choice(list(missing_votes))
                logger.debug("user %s has also app installed: notifying for category %s", user, category)
                
                msg = "We are looking for %s music gurus: do you have an expert among your friends?" % category
                href = "votes/" + category
                app_api[user].notifications.post(template=msg, href=href)
                db.mark_notification(user, notificationType)
                n_sent+=1
            else:
                logger.warn("User %s should have been notified for its missing votes, but its app cannot be accessed.", user)
        else:
            n_skipped += 1
    
    logger.info("Notifications about missing votes: %i sent, %i skipped.", n_sent, n_skipped)
