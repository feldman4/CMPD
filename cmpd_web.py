from flask.sessions import SessionMixin, SessionInterface
import random

import cmpd

phrases = cmpd.load_DIDB_pairs()

class Base(object):
    def __init__(self, adjectives, nouns, log=None):
        """Provide log as filehandle opened in append mode.
        """
        self.JJ = adjectives
        self.NN = nouns
        self.flag = 'JJ'

        self.wordbank = self.JJ

        self.log = log


    def reply(self, insult, emit):

        if self.flag == 'JJ':
            self.flag = 'NN'
            self.lastword = insult['insult']
            self.wordbank = self.NN
            
        else:
            self.flag = 'JJ'
            
            phrase = random.choice(phrases)
            retort = {'insult': self.lastword + ' ' + insult['insult'],
                           'reply': phrase}

            self.lastword = ''
            self.wordbank = self.JJ
                           
            emit('retort', retort, namespace='/base')

        emit('update_wordbank', {'wordbank': self.wordbank})

        if self.log:
            import time
            log.write('%f\n%s\n' % (time.time(), retort['retort']))






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
