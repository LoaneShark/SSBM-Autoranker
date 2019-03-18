// given a snapshot of p_infos for a certain metric (e.g. when fetching top ranked players)
// return a 2-D array of the table data
function snapshotToTable(snapshot) {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
    	var player = [];

	    player.push(childSnapshot.child('team').val());
	    player.push(childSnapshot.child('tag').val());
        if (childSnapshot.child('mainrank').exists()){
            player.push(Math.round(childSnapshot.child('mainrank').val()));
        } else {
            player.push('N/A');
        }
	    //player.push(Math.round(childSnapshot.child('elo').val()));
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
        if (snapshot.child('mainrank').exists()){
            returnArr.push(Math.round(snapshot.child('mainrank').val()));
        } else {
            returnArr.push('N/A');
        }
	//returnArr.push(Math.round(snapshot.child('elo').val()));
    returnArr.push(Math.round(snapshot.child('srank').val() * 10000.0) / 100.0);
    returnArr.push(Math.round(snapshot.child('elo').val()));
    returnArr.push(Math.round(snapshot.child('glicko').val()[0]));

    return returnArr;
}