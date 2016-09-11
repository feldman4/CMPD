from glob import glob
import regex as re
import pandas as pd
import external.types

def argsort(seq, key=lambda x: x):
    x = sorted([(v, i) for (i, v) in enumerate(seq)], key=lambda x: key(x[0]))
    return [i for (v, i) in x]


def despace(s):
    while '  ' in s:
        s = s.replace('  ' , ' ')
    return s.strip()

def get_types(txt):
    defns = []
    lines = txt.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('type alias'):
            type_alias = line.split()[2]
            defn = ''
            for line_ in lines[i+1:]:
                if line_ == '':
                    break
                defn += ' ' + despace(line_)
            defn = defn.replace(' ,', ',').strip()
            defns += [(type_alias, defn)]
    return defns


def inspect(srcs):
    # srcs = glob('*.elm') + glob('*/*.elm')
    types = []
    for src in srcs:
        txt = open(src, 'r').read()
        tmp = get_types(txt)
        if tmp:
            types += [(src, tmp)]

    arr = []
    for src, defns in types:
        for defn in defns:
            arr +=[ [src, defn[0], defn[1]]]

    df = pd.DataFrame(arr, columns=['elm file', 'type alias', 'definition'])

    df['python'] = ['cmpd_web.%s' % alias if alias in dir(external.types) else '??' 
                        for alias in df['type alias']]
    df = df[['elm file', 'type alias', 'python', 'definition']]
    df = df.set_index('type alias')
    ix = argsort(df.index, lambda x: (x=='Model', x))
    df = df.iloc[ix]
    return df