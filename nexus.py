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
    return redirect(url_for('versus'))


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


@app.route('/versus')
def versus():
    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]

    vocab = [('JJ', sorted(set(adjectives))),
             ('NN', sorted(set(nouns)))]

    session['versus'] = cmpd_web.VersusDIDB(vocab)

    return render_template('versus.html', 
        wordbank=session['versus'].wordbank,
        enemy=url_for('static', filename='images/ctenophora-1.jpg'))



@app.route('/versus-derp')
def versus_derp():
    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]

    vocab = [('JJ', sorted(set(adjectives))),
             ('NN', sorted(set(nouns)))]

    session['versus'] = cmpd_web.VersusDerp(vocab)

    return render_template('versus.html', 
        wordbank=session['versus'].wordbank,
        enemy=url_for('static', filename='images/derp-3.jpg'))


@socketio.on('insult', namespace='/base')
def reply(insult):
    print 'received', insult
    session['base'].reply(insult, emit)


@socketio.on('insult', namespace='/versus')
def reply(insult):
    session['versus'].reply(insult, emit)


@socketio.on('insult', namespace='/map')
def reply(insult):
    session['map'].reply(insult, emit)


@socketio.on('request_encounter', namespace='/map')
def send_encounter(message):
    encounter = message['encounter']
    enemy_image = url_for('static', filename='images/ctenophora-1.jpg')
    emit('send_encounter', {'image': enemy_image})

    adjectives = [p.split(' ')[0]  for p in cmpd_web.DIDB_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.DIDB_phrases]

    vocab = [('JJ', sorted(set(adjectives))),
             ('NN', sorted(set(nouns)))]

    session['map'] = cmpd_web.VersusDIDB(vocab)

    emit('update_wordbank', {'wordbank': session['map'].wordbank})

if __name__ == '__main__':
    socketio.run(app)


