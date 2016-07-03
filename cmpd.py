import nltk
from nltk.stem import WordNetLemmatizer
wnl = WordNetLemmatizer()
db = None


def load_DIDB():
    cats = {}
    flag = None
    for line in open('DIDB.txt', 'r'):
        if flag:
            cats[flag] = [[s.strip() for s in part.split(',')] 
                                     for part in line.split(';')]
            flag = None
        if line.startswith('###'):
            flag = line.split('###')[1].strip()
    words = [b for a in cats.values() for b in a]
    return cats


def load_DIDB_pairs():
    """Load two word insults only.
    """
    categories = load_DIDB()
    categories = {k: v[0] for k,v in categories.items() if len(v)>1}
    phrases = sum(categories.values(), [])
    phrases = [singular(phrase) for phrase in phrases 
                    if ' of ' not in phrase.lower()]
    return phrases

def singular(phrase):
    """Accepts either a list of words, or a string of space-separated words.
    """
    # nltk.pos_tag not reliable way to detect plural, WordNet is better
    # nltk.pos_tag(['mice'])
    # [('mice', 'NN')]
    def f(phrase):
        arr = []

        for word in phrase:
            flag, word_ = isplural(word)
            if flag:
                arr += [word_]
            elif '-' in word:
                last_word = word.split('-')[-1]
                flag, word_ = isplural(last_word)
                arr += ['-'.join(word.split('-')[:-1] + [word_])]
            else:
                # give up
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
                'simonists': 'simonist',
                'somnambulants': 'somnambulant',
                'regurgitators': 'regurgitator',
                'enigmas': 'enigma',
                'witchdoctors': 'witchdoctor',
                'bigmouths': 'bigmouth'
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
    plural = True if word.lower() != lemma else False
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
    global db
    db = conn.root.exposed_db()
    return db


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
    try:
        db = conn.root.exposed_db()
    except NameError:
        print 'db not loaded'
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



def make_pairs(phrases):
    from nltk.corpus import wordnet as wn
    import pandas as pd
    import numpy as np
    
    phrases = [p for p in phrases if len(p.split()) == 2]
    tagged = [nltk.pos_tag('you are'.split() + p.lower().split())[2:] for p in phrases]
    phrases = [p for p, t in zip(phrases, tagged)
                  if t[0][1] == 'JJ' and t[1][1] == 'NNS']

    df = pd.DataFrame([p.split() for p in phrases], columns=['JJ', 'NNS'])
    df['NN'] = [singular(n) for n in df['NNS']]
    # remove if isplural fails (WordNet doesn't lemmatize to singular)
    filt = [isplural(n)[0] for n in df['NNS']]
    df = df[filt]
    
    arr = []
    for a,b in zip(df['JJ'], df['NN']):
        a = a.lower().replace('-', '_')
        b = b.lower().replace('-', '_')
        try:
            arr += [db.similarity(a,b)]
        except KeyError:
            arr += [np.nan]
    df['GN_similarity'] = arr
    
    df['JJ_synsets'] = [wn.synsets(a, 'a') for a in df['JJ']]
    df['NN_synsets'] = [wn.synsets(n, 'n') for n in df['NN']]

    return df


def show(s):
    if isinstance(s, nltk.corpus.reader.wordnet.Lemma):
        print 'Lemma: %s (%s)' % (s.name(), s.unicode_repr()[7:-2])
        if s.antonyms():
            print 'Antonyms: %s' % s.antonyms()
    elif isinstance(s, nltk.corpus.reader.wordnet.Synset):
        if s.lexname() == 'adj.all':
            lemmas = s.lemmas()
            print 'Lemmas:' 


def cluster_features(features, names, distance=None, orientation='top'):
    """Cluster features according to distance function. Should be superseded
    by something in scipy. 
    """
    import pandas as pd
    import scipy
    if distance is None:
        distance = lambda n, n_: len(set(n) & set(n_))/float(len(set(n)|set(n_)))
    
    arr = []
    for n, w in zip(features, names):
        for n_, w_ in zip(features, names):
            arr += [[w, w_, distance(n, n_)]]
    df = pd.DataFrame(arr)
    df[2] = df[2].astype(float)
    M = df.pivot_table(index=0, columns=1, values=2)
    Z = scipy.cluster.hierarchy.linkage(M)
    def plot_cluster():
        import seaborn as sns
        import matplotlib.pyplot as plt
        sns.set(style='white', font_scale=1.5)
        fs = (4,len(features)/3.5)
        fig, ax = plt.subplots()
        x = scipy.cluster.hierarchy.dendrogram(Z, labels=M.index, 
            ax=ax, orientation=orientation);
        if orientation in ('top', 'bottom'):
            ax.set_xticklabels(ax.get_xticklabels(), {'size': 15});
            fig.set_figheight(fs[0])
            fig.set_figwidth(fs[1])
        else:
            ax.set_yticklabels(ax.get_yticklabels(), {'size': 15});
            fig.set_figheight(fs[1])
            fig.set_figwidth(fs[0])
        fig.tight_layout()
        return ax
    return M, Z, plot_cluster