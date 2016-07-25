from flask import url_for
from flask.sessions import SessionMixin, SessionInterface
import re
import random
from collections import OrderedDict
from itertools import cycle, product
import difflib
from frozendict import frozendict

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


class Base(object):
    def __init__(self, vocab, emit, retorts=None, log=None):
        """Provide log as filehandle opened in append mode.
        """
        self.vocab = OrderedDict(vocab)
        self.retorts = retorts or DIDB_phrases
        self.log = log
        self.emit = emit

        self.initialize()
        
    def initialize(self):
        self.flag = cycle(self.vocab.keys())
        self.insult = []
        self.history = []
        self.wordbank = self.vocab[self.flag.next()]
        self.emit(flask_to_js['UPDATE_WORDBANK'], {'wordbank': self.wordbank})


    def reply(self, insult):
        """ Switches between adjectives and nouns. Retorts from 
        provided phrases.
        """

        self.insult += [insult['insult']]
        key = self.flag.next()
        self.wordbank = self.vocab[key]

        random.shuffle(self.wordbank)

        if key == self.vocab.keys()[0]:
            insult = ' '.join(self.insult)
            self.insult = []
        
            retort = random.choice(self.retorts)
            score = self.score(insult)
            remark = {'insult': insult, 
                      'retort': retort,
                      'score': score}
                           
            self.emit(flask_to_js['REMARK'], remark)

            self.history += [remark]

        self.emit(flask_to_js['UPDATE_WORDBANK'], {'wordbank': self.wordbank})

        if self.log:
            import time
            log.write('%f\n%s\n' % (time.time(), retort['retort']))

    def score(self, insult):

        past_insults = [remark['insult'] for remark in self.history]
        past_retorts = [remark['retort'] for remark in self.history]

        if insult in past_insults:
            return -0.05
        if insult in past_retorts:
            return -0.05

        return 0.1


class VersusDerp(Base):
    def __init__(self, *args, **kwargs):
        super(VersusDerp, self).__init__(*args, **kwargs)

    def reply(self, insult):
        
        progress = insult['progress']

        enemy_index = int(progress * 5.999) + 1
        enemy_image = url_for('static', 
            filename='images/derp-%d.jpg' % enemy_index)

        self.emit(flask_to_js['SEND_ENCOUNTER'], {'image': enemy_image})

        if progress > 0.8:
            self.retorts = derp_phrases
        else:
            self.retorts = DIDB_phrases

        super(VersusDerp, self).reply(insult)




class VersusDIDB(Base):
    def __init__(self, *args, **kwargs):
        super(VersusDIDB, self).__init__(*args, **kwargs)

    def score(self, insult):

        past_insults = [remark['insult'] for remark in self.history]

        if insult in past_insults:
            return -0.05
        if insult in DIDB_phrases:
            return 0.3

        return 0.05
        


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


class LocalEncounter(object):
    def __init__(self):
        self.opponent = None
        self.wordbank = None
        
    def prompt(self):
        # launch a prompt to interact with opponent, instead
        # of elm
    
        print 'Enemy:', self.opponent
        print 'Enter text to insult, enter nothing to quit.'
        self.progress = 0.5
        
        while True:
            print 'Wordbank:', ', '.join(self.wordbank[:4] +  ['...'])
            user_input = raw_input()
            if user_input == '':
                break
            word = nearest_word(user_input, self.wordbank)
            
            insult = {'insult': word}
            
            reply = self.opponent.reply(insult)
    
    def local_emit(self, message, data):
        """ Local simulation of sending message and data through socket.
        """
        
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
            
        if message == flask_to_js['UPDATE_WORDBANK']:
            self.wordbank = data['wordbank']

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
    
    def __init__(self, places, enemies, vocab, map_src):
        # coordinates and tag (key)
        self.places = places
        self.vocab = vocab
        
        vocab_size = 10
        capacity = [(pos, 6) for pos,_ in vocab]

        loaded, unloaded = [], []
        for pos, examples in vocab:
            words = random.sample(examples, vocab_size)
            loaded   += [{'word': word, 'partOfSpeech': pos} for word in words[:4]]
            unloaded += [{'word': word, 'partOfSpeech': pos} for word in words[4:]]
        
        self.player = {'loaded': loaded,
                       'unloaded': unloaded,
                       'capacity': capacity}
        
        self.map_src = map_src
        
        self.enemies = enemies
        
        self.current_enemy = None
        
    def initialize(self, emit):
        """ 
        Send the map and player info. 
        Determines loadout and displayed map.
        Called when JS loads and emits INITIALIZE.
        """
        map_data = {'image': self.map_src, 
                    'places': self.places}
        
        emit('SEND_PLAYER', {'player': self.player})
        emit('SEND_MAP', map_data)
        
    def request_encounter(self, enemy, emit):
        image = self.enemies[enemy]['image']
        enemyClass = self.enemies[enemy]['class']
        vocab = self.player_to_vocab(self.player)
        
        print 'image is', image
        print 'vocab is', vocab
        self.current_enemy = enemyClass(vocab, emit)
        
        # make the enemy with right vocab
        emit('SEND_ENCOUNTER', {'image': image})
        
    def reply(self, insult, emit):
        self.current_enemy.emit = emit
        self.current_enemy.reply(insult)
        
        
    def update_player(self, update):
        self.player = update
        
    def player_to_vocab(self, player):
        from collections import defaultdict
        words = player['loaded']
        vocab = defaultdict(list)

        for word in words:
            vocab[word['partOfSpeech']] += [word['word']]
        return sorted(vocab.items())





stable = frozendict({'ctenophora': frozendict({'image': 'images/ctenophora.png',
                         'class': VersusDIDB}),
          'derp': frozendict({'image': 'images/derp-3.jpg',
                         'class': VersusDerp}),
          'underground': frozendict({'image': 'images/underground.png',
                         'class': VersusDIDB}),
          'buddha': frozendict({'image': 'images/buddha.jpg',
                         'class': VersusDIDB}),


                         })



derp_categories = [('A', ['Lazy',
  'Stupid',
  'Insecure',
  'Idiotic',
  'Slimy',
  'Smelly',
  'Pompous',
  'Pie-Eating',
  'Racist',
  'Elitist',
  'White Trash',
  'Drug-Loving',
  'Tone Deaf',
  'Ugly',
  'Creepy']),
 ('B', ['Douche',
  'Ass',
  'Turd',
  'Butt',
  'Cock',
  'Shit',
  'Crotch',
  'Prick',
  'Taint',
  'Fuck',
  'Dick',
  'Nut']),
 ('C', ['Pilot',
  'Captain',
  'Pirate',
  'Knob',
  'Box',
  'Jockey',
  'Nazi',
  'Waffle',
  'Goblin',
  'Blossum',
  'Clown',
  'Socket',
  'Balloon'])]

derp_phrases = [' '.join(x) for x in product(
                        *[words for _, words in derp_categories])]

DIDB_phrases = \
"""Irreligious Latecomer
Jaded Miscreant
Predatory Liar
Lonely Regurgitator
Disguised Carrion
Candy-Assed Filth
Unsuccessful Looter
Talentless Hack
Floundering Enigma
Licentious Turd
Renegade Dwarf
Underhanded Sinner
Deceased Tyrant
Celebrated Nincompoop
Avaricious Poltergeist
Constipated Moocher
Tufted Eunuch
Low-ranking Sycophant
Inveterate Plagiarizer
Cantankerous Poltroon
Impoverished Lunatic
Clamorous Weakling
Unelected Yahoo
Despicable Bastard
Sweaty Pygmy
Gutless Traitor
Defenceless Neophyte
Sinister Halfwit
Poisonous Fool
Self-Promoting Judas
Treacherous Failure
Subservient Wimp
Botched Experiment
Powdered Fop
Monied Aristocrat
Litigious Upstart
Ignorant Amateur
Worm-Eaten Pilferer
Garish Reptile
Overpaid Invertebrate
Loathsome Creature
Precocious Weasel
Overfunded Mouth-Breather
Backwater Racist
Ill-Bred Yokel
Oxygen-Deprived Redneck
Prejudiced Swamp-Dweller
Officious Transient
Fear-Mongering Coward
Mean Turncoat
Odious Riffraff
Meddlesome Fanatic
Armchair Rapist
Atrophied Sponge
Free-Range Moron
Unemployed Fetishist
Variegated Cretin
Vindictive Abuser
Synthetic Ape-Man
Asthmatic Gelding
Intellectual Centipede
Nauseating Hypocrite
Irrelevant Bigmouth
Underqualified Drunk
Bankrupt Loser
Insincere Huckster
Unregenerate Philistine
Antediluvian Trash
Pompous Narcissist
Disorganized Pushover
Tendentious Boob
Scheming Crackpot
Drug-Addled Parasite
Egg-Sucking Caveman
Foul Betrayer
Worthless Cheater
Bellicose Scum
Unprincipled Marxist
Political Insect
Mistaken Demagogue
Closet Communist
Garden-Variety Reactionary
Diseased Collaborator
Jilted Counter-Revolutionary
Drugstore Fascist
Dirty Trotskyite
Crass Individualist
Feather-Brained Idealist
Humorless Jingoist
Incontinent Meat-Packer
Sniveling Ratcatchers
Breastfed Academic
Kowtowing Swineherd
Apprentice Spook
Hoity-Toity Intellectual
Insufferable Clerk
Spineless Middle-Manager
Backwoods Trapper
Impotent Fish-Cleaner
Unwitting Peasant
Insignificant Garbageman
Self-Satisfied Undertaker
Bearded Mystic
Dishonest Mortician
Simpering Priest
Pallid Functionary
Melancholy Organ-Grinder
Deranged Pornographer
Ill-Tempered Philanthropist
Misinformed Yes-Man
Hairless Dignitary
Medicated Stenographer
Orthodox Gravedigger
Dimwitted Philosopher
Disingenuous Hitman
Common Thug
Preposterous Highwayman
Alcoholic Criminal
Jackbooted Accomplice
Ineffectual Mercenary
Small-Time Assassin
Rented Executioner
Careless Arsonist
Malignant Squatter
Reckless Lawbreaker
Obsequious Pimp
Indiscreet Murderer
Retired Slave-Trader
Well-Fed Scoundrel
Bucktoothed Swindler
Flesh-Eating Goon
Craven Warlord
Clumsy Villain
Embarrassing Backstabber
Unwashed Kidnapper
Unctuous Vandal
Fraudulent Monk
Bigoted Soothsayer
Defrocked Witchdoctor
Luckless Zealot
Forsaken Apostate
Morose Cultist
White-Collar Simonist
Wretched Atheist
Belligerent Fakir
Disgraced Pederast
Listless Masturbator
Limp-wristed Onanist
Daft Cuckold
Gilded Concubine
Self-Appointed Rapist""".split('\n')