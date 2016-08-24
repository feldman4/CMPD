# extra functions for parsing exported Harlowe HTML
from . import harlowe
from .harlowe import HarloweMacro, HarloweVariable, HarloweLink, HarloweHook

import re
from collections import namedtuple


# move to types definition file
Map = namedtuple('Map', 'name image places')
Place = namedtuple('Place', 'x y key label preview')
default_places = tuple((0.75, 0.75, c) for c in 'abcdefgh')


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
    for name, passage in passages.items():
        links = [l.passage_name[0] for l in find_links(passage)]
        passage.destinations |= set(links)
        for link in links:
            passages[link].parents |= {name}

    return attrs, non_passages, passages




def get_set_args(macro):
    return [c for c in macro.code if not isinstance(c, harlowe.text_type)]


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

def find_links(passage):
    return list(passage.find_matches(lambda x: isinstance(x, HarloweLink)))


def get_set_macros(passage, name):
    # find macros of form (set: $name to $anything)
    hits = passage.find_matches(lambda x: isinstance(x, HarloweMacro)
                                          and x.canonical_name == 'set'
                                          and get_set_args(x)
                                          and re.findall(name, get_set_args(x)[0].name ))
    return list(hits)
    

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



def find_map(passage, image_urls):
    
    # check for the nametag: []<map|
    map_nametag = get_named_hooks(passage, '^map$')

    if not map_nametag:
        # print 'no <map| nametag found in', passage.name
        return None
    
    map_image = get_set_macros(passage, 'mapImage')[0]
    if not map_image:
        # print 'no (set: $mapImage to $x) found in', passage.name
        return None
    
    map_image = get_set_args(map_image)
    url = image_urls[map_image[1].name]
    
    # filter args from (set: $x to $y)

    # recursively search for links inside any Harlowe elements
    links = [(l.passage_name[0], l.link_text[0]) for l in find_links(passage)]

    # get x, y, and key if $places variable is set 
    places = extract_places(passage)

    places = places + default_places

    # fill in defaults if needed
    place_records = [Place(*p + l) for l, p in zip(links, places)]
    print 'map with %d places in %s' % (len(place_records), passage.name) 
    return Map(name=passage.name, image=url, places=place_records)



def find_encounter(passage):
    enemy_name  = get_named_hooks(passage, '^enemy$')
    
    if not enemy_name:
        # print 'no <enemy| nametag found in', passage.name
        return
    
    enemy_name = enemy_name[0].hook[0].name
    print '%s found in %s' % (enemy_name, passage.name)
    # enemy = cmpd_web.stable[enemy_name]
    
#     enemy_image = get_named_hooks(passage, 'enemyImage')
#     if enemy_image:
#         url = image_urls[enemy_image[0].hook[0].name]
#         enemy = dict(enemy)
#         enemy.update({'image': url})
    return enemy_name


def html_to_nodes(html):
    attrs, non_passages, passages = parse_harlowe_html(html)
    
    # find global image variables
    image_passages = [p for n,p in passages.items() if 'Images' in n]
    image_urls = {}
    [image_urls.update(get_image_urls(p)) for p in image_passages]
    
    filter_out = 'header', 'footer', 'startup'
    remaining_passages = [p for p in passages.values()
                             if not any(f in p.tags for f in filter_out)]
    
    # find maps
    maps = [find_map(p, image_urls) for p in remaining_passages]
    maps = {m.name: m for m in maps if m}
    
    # find encounters
    remaining_passages = [p for p in passages.values() 
                              if p.name not in maps]
    encounters = {p.name: find_encounter(p) for p in remaining_passages}
    encounters = {k: v for k,v in encounters.items() if v}
    
    # check graph integrity
    # missing links, ...
    
    return maps, encounters