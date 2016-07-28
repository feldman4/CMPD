from flask import url_for, Flask
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

flask_to_js = {
  'REMARK': 'REMARK',
  'UPDATE_WORDBANK': 'UPDATE_WORDBANK',
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
    with open('resources/crypt.json', 'r') as fh:
        key1, key2 = os.environ['KEY1'], os.environ['KEY2']
        text = fh.read()
        aes = AES.new(key1, AES.MODE_CBC, key2)
        text = aes.decrypt(text)
    with open('resources/key.json', 'w') as fh:
        fh.write(text)

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


Place = namedtuple('Place', 'x y label enemy')

Remark = namedtuple('Remark', 'insult retort score')

class Word(namedtuple('Word', 'word partOfSpeech tag')):
  # namedtuple with defaults
    def __new__(cls, word, partOfSpeech, tag=''):
        return super(Word, cls).__new__(cls, word, partOfSpeech, tag)


class Enemy(object):
    def __init__(self, vocab, view):
        
        self.vocab = vocab
        self.grammar = None
        self.view = view
        
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


class GameMaster(object):
    
    def __init__(self, places, enemies, player, map_src):
        # coordinates and tag (key)
        self.places = places
        self.player = player
        
        self.map_src = map_src
        
        self.enemies = enemies
        
        self.current_enemy = None
        self.remarks = []
        
    def initialize(self, emit):
        """ 
        Send the map and player info. 
        Determines loadout and displayed map.
        Called when JS loads and emits INITIALIZE.
        """
        map_data = {'image': self.map_src, 
                    'places': [p._asdict() for p in self.places]}
        
        emit('SEND_PLAYER', self.player.model)
        emit('SEND_MAP', map_data)
        
    def request_encounter(self, enemy, emit):
        """ Initializes enemy. Starts Player and asks to send an updated Wordbank.
        """
        image = self.enemies[enemy]['image']
        enemyClass = self.enemies[enemy]['class']

        enemy_vocab = load_vocab(self.enemies[enemy]['vocab'])
        enemy_view = {'image': image}

        self.current_enemy = enemyClass(enemy_vocab, enemy_view)
        
        emit('SEND_ENCOUNTER', enemy_view)

        self.player_phrase = []
        self.next_word(emit)

    def next_word(self, emit):
        """ Weird to have end-of-phrase logic here.
        """
        new_wordbank = self.player.next_word(self.player_phrase)
        if new_wordbank:
            new_wordbank = [w._asdict() for w in new_wordbank]
            
            emit('UPDATE_WORDBANK', new_wordbank)
        else:
            self.reply(emit)
            self.player_phrase = []
            self.next_word(emit)

    def insult(self, insult, emit):
        """ Responds to incoming insult. Called by socketio.on('INSULT').
        """
        insult['word'] = Word(**insult['word'])
        self.player_phrase += [insult['word']]
        self.next_word(emit)
        
    def reply(self, emit):
        insult = ' '.join(w.word for w in self.player_phrase)
        retort = self.current_enemy.retort(insult, self.remarks)
        score = self.score(insult, retort)
        remark = Remark(insult, retort, score)
        self.remarks += [remark]

        emit('REMARK', remark._asdict())
        
        
    def score(self, insult, retort):

        past_insults = [remark.insult for remark in self.remarks]
        past_retorts = [remark.retort for remark in self.remarks]

        if insult in past_insults:
            return -0.05
        if insult in past_retorts:
            return -0.05

        return 0.1
        

class LocalEncounter(GameMaster):
    def __init__(self, player, enemies=None):
        self.player = player
        self.enemies = enemies or stable
        self.remarks = []


        app = Flask(__name__)
        self.app_context = app.test_request_context()

        
    def prompt(self, enemy):
        # launch a prompt to interact with opponent, instead
        # of elm
    
        self.request_encounter(enemy, self.emit)
        print 'Enemy:', enemy
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
            # with self.app_context:
            self.insult(insult, self.emit)

            # if at end of phrase, reply

    
    def emit(self, message, data):
        """ Local simulation of sending message and data through socket.
        """
        
        if message == flask_to_js['UPDATE_WORDBANK']:
            wordbank = data
            wordbank = [w['word'] for w in wordbank]
            print 'Wordbank:', ', '.join(wordbank[:4] +  ['...'])

        if message == flask_to_js['REMARK']:
            
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


google_json_key = 'resources/key.json'

def load_sheet(worksheet, g_file='CMPD', credentials=google_json_key):
    """Load sheet as array of strings (drops .xls style index)
    gspread allows for .xlsx export as well, which can capture style info.
    :param worksheet: provide None to return a dictionary of all sheets
    :param g_file:
    :return:
    """
    # see http://gspread.readthedocs.org/en/latest/oauth2.html

    from oauth2client.service_account import ServiceAccountCredentials
    import gspread

    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_json_key, scope)
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
  path = 'resources/vocab/%s.json' % sheet

  def load_remote(sheet):
      sheet = load_sheet(sheet)
      df = pd.DataFrame(sheet[1:], columns=sheet[0])
      vocab = []
      for col in df:
          words = [w for w in df[col] if w]
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

stable = frozendict({'ctenophora': frozendict({'image': 'images/ctenophora.png',
                         'class': Enemy,
                         'vocab': 'DIDB'}),
          'derp': frozendict({'image': 'images/derp-3.jpg',
                         'class': VersusDerp,
                         'vocab': 'DIDB'}),
          'underground': frozendict({'image': 'images/underground.png',
                         'class': Enemy,
                         'vocab': 'high school shakespeare'}),
          'buddha': frozendict({'image': 'images/buddha.jpg',
                         'class': Enemy,
                         'vocab': 'DIDB'}),

                         })

