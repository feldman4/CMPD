from flask.sessions import SessionMixin, SessionInterface
import random


def load_phrases(path):
    with open(path, 'r') as fh:
        return fh.read().split('\n')

# default_phrases = load_phrases('resources/phrases.txt')


class Base(object):
    def __init__(self, adjectives, nouns, phrases=None, log=None):
        """Provide log as filehandle opened in append mode.
        """
        self.JJ = adjectives
        self.NN = nouns
        self.phrases = phrases or default_phrases
        self.flag = 'JJ'

        self.wordbank = self.JJ

        self.log = log


    def reply(self, insult, emit):
        """ Switches between adjectives and nouns. Retorts from 
        provided phrases.
        """

        if self.flag == 'JJ':
            self.flag = 'NN'
            self.lastword = insult['insult']
            self.wordbank = self.NN
            
        else:
            self.flag = 'JJ'
            
            phrase = random.choice(self.phrases)
            retort = {'insult': self.lastword + ' ' + insult['insult'],
                           'retort': phrase}

            self.lastword = ''
            self.wordbank = self.JJ
                           
            emit('remark', retort)

        emit('update_wordbank', {'wordbank': self.wordbank})

        if self.log:
            import time
            log.write('%f\n%s\n' % (time.time(), retort['retort']))



class Versus(Base):
    def __init__(self, *args, **kwargs):
        super(Versus, self).__init__(*args, **kwargs)
        self.history = []

    def reply(self, insult, emit):
        insult = insult['insult']

        if self.flag == 'JJ':
            self.flag = 'NN'
            self.lastword = insult
            self.wordbank = self.NN
            
        else:
            self.flag = 'JJ'
            
            insult = self.lastword + ' ' + insult
            phrase = random.choice(self.phrases)
            retort = {'insult': insult,
                           'retort': phrase,
                           'score': self.score(insult)}

            self.lastword = ''
            self.wordbank = self.JJ
                           
            emit('remark', retort)

            self.history += [(insult, retort)]

        random.shuffle(self.wordbank)
        emit('update_wordbank', {'wordbank': self.wordbank})

        if self.log:
            import time
            log.write('%f\n%s\n' % (time.time(), retort['retort']))

    def score(self, insult):

        past_insults = [i for i, r in self.history]

        if insult in past_insults:
            return -0.05
        if insult in default_phrases:
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


default_phrases = \
"""Irreligious Latecomer
Jaded Miscreant
Predatory Liar
Lonely Regurgitator
Disguised Carrion
Candy-Assed Filth
Unsuccessful Looter
Talentless Hack
Floundering Engimas
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