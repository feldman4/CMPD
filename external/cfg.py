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


