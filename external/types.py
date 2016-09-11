from collections import namedtuple
import random

Map     = namedtuple('Map', 'name image places intro')
Place   = namedtuple('Place', 'x y key label preview')
Message = namedtuple('Message', 'name text choices')
Choice  = namedtuple('Choice', 'key label name')


Remark = namedtuple('Remark', 'insult retort score health')
Enemy  = namedtuple('Enemy',  'name image cls vocab victory')
# Enemy = namedtuple('Enemy', 'image name health')


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
