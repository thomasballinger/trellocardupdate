TrelloCardUpdater

Command-line tool for updating Trello cards.

Sort of mimics the git interface.

Installation
============
pip install TrelloCardUpdater

or for development, clone the repo, then

- ``cd TrelloCardUpdate``
- ``virtualenv venv``
- ``source venv/bin/activate``
- ``pip install -e . -r requirements.txt``

Current Features:
=================

-  ability to add comments to cards
-  fuzzy matching on card name
-  single board at a time, which is persitently set

Bash Completion
---------------

For now, just completes cards and --flags. Paste this into your bashrc:

``complete -C 'tu --get-bash-completion' tu``
