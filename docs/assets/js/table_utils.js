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
	    player.push(Math.round(childSnapshot.child('srank').val() * 1000.0) / 1000.0);
	    player.push(Math.round(childSnapshot.child('elo').val()));
	    player.push(Math.round(childSnapshot.child('glicko').val()[0]));
        player.push(Math.round(childSnapshot.child('trueskill/expose').val()));
        player.push(Math.round(childSnapshot.child('glixare').val()));
        player.push(Math.round(childSnapshot.key));

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
    returnArr.push(Math.round(snapshot.child('srank').val() * 1000.0) / 1000.0);
    returnArr.push(Math.round(snapshot.child('elo').val()));
    returnArr.push(Math.round(snapshot.child('glicko').val()[0]));
    returnArr.push(Math.round(snapshot.key));

    return returnArr;
}

// given a snapshot of the p_infos, returns their regional data table result
// fix this once regions are better imported and tracked in p_info than they are now
function snapshotToRegionTable(snapshot,continent) {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
        var player = [];
        var playerRegion = childSnapshot.child('region/1').val();
        var playerMatch = false;
        if (continent == 'america'){
            if (playerRegion == 'USA' || playerRegion == 'Mexico' || playerRegion == 'Canada' || playerRegion == 'NA' || playerRegion == 'North America' || playerRegion == 'America'){
                playerMatch = true;
            }
        } else if (continent == 'europe'){
            if (playerRegion == 'Europe'){
                playerMatch = true;
            }
        } else if (continent == 'asia'){
            if (playerRegion == 'Japan'|| playerRegion == 'China' || playerRegion == 'South Korea' || playerRegion == 'PRC'  || playerRegion == 'Asia'){
                playerMatch = true;
            }
        } else if (continent == 'other'){
            if (['USA','Mexico','Canada','NA','North America','Japan','China','South Korea','PRC','Asia','Europe','America'].indexOf(playerRegion) <= -1){
                playerMatch = true;
            }
        }

        if (playerMatch){
            player.push(childSnapshot.child('team').val());
            player.push(childSnapshot.child('tag').val());
            if (childSnapshot.child('mainrank').exists()){
                player.push(Math.round(childSnapshot.child('mainrank').val()));
            } else {
                player.push('N/A');
            }
            //player.push(Math.round(childSnapshot.child('elo').val()));
            player.push(Math.round(childSnapshot.child('srank').val() * 1000.0) / 1000.0);
            player.push(Math.round(childSnapshot.child('srank-rnk').val()));
            if ((continent == 'america' && playerRegion != 'America') || playerRegion == 'Japan'){
                player.push(playerRegion);
            } else {
                playerRegion = childSnapshot.child('region/2').val();
                if (playerRegion == 'D.R.'){
                    playerRegion = 'Dominican Republic'
                }
                player.push(playerRegion);
            }
            player.push(Math.round(childSnapshot.key));

            returnArr.push(player);
        }

    });

    return returnArr.slice(0,10);
}