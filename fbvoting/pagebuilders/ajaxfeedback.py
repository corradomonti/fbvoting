from fbvoting.mylogging import report
import fbvoting.db.feedback
import fbvoting.apis.fb as fbapi

def put_feedback(category, song, args):
    feedbacks = {}
    if args.get('video_playback'):
        report.mark('feedback-video')
        feedbacks['video_playback'] = float(args.get('video_playback'))
    if args.get('rating'):
        report.mark('rating')
        feedbacks['rating'] = int(args.get('rating'))
    
    fbvoting.db.feedback.put(fbapi.get_user_id(), song, category, **feedbacks)
    return 'OK'

def get_rating(category, song):
    rating = fbvoting.db.feedback.get_rating(fbapi.get_user_id(), song, category)
    return str(rating if rating is not None else 0)

