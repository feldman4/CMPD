from flask import url_for
from flask.sessions import SessionMixin, SessionInterface
import random
from collections import OrderedDict
from itertools import cycle, product


def load_phrases(path):
    with open(path, 'r') as fh:
        return fh.read().split('\n')



class Base(object):
    def __init__(self, vocab, retorts=None, log=None):
        """Provide log as filehandle opened in append mode.
        """

        self.vocab = OrderedDict(vocab)
        self.retorts = retorts or DIDB_phrases

        self.flag = cycle(self.vocab.keys())

        self.wordbank = self.vocab[self.flag.next()]

        self.insult = []
        self.history = []

        self.log = log

        print self.vocab


    def reply(self, insult, emit):
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
                           
            emit('remark', remark)

            self.history += [remark]

        emit('update_wordbank', {'wordbank': self.wordbank})

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

    def reply(self, insult, emit):
        
        progress = insult['progress']

        enemy_index = int(progress * 5.999) + 1
        enemy_image = url_for('static', 
            filename='images/derp-%d.jpg' % enemy_index)

        emit('send_encounter', {'image': enemy_image})

        if progress > 0.8:
            self.retorts = derp_phrases
        else:
            self.retorts = DIDB_phrases

        super(VersusDerp, self).reply(insult, emit)




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