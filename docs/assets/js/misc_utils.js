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
		case 1386:
			return 'Ultimate';
			break;
	}
}

function getGameIconPath(gameId){
	switch(gameId) {
		case 1:
			return "/assets/images/game_icons/36px-SSBM_Icon.png"
			break;
		case 2:
			return "/assets/images/game_icons/36px-PM_Icon.png"
			break;
		case 3:
			return "/assets/images/game_icons/36px-SSB4_Icon.png"
			break;
		case 4:
			return "/assets/images/game_icons/36px-SSB64_Icon.png"
			break;
		case 5:
			return "/assets/images/game_icons/36px-SSBB_Icon.png"
			break;
		case 1386:
			return "/assets/images/game_icons/36px-SSBU_Icon.png"
			break;
	}
}

function snapshotToArray(snapshot,attr="val") {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
    	if (attr == "val") {
	        var item = childSnapshot.val();
		} else if (attr == "key") {
        	var item = childSnapshot.key;
        } else if (attr == "both") {
        	var item = childSnapshot.val();
        	item.key = childSnapshot.key;
        }
        returnArr.push(item);
    });
    return returnArr;
}

function otherGameActivity(p_id,game_id){
	var gameIds = [1,2,3,4,5,1386];
	var gamePromises = [];
	var otherGames = [];
	for (i=0;i<gameIds.length;i++){
		if (gameIds[i] != game_id){
			var refStr = "/" + gameIds[i] + "_2018_1/p_info/" + p_id + "/";
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
		//console.log(results);
		for (j=0;j<gameIds.length;j++){
			if(results[j]){
				otherGames.push(gameIds[j]);
			}
		}
		return otherGames;
	});

	return otherGamesPromise;
}

function snapshotToSearchbar(snapshot){
	var returnArr = [];
	snapshot.forEach(function(childSnapshot) {
		var player = {name: childSnapshot.child('tag').val(),
					  id: childSnapshot.key,
					  aliases: childSnapshot.child('aliases').val()};

		returnArr.push(player)
	});
	return returnArr;
}