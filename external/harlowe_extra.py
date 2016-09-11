# extra functions for parsing exported Harlowe HTML
from . import harlowe
from .harlowe import (HarloweMacro, HarloweVariable, 
                      HarloweLink, HarloweHook, RawHtml, HarlowePassage)

import re
from collections import namedtuple

from .types import Map, Place, Message, Choice, Enemy, Opponent

default_places = tuple((0.75, 0.75, c) for c in 'abcdefgh')


def html_to_nodes(html):
    attrs, non_passages, passages = parse_harlowe_html(html)
    
    # find global variables
    global_vars = find_global_vars(passages.values())

    image_urls = {}
    for v in global_vars:
        if v.endswith('Image'):
            image_urls[v] = re.findall('src="(.*?)"', global_vars[v])[0]


    print 'image_urls', image_urls

    filter_out = 'header', 'footer', 'startup'
    remaining_passages = [p for p in passages.values()
                             if not any(f in p.tags for f in filter_out)]
    
    # find maps
    maps = [find_map(p, image_urls) for p in remaining_passages]
    maps = {m.name: m for m in maps if m}
    
    # find encounters
    remaining_passages = [p for p in passages.values() 
                            if p.name not in maps]
    encounters = {p.name: find_encounter(p, image_urls) for p in remaining_passages}
    encounters = {k: v for k,v in encounters.items() if v}

    # find messages
    arr = []
    for p in remaining_passages:
        if p.name not in encounters:
            p.parsed_contents = substitute_globals(p, global_vars)
            arr += [p]
    remaining_passages = arr
    messages = {p.name: find_message(p) for p in remaining_passages}
    messages = {k: v for k,v in messages.items() if v}

    print 'all messages', messages
    # check graph integrity
    # missing links, ...

    
    return maps, encounters, messages


def html_to_trees(html):
    def make_tree(passage):
        return preprocess(HarloweHook(passage.parsed_contents))

    attrs, non_passages, passages = parse_harlowe_html(html)

    # execute startup
    startups = {p.name: (p, make_tree(p)) for p in passages.values() if 'startup' in p.tags.split(' ')}
    global_vars = {}
    for _, tree in startups.values():
        # ignore output
        evaluate(tree, global_vars)

    headers = {p.name: (p, make_tree(p)) for p in passages.values() if 'header' in p.tags.split(' ')}
    
    passages = {p.name: (p, make_tree(p)) for p in passages.values()
                    if 'startup' not in p.tags.split(' ') 
                    and 'header'  not in p.tags.split(' ')}

    return startups, headers, passages, global_vars


def parse_harlowe_html(html_file):
    
    with open(html_file) as fh:
        html = fh.read()

    i = html.find('<tw-storydata')
    j = html.find('</tw-storydata>')

    storydata = html[i:j] + '</tw-storydata>'
    
    attrs, non_passages, passages = harlowe.parse_harlowe_html(storydata)
    
    for p in passages:
        passages[p].parse_contents()

    # use all links to define passage parents and destinations
    # for name, passage in passages.items():
    #     links = []
    #     for l in find_links(passage):
    #         if l.passage_name:
    #             links += [l.passage_name[0]]
    #         else:
    #             # doesn't deal with variable
    #             links += [l.link_text[0]]
    #     # links = [l.passage_name[0] for l in find_links(passage)]
    #     passage.destinations |= set(links)
    #     for link in links:
    #         passages[link].parents |= {name}

    return attrs, non_passages, passages


def find_links(passage):
    return list(passage.find_matches(lambda x: isinstance(x, HarloweLink)))


def get_set_macros(passage, name):
    # find macros of form (set: $name to $anything)
    hits = passage.find_matches(lambda x: isinstance(x, HarloweMacro)
                                          and x.canonical_name == 'set'
                                          and get_set_args(x)
                                          and re.findall(name, get_set_args(x)[0].name ))
    return list(hits)
    
def get_set_args(macro):
    return [c for c in macro.code if not isinstance(c, harlowe.text_type)]


def get_named_hooks(passage, name):
    hits = passage.find_matches(lambda x: isinstance(x, HarloweHook) 
                                                and x.nametag
                                                and re.findall(name, x.nametag))
    return list(hits)


def extract_places(passage):

    place_macro = get_set_macros(passage, 'places')[0]
    arr = tuple()
    if place_macro:
        place_array = get_set_args(place_macro)[1]
        place_array = get_set_args(place_array)
        
        for macro in place_array:
            txt = macro.code[0].strip().split(',')
            arr += (tuple(eval(x) for x in txt),)
    return arr



def find_map(passage, global_vars):
    
    # check for the nametag: []<map|
    map_nametag = get_named_hooks(passage, '^map$')

    if not map_nametag:
        # print 'no <map| nametag found in', passage.name
        return None
    
    
    # map_image = get_set_args(map_image)
    # url = image_urls[map_image[1].name]
    url = get_img_tag_url(global_vars['mapImage'])
    print 'map image url is', url, 'from', global_vars['mapImage']
    
    # filter args from (set: $x to $y)

    # recursively search for links inside any Harlowe elements
    # links = [(l.passage_name[0], l.link_text[0]) for l in find_links(passage)]
    links = [(str(i), l.link_text) for i,l in enumerate(find_links(passage))]

    # get x, y, and key if $places variable is set 
    # places = extract_places(passage)
    places = global_vars.get('places', tuple())

    places = places + default_places

    # fill in defaults if needed
    place_records = [Place(*p + l) for l, p in zip(links, places)]

    # optional intro text
    intro_hook = get_named_hooks(passage, 'intro')
    intro_text = intro_hook[0].hook[0] if intro_hook else ''

    print 'map with %d places in %s' % (len(place_records), passage.name) 
    return Map(name=passage.name, image=url, 
               places=place_records, intro=intro_text)



def find_encounter(passage, global_vars):

    name         = get_named_hooks(passage, '^enemy$')
  
    def reverse_lookup(x):
        return {v: k for k,v in global_vars.items()}[x]

    if name:
        name = reverse_lookup(name[0].hook[0])
    else:   
        return

    vocab        = get_named_hooks(passage, '^vocab$')
    enemy_class  = get_named_hooks(passage, '^class$')
    image        = get_named_hooks(passage, '^enemyImage$')

    links        = find_links(passage)
    print 'encounter links', [l.link_text for l in links]
    victory      = [l.link_text for l in links].index('Victory')
    defeat       = [l.link_text for l in links].index('Defeat')


    if vocab:
        vocab = reverse_lookup(vocab[0].hook[0])
    else:
        vocab = 'derp'

    if enemy_class:
        enemy_class = reverse_lookup(enemy_class[0].hook[0])
        enemy_class = globals().get(enemy_class, Opponent)
    else:
        enemy_class = Opponent

    default_image = 'http://vignette1.wikia.nocookie.net/sonicfanon/images/1/12/TRolOLolOL.jpg/revision/latest?cb=20111030181448'
    if image:
        image = image[0].hook[0]
        image = get_img_tag_url(image)
        print 'the image is', image
    else:
        image = default_image

    
    print '%s found in %s' % (name, passage.name)

    return Enemy(name, image, enemy_class, vocab, str(victory))


def find_message(passage):
    # if 'message' not in passage.tags:
    #     return None

    text = display_passage(passage)

    letters = 'abcdefghiklmnop'
    # splash tag = any key to dismiss, always go to first link
    if 'splash' in passage.tags:
        letters = '*'

    # want to track key, choiceText, and passage_name
    choices = []
    for i, (l, key) in enumerate(zip(find_links(passage), letters)):
        choices += [Choice(key=key, label=l.link_text, name=str(i))]

    print 'message with %d choices %s in %s' % (len(choices), choices, passage.name)

    return Message(name=passage.name, text=text, choices=choices)


def find_global_vars(passages):
    variables = {}
    passages = sorted(passages,key=lambda x: x.name)

    for p in passages:
        if 'header' in p.tags:
            vars_ = {}
            macros = get_set_macros(p, '.*')
            for macro in macros:
                codes = []
                for c in macro.code:
                    if isinstance(c, harlowe.text_type):
                        # eliminate ' to ' surrounded by variable spaces
                        if c.lstrip().startswith('to '):
                            c = c.lstrip()[3:]
                            codes += [c.lstrip()[1:-1]]
                    else:
                        codes += [c]
                name, value = [c for c in codes if c]
                # don't deal with this crap
                if not isinstance(name, HarloweVariable):
                    continue
                if isinstance(value, harlowe.text_type):
                    vars_[name.name] = value
                elif isinstance(value, RawHtml):
                    vars_[name.name] = '<' + value.tag + '>'
            print 'in %s, found variables: %s' % (p.name, ', '.join(vars_.keys()))
            variables.update(vars_)
    return variables



def get_image_urls(passage):
    # extract dict of $varImage to URL
    images = [m for m in passage.parsed_contents 
                  if isinstance(m, HarloweMacro)]

    urls = {}
    for hm in images:
        hrh = hm.code[-2]
        url = re.findall('src="(.*)"', hrh.tag)[0]
        hv = hm.code[1]
        name = hv.name
        urls[name] = url
        
    return urls

def get_img_tag_url(tag):
    match = re.findall('src="(.*)"', tag)
    if match:
        return match[0]
    match = re.findall('src=&quot;(.*)&quot', tag)
    if match:
        return match[0]


alignment = { '==>':  '<div align="right">'
            , '<==':  '<div align="left">'
            , '=><=': '<div align="center">'
            , '==><=': '<div style="text-align: center; max-width:50%; margin-left: 33%;">'
            , '=><==': '<div style="text-align: center; max-width:50%; margin-left: 17%;">'
            }

def substitute_globals(passage, global_vars):
    # top-level only
    contents = []
    for c in passage.parsed_contents:
        if isinstance(c, HarloweVariable):
            contents += [global_vars.get(c.name, c)]
        if isinstance(c, harlowe.text_type):
            pat = re.compile(r'(' + '|'.join(alignment.keys()) + r')')
            c = pat.sub(lambda x: alignment[x.group()], c)
            contents += [c]
        else:
            contents += [c]
    contents += []
    return contents

def substitute_alignment(s):
    pat = re.compile(r'(' + '|'.join(alignment.keys()) + r')')
    return pat.sub(lambda x: alignment[x.group()], s)



def _set(a, b):
    a_ = _evaluate(a)
    b_ = _evaluate(b)
    global_vars.update({a_: b_})
    return None

def _hook(a, nametag):
    hook = []
    for b in a:
        x = _evaluate(b)
        if x:
            hook.append(x)
        # print b, '->', x
    return HarloweHook(hook, nametag=nametag)
    

def _if(predicate, branch):
    result = _evaluate(predicate)
    if result is True:
        return _evaluate(branch)
    else:
        return None

def _unless(predicate, branch):
    result = _evaluate(predicate)
    if result is False:
        return _evaluate(branch)
    else:
        return None    


def _is(a, b):
    truth = _evaluate(a) == _evaluate(b)
    return truth

def _id(a):
    if isinstance(a, harlowe.text_type):
        if a.strip() == 'true':
            return True
        if a.strip() == 'false':
            return False
        try:
            return float(a)
        except ValueError:
            s = str(a).strip(' ') # leave newline alone
            # if "''" in s:
            #     assert False
            quotemark = ("'", '"')
            while s.startswith(quotemark) and s.endswith(quotemark):
                if len(s)>1:
                    s = s[1:-1]
                else:
                    break
            return substitute_alignment(s)

    if isinstance(a, HarloweVariable):
        return global_vars[a.name]
    if isinstance(a, HarloweLink):
        return a
    if isinstance(a, tuple):
        return tuple(_evaluate(x) for x in a)
    print "can't id", a

def _link(link_text, hook, goto):
    
    # link text is evaluated immediately
    link_text_ =_evaluate(link_text)
    
    # delayed evaluation for hook and goto
    
    def do_transition(global_vars):
        # changes global_vars
        # throw away output
        global_vars, _ = evaluate(hook, global_vars)
        global_vars, destination = evaluate(goto, global_vars)
        assert(isinstance(destination, harlowe.text_type))
        
        return global_vars, destination
         
    
    dummy_link = HarloweLink(link_text_, passage_name='_dummy_link')
    dummy_link.do_transition = do_transition
    return dummy_link

def _evaluate(args):
    f, args = args[0], args[1:]
    return f(*args)

def evaluate(tree, global_vars_):
    """ Mutates input global_vars :(. Could deep copy.
    """
    global global_vars
    global_vars = global_vars_
    output = _evaluate(tree)
    return global_vars, output

def preprocess(obj0, obj1=None):
    """Accepts the following. Produces a tree of (f, *args).
    HarloweMacro (if, set, link, a [ignored])
    HarloweLink (a->b, $a->b, a->$b)
    HarloweVariable
    RawHtml (converted to str)
    harlowe.text_type (str, unicode)
    """
    ignore_ws = "'{}"
    def no_empties(y):
        return [x for x in y if not isinstance(x, harlowe.text_type) 
                             or x.strip() 
                             and x.strip() not in ignore_ws]
    
    if isinstance(obj0, HarloweMacro):
        name = obj0.name_in_source
        code = no_empties(obj0.code)
        if name == 'if':
            args = tuple(preprocess(x) for x in code)
            # obj1 is the hook
            # implement comparators like 'contains'
            return (_if,) + args + (preprocess(obj1),)
        if name == 'unless':
            args = tuple(preprocess(x) for x in code)
            # obj1 is the hook
            return (_unless,) + args + (preprocess(obj1),)    
        if name == 'set':
            if len(code) == 2:
                # eliminate 'to'
                code[1] = code[1].strip()[2:]
                return (_set, preprocess(code[0].name), preprocess(code[1]))
            if len(code) == 3:
                return (_set, preprocess(code[0].name), preprocess(code[2]))
            # if any(isinstance(c, RawHtml) for c in code):
        if name == 'a':
            args = tuple(preprocess(x) for x in no_empties(csl(obj0.code)))
            return (_id, args)
        if name == 'link':
            link_text = preprocess(code[0])
            hook_code = no_empties(obj1.hook)
            # find the (goto:)
            # only support literal goto destination
            # only include hook up to the first goto
            hook_code_ = []
            for c in hook_code:
                if isinstance(c, HarloweMacro) and c.name_in_source == 'goto':
                    # the contents need to evaluate to a string
                    goto_code = no_empties(c.code)
                    assert(len(goto_code) == 1)
                    goto = preprocess(c.code[0])
                    break
                else:
                    hook_code_ += [c]

            new_hook = preprocess(HarloweHook(hook_code_))

            return (_link, link_text, new_hook, goto)

                
    
    if isinstance(obj0, HarloweHook):
        # contents = no_empties(obj0.hook)[::-1]
        contents = obj0.hook[::-1]
        # account for macro with hook following
        args = []
        while contents:
            obj0_ = contents.pop()
            # needs to consume next hook
            if isinstance(obj0_, HarloweMacro) and obj0_.name_in_source in ('if', 'link', 'unless'):
                obj1_ = contents.pop()
                args += [preprocess(obj0_, obj1_)]
            else:
                args += [preprocess(obj0_)]
        return (_hook, args, obj0.nametag)
    
    if isinstance(obj0, harlowe.text_type):
        # should do something about {}
        return (_id, obj0)
    if isinstance(obj0, RawHtml):
        return (_id, '<' + obj0.tag + '>')
    if isinstance(obj0, HarloweVariable):
        return (_id, obj0)
    if isinstance(obj0, HarloweLink):
        link_text = preprocess(obj0.link_text[0])
        hook = preprocess('')
        if obj0.passage_name:
            goto = preprocess(obj0.passage_name[0])
        else:
            # [[Goomba]]
            goto = link_text

        return (_link, link_text, hook, goto)
    
    # print 'did not preprocess', obj0
    return (_id, 'wtf')

def csl(x):
    arr = []
    for a in x:
        if isinstance(a, harlowe.text_type):
            a_ = a.split(',')
            arr += a_
        else:
            arr += [a]
    return arr


def make_node(passage, global_vars):
   
    map_ = find_map(passage, global_vars)
    if map_:
        return map_
    
    encounter = find_encounter(passage, global_vars)
    if encounter:
        return encounter
    
    message = find_message(passage)
    if message:
        return message
    
    class FuckYouError(Exception):
        pass
    raise FuckYouError('failed to create node from %s' % passage.name)
    
    
def enter(passage, tree, global_vars):
    """ 
    1. evaluate the passage tree, in global_vars context
    2. put the result in passage.parsed_contents
    3. try to make the passage into a node. 
        - if this fails, return None for node
    """
    
    global_vars, contents = evaluate(tree, global_vars) 

    passage.parsed_contents = contents.hook
    node = make_node(passage, global_vars)
    
    links = find_links(passage)
    return node, links, global_vars

def display_passage(x):
    if isinstance(x, str):
        return x
    if isinstance(x, HarloweHook):
        s = ''
        for y in x.hook:
            s += display_passage(y)
        return s
    if isinstance(x, HarlowePassage):
        s = ''
        for y in x.parsed_contents:
            s += display_passage(y)
        return s
    return ''
    