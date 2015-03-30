import urlparse, urllib, urllib2, json, logging, functools

from flask import url_for as old_url_for

from fbvoting.conf import DEBUG, Config

logger = logging.getLogger(__name__)

def retrieve_json(url):
    """ Retrieve and decode JSON from a url."""
    logger.debug('Retrieving json from %s', url)
    apiRequest = urllib2.Request(url, headers={"Accept" : "application/json"})
    apiResponse = urllib2.urlopen(apiRequest)
    return json.load(apiResponse)

def uniquify(l):
    seen = set()
    return [x for x in l if x not in seen and not seen.add(x)]


def add_GET_params(url, params):
    assert type(url) in (str, unicode)
    assert type(params) is dict
    
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.urlencode(query)
    
    return urlparse.urlunparse(url_parts)


def url_for(*args, **kwargs):
    """ decorating url_for in a way that always returns https """
    kwargs['_external'] = True
    url = old_url_for(*args, **kwargs)
    if 'http:/' in url:
        url = url.replace('http:/', 'https:/')
    else:
        if not url.startswith('https:/'):
            logger.warn("URL not changed to https: %s", url)
    return url


assert not Config.SERVER_NAME.startswith('https://')

def as_full_url(path_on_server):
    assert type(path_on_server) in (str, unicode)
    assert path_on_server[0] == '/'
    
    return 'https://' + Config.SERVER_NAME + path_on_server




class cached(dict):
    """
Decorator that caches results of the function.
What happens is that the function is transformed into a dictionary
that calls the function when values are missing. Invoking .clear()
on the function clears this cache.
    """
    def __init__(self, func):
        dict.__init__(self)
        self.func = func
    
    def __call__(self, *args):
        return self[args]
    
    def __missing__(self, key):
        result = self[key] = self.func(*key)
        return result


def digest(s, max_len=50):
    assert type(s) in (str, unicode)
    if len(s) <= max_len:
        return s
    else:
        return s[:(max_len-3)] + '...'



def ignore_errors(funct):
    """
Decorator that, if we are not debugging, makes a function ignore its errors.
    """
    if DEBUG:
        return funct
    
    @functools.wraps(funct)
    def new_fun(*args, **kwargs):
        try:
            return funct(*args, **kwargs)
        except Exception as e:
            func_description = (funct.__name__ + '(' +
                digest(str(args) + ',' + str(kwargs)) + ')')
            logger.exception('error on ' + func_description + ': ' + e.message)
    
    return new_fun
    
