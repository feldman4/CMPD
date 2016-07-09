
////////////////////// SOCKET MESSAGES //////////////////////

flask_to_js = {
	'REMARK': 'REMARK',
	'UPDATE_WORDBANK': 'UPDATE_WORDBANK',
	'SEND_ENCOUNTER': 'SEND_ENCOUNTER',
	'SEND_MAP': 'SEND_MAP',
	'CHANGE_ENEMY': 'CHANGE_ENEMY'
}

js_to_flask = {
	'INSULT': 'INSULT', 
	'REQUEST_ENCOUNTER': 'REQUEST_ENCOUNTER'
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

function updateWordbank(app) {
	// initializes wordbank from server
	socket.on(flask_to_js.UPDATE_WORDBANK, function(data) {
	        app.ports.newWordbank.send(data.wordbank)
	    })
}


function remark(app) {
	socket.on(flask_to_js.REMARK, function(data) {
			app.ports.remark.send(data)
	})
}

function changeEnemy(app) {
	socket.on(flask_to_js.CHANGE_ENEMY, function(data) {
		
		app.ports.setEnemyImage.send(data.image)
	})
}

function sendEncounter(app) {
	socket.on(flask_to_js.SEND_ENCOUNTER, function(data) {
		app.ports.setEnemyImage.send(data.image)

	})
}

function sendMap(app) {
	socket.on(flask_to_js.SEND_MAP, function(data) {
		app.ports.setMap.send(data)
	})
}



////////////////////// ELM -> FLASK //////////////////////

// pass input words on to flask
function sendInsult(app) {
	app.ports.sendInsult.subscribe(function(comm) {
		var word = comm[0]
		var progress = comm[1]
		socket.emit(js_to_flask.INSULT, {
			insult: word,
			progress: progress
		})
	})

}

function requestEncounter(app) {
	app.ports.requestEncounter.subscribe(function(encounter) {
		socket.emit(js_to_flask.REQUEST_ENCOUNTER, {
			encounter: encounter
		})
	})
}


////////////////////// ELM -> JS //////////////////////

// immediately respond to requests for suggestions from elm
function askFuse(app) {
    app.ports.askFuse.subscribe(function(comm) {
        var word = comm[0]
        var wordbank = comm[1]
        if (word === "") {
        	app.ports.newWordbank.send(_.shuffle(wordbank))
        	return
        }
        var suggestions = fuseSuggest(word, wordbank);
        app.ports.suggestions.send(suggestions);
    });

}

function scrollTop(app) {

	app.ports.scrollTop.subscribe(scrollSelector)
}

function setFocus(app) {
	app.ports.setFocus.subscribe(focusSelector)
}


////////////////////// JS  //////////////////////


// helper to deal with scrolling (not in elm?)
function scrollSelector(selector) {
	var $d = $(selector)
	setTimeout(function() {
		$d.scrollTop($d[0].scrollHeight);
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