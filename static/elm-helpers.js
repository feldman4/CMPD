
////////////////////// LOADING //////////////////////

var socketTarget 
var socket
var fuse_opts = {threshold: 0.4}

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
	socket.on('update_wordbank', function(data) {
	        app.ports.newWordbank.send(data.wordbank)
	    })
}


function remark(app) {
	socket.on('remark', function(data) {
			app.ports.remark.send(data)
	})
}

function changeEnemy(app) {
	socket.on('change_enemy', function(data) {
		
		app.ports.setEnemyImage.send(data.image)
	})
}

function sendEncounter(app) {
	socket.on('send_encounter', function(data) {
		app.ports.setEnemyImage.send(data.image)
	})
}



////////////////////// ELM -> FLASK //////////////////////

// pass input words on to flask
function sendInsult(app) {
	app.ports.sendInsult.subscribe(function(comm) {
		var word = comm[0]
		var progress = comm[1]
		socket.emit('insult', {
			insult: word,
			progress: progress
		})
	})

}

function requestEncounter(app) {
	app.ports.requestEncounter.subscribe(function(encounter) {
		socket.emit('request_encounter', {
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


////////////////////// JS  //////////////////////


// helper to deal with scrolling (not in elm?)
function scrollSelector(selector) {
	var $d = $(selector)
	setTimeout(function() {
		$d.scrollTop($d[0].scrollHeight);
	}, 30)

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