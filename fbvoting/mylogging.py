import logging, logging.config, logging.handlers, traceback
import os, threading, functools, random, string, urllib2, sys
from collections import defaultdict

from fbvoting.conf import LOGGING_DIRECTORY, DEBUG, BASEPATH

LEVEL_STDOUT = logging.INFO

## ensure existence of logging directory ##
if LOGGING_DIRECTORY is not None:
    if not os.path.isdir(LOGGING_DIRECTORY):
        os.mkdir(LOGGING_DIRECTORY)



logger = logging.getLogger(__name__)

class Report(object):
    interval = 60 * 60 #seconds
    
    def __init__(self, name):
        assert type(name) is str
        
        self.events = defaultdict(int)
        self.log_id = ''.join([random.choice(string.ascii_uppercase) for _ in range(3)])
        self.name = name
        
        # set up logger #
        self.logger = logging.getLogger('report-' + name)
        self.logger.setLevel(logging.INFO)
        
        # setting up its own file ##
        logger.info('Creating logger for report ' + name)
        if LOGGING_DIRECTORY is not None:
            logFileHandler = logging.handlers.RotatingFileHandler(LOGGING_DIRECTORY + name + '-report.log', maxBytes=4000)
        else:
            logFileHandler = logging.StreamHandler(sys.stdout)
        logFileHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logFileHandler.setLevel(logging.INFO)
        self.logger.addHandler(logFileHandler)
        
        # periodic write it #
        @functools.wraps(self.log)
        def periodic_logging():
            self.log()
            timer = threading.Timer(self.interval, periodic_logging)
            timer.daemon=True
            timer.start()
        
        periodic_logging()
    
    def mark(self, event_name):
        logger.debug('Event in %s: %s', self.name, event_name)
        self.events[event_name]+=1
    
    def log(self, ):
        if self.events:
            events = self.events.items()
            self.events = defaultdict(int)
            message = ", ".join([ (str(v) + ' ' + k) for (k, v) in events])
            self.logger.info("logger" + self.log_id  + " - " + message)



report = Report('misc')
viewReport = Report('view')
musicbrainzReport = Report('musicbrainz')


def report_view(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        viewReport.mark(func.__name__)
        return func(*args, **kwargs)
    
    return newfunc



def configure_logging(add_handler_to=None):
    
    if add_handler_to is None:
        add_handler_to = []
    assert type(add_handler_to) is list
    
    minimum_level = logging.DEBUG if DEBUG else logging.INFO
    
    # define global formatter (there is a bug if you want multiple formatter)
    class MyLoggingFormat(logging.Formatter):
        def formatException(self, exc_tuple):
            _, exc, exc_raw_traceback = exc_tuple
            exc_type = type(exc)
            
            try:
                exc_trace = traceback.extract_tb(exc_raw_traceback, limit=15)
                interesting_stacks = (
                    (filename.replace(BASEPATH, '') + ':' + str(lineno))
                    for (filename, lineno, funcname, content) in reversed(exc_trace)
                    if '/fbvoting/' in filename and '/venv/' not in filename)
                
                location = next( interesting_stacks, 'unknown')
            except Exception as e:
                logger.warn("Cannot extract trace: %s", e)
                location = 'unknown'
            
            
            if exc_type == urllib2.HTTPError:
                try:
                    return """HTTPException: %s
                        location: %s
                        reason: %s
                        code: %i
                        url: %s
                        response: %s, 
                        """ % (exc, location, exc.reason, exc.code, exc.url, str(exc.read()))
                except:
                    pass
            
            return 'Exception %s in %s. %s' % (exc_type, location, str(exc))
    
    formatter = MyLoggingFormat('%(asctime)s - %(module)s.%(funcName)s - %(levelname)s - %(message)s')
    
    # define handler with it
    def handler(name, level):
        handler = logging.handlers.TimedRotatingFileHandler(LOGGING_DIRECTORY + name, when='D', backupCount=31)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        for logging_thing in add_handler_to:
            logging_thing.addHandler(handler)
        return handler
    
    ## log warnings and errors on a file ##
    logErrFileHandler = handler('problems.log', logging.WARNING)
    
    ## all messages on another file ##
    logFileHandler = handler('all.log', minimum_level)
    
    ## connect to root ##
    rootLogger = logging.getLogger()
    rootLogger.setLevel(minimum_level)
    for handler in (logFileHandler, logErrFileHandler):
        rootLogger.addHandler(handler)
    
    ## quiet noisy library loggers ##
    logging.getLogger('apiclient.discovery').setLevel(logging.WARN)

