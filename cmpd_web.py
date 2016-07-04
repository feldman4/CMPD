from flask.sessions import SessionMixin, SessionInterface
import random


def load_phrases(path):
    with open(path, 'r') as fh:
        return fh.read().split('\n')

default_phrases = load_phrases('resources/phrases.txt')


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
