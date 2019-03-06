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
	};
}

function snapshotToArray(snapshot) {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
        var item = childSnapshot.val();
        item.key = childSnapshot.key;

        returnArr.push([item]);
    });
    return returnArr;
}