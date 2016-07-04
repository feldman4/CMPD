from flask import Flask, render_template, url_for, redirect, session
from flask_socketio import emit, SocketIO
import random

import cmpd_web

app = Flask(__name__)
app.session_interface = cmpd_web.CMPDSessionInterface()
app.config['SECRET_KEY'] = '36dab92b-7550-4476-9984-5bc162115cf7'
app.debug=True
socketio = SocketIO(app)



@app.route('/')
def index():
    return redirect(url_for('versus'))


@app.route('/bas<string:flavor>')
def base(flavor):
    """Show a demo powered by Elm or only JS.
    """
    adjectives = [p.split(' ')[0]  for p in cmpd_web.default_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.default_phrases]

    session['base'] = cmpd_web.Base(adjectives, nouns)

    template = 'bas%s.html' % flavor
    return render_template(template, wordbank=session['base'].wordbank,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@app.route('/versus')
def versus():
    adjectives = [p.split(' ')[0]  for p in cmpd_web.default_phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.default_phrases]

    session['versus'] = cmpd_web.Versus(adjectives, nouns)

    return render_template('versus.html', 
        fuse_threshold = 0.3,
        wordbank=session['versus'].wordbank,
        enemy=url_for('static', filename='images/ctenophora-1.jpg'))


@socketio.on('insult', namespace='/base')
def reply(insult):
    session['base'].reply(insult, emit)

@socketio.on('insult', namespace='/versus')
def reply(insult):
    session['versus'].reply(insult, emit)


if __name__ == '__main__':
    socketio.run(app)


