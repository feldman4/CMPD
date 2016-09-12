from collections import defaultdict


"""Exercise caution! These methods may hang for CFG with cycles and/or
infinite CFG if halt condition is not set!

"""
# depth-first
# Grammar -> Sentence -> List Sentence

def extend(grammar, sentence, halt=None, discard=lambda x: False):
    # if halt is not provided, return any all-terminal sentences
    # if halt is provided, only return sentences for which halt is True
    # these can be sentences with non-terminal symbols
    if discard(sentence):
        return []
    if halt is not None and halt(sentence):
        return [sentence]
    
    result = []
    for i, symbol in enumerate(sentence):
        if symbol in grammar:
            for symbol_chain in grammar[symbol]:
                new_sentence = sentence[:i] + symbol_chain.split() + sentence[i+1:]
                result += extend(grammar, new_sentence,
                                 halt=halt, discard=discard)
            return result
    if halt is None:
        return [sentence]
    else:
        return []


def discard_mismatch(grammar, sentence, so_far):
    for a, b in zip(sentence, so_far):
        if a not in grammar and a != b:
            return True
    return False

def halt_on_match(grammar, sentence, so_far):
    i = -1
    for i, (a, b) in enumerate(zip(sentence, so_far)):
        if a != b:
            return False
    if len(sentence) > len(so_far):
        if sentence[i+1] not in grammar:
            return True
    if len(sentence) == len(so_far):
        return True
    return False

def constructs(grammar, so_far, start='S'):
    d = lambda s: discard_mismatch(grammar, s, so_far)
    h = lambda s: halt_on_match(grammar, s, so_far)
    return extend(grammar, [start], discard=d, halt=h)

def choices(grammar, so_far, start='S'):
    n = len(so_far)
    options = []
    for sentence in constructs(grammar, so_far, start=start):
        options.extend(sentence[n:n+1])
    return sorted(set(options))

def is_complete(grammar, so_far):
    return so_far in constructs(grammar, so_far)

def get_terminals(grammar, every=False):
    """Returns list of symbols and parts of speech.
    If every is true, only gets terminals occuring in symbol chains without
    any nonterminals.
    """
    if every:
        symbols = [(symbol, LHS) for LHS, symbol_chains in grammar.items()
                      for symbol_chain in symbol_chains
                      if not any(symbol in grammar for symbol in symbol_chain.split())
                      for symbol in symbol_chain.split()]
    else:
        symbols = [(symbol, LHS) for LHS, symbol_chains in grammar.items()
                          for symbol_chain in symbol_chains
                          for symbol in symbol_chain.split()
                          if symbol not in grammar]
    return sorted(set(symbols))


def filter_terminals(grammar, subset, keep):
    """Filter a grammar. For each LHS in subset, remove symbol chains
    that contain terminals not in keep.
    """
    new_grammar = defaultdict(tuple)
    keep = set(keep)
    all_terminals = set([s for s,_ in get_terminals(grammar)])
    for LHS, symbol_chains in grammar.items():
        if LHS not in subset:
            new_grammar[LHS] = symbol_chains
            continue
        new_chains = []
        for symbol_chain in symbol_chains:
            chain_terminals = set(symbol_chain.split()) 
            chain_terminals &= all_terminals
            if chain_terminals < keep or not chain_terminals: 
                new_chains.append(symbol_chain)
        new_grammar[LHS] = tuple(new_chains)
    return dict(new_grammar)


def prune_nonterminal(grammar):
    """Keep only productions that occur in terminal-only sentences.
    Does not assume a starting node, though.
    Very sketchy. 
    """
    s_cache = {}
    def reduce_symbol(symbol):
        if symbol not in s_cache:
            if symbol in grammar:
                s_cache[symbol] = any(reduce_symbol_chain(sc, symbol) 
                                      for sc in grammar[symbol])
            else:
                s_cache[symbol] = True
        return s_cache[symbol]
    
    def reduce_symbol_chain(symbol_chain, LHS):
        # all symbols must be valid
        
        if LHS in symbol_chain:
            return False
        else:
            return all(reduce_symbol(symbol) 
                                         for symbol in symbol_chain.split())
        
    # start anywhere
    new = {}
    for LHS, symbol_chains in grammar.items():
        if all(LHS in sc.split() for sc in symbol_chains):
            s_cache[LHS] = False
            continue
        keep = []
        for symbol_chain in symbol_chains:
            
            if reduce_symbol_chain(symbol_chain, LHS):
                keep += [symbol_chain]
        
        for symbol_chain in symbol_chains:
            symbol_chain_ = symbol_chain.split()
            if LHS in symbol_chain_ and keep:
                symbol_chain_.remove(LHS)
                symbol_chain_ = ' '.join(symbol_chain_)
                if reduce_symbol_chain(' '.join(symbol_chain_), LHS):
                    keep += [symbol_chain]
        # if LHS == 'PP':
        #     assert False
        
        if keep:
            new[LHS] = tuple(keep)
    return new
    


# breadth-first
# Grammar -> List Sentence -> List Sentence
def _extend(grammar, sentences):
    for j, head in enumerate(sentences):
        head = sentences[j]
        tail = sentences[j+1:] + sentences[:j]

        for i, symbol in enumerate(head):
            if symbol in grammar:
                for symbol_chain in grammar[symbol]:
                    new_sentence = head[:i] + symbol_chain.split() + head[i+1:]
                    tail.append(new_sentence)
                return extend(grammar, tail)
    return sentences
    

def print_calgary_CFG(grammar, start):
    """ http://smlweb.cpsc.ucalgary.ca/start.html
    """
    items = sorted(grammar.items(), key=lambda x: x[0]!=start)
    for LHS, symbol_chains in items:
        out = LHS + ' -> '
        for sc in symbol_chains:
            for s in sc.split():
                if (s, LHS) in terminals:
                    out += ' ' + s.lower()
                else:
                    out += ' ' + s
            print out

            out = '|'
        print '.'
        