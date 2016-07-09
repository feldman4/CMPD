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
    map_src = url_for('static', filename='images/map.png')
    places = [(0.16, 0.08, 'w'),
              (0.12, 0.65, 'x'), 
              (0.72, 0.18, 'y'),
              (0.66, 0.65, 'z')]
    places = [{'x': x, 'y': y, 'label': l} for (x,y,l) in places]
    map_data = {'image': map_src, 
                'places': places}
    return render_template('map.html', map=map_data)

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
    session['map'].emit = emit
    session['map'].reply(insult)



@socketio.on('REQUEST_ENCOUNTER', namespace='/versus')
def send_encounter(message):

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

    


@socketio.on('REQUEST_ENCOUNTER', namespace='/map')
def send_encounter(message):
    encounter = message['encounter']
    enemy_image = url_for('static', filename='images/ctenophora.png')
    emit('SEND_ENCOUNTER', {'image': enemy_image})

    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]

    vocab = [('JJ', sorted(set(adjectives))),
             ('NN', sorted(set(nouns)))]

    session['map'] = cmpd_web.VersusDIDB(vocab, emit)

    emit('UPDATE_WORDBANK', {'wordbank': session['map'].wordbank})

if __name__ == '__main__':
    socketio.run(app)

    path = url_for('static', filename='/elm-helpers.js')
    cmpd_web.load_elm_helpers(path)



