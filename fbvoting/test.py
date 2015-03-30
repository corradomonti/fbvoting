
import random

from fbvoting.conf import TEST_USER_IDS
from fbvoting.apis.fb import get_user_id
import fbvoting.apis.lastfm as lastfm
from fbvoting.db.categories import categories
from fbvoting.db.directvote import assign_direct_votes
from fbvoting.db.delegatevote import assign_delegate

def is_testing_user():
    return get_user_id() in TEST_USER_IDS


class Tester(object):
    _songs = dict()
    
    def get_songs(self, tag):
        assert type(tag) in (str, unicode)
        
        if tag not in self._songs:
            self._songs[tag] = lastfm.get_vote_items(tag)
        
        return self._songs[tag]

    def random_directvote(self, tag):
        author, title, vid = None, None, None
        for author, title, vid in self.get_songs(tag):
            if random.random() < 0.2:
                break
        
        return {"author": author, "song": title, "video": vid}


    def make_votes_for_category(self, cat):
        for user in TEST_USER_IDS:
            votes = [self.random_directvote(cat) for _ in range(random.randint(0, 3))]
            assign_direct_votes(user, cat, votes)
            
            if not votes or random.random() < 0.8:
                delegate = random.choice([u for u in TEST_USER_IDS if u != user])
                assign_delegate(user, cat, delegate, do_store_people_info=False)


    def make_votes_for_all_category(self):
        for cat in categories():
            self.make_votes_for_category(cat)


tester = Tester()
