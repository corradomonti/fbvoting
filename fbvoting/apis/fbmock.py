import random, logging

import flask
from flask import request

from fbvoting.conf import MOCKING_MODE, MOCKING_KEY

logger = logging.getLogger(__name__)

class FakeUser(dict):
    
    def __init__(self, custom_id=None):
        dict.__init__(self)
        self['id'] = random.randint(0, 1024) if custom_id is None else custom_id
    
    
    def __getitem__(self, key):
        if key not in self:
            self[key] = key + str(self['id'])
        logger.warn('Mock user api providing "' + str(key) + '"')
        return dict.__getitem__(self, key)
    
    def __getattr__(self, key):
        return self.__getitem__(key)
    
    def __call__(self):
        return self
    
    def __repr__(self):
        return "FBFakeUser<" + str(self.id) + ">"
    
    

class FakeApi(dict):
    
    def me(self):
        current_id = _mock_id()
        self[current_id] = FakeUser(current_id)
        return self[current_id]
    
    def __getitem__(self, key):
        if key not in self:
            self[key] = FakeUser(key)
        logger.warn('Mock api providing user "' + str(key) + '"')
        return dict.__getitem__(self, key)
    
    def __repr__(self):
        return "FB-Fake-Api"
    

fakeApi = FakeApi()

def _mock_id():
    try:
        return int(request.args['mock'])
    except KeyError:
        return random.randint(0, 1000)


def should_we_mock():
    if flask.has_request_context() and bool(request.args.get('mock')):
        if request.args.get('mocking-key') == MOCKING_KEY:
            return True
        else:
            logger.warn('Somebody tried to use mocking mode without mocking key.')
    else:
        return MOCKING_MODE


def mocking_false(funct):
    def new_fun(*args, **kwargs):
        return False if should_we_mock() else funct(*args, **kwargs)
    
    return new_fun

def mocking_api(funct):
    def new_fun(*args, **kwargs):
        return fakeApi if should_we_mock() else funct(*args, **kwargs)
    
    return new_fun
