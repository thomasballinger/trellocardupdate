import webbrowser
from unidecode import unidecode

from local import user, cache

import trolly
from trolly.client import Client
from trolly.board import Board
from trolly.card import Card

APP_KEY = '10533337e4b5778c1c356c39dd3c79e9'

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
    """
    Returns trello API token if stored, else repeatedly tries to genreate token and returns
    """
    while True:
        token = user['token']
        if token: return token
        generate_token()

def test_token():
    token = get_user_token()
    client = Client(APP_KEY, token)
    try:
        b = Board(client, user.board_id)
        print b.getBoardInformation()
        return True
    except trolly.ResourceUnavailable:
        print 'bad board id'
        return False
    except trolly.Unauthorised:
        print 'bad permissions (refresh token)'
        return False


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
    except trolly.Unauthorised:
        print 'bad permissions (refresh token)'
        return False

#TODO need sensible way to figure out when we need to do a refresh
def get_cards(cache=False):
    """
    Returns [name, id] of cards from cache if cache flag is True else returns from Trello and 
    refreshes cache
    """
    if cache:
        return cache.cards
    token = get_user_token()
    client = Client(APP_KEY, token)
    print client, user.board_id
    if user.board_id is None:
        set_board()
    b = Board(client, user.board_id)
    cards = b.getCards()
    cache.cards = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]
    return cards

def get_card_names():
    return cache.cards

def add_comment_to_card(card_id, comment, move_to_bottom=False):
    token = get_user_token()
    client = Client(APP_KEY, token)
    c = Card(client, card_id)
    c.addComments(comment)
    print 'card comment added'
    if move_to_bottom:
        c.updateCard({'pos':'bottom'})
        print 'card moved to bottom of list'
