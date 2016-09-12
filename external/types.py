from collections import namedtuple
import random
from external import cfg

Map     = namedtuple('Map', 'name image places intro')
Place   = namedtuple('Place', 'x y key label preview')
Message = namedtuple('Message', 'name text choices')
Choice  = namedtuple('Choice', 'key label name')


Remark = namedtuple('Remark', 'insult retort score health')
Enemy  = namedtuple('Enemy',  'name image cls grammar victory')
# Enemy = namedtuple('Enemy', 'image name health')


class Word(namedtuple('Word', 'word partOfSpeech tag')):
  # namedtuple with defaults
    def __new__(cls, word, partOfSpeech, tag=''):
        return super(Word, cls).__new__(cls, word, partOfSpeech, tag)


class Opponent(object):
    def __init__(self, grammar, model):
        """ Opponent has vocab, grammar, model (health etc). Created from 
        Enemy template.
        """
        self.grammar = grammar
        self.model = model
        
    def retort(self, insult, remarks):
        """ Retorts from provided vocab.
        """
        so_far = []
        for _ in range(100):
            choices = cfg.choices(self.grammar, so_far)
            choices = [c for c in choices if c not in so_far]
            if cfg.is_complete(self.grammar, so_far):
                choices += [-1]
            next_word = random.choice(choices)
            if next_word == -1:
                return ' '.join(so_far)
            so_far += [next_word]

        return 'enemy timed out'