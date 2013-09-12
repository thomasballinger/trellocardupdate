from setuptools import setup

setup(
    name='TrelloCardUpdate',
    version='0.0.3',
    author='Thomas Ballinger',
    author_email='tom@hackerschool.com',
    packages=['trellocardupdate'],
    scripts=['bin/tu.py', 'bin/tu'],
    url='https://github.com/thomasballinger/trellocardupdate',
    install_requires=[
        'unidecode',
        'python_Levenshtein',
        'clint',
        'httplib2',
        'trolly',
        ],
    license='LICENSE.txt',
    description='basic command line trello client',
    long_description=open('README.txt').read(),
)


