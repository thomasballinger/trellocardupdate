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
        try:
            return func(*args, **kwargs)
        except trolly.Unauthorised:
            sys.stderr.write('bad permissions (refresh token)\n')
            init_client(True)
            return newfunc(*args, **kwargs)
    return newfunc

#TODO trolly has something for this
def generate_token():
    url = "https://trello.com/1/authorize?key=" + APP_KEY + "&name=trello-card-updater&response_type=token&scope=read,write"
    webbrowser.open(url)
    try:
        token = raw_input("paste in token: ").strip()
    except KeyboardInterrupt:
        print '\ntoken set canceled'
        sys.exit(1)
    user.token = token
    return user.token

#TODO decide on a standard way for these to work, or at least check it if while True
# decide on return code for these too
def init_client(new_token=False):
    """
    Initializes the client use for all Trello requests as a module-level variable
    """
    global client
    if new_token or not user.token:
        token = generate_token()
        user.token = token
    else:
        token = user.token
    client = Client(APP_KEY, token)

@provide_client
def get_user_token():
    return client.api_key

@provide_client
def test_token():
    try:
        Board(client, user.board_id).getBoardInformation()
        return True
    except trolly.ResourceUnavailable:
        sys.stderr.write('bad board id\n')
        return False
    except trolly.Unauthorised:
        sys.stderr.write('bad permissions (refresh token)\n')
        return False

@provide_client
def set_board():
    if user.board_id:
        print 'current board id: %s, https://trello.com/b/%s' % (user.board_id, user.board_id)
    else:
        print 'no board currently selected'
    try:
        board_id = raw_input("paste in id of new board, or ctl-c to cancel: ").strip()
    except KeyboardInterrupt:
        print '\nboard set canceled'
        sys.exit(1)

    try:
        Board(client, board_id).getBoardInformation()
    except trolly.ResourceUnavailable:
        sys.stderr.write('bad board id\n')
        return False
    except trolly.Unauthorised:
        sys.stderr.write('bad permissions (refresh token)\n')
        return False

    user.board_id = board_id
    return board_id

@provide_client
#TODO need sensible way to figure out when we need to do a refresh
def get_cards(use_cache=False, verbose=False):
    """
    Returns [name, id] of cards from cache if cache flag is True else returns from Trello and 
    refreshes cache
    """
    if use_cache:
        cards = cache.cards
        if cards:
            return cache.cards
    if user.board_id is None:
        board_id = set_board()
    else:
        board_id = user.board_id
    b = Board(client, board_id)
    cards = b.getCards()

    if verbose:
        card_names_and_ids = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]
        return card_names_and_ids
    else:
        card_names_and_ids = [(unidecode(c.name.decode('utf8')), c.id) for c in cards]
        cache.cards = card_names_and_ids
        return card_names_and_ids

@provide_client
def add_comment_to_card(card_id, comment, move_to_bottom=False):
    c = Card(client, card_id)
    c.addComments(comment)
    sys.stderr.write('card comment added\n')
    if move_to_bottom:
        c.updateCard({'pos':'bottom'})
        sys.stderr.write('card moved to bottom of list\n')
