import json, httplib2, logging, re

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import SignedJwtAssertionCredentials

from fbvoting.conf import GOOGLE_CREDENTIALS_PATH
from fbvoting.rediscache import redis_cached

logger = logging.getLogger(__name__)

_parenthesis = re.compile(r'\(.+\)')

class YoutubeApi(object):
    def __init__(self, client_email, my_private_key):
        self.youtube = None
        self.client_email = client_email
        self.private_key = my_private_key
        self.authorize()
    
    def authorize(self):
        logger.info('Youtube API client is authorizing')
        http = httplib2.Http()
        storage = Storage(GOOGLE_CREDENTIALS_PATH + 'googleoauth.dat')
        credentials = storage.get()
        
        if credentials is None or credentials.invalid:
            credentials = SignedJwtAssertionCredentials(self.client_email, self.private_key, scope= "https://www.googleapis.com/auth/youtube")
            storage.put(credentials)
        else:
            credentials.refresh(http)
        
        http = credentials.authorize(http)
        self.youtube = build(serviceName="youtube", version="v3", http=http)
    
    def search(self, query, max_results=4, do_not_reauth=False):
        # pylint: disable=E1101
        # youtube-provided api sucks and pylint signals errors when using them.
        try:
            logger.debug('Youtube query "%s".', query)
            
            search_response = self.youtube.search().list(
              q=query.strip(),
              videoEmbeddable="true",
              type="video",
              part="id,snippet",
              maxResults=max_results
            ).execute()
          
            results = [search_result for search_result in search_response.get("items", [])]
            if not results:
                new_query, differences = _parenthesis.subn('', query)
                if differences:
                    logger.debug('Retrying youtube search with query "%s".', new_query)
                    return self.search(new_query, max_results=max_results)
            
            return results
            
        except AccessTokenRefreshError as e:
            logging.warn('Youtube API client got AccessTokenRefreshError')
            if do_not_reauth:
                logger.error("Youtube API got AccessTokenRefreshError after authentication!")
                raise e
            else:
                self.authorize()
                return self.search(query, max_results=max_results, do_not_reauth=True)





with open(GOOGLE_CREDENTIALS_PATH + 'client_secret.json') as f:
    google_client_data = json.load(f)['web']

with open(GOOGLE_CREDENTIALS_PATH + 'privatekey.p12') as f:
    private_key = f.read()

_youtubeApi = YoutubeApi(google_client_data['client_email'], private_key)

@redis_cached
def youtube_search(query, max_results=4):
    return _youtubeApi.search(query, max_results)

