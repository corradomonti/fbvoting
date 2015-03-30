from urllib import urlencode
from itertools import islice
import re, requests, os, errno, os.path, logging

from fbvoting.lib import retrieve_json
import fbvoting.conf as conf
from fbvoting.apis.youtube import youtube_search
from fbvoting.apis.musicbrainz import check_existence_of
from fbvoting.mylogging import report

logger = logging.getLogger(__name__)
_parenthesis = re.compile(r'\(.+?\)')

def get_cover(artist, title):
    title = _parenthesis.sub('', title)
    filepath = get_path_for(artist, title)
    if os.path.exists(filepath):
        return conf.COVER_BASE_PATH_TO_URL(filepath)
    else:
        report.mark("cover-search")
        cover_url = get_track_cover_url(artist, title)
        if cover_url is None:
            report.mark("cover-not-found")
            logger.warn('Cover not found on last.fm for %s - %s: symlink to blank.', artist, title)
            os.symlink(conf.BLANK_COVER_PATH, filepath)
        else:
            logger.info('Cover found on last.fm for %s - %s: saving.', artist, title)
            _save_cover(filepath, cover_url)
        
        return conf.COVER_BASE_PATH_TO_URL(filepath)

def get_track_cover_url(artist, title, requested_size="medium"):
    base_url = "http://ws.audioscrobbler.com/2.0/?"
    params = {
        "method" : "track.getInfo",
        "api_key" : conf.LAST_FM_KEY,
        "format": "json",
        "artist": unicode(artist).encode('utf-8', 'replace'),
        "track": unicode(title).encode('utf-8', 'replace')
    }
    
    url = base_url + urlencode(params)
    
    try:
        response = retrieve_json(url)['track']
        
        if 'album' not in response:
            logger.warn('Cannot get album cover for track %s - %s: there is no album associated to this. \n Url: %s', artist, title, url)
            return None
        
        all_size_covers = response['album']['image']
    except Exception as e:
        logger.warn('Cannot get album cover for track %s - %s: %s. \n Url: %s',
            artist, title, e.message, url)
        return None
    
    for cover_description in all_size_covers:
        if cover_description.get('size') == requested_size:
            return cover_description.get('#text')
    
    logger.warn('Cannot get album cover for track %s - %s: there is no cover of size "%s". \n Url: %s', artist, title, requested_size, url)
    
    return None

_valid_path_chars = set('-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')    

def get_path_for(artist, title):
    artist = ''.join(filter(_valid_path_chars.__contains__, artist.title()))
    title  = ''.join(filter(_valid_path_chars.__contains__, title.title()))
    
    dir_path = conf.COVER_BASE_FOLDER + artist
    try:
        os.makedirs(dir_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else:
            raise
    
    return dir_path + '/' + title + '.png'


def _save_cover(filepath, url):
    url_stream = requests.get(url)
    if url_stream.status_code == 200:
        with open(filepath, 'wb') as f:
            for chunk in url_stream.iter_content(1024):
                f.write(chunk)
    
    logger.info('cover saved on ' + filepath)


def get_vote_items(tag):
    base_url = "http://ws.audioscrobbler.com/2.0/?"
    params = {
        "method" : "tag.gettoptracks",
        "api_key" : conf.LAST_FM_KEY,
        "format": "json",
        "tag": tag
    }
    
    youtube_id = lambda author, title : youtube_search(author + " " + title)[0]['id']['videoId']
    
    top_last_fm = retrieve_json(base_url + urlencode(params))
    
    def top_last_fm_iterator():
        for item in top_last_fm['toptracks']['track']:
            author, title = item['artist']['name'], item['name']
            try:
                is_ok, is_artist_wrong, best_match = check_existence_of(author, title, category=tag)
                if is_ok:
                    yield author, title, youtube_id(author, title)
                elif not is_artist_wrong and best_match is not None:
                    yield author, best_match, youtube_id(author, best_match)
            except:
                logger.exception("While validating LastFm result, an error was obtained for %s - '%s' in tag %s", author, title, tag)
    
    return list(islice(top_last_fm_iterator(), 8))


    
