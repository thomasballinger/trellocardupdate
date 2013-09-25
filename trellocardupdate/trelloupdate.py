import os
import sys
import webbrowser
import json
import re
from functools import wraps

from unidecode import unidecode
import trolly
from trolly.client import Client
from trolly.board import Board
from trolly.card import Card

def retry_on_bad_auth(func):
    """If bad token or board, try again after clearing relevant cache entries"""
    @wraps(func)
    def retry_version(self, *args, **kwargs):
        while True:
            try:
                return func(self, *args, **kwargs)
            except trolly.ResourceUnavailable:
                sys.stderr.write('bad request (refresh board id)\n')
                self._board_id = None
                self.save_key('board_id', None)
            except trolly.Unauthorised:
                sys.stderr.write('bad permissions (refresh token)\n')
                self._client = None
                self._token = None
                self.save_key('token', None)
    return retry_version

def cached_accessor(func_or_att):
    """Decorated function checks in-memory cache and disc cache for att first"""
    if callable(func_or_att): #allows decorator to be called without arguments
        att = func_or_att.__name__
        return cached_accessor(func_or_att.__name__)(func_or_att)
    att = func_or_att
    def make_cached_function(func):
        @wraps(func)
        def cached_check_version(self):
            private_att = '_'+att
            if getattr(self, private_att):
                return getattr(self, private_att)
            setattr(self, private_att, self.load_key(att))
            if getattr(self, private_att):
                return getattr(self, private_att)
            value = func(self)
            setattr(self, private_att, value)
            self.save_key(att, value)
            return value
        return cached_check_version
    return make_cached_function

class TrelloUpdater(object):

    APP_KEY = '10533337e4b5778c1c356c39dd3c79e9'
    AUTH_URL = "https://trello.com/1/authorize?key=" + APP_KEY + "&name=trello-card-updater&response_type=token&scope=read,write"

    def __init__(self, filename=os.path.expanduser('~/.trelloupdate')):
        self.filename = filename
        self._board_id = None
        self._card_names_and_ids = []
        self._client = None
        self._token = None

    def clear_cache(self):
        self.save_key('board_id', None)
        self.save_key('token', None)
        self.save_key('card_names_and_ids', [])
        sys.exit(0) # in memory caches don't match disc cache, so die to kill the memory cache

    def save_key(self, key, value):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except IOError:
            data = {}
        if key == 'card_names_and_ids':
            data[key] = [(card[0].encode('rot13'), card[1]) for card in value]
        else:
            data[key] = value
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f)
        except IOError:
            sys.stderr.write('Error saving data to %r\n' % self.filename)
            # to allow platforms that can't save, just disable this next line
            raise

    def load_key(self, key):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except IOError:
            data = {}
        if key == 'card_names_and_ids':
            # ROT13 encoded so names of cards don't get indexed
            return [(card[0].decode('rot13'), card[1]) for card in data.get(key, [])]
        else:
            return data.get(key, None)

    @property
    @cached_accessor
    @retry_on_bad_auth
    def board_id(self):
        board_id = self.ask_for_board_id()
        Board(self.client, board_id).getBoardInformation() # raises errors if bad board id
        return board_id

    def ask_for_board_id(self):
        """Factored out in case interface isn't keyboard"""
        board_id = raw_input("paste in board id or url: ").strip()
        m = re.search(r"(?:https?://)?(?:trello.com)?/?b?/?([a-zA-Z]{8})/(?:.*)", board_id)
        if m:
            board_id = m.group(1)
        return board_id

    @property
    @cached_accessor
    def token(self):
        webbrowser.open(TrelloUpdater.AUTH_URL)
        token = raw_input("paste in token: ").strip()
        return token

    @property
    @cached_accessor
    @retry_on_bad_auth
    def card_names_and_ids(self):
        """Returns [(name, id), ...] pairs of cards from current board"""
        b = Board(self.client, self.board_id)
        cards = b.getCards()
        card_names_and_ids = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]
        return card_names_and_ids

    @property
    @retry_on_bad_auth
    def client(self):
        if self._client:
            return self._client
        client = Client(TrelloUpdater.APP_KEY, self.token)
        data = client.fetchJson('/members/me')
        sys.stderr.write('token found to be valid for user %s\n' % data['username'])
        self._client = client
        return client

    @property
    @cached_accessor('card_names_and_ids')
    def cached_card_names_and_ids(self):
        return []

    @retry_on_bad_auth
    def add_comment_to_card(self, card_id, comment, move_to_bottom=False):
        c = Card(self.client, card_id)
        c.addComments(comment)
        sys.stderr.write('card comment added\n')
        if move_to_bottom:
            c.updateCard({'pos':'bottom'})
            sys.stderr.write('card moved to bottom of list\n')

    def set_board(self):
        old_board_id = self._board_id or self.load_key('board_id')
        if old_board_id:
            sys.stderr.write('current board id: %s, https://trello.com/b/%s\n' % (old_board_id, old_board_id))
        else:
            sys.stderr.write('no board currently selected\n')
        try:
            self._board_id = None
            self.save_key('board_id', None)
            self.save_key('card_names_and_ids', [])
            self.board_id
        except KeyboardInterrupt:
            self._board_id = old_board_id
            self.save_key('board_id', old_board_id)
            sys.stderr.write('\n')
            sys.exit(1)
        sys.stderr.write('board id set\n')

    def test_token(self):
        self._client = Client(TrelloUpdater.APP_KEY, self.token)
        try:
            data = self._client.fetchJson('/members/me')
            sys.stderr.write('token found to be valid for user %s\n' % data['username'])
        except trolly.Unauthorised:
            self.client

    def generate_token(self):
        self._client = None
        self._token = None
        self.save_key('token', None)
        self.client

if __name__ == '__main__':
    u = TrelloUpdater()
    #os.system('rm temp*.json')
    #print 'getting a token:', TrelloUpdater('temp1.json').token
    #print 'getting a client:', TrelloUpdater('temp2.json').client
    #print 'getting a board id:', TrelloUpdater('temp3.json').board_id
    #print 'getting card names:', TrelloUpdater('temp4.json').card_names_and_ids
    #os.system('rm temp*.json')
    print TrelloUpdater().cached_card_names_and_ids
