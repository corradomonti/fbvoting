# -*- coding: utf-8 -*-

import urllib, logging, re, functools

from fbvoting.lib import retrieve_json, digest, uniquify
from fbvoting.rediscache import redis_cached
from fbvoting.conf import MUSICBRAINZ_SERVER, DEBUG
from fbvoting.mylogging import musicbrainzReport

logger = logging.getLogger(__name__)

LIMIT_RESULTS_ARTIST = 10
LIMIT_RESULTS_SONG = 20

def if_error_empty_results(funct):
    if DEBUG:
        return funct
    
    @functools.wraps(funct)
    def controlled_func(*args, **kwargs):
        try:
            return funct(*args, **kwargs)
        except Exception as e:
            func_description = (funct.__name__ + '(' +
                digest(str(args) + ',' + str(kwargs)) + ')')
            logger.exception('error on ' + func_description + ': ' + e.message)
            return []
    
    return controlled_func
    

@if_error_empty_results
@redis_cached
def search_artists(query):
    logger.debug("Artist query: %s", query)
    url = MUSICBRAINZ_SERVER+"/ws/js/artist?fmt=json&%s" % urllib.urlencode({
                'q': query.encode('utf-8', 'replace'),
                'limit': LIMIT_RESULTS_ARTIST
            })
    jsonResponse = retrieve_json(url)
    return uniquify([x['name'].strip() for x in jsonResponse if 'name' in x])


ITEM_PER_PAGE = 100


lucene_specials = frozenset(r'\/+-&|!(){}[]^"~*?:')
_escape_lucene = lambda s : ''.join(["\\" + c if c in lucene_specials else c for c in s])

_lucene_separators = ur'\/-,°()'
_non_alpha = re.compile(r'[^\w\s'+re.escape(_lucene_separators)+r']+', flags=re.UNICODE)
_sep = re.compile(r'(?:[\s'+re.escape(_lucene_separators)+r']+\*?)+', flags=re.UNICODE)
_jazz = re.compile(r'(.+)\s*\(\s*(.+?)\s*\)?\s*$', flags=re.UNICODE)

def _field_query(query, field):
    query = _non_alpha.sub('*', query.strip()).strip('* ')
    return field + ':' + _sep.sub(u' AND %s:' % field, query)

def _split_release_if_is_there(lucene_query, category):
    release = None
    if category == 'Jazz':
        with_release = _jazz.match(lucene_query)
        if with_release:
            lucene_query, release = with_release.groups()
    return lucene_query, release

def postprocess_recordings(jsonResponse, category):
    #_normalize_results = lambda s : _parenthesis.sub('', s).strip().title()
    if category == 'Jazz':
        suggestions = [
            item['title'].strip() +
            ' (' + item['releases'][0]['title'] + ')'
            for item in jsonResponse if item.get('title') ]
    else:
        suggestions = [item['title'].strip() for item in jsonResponse if item.get('title')]
    return uniquify(suggestions)


@if_error_empty_results
@redis_cached
def search_songs(query, artist_name, category=None, yet_to_complete=True, fuzzy=False):
    
    logger.debug("Query = '%s', artist = '%s', category = '%s', yet_to_complete=%s, fuzzy=%s", query, artist_name, category, yet_to_complete, fuzzy)
    
    query, release = _split_release_if_is_there(query, category)
    query = re.compile(r'\.([0-9])').sub(r' \1', query)
    query = _non_alpha.sub('*', query.strip()).strip('* ')
    query = query.strip(_lucene_separators)
    query = _sep.sub(' AND ' if not fuzzy else '~ AND ', query)
    
    if fuzzy: query += '~'
    elif yet_to_complete: query += '*'
    
    if release:
        query += u' AND ' + _field_query(release, 'release')
        if yet_to_complete: query += '*'
    
    if artist_name:
        query += u' AND artist:"%s"' % _escape_lucene(artist_name)
    
    logger.debug("Lucene query = '%s'", query)
    
    url = MUSICBRAINZ_SERVER+"/ws/2/recording?fmt=json&%s" % urllib.urlencode({
                'query': query.encode('utf-8', 'replace'),
                'limit': LIMIT_RESULTS_SONG
    })
    
    jsonResponse = retrieve_json(url)['recording']
    
    logger.debug("%i results for this lucene query", len(jsonResponse))
    
    return postprocess_recordings(jsonResponse, category)


def _check_phrasal_existence(artist, item, category):
    song, release = _split_release_if_is_there(item, category)
    logger.debug("Check phrasal with '%s', '%s', '%s'", song, artist, release)
    query = '"%s" AND artist:"%s"' % (_escape_lucene(song) , _escape_lucene(artist))
    if release:
        query += ' AND release:"%s"' % _escape_lucene(release)
    logger.debug("Query: %s", query)
    url = MUSICBRAINZ_SERVER+"/ws/2/recording?fmt=json&%s" % urllib.urlencode({
                'query': query.encode('utf-8', 'replace'),
                'limit': 1
        })
    response = retrieve_json(url)['recording']
    if response:
        resp_artist = response[0]['artist-credit'][0]['artist']['name']
        resp_item = postprocess_recordings(response, category)[0]
        result = (artist == resp_artist and item == resp_item)
        if not result:
            logger.debug("Phrasal check returned false: %s != %s || %s != %s",
                artist, resp_artist, item, resp_item)
        return result
    else:
        return False


@redis_cached
def check_existence_of(artist, song, category=None, avoid_phrasal=False):
    """ Returns a tuple is_ok, is_artist_wrong, best_match,
        where the first is a boolean telling if it exists,
        the second is a boolean telling if the problem is
        on the artist (as opposite to the song name), and
        the last one is a string with the best match as a
        suggestion. The last two values are meaningful only
        if the first one is False, but the result should
        always be a tuple of three elements.
        
        (Do not add a kw-arg to avoid computing suggestions:
        better exploit redis caching.)
    """
    assert type(artist) in (unicode, str)
    assert type(song) in (unicode, str)
    
    artist = artist.strip()
    song = song.strip()
    
    logger.debug("Checking existence of %s, %s, %s", artist, song, category)
    
    if not avoid_phrasal and _check_phrasal_existence(artist, song, category):
        musicbrainzReport.mark('phrasal-ok')
    else:
        # check artist
        artist_suggestions = search_artists(artist)
        if not artist_suggestions:
            musicbrainzReport.mark('no-artist-suggestion')
            return False, True, None
        
        if not any(suggestion == artist for suggestion in artist_suggestions):
            musicbrainzReport.mark('artist-suggestion')
            return False, True, artist_suggestions[0]
        
        # artist is ok
        
        # check song
        song_suggestions = search_songs(song, artist, category=category, yet_to_complete=False)
        if not song_suggestions:
            fuzzy_suggestion = search_songs(song, artist, category=category, yet_to_complete=False, fuzzy=True)
            if not fuzzy_suggestion:
                musicbrainzReport.mark('no-song-suggestion')
                return False, False, None
            else:
                musicbrainzReport.mark('fuzzy-song-suggestion')
                return False, False, fuzzy_suggestion[0]
        
        if not any(suggestion == song for suggestion in song_suggestions):
            musicbrainzReport.mark('precise-song-suggestion')
            return False, False, song_suggestions[0]
    
    # song is ok too
    musicbrainzReport.mark('check-ok')
    return True, False, None
    
def log_update():
    musicbrainzReport.logger.info("Musicbrainz server has executed an update.")

    
