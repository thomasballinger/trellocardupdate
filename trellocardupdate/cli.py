#!/usr/bin/env python
#TODO write bash completion scripts - matching is already there,
#the work is just figuring out the syntax again to 'complete'

import sys
from operator import itemgetter

import Levenshtein

from external_editor import edit as external_edit
import trello_update
import argparse

def choose(s, possibilities, threshold=.6):
    """
    Returns the closest match to string s if exceeds threshold, else returns None
    """
    if s in possibilities:
        return s
    if s == '':
        return None
    startswith = [x for x in possibilities if x.lower().startswith(s.lower())]
    if len(startswith) == 1: return startswith[0]
    contained = [x for x in possibilities if s.lower() in x.lower()]
    if len(contained) == 1: return contained[0]
    close = sorted([(x, Levenshtein.jaro_winkler(s, x, .05)) for x in possibilities], key=itemgetter(1))
    best = max([(x, Levenshtein.jaro_winkler(s, x, .05)) for x in possibilities], key=itemgetter(1))
    if best[1] < threshold:
        #print 'did you mean %s?' % best[0]
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
        if diff > .05: break
        if len(output) > 5: break
    return output

def get_card_completions(s):
    cards = trello_update.get_cards(use_cache=True)
    m = suggestions(unicode(s), [unicode(n) for n, _id in cards])
    return m

def get_card_name_and_id(card_query):
    cards = trello_update.get_cards()
    match = choose(unicode(card_query), [unicode(name) for name, id_ in cards])
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
    return message

def getcompletion(args):
    assert len(args) == 3
    try:
        first, arg, prevarg = args
    except ValueError:
        raise Exception('Bad completions arguments')
    subcommands = ['board', 'cards', 'token', 'comment']
    comment_flags = ['-d', '-m', '--message', '--move-down']
    token_flags = ['--get', '--generate', '--test']
    if prevarg == first:
        print '\n'.join([x for x in subcommands + ['-h', '--help'] if arg in x])
    elif prevarg in ['board', 'cards']:
        pass
    elif prevarg == 'comment':
        cards = trello_update.get_cards(use_cache=True)
        match = choose(unicode(arg), [unicode(name) for name, id_ in cards], .98)
        if match:
            print match
        else:
            print '\n'.join(suggestions(unicode(arg), [unicode(name) for name, id_ in cards]))
        #print '\n'.join([x for x in comment_flags + get_card_completions(arg) if arg in x])
    elif prevarg == 'token':
        print '\n'.join([x for x in token_flags if arg in x])
    elif prevarg == '-m':
        print 'TYPE_A_COMMENT_HERE'
    elif prevarg == '-d':
        print '\n'.join(get_card_completions(arg))
    else:
        pass

def add_comment(args):
    message = ' '.join(args.message)
    card = ' '.join(args.card)
    card_name, card_id = get_card_name_and_id(card)
    if card_id is None:
        print "Can't find card for query", card
        sys.exit()
    if not message:
    #TODO populate trello card url
        message = get_message_from_external_editor('NOT YET IMPLEMENTED', card_name, args.move_down)
    if not message.strip():
        print 'Aborting comment due to empty comment message.'
        sys.exit()
    trello_update.add_comment_to_card(card_id, message, args.move_down)

def list_cards(args):
    sys.stdout.write(''.join(name+'\n' for name, _ in trello_update.get_cards(verbose=args.verbose)[:args.limit]))


def CLI():
    # argparse can't parse some arguments to getcompletion, so special cased here
    if '--get-bash-completion' in sys.argv:
        i = sys.argv.index('--get-bash-completion')
        getcompletion(sys.argv[i+1:i+4])
        sys.exit()

    parser = argparse.ArgumentParser(
                description='Trello card updater')

    subparsers = parser.add_subparsers(help='action')

    comment = subparsers.add_parser('comment', help='add comment to card')
    comment.add_argument('card', action="store", nargs='+')
    comment.add_argument('-d', '--move-down', action="store_true", default=False)
    comment.add_argument('-m', '--message', action="store", dest="message", nargs='+', help='inline message to add to card (instead of launching editor', default=[])
    comment.set_defaults(action=add_comment)

    board = subparsers.add_parser('board', help='set the active board')
    board.set_defaults(action=lambda args: trello_update.set_board())

    token = subparsers.add_parser('token', help='actions with Trello API key')
    print_token_test = lambda args: sys.stdout.write(str(trello_update.test_token())+'\n')
    token.set_defaults(action=print_token_test)
    token.add_argument('--get', action="store_const", dest='action',
                       const=lambda args: sys.stdout.write(trello_update.get_user_token()+'\n'))
    token.add_argument('--generate', action="store_const", dest='action',
                       const=lambda args: trello_update.generate_token())
    token.add_argument('--test', action="store_const", dest='action',
                       const=print_token_test)

    cards = subparsers.add_parser('cards', help='display all cards')
    cards.add_argument('limit', type=int, nargs='?', default=sys.maxint, help='limit the number of cards shown')
    cards.add_argument('-v', '--verbose', action="store_true", dest='verbose', help='get more info')
    cards.set_defaults(action=list_cards)

    args = parser.parse_args(sys.argv[1:])
    args.action(args)

#TODO add ability to edit last comment
#TODO add ability to read last all comments on a card

if __name__ == '__main__':
    CLI()
