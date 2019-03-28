// Custom plugin to only render tooltips for certain datasets (so as to not render for initialSkillset)
Chart.plugins.register({
  // need to manipulate tooltip visibility before its drawn (but after update)
  beforeDraw: function(chartInstance, easing) {
    // check and see if the plugin is active (its active if the option exists)
    if (chartInstance.config.options.tooltips.onlyShowForDatasetIndex) {
      // get the plugin configuration
      var tooltipsToDisplay = chartInstance.config.options.tooltips.onlyShowForDatasetIndex;

      // get the active tooltip (if there is one)
      var active = chartInstance.tooltip._active || [];

      // only manipulate the tooltip if its just about to be drawn
      if (active.length > 0) {
        // first check if the tooltip relates to a dataset index we don't want to show
        if (tooltipsToDisplay.indexOf(active[0]._datasetIndex) === -1) {
          // we don't want to show this tooltip so set it's opacity back to 0
          // which causes the tooltip draw method to do nothing
          chartInstance.tooltip._model.opacity = 0;
        }
      }
    }
  }
});


function skillChart(skillHistory,tourneySnapshot,placementSnapshot,gameId,type='elo'){
	var ctx = $('#'+type+'_chart')[0].getContext('2d');
	//var ctx = $('#tempChart');

	var skillset = [];
	var initialSkillset = [];
	var rankPeriod = [];
	var postPeriod = [];
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

			// add to skillset
			skillset.push({'t': jsDate, 'y': skillval, 'label':t_name});
		});
	}
	skillset.sort(function(a,b){
		return a.t-b.t;
	})


	var legendColors = chartColorsFromType(type);
	var todayDate = new Date();
	firstEvent = skillset[0]
	lastEvent = skillset[skillset.length-1]
	var initialDate = new Date(firstEvent.t.getFullYear(),Math.max(firstEvent.t.getMonth()-1,0),1);
	var yBounds = getYAxisBounds(gameId,type);
	// fill in "skill" before being placed,ranked (dashed line)
	if (type == 'srank'){
		initialSkillset.push({'t':initialDate,'y':1.0,'label':''});
		initialSkillset.push({'t':firstEvent.t,'y':firstEvent.y,'label':''});
	} else if (type == 'elo' || type == 'glicko' || type == 'trueskill'){
		initialSkillset.push({'t':initialDate,'y':1500,'label':''})
		initialSkillset.push({'t':firstEvent.t,'y':firstEvent.y,'label':''});
	}
	initialSkillset.sort(function(a,b){
		return a.t-b.t;
	})
	// add a dotted line from their last event to today's date
	postPeriod.push({'t':lastEvent.t,'y':lastEvent.y,'label':''})
	postPeriod.push({'t':todayDate,'y':postPeriod[0].y,'label':''})
	// separate out the period before being ranked from the rest of the sets
	if (type == 'srank'){
		rankLen = Math.min(3,skillset.length);
		for (i=0;i<rankLen;i++){
			if (i<rankLen-1){
				rankEvent = skillset.shift()
				rankPeriod.push({'t':rankEvent.t,'y':rankEvent.y,'label':rankEvent.label});
			} else {
				rankPeriod.push({'t':skillset[0].t,'y':skillset[0].y,'label':skillset[0].label});
			}
		}
	}

	var myChart = new Chart(ctx, {
		type: 'line',
		data: {
			datasets: [{
				label: chartLabelFromType(type,gameId),
				backgroundColor: legendColors[0][1],
				borderColor: legendColors[0][0],
				steppedLine: true,
				fill: false,
				data: skillset
			},{
				label: chartLabelFromType(type,gameId)+' (Inferred)',
				backgroundColor: legendColors[1][1],
				borderColor: legendColors[1][0],
				steppedLine: true,
				pointRadius: 0,
				pointHoverRadius: 0,
				fill: false,
				borderDash: [5,5],
				data: initialSkillset
			},{
				label: chartLabelFromType(type,gameId)+' (Current)',
				backgroundColor: legendColors[2][1],
				borderColor: legendColors[2][0],
				steppedLine: true,
				pointRadius: 0,
				pointHoverRadius: 0,
				fill: false,
				borderDash: [5,5],
				data: postPeriod
			},{
				label: chartLabelFromType(type,gameId)+' (Unranked)',
				backgroundColor: legendColors[3][1],
				borderColor: legendColors[3][0],
				steppedLine: true,
				fill: false,
				borderDash: [5,5],
				data: rankPeriod
			}]
		},
		options: {
			responsive: true,
			legend: false,
			title: {
				display: true,
				text: chartLabelFromType(type,gameId)
			},
			elements: {
				line: {
					tension: 0
				}
			},
			hover: {
				mode: 'x'
			},
			tooltips: {
				onlyShowForDatasetIndex: [0,3],
				displayColors: false,
				callbacks: {
					title: function(tooltipItem,data){
						var eventDate = new Date(tooltipItem[0].xLabel)
						return eventDate.toDateString();
					},
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
						//console.log(tooltipItem)
						if (tooltipItem.index == 0){
							if (type == 'srank'){
								var oldSkill = 1.0;
							} else if (type == 'mainrank'){
								var oldSkill = getMainrankSize(gameId);
								return 'NEW!'
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
							if (type == 'mainrank'){
								var oldSkill = 999999;
							}else if (type == 'srank'){
								var oldSkill = 1;
							} else {
								var oldSkill = 1500.0;
							}
						} else {
							var oldSkill = data.data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index-1].y;
						}
						var skillDel = data.data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y - oldSkill;
						if (type == 'mainrank'){
							skillDel = -skillDel;
						}
						if (type == 'srank'){
							skillDel = -100.0*skillDel;
						}
						skillDel = Math.round(skillDel)
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
	                    unit: 'month',
	                    min: initialDate,
	                    max: todayDate
	                }
	            }],
	            yAxes: [{
	            	type: 'linear',
	            	ticks: {
	            		suggestedMin: yBounds[0],
	            		suggestedMax: yBounds[1]
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
			return {0:['rgb(30, 173, 234, 1)','rgb(40, 183, 244, 1)'],
					1:['rgb(30, 173, 234, 0.5)','rgb(40, 183, 244, 0.5)'],
					2:['rgb(30, 173, 234, 0.5)','rgb(40, 183, 244, 0.5)'],
					3:['rgb(30, 173, 234, 1)','rgb(40, 183, 244, 1)']};
			break;
		case 'elo':
			return {0:['rgb(144,227,184, 1)','rgb(154,247,194, 1)'],
					1:['rgb(144,227,184, 0.5)','rgb(154,247,194, 0.5)'],
					2:['rgb(144,227,184, 0.5)','rgb(154,247,194, 0.5)'],
					3:['rgb(144,227,184, 1)','rgb(154,247,194, 1)']};
			break;
		case 'glicko':
			return {0:['rgb(242, 96, 96, 1)','rgb(252, 106, 106, 1)'],
					1:['rgb(242, 96, 96, 0.5)','rgb(252, 106, 106, 0.5)'],
					2:['rgb(242, 96, 96, 0.5)','rgb(252, 106, 106, 0.5)'],
					3:['rgb(242, 96, 96, 1)','rgb(252, 106, 106, 1)']};
			break;
		case 'trueskill':
			return {0:['rgb(204, 204, 10, 1)','rgb(214, 214, 20, 1)'],
					1:['rgb(204, 204, 10, 0.5)','rgb(214, 214, 20, 0.5)'],
					2:['rgb(204, 204, 10, 0.5)','rgb(214, 214, 20, 0.5)'],
					3:['rgb(204, 204, 10, 1)','rgb(214, 214, 20, 1)']};
			break;
		case 'srank':
			return {0:['rgb(139, 55, 229, 1)','rgb(149, 65, 239, 1)'],
					1:['rgb(139, 55, 229, 0.5)','rgb(149, 65, 239, 0.5)'],
					2:['rgb(139, 55, 229, 0.5)','rgb(149, 65, 239, 0.5)'],
					3:['rgb(139, 55, 229, 1)','rgb(149, 65, 239, 1)']};
			break;
	}
}

function getMainrankSize(gameId){
	switch (gameId){
		case 1:
			return 100;
			break;
		case 2:
			return 50;
			break;
		case 3:
			return 50;
			break;
		case 4:
			return 64;
			break;
		case 5:
			return 100;
			break;
		case 1386:
			return 50;
			break;
	}

}

function getYAxisBounds(gameId,skillType){
	if (skillType == 'mainrank'){
		var minVal = 0;
		var maxVal = getMainrankSize(gameId)+1;
	} else if (skillType == 'srank'){
		var minVal = -0.05
		var maxVal = 1.05
	} else {
		var minVal = 1000
		var maxVal = 2500
	}

	return [minVal,maxVal];
}