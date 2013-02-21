import sys
import webbrowser

from unidecode import unidecode
import trolly
from trolly.client import Client
from trolly.board import Board
from trolly.card import Card

from local import user, cache

APP_KEY = '10533337e4b5778c1c356c39dd3c79e9'

client = None

def provide_client(func):
    """
    Supplies a client and catches errors and re-tries
    """
    init_client()
    def newfunc(*args, **kwargs):
        kwargs['client'] = client
        try:
            return func(*args, **kwargs)
        except trolly.Unauthorised:
            sys.stderr.write('bad permissions (refresh token)\n')
            init_client(True)
            kwargs['client'] = client
            return newfunc(*args, **kwargs)
    return newfunc

#TODO trolly has something for this
def generate_token():
    url = "https://trello.com/1/authorize?key=%s&name=trello-card-updater&expiration=1day&response_type=token&scope=read,write" % APP_KEY
    webbrowser.open(url)
    token = raw_input("paste in token: ").strip()
    user.token = token
    return user.token

#TODO decide on a standard way for these to work, or at least check it if while True
# decide on return code for these too
def init_client(new_token=False):
    """
    Initializes the client use for all Trello requests as a module-level variable
    """
    global client
    while True:
        if new_token:
            token = generate_token()
            user.token = token
            client = Client(APP_KEY, token)
            return
        token = user.token
        if token:
            client = Client(APP_KEY, token)
            return
        token = generate_token()

@provide_client
def get_user_token(client=None):
    return client.api_key

@provide_client
def test_token(client=None):
    try:
        b = Board(client, user.board_id)
        return True
    except trolly.ResourceUnavailable:
        sys.stderr.write('bad board id\n')
        return False
    except trolly.Unauthorised:
        sys.stderr.write('bad permissions (refresh token)\n')
        return False

@provide_client
def set_board(client=None):
    board_id = raw_input("paste in id of board: ").strip()
    b = Board(client, board_id)
    user.board_id = board_id
    return True

@provide_client
#TODO need sensible way to figure out when we need to do a refresh
def get_cards(use_cache=False, client=None):
    """
    Returns [name, id] of cards from cache if cache flag is True else returns from Trello and 
    refreshes cache
    """
    if use_cache:
        cards = cache.cards
        if cards:
            return cache.cards
    if user.board_id is None:
        set_board()
    b = Board(client, user.board_id)
    cards = b.getCards()
    card_names_and_ids = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]
    cache.cards = card_names_and_ids
    return card_names_and_ids

@provide_client
def add_comment_to_card(card_id, comment, move_to_bottom=False, client=None):
    c = Card(client, card_id)
    c.addComments(comment)
    sys.stderr.write('card comment added\n')
    if move_to_bottom:
        c.updateCard({'pos':'bottom'})
        sys.stderr.write('card moved to bottom of list\n')
