import webbrowser
import os
from unidecode import unidecode

from local import user, cache

import trolly
from trolly.client import Client
from trolly.board import Board
from trolly.card import Card

#TODO trolly uses lazy objects, if we're going to cache
# them we probably ought to do something neater like
# subclassing and saving the json

#TODO I guess this should be hardcoded?
APP_KEY = os.environ['TRELLO_API_KEY']

#TODO trolly has something for this
def generate_token():
    url = "https://trello.com/1/authorize?key=%s&name=trello-card-updater&expiration=1day&response_type=token&scope=read,write" % APP_KEY
    webbrowser.open(url)
    token = raw_input("paste in token: ").strip()
    user['token'] = token
    return user['token']

#TODO decide on a standard way for these to work, or at least check it if while True
# decide on return code for these too
def get_user_token():
    while True:
        token = user['token']
        if token: return token
        generate_token()

def test_token():
# doesn't actually test token yet, trolly is too lazy
    token = get_user_token()
    client = Client(APP_KEY, token)
    print client

def set_board():
    token = get_user_token()
    client = Client(APP_KEY, token)
    board_id = raw_input("paste in id of board: ").strip()
    b = Board(client, board_id)
    try:
        print b.getBoardInformation()
        user.board_id = board_id
        return True
    except trolly.ResourceUnavailable:
        print 'bad board id'
        return False

#TODO need sensible way to figure out when we need to do a refresh
def refresh_cards():
    token = get_user_token()
    client = Client(APP_KEY, token)
    print client, user.board_id
    if user.board_id is None:
        set_board()
    b = Board(client, user.board_id)
    cards = b.getCards()
    cache.cards = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]

def get_names():
    return cache.cards

def add_comment_to_card(card_id, comment, move_to_bottom=False):
    token = get_user_token()
    client = Client(APP_KEY, token)
    print client, user.board_id
    c = Card(client, card_id)
    c.addComments(comment)
    if move_to_bottom:
        c.updateCard({'pos':'bottom'})
