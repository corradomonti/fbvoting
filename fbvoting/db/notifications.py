import logging, datetime

from db import mongodb

logger = logging.getLogger(__name__)

class NotificationType:
    missing_votes = 'mv'

notification_types = set([NotificationType.missing_votes])

def is_last_notification_expired(user_id, notification_type, expire_time=datetime.timedelta(days=7)):
    assert type(user_id) in (int, long)
    assert notification_type in notification_types
    assert type(expire_time) is datetime.timedelta
    
    now = datetime.datetime.now()
    
    user_notifications = list(mongodb.notifications.find({ '_id': user_id }, limit=1))
    if user_notifications:
        return (now - user_notifications[0][notification_type]) > expire_time
    else:
        return True


def mark_notification(user_id, notification_type):
    assert type(user_id) in (int, long)
    assert notification_type in notification_types
    
    mongodb.notifications.save({ '_id' : user_id, notification_type: datetime.datetime.now() })
