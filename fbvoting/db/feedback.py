from db import mongodb

from categories import categories
import fbvoting.db.directvote as directvote
from fbvoting.directvote import YoutubeId

def put(user_id, song, category, video_playback = None, rating = None):
    assert type(user_id) in (int, long)
    assert type(category) in (str, unicode)
    assert type(song) in (str, unicode)
    
    assert video_playback is None or type(video_playback) is float
    assert rating is None or type(rating) is int
    
    if video_playback is None and rating is None:
        raise Exception("One between video_playback and rating must be used.")
    
    if category not in categories():
        raise Exception(category + ": category not valid")
    
    query = {'user' : user_id, 'category': category, 'song': song}
    
    existing_docs = list(mongodb.feedback.find(query, ('_id',), limit=1))
    if existing_docs:
        # UPDATE THE EXISTING DOC
        doc_id = existing_docs[0]
        update = {}
        if video_playback is not None:
            update['$push'] = {'video_playback': video_playback}
        if rating is not None:
            update['$set'] = {'rating': rating}
        mongodb.feedback.update(doc_id, update)
    else:
        # CREATE NEW DOC
        new_doc = query
        if video_playback is not None:
            new_doc['video_playback'] = [video_playback]
        if rating is not None:
            new_doc['rating'] = rating
        mongodb.feedback.insert(new_doc)


def get_rating(user_id, song, category):
    query = {'user' : user_id, 'category': category, 'song': song}
    results = list(mongodb.feedback.find(query, fields={"rating":1, "_id":0}, limit=1))
    if results:
        return results[0].get("rating")
    else:
        return None


def find_success_of_advices(user_id, only_above=0):
    assert type(user_id) in (int, long)
    results = []
    for category, votes in directvote.get_direct_votes_of(user_id).items():
        for vote in votes:
            listened = 0
            for feedback in mongodb.feedback.find({"song" : vote[YoutubeId.db_id]}):
                listened += sum(1 for playing_time in feedback.get("video_playback", []) if playing_time > 30)
            if listened > only_above:
                results.append((category, vote, listened))
    
    return results

