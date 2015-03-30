#############################################
####### EXTERNAL SERVICES ACCESS ############
#############################################

MUSICBRAINZ_SERVER = None              # example: "http://localhost:5001"

# mongodb complete URI
MONGO_URI = None                       # example: "mongodb://localhost:27017/db"

# Google access credentials (for youtube)
# This path must contain the client secrets JSON (where client_email is)
# and also the private key given by google. Must end with /.
GOOGLE_CREDENTIALS_PATH = None         # example '/home/vagrant/fbvoting/googledata/'

# last fm (for cover arts)
LAST_FM_KEY = None

# FB access credentials
FB_APP_ID = None                        # example: '1234567890123456'
FB_APP_SECRET = None
FB_APP_LINK = None                      # i.e.: 'https://apps.facebook.com/' + str(FB_APP_ID) + '/'

# FB options
FB_APP_SCOPE = ['email', 'user_friends', ]

#############################################
############## APP OWN OPTIONS ##############
#############################################

DEBUG = False
DOMAIN = None                           # example: 'www.myserver.it'
BASEPATH = '/home/vagrant/fbvoting/'
LOGGING_DIRECTORY = BASEPATH + '/logging/'
AUTHORIZED_IPS = ()

N_ITEMS = 3 # number of direct vote you can put

APP_NAME = "Liquid FM"
APP_HOMEPAGE = FB_APP_LINK
DESCRIPTION = "Find the best music, through friends."

ORDERED_VOTE = False # must users vote in the specified order?
STORE_NAMES_OF_FRIENDS = False # should we store names and emails of every friend of our users?

# ids of facebook profiles that have admin privileges on this app
ADMIN_FB_IDS = ()                       # example: (1234567890, )

# ids of test users
TEST_USER_IDS = ()                      # example: (123456789012345, )

MOCKING_MODE = False
# Key to put in url as mocking-key=MOCKING_KEY in url to authorize mocking.
MOCKING_KEY = ''                        # example: 'abcdefgh123'


JAVA_CHART_JAR_PATH = BASEPATH + 'java/fbvoting-Main.jar'

# place where album cover will be saved
COVER_BASE_FOLDER = BASEPATH + 'fbvoting/static/images/covers/'
BLANK_COVER_PATH  = BASEPATH + 'fbvoting/static/images/covers/blank.png'
COVER_BASE_PATH_TO_URL = lambda path : path.replace(BASEPATH + 'fbvoting/', '/')

# weight of personalized ranks over global ranks in forming recommendations
MIXING_FACTOR = 0.9

# dump factor for personalized ranks
DUMP_FACTOR = .75

# threshold for personalized ranks:
# if threshold > (DUMP_FACTOR ^ i), i'll stop the computation
RANK_THRESHOLD = 1E-6

# to which level delegators should be notified about a delegate direct vote
# (1 meaning "if x voted, notify only delegators of x"
NOTIFICATION_DEPTH = 1
NOTIFICATION_CHANCE = 0.1

# timeout in seconds for redis caching
ACTIVATE_REDIS = True
REDIS_TIMEOUT = 60 * 60

#############################################
############## FLASK CONFIGURATION ##########
#############################################

# flask will answer to this port (default = 3000)
PORT = 3000

# key used by flask to encrypt its things
MY_SECRET_KEY = None                    # example: '1234abcde1234abcde'

class Config(object):
    PROFILE = False # enables profile
    DEBUG = DEBUG
    TESTING = DEBUG
    LOG_LEVEL = 'DEBUG'
    SERVER_NAME = DOMAIN
    PREFERRED_URL_SCHEME = 'https'

if None in (MY_SECRET_KEY, DOMAIN, MUSICBRAINZ_SERVER, FB_APP_SECRET, FB_APP_LINK, LAST_FM_KEY, APP_HOMEPAGE, FB_APP_ID, GOOGLE_CREDENTIALS_PATH, MONGO_URI):
    import os
    raise Exception("You must fill every None value in " + str(os.path.abspath(__file__)))

if __name__ == '__main__':
    for k, v in locals().items():
        if k[0] != '_':
            print k, '=', v
    

