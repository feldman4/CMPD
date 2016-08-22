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



@app.route('/')
def index():
    return redirect(url_for('custom_map', map_name='ovaloffice'))


@app.route('/vocab/<string:vocab>')
def vocab(vocab):
    try:
        dump = json.dumps(cmpd_web.load_vocab(vocab, reload=True), indent=4)
        return dump.replace('\n', '<br/>').replace(' ', '&nbsp;')
    except Exception as e:
        return 'Error retrieving %s: %s' % (vocab, e.__repr__())


@app.route('/components')
def show_components():
    return redirect(url_for('component', elm_component='none'))

@app.route('/components/<string:elm_component>')
def component(elm_component):
    # component names and files are uppercase, like Elm.js
    elm_component = elm_component[0].upper() + elm_component[1:]

    defined_components = ('Map', 'Loadout', 'Menu', 'Versus')
    if elm_component not in defined_components:
        return '<h3>fuck you</h3> <p>try one of %s</p>' % (defined_components,)
        
    # elif elm_component == 'Versus':
    # some components need setup

    else:
        return render_template('base.html', elm_component=elm_component)
        

@app.route('/map')
def default_map():
    return redirect(url_for('custom_map', map_name='islands'))

@app.route('/map/<string:map_name>')
def custom_map(map_name):
    # session['initialize'] is a function called by INITIALIZE message after elm loads
    session['initialize'] = cmpd_web.initialize_map(map_name)
    return render_template('base.html', elm_component='Map')

@app.route('/harlowe/<string:harlowe_name')
def launch_harlowe(harlowe_name):
    GM = cmpd_web.GameMaster([], '', player)
    GM.load_html('resources/harlowe/' + harlowe_name)
    session['GM'] = GM
    session['initialize'] = GM.initialize
    return render_template('base.html', elm_component='Map')



@app.route('/versus/')
def versus():
    return redirect(url_for('versus_enemy', enemy='none'))


@app.route('/versus/<string:enemy>')
def versus_enemy(enemy):
    """ Not currently working. Should render base.html with Versus component and set initialize function to create GameMaster and begin encounter.
    Beginning encounter requires sending 
    """
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



@socketio.on('INSULT')
def insult(insult):
    session['emit'] = emit
    session['GM'].insult(insult)


@socketio.on('INITIALIZE')
def initialize(message):
    # elm app triggers this when it is ready
    session['emit'] = emit
    session['initialize']()

@socketio.on('SEND_TRANSITION')
def transition(message):
    node = message['node']
    session['GM'].transition(node)


@socketio.on('REQUEST_ENCOUNTER')
def send_encounter(message):
    session['emit'] = emit

    enemy = message['enemy']
    player = message['player']
    GM = session['GM']

    # updates the loaded vocab
    # should probably do this when loaded changes
    GM.player.model.update(player)

    # GM checks its enemies list, initializes w/ vocab
    GM.request_encounter(enemy)



if __name__ == '__main__':

    cmpd_web.app = app
    cmpd_web.json_key = cmpd_web.make_gspread_json()

    
    socketio.run(app)

    path = url_for('static', filename='/elm-helpers.js')
    cmpd_web.load_elm_helpers(path)
    



