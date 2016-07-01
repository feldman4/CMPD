from flask import Flask, render_template, url_for, redirect, session
from flask_socketio import emit, SocketIO
import cmpd
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug=True
socketio = SocketIO(app)

phrases = []

flag = 'JJ'
lastword = ''


@app.route('/')
def index():
    return redirect(url_for('base'))


@app.route('/base')
def base():
    JJ = [p.split(' ')[0] for p in phrases]
    return render_template('index.html', wordbank=JJ,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@app.route('/versus')
def versus():
    JJ = [p.split(' ')[0] for p in phrases]
    return render_template('index.html', wordbank=JJ,
        enemy=url_for('static', filename='images/cyclops.jpg'))


@socketio.on('insult', namespace='/base')
def reply(insult):

    global flag
    JJ = [p.split(' ')[0] for p in phrases]
    NN = [p.split(' ')[-1] for p in phrases]
    if flag == 'JJ':
        emit('update_wordbank', {'wordbank': NN})
        flag = 'NN'
        session['lastword'] = insult['insult']
        print session, session['lastword']
    else:
        emit('update_wordbank', {'wordbank': JJ[:10]})
        flag = 'JJ'

        phrase = random.choice(phrases)
        retort = {'insult': session['lastword'] + ' ' + insult['insult'],
                       'reply': phrase}
        print retort
        emit('retort', retort, namespace='/base')

        # with open('record', 'a') as fh:
        #   import time
        #   fh.write('%f\n%s\n' % (time.time(), retort['retort']))

if __name__ == '__main__':
    phrases = cmpd.load_DIDB_pairs()
    socketio.run(app)


