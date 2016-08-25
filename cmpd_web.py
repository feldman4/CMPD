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

import pandas as pd

from external import harlowe_extra
from external.harlowe_extra import html_to_nodes, Map, Place, Message


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

Place  = namedtuple('Place',  'x y label enemy')
Remark = namedtuple('Remark', 'insult retort score')
Enemy  = namedtuple('Enemy',  'name image cls vocab')
# Enemy = namedtuple('Enemy', 'image name health')



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


class Word(namedtuple('Word', 'word partOfSpeech tag')):
  # namedtuple with defaults
    def __new__(cls, word, partOfSpeech, tag=''):
        return super(Word, cls).__new__(cls, word, partOfSpeech, tag)


class Opponent(object):
    def __init__(self, vocab, model):
        """ Opponent has vocab, grammar, model (health etc). Created from 
        Enemy template.
        """
        self.vocab = vocab
        self.grammar = None
        self.model = model
        
    def retort(self, insult, remarks):
        """ Retorts from provided vocab.
        """
        retorts = zip(*[w for _, w in self.vocab])
        return ' '.join(random.choice(retorts))

        
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

            

class StoreReturns(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.returns = []

    def __call__(self, *args, **kwargs):
        value = self.func(*args, **kwargs)
        self.returns += [value]
        return value

    def __repr__(self):
        """Return the function's docstring."""
        if self.func.__doc__:
            return self.func.__doc__
        return self.func.__str__()


def emit(*args, **kwargs):
    """ Use the emit function bound to the current session. 
    """
    return session['emit'](*args, **kwargs)


class GameMaster(object):
    
    def __init__(self, nodes, starting_node, player):
        # nodes dict can be obtained using html_to_nodes()

        self.nodes = nodes
        self.starting_node = starting_node
        self.player = player

        self.current_enemy = None
        self.remarks = []


    def initialize(self):
        """ 
        Send the map and player info. 
        Determines loadout and displayed map.
        Called when JS loads and emits INITIALIZE.
        """
        self.transition(self.starting_node)
        

    def load_html(self, html):
        maps, encounters, messages = html_to_nodes(html)
        attrs, _, passages = harlowe_extra.parse_harlowe_html(html)


        # TODO: check graph for completeness
        # maps = {k: maps[k] for k in ['Dummy office', 'presidential library']}
        # encounters = {k: encounters[k] for k in ['Challenge ctenophora']}
        
        # passage_names = maps.keys() + encounters.keys()
        # for passage, m in maps.items():
        #     for place in m.places:
        #         assert (place.label in passage_names)

        self.nodes = maps
        self.nodes.update({k: stable[encounters[k]] for k in encounters})
        self.nodes.update(messages)

        self.starting_node = [n for n, p in passages.items()
                                if p.pid == attrs['startnode']][0]
       

    def transition(self, node, story_vars=None):
        
        self.node = self.nodes[node]
        if isinstance(self.node, Map):
            self.to_map()
        if isinstance(self.node, Enemy):
            self.to_encounter()
        if isinstance(self.node, Message):
            self.to_message()

    def to_message(self):
        message = self.node._asdict()
        # deal with nested namedtuple
        message['choices'] = [c._asdict() for c in message['choices']]
        emit('SEND_MESSAGE', message)
        print 'sent message', message
            
    def to_map(self):
        map_ = self.node._asdict()
        # deal with nested namedtuple
        map_['places'] = [p._asdict() for p in map_['places']]
        emit('SEND_PLAYER', self.player.model)
        emit('SEND_MAP', map_)
        print 'sent map', map_
        
    def to_encounter(self):
        """ Based on request_encounter()
        Initializes enemy. Starts Player and asks to send an updated Wordbank.
        """
        enemyClass = self.node.cls
        
        enemy_vocab = load_vocab(self.node.vocab)
        image = url_for('static', filename=self.node.image)
        enemy_model = {'image': image, 
                       'health': 1, 
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
        remark = Remark(insult, retort, score)
        self.remarks += [remark]

        emit('SEND_REMARK', remark._asdict())
        
        
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
        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).to_encounter()

        print 'Enemy:', self.node
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
        with self.app_context:
            session['emit'] = self.emit
            super(LocalGameMaster, self).to_map()

        places = [p.label for p in self.node.places]

        print 'Current map:', self.node.name
        print 'Go to'
        print '\n'.join(places)

        flag = True
        while flag:
            user_input = raw_input()
            if user_input == '':
                break

            for p in places:
                if p.startswith(user_input):
                    self.transition(p)
                    flag = False
                    break

    
    def emit(self, message, data):
        """ Local simulation of sending message and data through socket.
        """
        
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
            print 'image:', data.image
            print 'places:', data.places

        if message == flask_to_js['SEND_ENCOUNTER']:
            print 'Launching encounter with', data
            print


def initialize_map(map_name):
    """ Wrapper for initialization function. Called after jQuery document ready emits INITIALIZE message.
    """
    def f():

        print 'initializing map: %s' % map_name

        map_image = maps[map_name]['image']
        places = maps[map_name]['places']
        places = [Place(*p) for p in places]
        player_vocab = load_vocab(maps[map_name]['vocab'])

        new_vocab = []
        for pos, words in player_vocab:
            words = list(words)
            random.shuffle(words)
            new_vocab += [(pos, words[:12])]
        player_vocab = new_vocab

        map_src = url_for('static', filename=map_image)

        enemies = {}
        for enemy in stable:
            enemies[enemy] = dict(stable[enemy])
            enemies[enemy]['image'] = url_for('static', 
                                                filename=enemies[enemy]['image'])


        player = Player(player_vocab, None, capacity=6)
        player.model['image'] = url_for('static', filename='images/back.png')
        player.model['name'] = 'player'
        player.model['health'] = 0.5
        GM = GameMaster(places, enemies, player, map_src)
        GM.initialize()
        session['GM'] = GM

    return f



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


def load_vocab(sheet, reload=False):
  """ Load columns of google sheet into vocab of type [(header, [word])]. 
  No entry for empty header. Empty and duplicate words removed.

  Uses local cached json if reload is False and file exists.
  """
  path = 'resources/vocab/%s.json' % sheet

  def load_remote(sheet):

      sheet = load_sheet(sheet)
      df = pd.DataFrame(sheet[1:], columns=sheet[0])
      vocab = []
      for col in df:
          if col:
              words = sorted(set([w for w in df[col] if w]))
              vocab += [(col, words)]

      with open(path, 'w') as fh:
          json.dump(vocab, fh, indent=4)
      return vocab

  if reload:
    return load_remote(sheet)

  try:
      with open(path, 'r') as fh:
          return json.load(fh)
  except (IOError, ValueError):
      return load_remote(sheet)


def make_all_phrases(vocab):
    return [' '.join(x) for x in product(
                          *[words for _, words in vocab])]

def make_row_phrases(vocab):
  phrases = []
  for row in zip(*[words for cat,words in vocab]):
      phrases += [' '.join(row)]
  return phrases


make_DIDB_phrases = lambda: make_row_phrases(load_vocab('DIDB'))

stable = (
    ('ctenophora',  'images/ctenophora.png',  Opponent,      'more'),
    ('derp',        'images/derp-3.jpg',      VersusDerp,    'DIDB'),
    ('underground', 'images/underground.png', Opponent,      'high school shakespeare'),
    ('buddha',      'images/buddha.jpg',      Opponent,      'DIDB'),
    ('generalAbrams', 'images/abrams.jpg',    Opponent,      'dec2')
    )

stable = frozendict({s[0]: Enemy(*s) for s in stable})





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

