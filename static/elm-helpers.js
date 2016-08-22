
////////////////////// COMPONENTS //////////////////////

elmJS = {
	Map: ["/static/Map.js", "https://drive.google.com/uc?export=download&id=0B3flOzQHFe1mUFNpekI4QUVxdnM"],
	Loadout: ["/static/Loadout.js", ""],
	Menu: ["/static/Menu.js", ""],
	Versus: ["/static/Versus.js", ""]
}


////////////////////// SOCKET MESSAGES //////////////////////

flask_to_js = {
	'SEND_REMARK': 'SEND_REMARK',
	'SEND_WORDBANK': 'SEND_WORDBANK',
	'SEND_ENCOUNTER': 'SEND_ENCOUNTER',
	'SEND_MAP': 'SEND_MAP',
	'SEND_ENEMY': 'SEND_ENEMY',
	'SEND_PLAYER' : 'SEND_PLAYER',
}

js_to_flask = {
	'SEND_INSULT': 'SEND_INSULT', 
	'SEND_TRANSITION': 'SEND_TRANSITION',
	'SEND_LOADOUT': 'SEND_LOADOUT',
	'INITIALIZE': 'INITIALIZE',
}


////////////////////// LOADING //////////////////////

var socketTarget 
var socket
var fuse_opts = {threshold: 0.4}
var timeoutDelay = 30 // delay for Elm requests to modify updated DOM

function documentReady(socketRoom) {
	// set up socket.io connection to flask
	socketTarget = 'http://' + document.domain + ':' + location.port + socketRoom
	socket = io.connect(socketTarget);
}

function getScriptLocalHosted(local, hosted, success) {
	  if (document.domain === "localhost")
		{
			$.getScript(local, success)
		} else {
			$.getScript(hosted, success)
		}

}


////////////////////// FLASK -> ELM //////////////////////

function sendWordbank(app) {
	// initializes wordbank from server
	socket.on(flask_to_js.SEND_WORDBANK, function(data) {
	        app.ports.setWordbank.send(data)
	    })
}


function sendRemark(app) {
	socket.on(flask_to_js.SEND_REMARK, function(data) {
			app.ports.addRemark.send(data)
	})
}

function sendEnemy(app) {
	socket.on(flask_to_js.CHANGE_ENEMY, function(data) {
		
		app.ports.setEnemyImage.send(data.image)
	})
}

function sendEncounter(app) {
	socket.on(flask_to_js.SEND_ENCOUNTER, function(data) {
		app.ports.setEnemy.send(data)

	})
}

function sendMap(app) {
	socket.on(flask_to_js.SEND_MAP, function(data) {
		app.ports.setMap.send(data)
	})
}

function sendPlayer(app) {
	socket.on(flask_to_js.SEND_PLAYER, function(data) {
		app.ports.setPlayer.send(data)
	})
}

/////////////////////// JS -> FLASK //////////////////////

function initialize() {
	socket.emit(js_to_flask.INITIALIZE, {})
}



////////////////////// ELM -> FLASK //////////////////////

// pass input words on to flask
function sendInsult(app) {
	app.ports.sendInsult.subscribe(function(comm) {
		var word = comm[0]
		var progress = comm[1]
		socket.emit(js_to_flask.SEND_INSULT, {
			word: word,
			progress: progress
		})
	})

}

// transition Map, Encounter, Message, etc
function sendTransition(app) {
	app.ports.sendTransition.subscribe(function(comm) {
		var name = comm[0]
		socket.emit(js_to_flask.SEND_TRANSITION, {
			name: name
		})
	})

}
	 

function sendLoadout(app) {
	app.ports.sendLoadout.subscribe(function(player) {
		socket.emit(js_to_flask.SEND_LOADOUT, player)
	})
}


////////////////////// ELM -> JS //////////////////////

// immediately respond to requests for suggestions from elm
function askFuse(app) {
    app.ports.askFuse.subscribe(function(comm) {
        var word = comm[0]
        var wordbank = comm[1]
        if (word === "") {
        	app.ports.suggestions.send(wordbank)
        	return
        }
        var suggestions = fuseSuggest(word, wordbank);
        app.ports.suggestions.send(suggestions);
    });

}

function scrollTop(app) {

	app.ports.scrollTop.subscribe(scrollTop)
}

function scrollParent(app) {
	app.ports.scrollParent.subscribe(scrollParent)
}

function setFocus(app) {
	app.ports.setFocus.subscribe(focusSelector)
}


////////////////////// JS  //////////////////////


// helper to deal with scrolling (not in elm?)
function scrollTop(selector) {
	var $d = $(selector)
	setTimeout(function() {
		$d.scrollTop($d[0].scrollHeight);
	}, timeoutDelay)
}

// scrolls a parent the minimum distance to keep selected child visible
function scrollParent(selector) {
	var $child = $(selector)
	var $parent = $(selector).parent()
	var height = 0
	setTimeout(function() {
		$parent.scrollTop(height)
	}, timeoutDelay)
}

function focusSelector(selector) {
	setTimeout(function() {
		$(selector).focus()
	}, timeoutDelay )
}


function fuseSuggest(word, wordbank) {

    var fuse = new Fuse(wordbank.map(
    	function(w){return w.toLowerCase()}),
     	fuse_opts);

    var suggestions = fuse.search(word.toLowerCase())
    		.map(function(i) {
        			return wordbank[i]
    				}
    			)

    return suggestions
}