from flask import url_for, Flask, session
from flask.sessions import SessionMixin, SessionInterface
import re
import random
from collections import OrderedDict, defaultdict, namedtuple
from itertools import cycle, product
import difflib
from frozendict import frozendict
import json
import os
from Crypto.Cipher import AES
from urlparse import urlparse

import pandas as pd

from external import harlowe_extra
from external.harlowe_extra import html_to_nodes, html_to_trees

from external.types import (Opponent, Enemy, Remark, 
                            Word, Map, Place, Message)


local_app = Flask(__name__)
json_key = ''

flask_to_js = {
  'SEND_REMARK': 'SEND_REMARK',
  'SEND_WORDBANK': 'SEND_WORDBANK',
  'SEND_ENCOUNTER': 'SEND_ENCOUNTER',
  'SEND_MAP': 'SEND_MAP',
  'CHANGE_ENEMY': 'CHANGE_ENEMY',
  'SEND_PLAYER' : 'SEND_PLAYER'
}

js_to_flask = {
  'INSULT': 'INSULT', 
  'REQUEST_ENCOUNTER': 'REQUEST_ENCOUNTER',
  'UPDATE_PLAYER': 'UPDATE_PLAYER'
}



def load_phrases(path):
    with open(path, 'r') as fh:
        return fh.read().split('\n')


def make_gspread_json():
    global json_key
    with local_app.open_resource('resources/crypt.json', 'r') as fh:
        key1, key2 = os.environ['KEY1'], os.environ['KEY2']
        text = fh.read()
        aes = AES.new(key1, AES.MODE_CBC, key2)
        return json.loads(aes.decrypt(text))

    

def load_elm_helpers(path):
  """ Load socket message names from static/elm-helpers.js
  """

  global js_to_flask
  global flask_to_js

  pat_0 = 'js_to_flask = (\{.*?\})'
  pat_1 = 'flask_to_js = (\{.*?\})'


  with open(path, 'r') as fh:
    js_code = open(path, 'r').read()
    js_code = js_code.replace('\n', ' ').replace('\t', '')

    match = re.findall(pat_0, js_code)
    js_to_flask =  eval(match[0])

    match = re.findall(pat_1, js_code)
    flask_to_js =  eval(match[0])


        
class Player(object):

    def __init__(self, vocab, grammar, capacity=6):
        """ Player manages vocab and grammar. 
        Given a partial phrase, has a method to return next words/possible completions.
        Model describes loaded/unloaded words. Corresponds to Elm model. 
        """
        self.vocab = vocab
        self.grammar = grammar
        capacity = [(pos, capacity) for pos,_ in vocab]

        loaded, unloaded = [], []
        for pos, examples in vocab:
            loaded   += [Word(word, pos)._asdict() for word in examples[:4]]
            unloaded += [Word(word, pos)._asdict() for word in examples[4:]]
        
        self.model = {'loaded': sorted(loaded),
                       'unloaded': sorted(unloaded),
                       'capacity': capacity}


    def next_word(self, phrase):
        """ Provides list of possible next Words based on a phrase (list of Words)
        If nothing is possible (e.g., end of phrase) return empty list.
        Filters words based on loaded.
        """
        if phrase:
            last = phrase[-1]
            index = 1 + [pos for pos,_ in self.vocab].index(last.partOfSpeech)
            if index >= len(self.vocab):
                return []
        else:
            index = 0

        next_words = []
        for word in self.vocab[index][1]:
            if word in [w['word'] for w in self.model['loaded']]:
                next_words += [Word(word, self.vocab[index][0])]

        return next_words



class VersusDerp(Enemy):
    def __init__(self, *args, **kwargs):
        super(VersusDerp, self).__init__(*args, **kwargs)

    def reply(self, insult):
        
        progress = insult['progress']

        enemy_index = int(progress * 5.999) + 1
        self.view = {'image': url_for('static', 
            filename='images/derp-%d.jpg' % enemy_index)}

        if progress > 0.8:
            self.vocab = load_vocab('derp')
        else:
            self.vocab = load_vocab('DIDB')

        super(VersusDerp, self).reply(insult)



class Session(dict, SessionMixin):
    def __init__(self, sid=None):
        self.sid = sid


class CMPDSessionInterface(SessionInterface):

    def __init__(self):
        self.db = {}

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if sid not in self.db:
            self.db[sid] = Session(sid=sid)

        return self.db[sid]

    def save_session(self, app, session, response):
        print 'saved', session.sid
        self.db[session.sid] = session


def nearest_word(word, wordbank, case=False):
    """ Return closest word. Case-insensitive unless case=True.
    """
    # import difflib

    SM = difflib.SequenceMatcher
    distance = lambda a, b: SM(None, a, b).ratio()
    if not case:
        distance = lambda a, b: SM(None, a.lower(), b.lower()).ratio()
        
    N = float(len(wordbank))
    
    distances = [distance(word, w) for w in wordbank]
    hit = wordbank[distances.index(max(distances))]
    return hit




def emit(*args, **kwargs):
    """ Use the emit function bound to the current session. 
    """
    return session['emit'](*args, **kwargs)


class GameMaster(object):
    
    def __init__(self, player):
        # nodes dict can be obtained using html_to_nodes()

        self.player = player
        self.current_enemy = None
        self.remarks = []

        self.passage_trees = {}
        self.story_vars = {}
        self.node = None
        self.current_passage = None


    def initialize(self):
        """ 
        Send the map and player info. 
        Determines loadout and displayed map.
        Called when JS loads and emits INITIALIZE.
        """
        self._transition(self.current_passage)
        

    def load_html(self, html):
        # maps, encounters, messages = html_to_nodes(html)
        attrs, _, passages = harlowe_extra.parse_harlowe_html(html)

        # startups and headers not used, for now
        startups, headers, passages, story_vars = html_to_trees(html)

        self.story_vars = story_vars
        self.passage_trees = passages # {name: (passage, tree)}

        self.current_passage = [n for n, (p,_) in passages.items()
                                if p.pid == attrs['startnode']][0]



        # TODO: check graph for completeness
        # maps = {k: maps[k] for k in ['Dummy office', 'presidential library']}
        # encounters = {k: encounters[k] for k in ['Challenge ctenophora']}
        
        # passage_names = maps.keys() + encounters.keys()
        # for passage, m in maps.items():
        #     for place in m.places:
        #         assert (place.label in passage_names)

        # self.nodes = maps
        # # use enemy definitions in stable
        # # self.nodes.update({k: stable[encounters[k]] for k in encounters})
        # self.nodes.update(encounters)
        # self.nodes.update(messages)

    def _transition(self, passage_name):
        passage, tree = self.passage_trees[passage_name]
        node, links, story_vars = harlowe_extra.enter(passage, tree, self.story_vars)
        self.node = node
        self.story_vars = story_vars
        self.current_passage = passage_name

        if isinstance(node, Message):
            self.to_message()
        if isinstance(node, Enemy):
            self.to_encounter()
        if isinstance(node, Map):
            self.to_map()

    def transition(self, name):
        
        # pick out HarloweLink from evaluated tree
        # call its on_transition method with global_vars
        # now check the HarloweLink.passage_name
        
        # the transition could point nowhere!!!
        # don't let evaluate mutate global_vars until we are sure it worked!!!
        # we are in dangerous territory
        # can't allow stupid shit in Harlowe

        passage, tree = self.passage_trees[self.current_passage]
        links = harlowe_extra.find_links(passage)
        self.story_vars, destination = links[int(name)].do_transition(self.story_vars)
        self._transition(destination)
        

        # if isinstance(self.node, Map):
        #     self.to_map()
        # if isinstance(self.node, Enemy):
        #     print 'sending enemy', self.node, 'victory', 
        #     self.to_encounter()
        # if isinstance(self.node, Message):
        #     self.to_message()

    def to_message(self):
        message = self.node._asdict()
        # deal with nested namedtuple
        message['choices'] = [c._asdict() for c in message['choices']]
        emit('SEND_MESSAGE', message)
            
    def to_map(self):
        map_ = self.node._asdict()
        # deal with nested namedtuple
        map_['places'] = [p._asdict() for p in map_['places']]
        emit('SEND_PLAYER', self.player.model)
        emit('SEND_MAP', map_)
        
    def to_encounter(self):
        """ Based on request_encounter()
        Initializes enemy. Starts Player and asks to send an updated Wordbank.
        """
        enemyClass = self.node.cls
        
        enemy_vocab = load_vocab(self.node.vocab)

        netloc = urlparse(self.node.image).netloc
        if 'localhost' in netloc:
            image = url_for('static', filename=self.node.image)
        else:
            image = self.node.image
        
        enemy_model = {'image': image, 
                       'health': 0.5, 
                       'name': self.node.name}

        self.current_enemy = enemyClass(enemy_vocab, enemy_model)
        
        emit('SEND_ENCOUNTER', self.current_enemy.model)

        self.player_phrase = []
        self.next_word()


    def next_word(self):
        """ Weird to have end-of-phrase logic here.
        """
        # returns None if the phrase is complete
        # doesn't work if player chooses to end phrase early
        # fix with better insult UI
        new_wordbank = self.player.next_word(self.player_phrase)
        if new_wordbank:
            new_wordbank = [w._asdict() for w in new_wordbank]
            
            emit('SEND_WORDBANK', new_wordbank)
        else:
            self.reply()
            self.player_phrase = []
            self.next_word()

    def insult(self, insult):
        """ Responds to incoming insult. Called by socketio.on('INSULT').
        """
        insult['word'] = Word(**insult['word'])
        self.player_phrase += [insult['word']]
        self.next_word()
        
    def reply(self):
        """ Send full remark (insult + retort + score).
        """
        insult = ' '.join(w.word for w in self.player_phrase)
        retort = self.current_enemy.retort(insult, self.remarks)
        score = self.score(insult, retort)
        self.current_enemy.model['health'] += score
        remark = Remark(insult=insult, retort=retort, 
                        score=score, health=self.current_enemy.model['health'])
        self.remarks += [remark]

        emit('SEND_REMARK', remark._asdict())

        print 'health is', self.current_enemy.model['health']
        if self.current_enemy.model['health'] > 0.7:
            self.transition(self.node.victory)

        
        
    def score(self, insult, retort):

        past_insults = [remark.insult for remark in self.remarks]
        past_retorts = [remark.retort for remark in self.remarks]

        if insult in past_insults:
            return -0.05
        if insult in past_retorts:
            return -0.05

        return 0.1
        

class LocalGameMaster(GameMaster):
    def __init__(self, *args, **kwargs):

        self.app = Flask(__name__)
        self.app.secret_key = 'fuck you'
        self.app_context = self.app.test_request_context()
        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).__init__(*args, **kwargs)

    def initialize(self):
        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).initialize()
 
    def transition(self, node):
        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).transition(node)

    def to_encounter(self):
        from IPython.display import clear_output, display, Image
        clear_output()

        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).to_encounter()

        # print 'Enemy:', self.node
        print 'Enter text to insult, enter nothing to quit.'
        self.progress = 0.5

        while True:

            user_input = raw_input()
            if user_input == '':
                break

            # match user input to get insult
            wordbank = self.player.next_word(self.player_phrase)
            wordbank_words = [w.word for w in wordbank]
            match = nearest_word(user_input, wordbank_words)

            insult = {'word': wordbank[wordbank_words.index(match)], 
                      'progress': self.progress}
            # looks like it's coming from Elm
            insult['word'] = insult['word']._asdict()

            # mimic insult
            with self.app_context:
                session['emit'] = self.emit
                self.insult(insult)


    def to_map(self):
        from IPython.display import clear_output
        clear_output()

        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).to_map()

        places = ['%s | %s' % (p.key, p.preview) for p in self.node.places]

        print 'Current map:', self.node.name
        print 'Go to'
        print '\n'.join(places)

        flag = True
        while flag:
            user_input = raw_input()
            if user_input == '':
                break

            for p in self.node.places:
                if p.key.startswith(user_input):
                    self.transition(p.label)
                    flag = False
                    break

    def to_message(self):
        from IPython.display import clear_output, HTML, display
        from markdown import markdown

        clear_output()

        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).to_message()

        print 'Current message:', self.node.name

        display(HTML(markdown(self.node.text)))
        s = '\n'.join('%s | %s' % (c.key, c.label) for c in self.node.choices)
        print 'Choose:\n' + s

        flag = True
        while flag:
            user_input = raw_input()
            if user_input == '':
                break

            for c in self.node.choices:
                if c.key == user_input or c.key == '*':
                    self.transition(c.name)
                    flag = False
                    break           



    
    def emit(self, message, data):
        """ Local simulation of sending message and data through socket.
        """
        from IPython.display import Image, display, HTML
        from markdown import markdown
        
        if message == flask_to_js['SEND_WORDBANK']:
            wordbank = data
            wordbank = [w['word'] for w in wordbank]
            print 'Wordbank:', ', '.join(wordbank[:4] +  ['...'])

        if message == flask_to_js['SEND_REMARK']:
            
            width = 49

            self.progress += data['score']
            bar =  '-' * int((width - 5) * self.progress)
            bar += ' ' * int((width - 5) * (1 - self.progress))

            insult_message = '# %s (%.2f)' % (data['insult'], data['score'])
            insult_spacer = ' ' * (width - len(insult_message) - 1)         

            print '#' * width
            print '# [%s] #' % bar
            print  '%s%s#' % (insult_message, insult_spacer)
            print '# %45s #' % data['retort'] 
            print '#' * width

        if message == flask_to_js['SEND_MAP']:
            display(Image(data['image'], width=200))
            if data['intro']:
                display(HTML(markdown(data['intro'])))
            # print 'places:', data['places']

        if message == flask_to_js['SEND_ENCOUNTER']:
            print 'Launching encounter with', data
            # some bs with image width
            display(HTML('<img src="%s" width="200">' % data['image']))
            # display(Image(data['image']), width=200)


def load_sheet(worksheet, g_file='CMPD'):
    """Load sheet as array of strings (drops .xls style index)
    gspread allows for .xlsx export as well, which can capture style info.
    :param worksheet: provide None to return a dictionary of all sheets
    :param g_file:
    :return:
    """
    # see http://gspread.readthedocs.org/en/latest/oauth2.html

    

    json_key = make_gspread_json()
    
    from oauth2client.service_account import ServiceAccountCredentials
    import gspread

    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    gc = gspread.authorize(credentials)
    xsheet = gc.open(g_file)

    if isinstance(worksheet, int):
        wks = xsheet.get_worksheet(worksheet)
    if worksheet is None:
        return {x.title: np.array(x.get_all_values()) for x in xsheet.worksheets()}
    else:
        wks = xsheet.worksheet(worksheet)
    xs_values = wks.get_all_values()
    return xs_values


def load_vocab(sheet, reload=False, subset=None):
    """ Load columns of google sheet into vocab of type [(header, [word])]. 
    No entry for empty header. Empty and duplicate words removed.

    Uses local cached json if reload is False and file exists.
    """
    path = 'resources/vocab/%s.json' % sheet



    def load_remote(sheet):

        sheet = load_sheet(sheet)
        df = pd.DataFrame(sheet[1:], columns=sheet[0])
        vocab, subsets = [], []
        for col in df:
            if col:
                words = list(df[col])
                vocab += [(col, words)]

        with open(path, 'w') as fh:
            json.dump(vocab, fh, indent=4)
        return vocab

    def filter_vocab(vocab, subset):
        """ If subset is None, all words returned.
        """
        if subset is None:
            subset = ''
        actual_vocab = []
        subset_index = []
        for (col, words) in vocab:
            if col.startswith('_') and re.findall(subset, col):
                subset_index += [i for i,x in enumerate(words) if x]
        subset_index = sorted(set(subset_index))
        
        for (col, words) in vocab:
            if not col.startswith('_'):
                if subset:
                    words = [w for i, w in enumerate(words) 
                               if i in subset_index]
                words = sorted(set(words))
                actual_vocab += [(col, words)]

        return actual_vocab


    if reload:
        vocab = load_remote(sheet)
    else:
        try:
            with open(path, 'r') as fh:
                vocab = json.load(fh)
        except (IOError, ValueError):
            vocab = load_remote(sheet)

    return filter_vocab(vocab, subset)



def make_all_phrases(vocab):
    return [' '.join(x) for x in product(
                          *[words for _, words in vocab])]

def make_row_phrases(vocab):
  phrases = []
  for row in zip(*[words for cat,words in vocab]):
      phrases += [' '.join(row)]
  return phrases



make_DIDB_phrases = lambda: make_row_phrases(load_vocab('DIDB'))


maps = frozendict({
    'islands': frozendict({
        'places': 
              [(0.24, 0.12, 'w', 'ctenophora'),
              (0.19, 0.68, 'x', 'ctenophora'), 
              (0.80, 0.22, 'y', 'derp'),
              (0.74, 0.71, 'z', 'underground')],
        'image': 'images/islands.png',
        'vocab': 'derp'}) ,

    'ovaloffice': frozendict({
        'places': 
            [(0.235, 0.77, 'a', 'ctenophora'),
             (0.055, 0.46, 'b', 'ctenophora'),
             (0.265, 0.42, 'c', 'ctenophora'),
             (0.723, 0.27, 'd', 'ctenophora'),
             (0.412, 0.22, 'e', 'ctenophora'),
             (0.798, 0.61, 'f', 'ctenophora')],

        'image': 'images/ovaloffice.png',
        'vocab': 'more'})
                        })

