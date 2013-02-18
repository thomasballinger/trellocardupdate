#!/usr/bin/env python
#TODO write bash completion scripts - matching is already there,
#the work is just figuring out the syntax again to 'complete'

import sys
import re
from operator import itemgetter

import Levenshtein

from external_editor import edit as external_edit
import trello_update
import simpledispatchargparse

def choose(s, possibilities, threshold=.6):
    """
    Returns the closest match to string s if exceeds threshold, else returns None 
    """
    if s in possibilities:
        return s
    startswith = [x for x in possibilities if x.lower().startswith(s.lower())]
    if len(startswith) == 1: return startswith[0]
    contained = [x for x in possibilities if s.lower() in x.lower()]
    if len(contained) == 1: return contained[0]
    close = sorted([(x, Levenshtein.jaro_winkler(s, x, .05)) for x in possibilities], key=itemgetter(1))
    best = max([(x, Levenshtein.jaro_winkler(s, x, .05)) for x in possibilities], key=itemgetter(1))
    if best[1] < threshold:
        print 'returning None because', best, 'is below threshold of', threshold
        print 'out of', close
        return None
    return best[0]

def suggestions(s, possibilities):
    #TODO don't use jaro_winkler, or use it more intelligently;
    # ie break up words and match on each of them
    # jaro_winkler weighs the front more
    startswith = [x for x in possibilities if x.lower().startswith(s.lower())]
    if startswith: return startswith
    contained = [x for x in possibilities if s.lower() in x.lower()]
    if contained: return contained
    jws = [(x, Levenshtein.jaro_winkler(s, x)) for x in possibilities]
    jws.sort(key=lambda x:0-x[1])
    diffs = [x[1] - y[1] for x, y in zip(jws[:-1], jws[1:])]
    output = []
    for (card_name, score), diff in zip(jws[:-1], diffs):
        output.append(card_name)
        print diff
        if diff > .05: break
        if len(output) > 5: break
    return output

def print_card_completions(s):
    cards = trello_update.get_cards()
    m = suggestions(unicode(s), [n for n, _id in cards])
    for x in m:
        print x

def get_card_name_and_id(card_query):
    cards = trello_update.get_cards()
    match = choose(unicode(card_query), [name for name, id_ in cards])
    if match is None: return None, None
    return [(name, id_) for (name, id_) in cards if name == match][0]

def get_message_from_external_editor(card_url, card_name, moved_down):
    moved_down_message = "\n#   card will be moved to bottom of stack"

    prompt = """
# Please enter the message you'd like to add to card. Lines starting
# with '#' will be ignored, and an empty message aborts the commit.
# On card {card_name}
# Changes to be committed:
#   (url of card: {card_url})
#
#   message will be added to card{moved_down}
#""".format(card_name=card_name, card_url=card_url, moved_down=moved_down_message if moved_down else '')
    from_external = external_edit(prompt)
    message = '\n'.join([line for line in from_external.split('\n') if ((len(line) > 0 and line[0] != '#'))])
    message = re.sub(r'[^\n]\n[^\n]', '', message)
    return message

#TODO move this out of here

def CLI():
    parser = simpledispatchargparse.ParserWithSimpleDispatch(description='Trello card updater')

    parser.add_argument('-d', '--move-down', action="store_true", default=False)
    parser.add_argument('-m', '--message', action="store", dest="message", nargs='+', help='inline message to add to card (instead of launching editor', default=[])
    parser.add_argument('card', action="store", nargs='+')

    #TODO get rid of almost all of these, just good for testing
    @parser.add_command
    def listcards():
        print 'listing cards'; print trello_update.get_card_names()
    @parser.add_command(metavar='CARD_NAME')
    def listcardcompletions(s): print 'listing card completions for', s; print_card_completions(s)
    @parser.add_command(metavar='BOARD_ID')
    def setboard(s): print 'setting board to', s
    @parser.add_command
    def get_token(): print 'token:'; print trello_update.get_user_token()
    @parser.add_command
    def generate_token(): print 'generating token...'; print trello_update.generate_token()
    @parser.add_command
    def test_token(): print 'testing token...'; print trello_update.test_token()
    @parser.add_command
    def set_board(): print 'setting board...'; print trello_update.set_board()
    @parser.add_command
    def refresh_cards(): print 'refreshing cards...'; print trello_update.refresh_cards()

    # At this point we've bailed if we're not adding a comment to a person

    args = parser.parse_args(sys.argv[1:])
    message = ' '.join(args.message)
    card = ' '.join(args.card)

#TODO handle when this doesn't get anything good, decide how lenient - fuzziness mostly happen during completion
    card_id, card_name = get_card_name_and_id(card)
    if card_id is None:
        print "Can't find name for query", card
        sys.exit()
    print 'got', card_id, card_name

    if not message:
#TODO populate trello card url
        message = get_message_from_external_editor('NOT YET IMPLEMENTED', card_name, args.move_down)

    if not message.strip():
        print 'Aborting comment due to empty comment message.'
        sys.exit()
    trello_update.add_comment_to_card(card_id, message, args.move_down)

#TODO add ability to edit last comment
#TODO add ability to read last all comments on a person

if __name__ == '__main__':
    CLI()
