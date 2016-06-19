from flask import Flask, render_template, url_for
from flask_socketio import emit, SocketIO
import cmpd
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug=True
socketio = SocketIO()
socketio.init_app(app)

phrases = []

@app.route('/')
def hello_world():
    return render_template('index.html', wordbank=phrases,
        enemy=url_for('static', filename='images/buddha-1.jpg'))

@app.route('/fuckyou')
def another_function():
    return 'fuck you'

@socketio.on('insult', namespace='/base')
def reply(insult):

    phrase = cmpd.similar_phrase(insult['insult'])
    phrase = cmpd.singular(phrase)
    if phrase == insult['insult']:
        phrase = random.choice(phrases)

    emit('message', {'insult': insult['insult'],
                     'reply': phrase})

if __name__ == '__main__':
    categories = cmpd.load_DIDB()
    phrases = categories['Criminal Professions'] + \
              categories['Southern'] + \
              categories['Lowly Professions'] + \
              categories['Sexual'] + \
              categories['Political'] + \
              categories['Uncategorized I'] + \
              categories['Uncategorized II'] + \
              categories['Uncategorized III'] + \
              categories['Uncategorized IV']
    phrases = [cmpd.singular(phrase) for phrase in phrases 
                    if ' of ' not in phrase.lower()]
    

    
    db = cmpd.get_db()

    socketio.run(app)


