function skillChart(skillHistory,tourneySnapshot,placementSnapshot,gameId,type='elo'){
	var ctx = $('#'+type+'-chart')[0].getContext('2d');
	//var ctx = $('#tempChart');

	var skillset = [];
	if (type == 'mainrank'){
		var skillKeys = Object.keys(skillHistory)
		//skillKeys = Object.keys(skillHistory[skillYear])
		for (j=0;j<skillKeys.length;j++){
			var rankName = skillKeys[j];
			var skillval = skillHistory[rankName][0];
			//skillval = skillHistory[skillYear][skillKeys[j]][0];
			var jsDate = new Date(2016+j,0,1);
			// var jsDate = skillYear;

			skillset.push({'t': jsDate, 'y': skillval, 'label': rankName});
		}
	} else {
		placementSnapshot.forEach(function(childSnapshot){
			var t_id = childSnapshot.key;
			var skillval = skillHistory[t_id];
			if (type == 'glicko'){
				skillval = skillval[0];
			}
			var t_date = tourneySnapshot.child(t_id.toString()).child('date').val();
			var t_name = tourneySnapshot.child(t_id.toString()).child('name').val();
			var jsDate = new Date(t_date[0],t_date[1]-1,t_date[2]);

			//console.log(t_id);
			//console.log(tourneySnapshot.child(t_id.toString()).child('name').val());
			//console.log(jsDate);
			//console.log(skillval);
			skillset.push({'t': jsDate, 'y': skillval, 'label':t_name});
		});
	}
	skillset.sort(function(a,b){
		return a.t-b.t;
	})

	var legendColors = chartColorsFromType(type);

	var myChart = new Chart(ctx, {
		type: 'line',
		data: {
			datasets: [{
				label: chartLabelFromType(type,gameId),
				backgroundColor: legendColors[1],
				borderColor: legendColors[0],
				steppedLine: true,
				fill: false,
				data: skillset
			}]
		},
		options: {
			responsive: true,
			//legend: false,
			elements: {
				line: {
					tension: 0
				}
			},
			tooltips : {
				displayColors: false,
				callbacks: {
					beforeLabel: function(tooltipItem,data){
						var eventName = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].label;
						var currSkill = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y;
						if (type == 'srank'){
							currSkill = Math.round(currSkill*100.0)/100.0;
						} else {
							currSkill = Math.round(currSkill);
						}
						return eventName+"\n"+currSkill;
					},
					label: function(tooltipItem,data){
						if (tooltipItem.index == 0){
							if (type == 'srank'){
								var oldSkill = 1.0;
							} else if (type == 'mainrank'){
								switch (gameId){
									case 1:
										var oldSkill = 100;
										break;
									case 2:
										var oldSkill = 50;
										break;
									case 3:
										var oldSkill = 50;
										break;
									case 4:
										var oldSkill = 64;
										break;
									case 5:
										var oldSkill = 100;
										break;
									case 1386:
										var oldSkill = 50;
										break;
								}
							} else {
								var oldSkill = 1500.0;
							}
						} else {
							var oldSkill = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index-1].y;
						}
						var skillDel = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y - oldSkill;
						if (type == 'srank'){
							skillDel = Math.round(100.0*skillDel)/100.0;
						} else {
							skillDel = Math.round(skillDel);
						}
						if (skillDel > 0){
							return '+'+skillDel;
						} else if (skillDel < 0) {
							return skillDel.toString();
						} else if (skillDel == 0) {
							return '~'+skillDel;
						} else {
							return 'Error';
						}
					},
					labelTextColor: function(tooltipItem,data){
						if (tooltipItem.index == 0){
							var oldSkill = 1500.0;
						} else {
							var oldSkill = data.data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index-1].y;
						}
						var skillDel = Math.round(data.data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y - oldSkill);
						if (type == 'mainrank' || type == 'srank'){
							skillDel = -skillDel;
						}
						if (skillDel > 0){
							return 'rgb(96,242,96)';
						} else if (skillDel < 0) {
							return 'rgb(242,96,96)';
						} else if (skillDel == 0) {
							return 'rgb(96,96,242)';
						} else {
							return 'rgb(255,255,255)';
						}
					}
				}
			},
	        scales: {
	            xAxes: [{
	                type: 'time',
	                time: {
	                    unit: 'month'
	                }
	            }]
	        }
	    }
	});
	return myChart;
}

function snapshotToSkillHistory(skillRefStr,playerId,skillTypes=['mainrank','elo','glicko','srank','trueskill']){
	var returnArr = [];
	for (j=0;j<skillTypes.length;j++){
		skillName = skillTypes[j];
		skillRef = firebase.database().ref(skillRefStr+skillName+'/'+playerId);
		skillQuery = skillRef.once('value').then(function(skillSnapshot){
			return skillSnapshot.val();
		});
		returnArr.push(skillQuery);
	}
	return returnArr;
}

function chartLabelFromType(type='elo',gameId){
	switch (type) {
		case 'elo':
			return 'Elo';
			break;
		case 'glicko':
			return 'Glicko-2';
			break;
		case 'mainrank':
			switch (gameId){
				case 1:
					return 'MPGR / SSBMRank';
					break;
				case 2:
					return 'PMRank';
					break;
				case 3:
					return 'PGR';
					break;
				case 4:
					return '64 League Rankings'
					break;
				case 5:
					return 'SSBBRank';
					break;
				case 1386:
					return 'PGRU';
					break;
			}
			break;
		case 'srank':
			return 'S-Rank';
			break;
		case 'trueskill':
			return 'TrueSkill';
			break;
	}
}

function chartColorsFromType(type='elo'){
	switch (type){
		case 'mainrank':
			return ['rgb(30, 173, 234)','rgb(40, 183, 244)'];
			break;
		case 'elo':
			return ['rgb(164,247,204)','rgb(174,255,214)'];
			break;
		case 'glicko':
			return ['rgb(242, 96, 96)','rgb(252, 106, 106)'];
			break;
		case 'trueskill':
			return ['rgb(204, 204, 10)','rgb(214, 214, 20)'];
			break;
		case 'srank':
			return ['rgb(139, 55, 229)','rgb(149, 65, 239)'];
			break;
	}
}