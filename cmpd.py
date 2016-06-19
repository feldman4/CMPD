import nltk
from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()






def load_DIDB():
    cats = {}
    flag = None
    for line in open('DIDB.txt', 'r'):
        if flag:
            cats[flag] = [s.strip() for s in line.split(',')]
            flag = None
        if line.startswith('###'):
            flag = line.split('###')[1].strip()
    words = [b for a in cats.values() for b in a]
    return cats

def singular(phrase):
    """Accepts either a list of words, or a string of space-separated words.
    """
    def f(phrase):
        arr = []
        # nltk.pos_tag(['mice'])
        # [('mice', 'NN')]
        for word in phrase:
            if '-' in word:
                last_word = word.split('-')[-1]
                flag, word_ = isplural(last_word)
                arr += ['-'.join(word.split('-')[:-1] + [word_])]
            else:
                arr += [isplural(word)[1]]
        return arr

    if isinstance(phrase, unicode):
        phrase = str(phrase)

    if isinstance(phrase, str):
        return ' '.join(f(phrase.split()))

    return f(phrase)

def match_case(a, b):
    """ Return a with the case of b.
    >>> match_case('kulak', 'Kulaks')
    >>> 'Kulak'
    """
    b_ = []
    b = b.ljust(len(a), ' ')
    for c1, c2 in zip(a,b):
        if c2 == c2.lower():
            b_ += c1.lower()
        else:
            b_ += c1.upper()
    return ''.join(b_) 


extra_plural = {'kulaks': 'kulak',
                'swineherds': 'swineherd',
                'molestors': 'molestor',
                'idolatrists': 'idolatrist',
                'goodniks': 'goodnik',
                'backstabbers': 'backstabber',
                'halfwits': 'halfwit',
                'simonists': 'simonist'
                }

def isplural(word):
    """Checks if word is plural against WordNet.
    """
    if word.lower() in extra_plural:
        return True, match_case(extra_plural[word.lower()], word)

    import unidecode 
    word = unicode(word, 'utf8')
    word_ = unidecode.unidecode_expect_ascii(word)

    lemma = str(wnl.lemmatize(word_.lower(), 'n'))
    plural = True if word.lower() is not lemma else False
    if plural:
        lemma = match_case(lemma, word)
    

    return plural, lemma


def literal_distance(w1, w2):
    from Levenshtein import distance
    return distance(unicode(w1), unicode(w2)) / float(len(w1))


def similar_phrase(phrase, topn=10):
    db = get_db()

    words = phrase.lower().split()
    words = [w.replace('-', '_') for w in words]
    new_phrase = []
    try:
        for w in words:
            hits, scores = zip(*db.most_similar(w, topn=topn))
            distances = [-literal_distance(w, h) for h in hits]
            ranks = [sorted(distances).index(d) for d in distances]
            ranks = [i+v for i,v in enumerate(ranks)]
            best = hits[ranks.index(min(ranks))]
            new_phrase += best.split('_')
        new_phrase = [match_case(w, 'X') for w in new_phrase]
        return ' '.join(new_phrase)
    except KeyError:
        return phrase




def get_db():
    conn = start_client()
    return conn.root.exposed_db()


PROTOCOL_CONFIG = {"allow_all_attrs": True,
           "allow_setattr": True,
           "allow_pickle": True}
PORT = 1234


def start_client(port=PORT):
    import rpyc
    class ServerService(rpyc.Service):
        pass


    conn = rpyc.connect("localhost", port, service=ServerService, config=PROTOCOL_CONFIG)
    rpyc.BgServingThread(conn)
    return conn



def start_server(db, port=PORT):
    import threading
    import rpyc
    import rpyc.utils.server
    class ServerService(rpyc.Service):
        def exposed_db(self):
            return db
    # start the rpyc server
    server = rpyc.utils.server.ThreadedServer(ServerService, port=port, protocol_config=PROTOCOL_CONFIG)
    t = threading.Thread(target=server.start)
    t.daemon = True
    t.start()
    return t





        