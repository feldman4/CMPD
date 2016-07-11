from flask import Flask, render_template, url_for, redirect, session
from flask_socketio import emit, SocketIO
import random

import cmpd_web

app = Flask(__name__)
app.session_interface = cmpd_web.CMPDSessionInterface()
app.config['SECRET_KEY'] = '36dab92b-7550-4476-9984-5bc162115cf7'
app.debug=True
socketio = SocketIO(app)



@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/')
def index():
    return redirect(url_for('versus_enemy', enemy='ctenophora'))


@app.route('/bas<string:flavor>')
def base(flavor):
    """Show a demo powered by Elm or only JS.
    """
    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]

    session['base'] = cmpd_web.Base(adjectives, nouns)

    template = 'bas%s.html' % flavor
    return render_template(template, wordbank=session['base'].wordbank,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@app.route('/versus/')
def versus():
    return redirect(url_for('versus_enemy', enemy='none'))


@app.route('/versus/<string:enemy>')
def versus_enemy(enemy):

    if enemy not in cmpd_web.stable:
        enemies = ''
        for e in sorted(cmpd_web.stable):
            url = url_for('versus_enemy', enemy=e)
            enemies += '<a href=%s>%s</a> ' % (url, e)


        return '<h1>404 not an enemy</h1>' + \
                '<h3>try: %s</h3>' % enemies



    session['versus_enemy'] = cmpd_web.stable[enemy]

    return render_template('versus.html')


@socketio.on('INSULT', namespace='/base')
def reply(insult):
    session['base'].emit = emit
    session['base'].reply(insult)


@socketio.on('INSULT', namespace='/versus')
def reply(insult):
    session['versus'].emit = emit
    session['versus'].reply(insult)


@socketio.on('INSULT', namespace='/map')
def reply(insult):
    session['map_GM'].reply(insult, emit)


@socketio.on('INITIALIZE', namespace='/map')
def initialize_map(message):
    print 'initializing map'
    map_src = url_for('static', filename='images/map.png')

    places = [(0.24, 0.12, 'w', 'ctenophora'),
              (0.19, 0.68, 'x', 'ctenophora'), 
              (0.80, 0.22, 'y', 'derp'),
              (0.74, 0.71, 'z', 'underground')]
    places = [{'x': x, 'y': y, 'label': l, 'enemy': e} for (x,y,l,e) in places]

    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]
    vocab = [('adjective', sorted(set(adjectives))),
             ('noun', sorted(set(nouns)))]

    enemies = cmpd_web.stable.copy()
    for enemy in enemies:
        image = enemies[enemy]['image']
        enemies[enemy]['image'] = url_for('static', 
                                            filename=image)
        print enemies[enemy]['image']

    GM = cmpd_web.GameMaster(places, enemies, vocab, map_src)
    GM.initialize(emit)
    session['map_GM'] = GM


@socketio.on('REQUEST_ENCOUNTER', namespace='/map')
def send_encounter(message):
    print message
    enemy = message['enemy']
    player = message['player']
    GM = session['map_GM']

    GM.update_player(player)

    # GM checks its enemies list, initializes w/ vocab
    GM.request_encounter(enemy, emit)



@socketio.on('REQUEST_ENCOUNTER', namespace='/versus')
def send_encounter(message):

    message['encounter']

    enemy = session['versus_enemy']
    print 'requested versus', enemy

    enemy_image =  url_for('static', filename=enemy['image'])
    emit('SEND_ENCOUNTER', {'image': enemy_image})

    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]
    vocab = [('JJ', sorted(set(adjectives))),
             ('NN', sorted(set(nouns)))]

    # this will initialize, emitting UPDATE_WORDBANK
    session['versus'] = enemy['class'](vocab, emit)

    




if __name__ == '__main__':
    socketio.run(app)

    path = url_for('static', filename='/elm-helpers.js')
    cmpd_web.load_elm_helpers(path)



