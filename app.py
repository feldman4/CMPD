from flask import Flask, render_template, url_for, redirect, session, request, send_from_directory
from flask_socketio import emit, SocketIO
from werkzeug import secure_filename
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
    return redirect(url_for('default_harlowe'))


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

@app.route('/harlowe')
def default_harlowe():
    return redirect(url_for('launch_harlowe', harlowe_name='index'))

@app.route('/harlowe/<string:harlowe_name>')
def launch_harlowe(harlowe_name):
    vocab = cmpd_web.load_vocab('DIDB')
    player = cmpd_web.Player(vocab, None)
    GM = cmpd_web.GameMaster([], '', player)

    try:
        GM.load_html('resources/harlowe/%s.html' % harlowe_name)
    except IOError:
        maps = [os.path.splitext(os.path.basename(m))[0] 
                    for m in  glob('resources/harlowe/*.html')]
        

        hrefs = []
        for map_ in sorted(maps):
            url_play     = url_for('launch_harlowe',   harlowe_name=map_)
            url_download = url_for('download_harlowe', harlowe_name=map_ + '.html')
            hrefs += """<li>%s: 
                        <a href=%s>play</a> <a href=%s>twine</a> 
                        <a href=%s download>download</a></li>""" % \
                            (map_, url_play, url_download, url_download)

        return """<h1>404 %s not a map</h1>
                <h3><a href=%s>upload one</a> 
                or try:</h3><ul>%s</ul>""" % \
                (harlowe_name, url_for('harlowe_upload'), ''.join(hrefs))

    # TODO: specify starting vocab / player capacity in harlowe, or as custom in CMPD sheet
    player.model['image'] = url_for('static', filename='images/back.png')
    player.model['name'] = 'InquilineKea'
    player.model['health'] = 0.3


    session['GM'] = GM
    session['initialize'] = GM.initialize
    return render_template('base.html', elm_component='Game')



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

    return render_template('base.html', elm_component='Versus')



@socketio.on('SEND_INSULT')
def insult(insult):
    print 'received insult', insult
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

@socketio.on('SEND_LOADOUT')
def loadout(message):
    session['GM'].player.model = message


@app.route('/download/<string:harlowe_name>')
def download_harlowe(harlowe_name):
    return send_from_directory('resources/harlowe', harlowe_name)

@app.route('/upload')
def harlowe_upload():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():

    print 'uploading file'

    def scrunch(s):
        delchars = {c: None for c in map(chr, range(256)) if not c.isalnum()}
        return s.translate(delchars)

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(scrunch(file.filename))
            file.save(os.path.join('resources/harlowe', filename))
            return ''
    return "ooooooppppppssss"



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
    



