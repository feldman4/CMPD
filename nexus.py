from flask import Flask, render_template, url_for, redirect, session
from flask_socketio import emit, SocketIO
from gspread import WorksheetNotFound
import random
from glob import glob
import json
import os
import uuid

import cmpd_web
from cmpd_web import Place

app = Flask(__name__)
app.session_interface = cmpd_web.CMPDSessionInterface()
app.config['SECRET_KEY'] = str(uuid.uuid4())
app.debug = os.environ.get('DEBUG', '') == 'TRUE'
socketio = SocketIO(app)





@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/')
def index():
    return redirect(url_for('versus_enemy', enemy='ctenophora'))

@app.route('/vocab/<string:vocab>')
def vocab(vocab):
    try:
        dump = json.dumps(cmpd_web.load_vocab(vocab, reload=True), indent=4)
        return dump.replace('\n', '<br/>').replace(' ', '&nbsp;')
    except Exception as e:
        return 'Error retrieving %s: %s' % (vocab, e.__repr__())


@app.route('/bas<string:flavor>')
def base(flavor):
    """Show a demo powered by Elm or only JS.
    """
    vocab = cmpd_web.load_vocab('DIDB')

    session['base'] = cmpd_web.Base(vocab[0], vocab[1])

    template = 'bas%s.html' % flavor
    return render_template(template, wordbank=session['base'].wordbank,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@app.route('/versus/')
def versus():
    return redirect(url_for('versus_enemy', enemy='none'))


@app.route('/versus/<string:enemy>')
def versus_enemy(enemy):

    print cmpd_web.stable

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
def insult(insult):
    session['map_GM'].insult(insult, emit)


@socketio.on('INITIALIZE', namespace='/map')
def initialize_map(message):
    print 'initializing map'
    map_src = url_for('static', filename='images/map.png')

    places = [(0.24, 0.12, 'w', 'ctenophora'),
              (0.19, 0.68, 'x', 'ctenophora'), 
              (0.80, 0.22, 'y', 'derp'),
              (0.74, 0.71, 'z', 'underground')]
    places = [Place(*p) for p in places]
    player_vocab = cmpd_web.load_vocab('derp')


    enemies = {}
    for enemy in cmpd_web.stable:
        enemies[enemy] = dict(cmpd_web.stable[enemy])
        enemies[enemy]['image'] = url_for('static', 
                                            filename=enemies[enemy]['image'])
        print enemies[enemy]['image']

    
    player = cmpd_web.Player(player_vocab, None, capacity=6)
    GM = cmpd_web.GameMaster(places, enemies, player, map_src)
    GM.initialize(emit)
    session['map_GM'] = GM


@socketio.on('REQUEST_ENCOUNTER', namespace='/map')
def send_encounter(message):
    print 'request encounter\n' , message
    enemy = message['enemy']
    player = message['player']
    GM = session['map_GM']

    GM.player.model = player

    # GM checks its enemies list, initializes w/ vocab
    GM.request_encounter(enemy, emit)



@socketio.on('REQUEST_ENCOUNTER', namespace='/versus')
def send_encounter(message):

    message['encounter']

    enemy = session['versus_enemy']
    print 'requested versus', enemy

    enemy_image =  url_for('static', filename=enemy['image'])
    emit('SEND_ENCOUNTER', {'image': enemy_image})

    vocab = cmpd_web.load_vocab('DIDB')

    # this will initialize, emitting UPDATE_WORDBANK
    session['versus'] = enemy['class'](vocab, emit)


if __name__ == '__main__':

    cmpd_web.app = app
    cmpd_web.json.key = cmpd_web.make_gspread_json()

    socketio.run(app)

    path = url_for('static', filename='/elm-helpers.js')
    cmpd_web.load_elm_helpers(path)



