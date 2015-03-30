import functools, logging
import bson.json_util as json_util

from fbvoting.conf import REDIS_TIMEOUT, ACTIVATE_REDIS
from fbvoting.mylogging import report

if ACTIVATE_REDIS:
    from flask_redis import Redis
    redis_store = Redis()

logger = logging.getLogger(__name__)

def _serialize(obj):
    return json_util.dumps(obj, sort_keys=True)

def _unserialize(item):
    return json_util.loads(item)

_test = [ {"a": 123, "b": 345, "C": [1,2,3]}, "ciao", -9, u"Hello"]
assert _unserialize(_serialize(_test)) == _test

def redis_cached(func):
    
    if not ACTIVATE_REDIS:
        logger.warn("Redis is not active: function %s not cached.", func.__name__)
        return func
    
    @functools.wraps(func)
    def search_cache_then_do_function(*args, **kwargs):
        # pylint: disable=E1101
        # redis_store methods will be there only after initialization
        
        func_name = func.__name__ # speed 
        redis_key = _serialize( (func_name, args, kwargs) )
        cache_result = redis_store.get( redis_key )
        
        if cache_result is None:
            report.mark(func_name + '-cacheless')
            func_result = func(*args, **kwargs)
            redis_store.set(redis_key, _serialize(func_result))
            redis_store.expire(redis_key, REDIS_TIMEOUT)
            return func_result
        else:
            report.mark(func_name + '-cached')
            return _unserialize(cache_result)
    
    return search_cache_then_do_function
    


def void_cache(func_to_void, *args, **kwargs):
    # pylint: disable=E1101
    # ibid.
    func_name = func_to_void.__name__ # speed
    redis_key = _serialize( (func_name, args, kwargs) )
    redis_store.delete(redis_key)
    report.mark(func_name + '-cache-voided')
