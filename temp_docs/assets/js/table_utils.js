function snapshotToArray(snapshot) {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
        var item = childSnapshot.val();
        item.key = childSnapshot.key;

        returnArr.push([item]);
    });
    return returnArr;
}
// given a snapshot of p_infos for a certain metric (e.g. when fetching top ranked players)
// return a 2-D array of the table data
function snapshotToTable(snapshot) {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
    	var player = [];

	    player.push(childSnapshot.child('team').val());
	    player.push(childSnapshot.child('tag').val());
	    //player.push(Math.round(childSnapshot.child('off_rank').val()));
	    player.push(Math.round(childSnapshot.child('elo').val()));
	    player.push(Math.round(childSnapshot.child('srank').val() * 10000.0) / 100.0);
	    player.push(Math.round(childSnapshot.child('elo').val()));
	    player.push(Math.round(childSnapshot.child('glicko').val()[0]));

    	returnArr.push(player);
    });

    return returnArr;
}
// given a player's p_info snapshot, returns their data table result
function snapshotToRankLine(snapshot) {
    var returnArr = [];
    returnArr.push(snapshot.child('team').val());
    returnArr.push(snapshot.child('tag').val());
    //returnArr.push(Math.round(snapshot.child('off_rank').val()));
	returnArr.push(Math.round(snapshot.child('elo').val()));
    returnArr.push(Math.round(snapshot.child('srank').val() * 10000.0) / 100.0);
    returnArr.push(Math.round(snapshot.child('elo').val()));
    returnArr.push(Math.round(snapshot.child('glicko').val()[0]));

    return returnArr;
}