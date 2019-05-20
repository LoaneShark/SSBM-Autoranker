function getGameId(gameTitle){
	switch(gameTitle) {
		case 'Melee':
			return 1;
			break;
		case 'PM':
			return 2;
			break;
		case 'Smash4':
			return 3;
			break;
		case '64':
			return 4;
			break;
		case 'Brawl':
			return 5;
			break;
		case 'Rivals':
			return 24;
			break;
		case 'Ultimate':
			return 1386;
			break;
	}
}

function getGameTitle(gameId){
	switch(gameId) {
		case 1:
			return 'Melee';
			break;
		case 2:
			return 'PM';
			break;
		case 3:
			return 'Smash4';
			break;
		case 4:
			return '64';
			break;
		case 5:
			return 'Brawl';
			break;
		case 24:
			return 'Rivals';
			break;
		case 1386:
			return 'Ultimate';
			break;
	}
}

// null -=> still a "current"/"active" db/game
function getLastYearFromGame(gameId){
	switch(gameId) {
		case 1:
			return null;
			break;
		// dead (?) game
		case 2:
			return 2018;
			break;
		// DEAD GAME
		case 3:
			return 2018;
			break;
		case 4:
			return null;
			break;
		// DEAD GAME
		case 5:
			return 2017;
			break;
		case 24:
			return null;
			break;
		case 1386:
			return null;
			break;
	}
}

function getGameIconPath(gameId){
	switch(gameId) {
		case 1:
			return "/assets/images/game_icons/36px-SSBM_Icon.png";
			break;
		case 2:
			return "/assets/images/game_icons/36px-PM_Icon.png";
			break;
		case 3:
			return "/assets/images/game_icons/36px-SSB4_Icon.png";
			break;
		case 4:
			return "/assets/images/game_icons/36px-SSB64_Icon.png";
			break;
		case 5:
			return "/assets/images/game_icons/36px-SSBB_Icon.png";
			break;
		case 24:
			return "/assets/images/game_icons/2000px-RoA_Icon.png";
			break;
		case 1386:
			return "/assets/images/game_icons/36px-SSBU_Icon.png";
			break;
	}
}

function getStockIconPath(gameId,charId){
	return "/assets/images/stock_icons/"+gameId+"/"+charId+".png";
}

function snapshotToArray(snapshot,attr="val") {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
    	if (attr == "val") {
	        var item = childSnapshot.val();
		} else if (attr == "key") {
        	var item = childSnapshot.key;
        } else if (attr == "both") {
        	var item = {val: childSnapshot.val()};
        	item.key = childSnapshot.key;
        }
        returnArr.push(item);
    });
    return returnArr;
}

function otherGameActivity(p_id,game_id){
	//var gameIds = [1,2,3,4,5,24,1386];
	var gameIds = [1,2,3,4,5,1386];
	var gamePromises = [];
	var otherGames = [];
	for (i=0;i<gameIds.length;i++){
		if (gameIds[i] != game_id){
			//var refStr = "/" + gameIds[i] + "_2018_1/p_info/" + p_id + "/";
			var refStr = "/" + gameIds[i] + "_2016_3_c/p_info/" + p_id + "/";
			var currGameId = gameIds[i];

			var gameRef = firebase.database().ref(refStr);
			var gamePromise = gameRef.once('value').then(function(GameSnapshot){
				return GameSnapshot.exists();
			});
			gamePromises.push(gamePromise);
		} else {
			gamePromises.push(true);
		}
	}
	var otherGamesPromise = Promise.all(gamePromises).then(function(results){
		for (j=0;j<gameIds.length;j++){
			if(results[j]){
				otherGames.push(gameIds[j]);
			}
		}
		return otherGames;
	});
	return otherGamesPromise;
}

function getEventById(dbRefStr,tourneyId){
	var refStr = dbRefStr+'/tourneys/'+tourneyId;

	var eventRef = firebase.database().ref(refStr);
	var eventQuery = eventRef.once('value').then(function(EventSnapshot){
		return EventSnapshot.val();
	});

	return eventQuery;
}

function placementsToEvents(placements,gameId){
	var eventPromises = [];
	for (i=0;i<placements.length;i++){
		eventId = placements[i].key;
		//var refStr = "/"+gameId+"_2018_1/tourneys/"+eventId;
		var refStr = "/"+gameId+"_2016_3_c/tourneys/"+eventId;

		var eventRef = firebase.database().ref(refStr)
		var eventQuery = eventRef.once('value').then(function(EventSnapshot){
			pyDate = EventSnapshot.child('date').val()
			jsDate = new Date(pyDate[0],pyDate[1]-1,pyDate[2])
			return [EventSnapshot.child('name').val(),jsDate,EventSnapshot.child('numEntrants').val(),EventSnapshot.child('active').val(),EventSnapshot.child('url_banner').val(),EventSnapshot.child('slug').val(),EventSnapshot.key];
		});
		eventPromises.push(eventQuery);
	}
	return eventPromises;
}

function snapshotToSearchbar(snapshot){
	var returnArr = [];
	snapshot.forEach(function(childSnapshot) {
		var player = {name: childSnapshot.child('tag').val(),
					  id: childSnapshot.key,
					  team: childSnapshot.child('team').val(),
					  fullname: childSnapshot.child('firstname').val() + ' ' + childSnapshot.child('lastname').val(),
					  aliases: childSnapshot.child('aliases').val()};

		returnArr.push(player)
	});
	return returnArr;
}

// returns the specified css property of a given page element
function css( element, property ) {
    return window.getComputedStyle( element, null ).getPropertyValue( property );
}

// returns the ordinal suffix of a number (-st,-nd,-rd,-th)
function ordinalSuffixOf(i) {
    var j = i % 10,
        k = i % 100;
    if (j == 1 && k != 11) {
        return "st";
    }
    if (j == 2 && k != 12) {
        return "nd";
    }
    if (j == 3 && k != 13) {
        return "rd";
    }
    return "th";
}

// returns the given tag, formatted for web (changing bracket type if is a 'transliterated cjk' tag)
function handleTransTag(tag){
	if (tag.includes('<')){
	    return '『'+tag.slice(1,tag.length-1)+'』';
	  } else {
	  	return tag
	  }
}

// returns the given tag, formatted for web (removing brackets if is a 'transliterated cjk' tag)
function handleTransTagEN(tag){
	if (tag.includes('<')){
	    return tag.slice(1,tag.length-1);
	  } else {
	  	return tag
	  }
}