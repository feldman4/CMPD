from flask import Flask, render_template, url_for, redirect, session
from flask_socketio import emit, SocketIO
import random

import cmpd
import cmpd_web

app = Flask(__name__)
app.session_interface = cmpd_web.CMPDSessionInterface()
app.config['SECRET_KEY'] = 'secret!'
app.debug=True
socketio = SocketIO(app)

phrases = []


@app.route('/')
def index():
    return redirect(url_for('base'))


@app.route('/bas<string:flavor>')
def base(flavor):
    """Show a demo powered by Elm or only JS.
    """
    adjectives = [p.split(' ')[0]  for p in cmpd_web.phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.phrases]

    session['base'] = cmpd_web.Base(adjectives, nouns)

    template = 'bas%s.html' % flavor
    return render_template(template, wordbank=session['base'].wordbank,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@app.route('/versus')
def versus():
    adjectives = [p.split(' ')[0]  for p in cmpd_web.phrases]
    nouns      = [p.split(' ')[-1] for p in cmpd_web.phrases]

    session['base'] = cmpd_web.Base(adjectives, nouns)

    return render_template('versus.html', wordbank=session['base'].wordbank,
        enemy=url_for('static', filename='images/ctenophora-1.jpg'))


@socketio.on('insult', namespace='/base')
def reply(insult):
    session['base'].reply(insult, emit)

@socketio.on('insult', namespace='/versus')
def reply(insult):
    session['base'].reply(insult, emit)


if __name__ == '__main__':
    socketio.run(app)


