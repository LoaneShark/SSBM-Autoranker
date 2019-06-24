// Custom plugin to only render tooltips for certain datasets (so as to not render for initialSkillset)
$(window).on('load',function(){
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
});
// Custom plugin to plot a mathematical function (in our case sigmoid)
var funcPlugin = {
    beforeInit: function(chart) {
        // We get the chart data
        var data = chart.config.data;

        // For every dataset after the first one...
        for (var i = 1; i < data.datasets.length; i++) {

            // For 1000 points between [0,1]
            var numPts = 100;
            var stepSize = 1/numPts;
            for (var j = 0; j < 1+stepSize; j+=stepSize) {

                // We get the dataset's function and calculate the value
                var fct = data.datasets[i].function,
                    x = j,
                    y = fct(x);
                // Then we add the value to the dataset data
                data.datasets[i].data.push({'x':x,'y':y});
            }
        }
    }
};

// draw skill history chart
function skillChart(skillHistory,tourneySnapshot,placementSnapshot,gameId,type='elo'){
	var ctx = $('#'+type+'_chart')[0].getContext('2d');
	//var ctx = $('#tempChart');
	var skillset = [];
	var initialSkillset = [];
	var rankPeriod = [];
	var postPeriod = [];
	if (type == 'mainrank'){
		var timeScale = 'year'
		var skillYears = Object.keys(skillHistory)
		//skillKeys = Object.keys(skillHistory[skillYear])
		for (j=0;j<skillYears.length;j++){
			var skillYear = skillYears[j];
			var yearRankNames = Object.keys(skillHistory[skillYear]);
			for (k=0;k<yearRankNames.length;k++){
				rankName = yearRankNames[k];
				rankVal = skillHistory[skillYear][rankName][0];
				var jsDate = new Date(skillYear,k*(12/yearRankNames.length),1);

				// prevents plotting of the same ranking twice -- needed until I fix my db
				if (!skillset.some(e => e.label === rankName)) {
					skillset.push({'t': jsDate, 'y': rankVal, 'label': rankName, 'present': true, 'idx':j});
				}

			}
			//skillval = skillHistory[skillYear][skillKeys[j]][0];
			// var jsDate = skillYear;

		}
		//console.log(skillset)
	} else if (type == 'srank'){
		var skillTourneys = Object.keys(skillHistory)
		//console.log(skillHistory)
		var timeScale = 'month';
		var placementArray = [];
		var tempArray = [];
		placementSnapshot.forEach(function(childSnapshot){
			placementArray.push(childSnapshot.key);
		});
		for (j=0;j<skillTourneys.length;j++){
			var t_id = skillTourneys[j];
			var skillval = skillHistory[t_id];

			var t_date = tourneySnapshot.child(t_id.toString()).child('date').val();
			var t_name = tourneySnapshot.child(t_id.toString()).child('name').val();
			var t_index = tourneySnapshot.child(t_id.toString()).child('index').val();
			var jsDate = new Date(t_date[0],t_date[1]-1,t_date[2]);

			// add to skillset
			var attendance = placementArray.includes(t_id);
			skillset.push({'t': jsDate, 'y': skillval, 'label':t_name, 'present':attendance, 'idx':t_index});
		}
		//const skillsetCopy = Object.assign({},skillset);
		//console.log(skillsetCopy)
		var totalLen = skillset.length;
	} else {
		placementSnapshot.forEach(function(childSnapshot){
			var t_id = childSnapshot.key;
			var timeScale = 'month'
			var skillval = skillHistory[t_id];
			if (type == 'glicko'){
				skillval = skillval[0];
			}
			var t_date = tourneySnapshot.child(t_id.toString()).child('date').val();
			var t_name = tourneySnapshot.child(t_id.toString()).child('name').val();
			var t_index = tourneySnapshot.child(t_id.toString()).child('index').val();
			var jsDate = new Date(t_date[0],t_date[1]-1,t_date[2]);

			// add to skillset
			skillset.push({'t': jsDate, 'y': skillval, 'label':t_name, 'present':true, 'idx':t_index});
		});
	}
	// return null if player is inactive
	if (skillset.length == 0){
		return null;
	}
	skillset.sort(function(a,b){
		return a.idx-b.idx;
	})

	var legendColors = chartColorsFromType(type);
	var todayDate = new Date();
	if (type != 'srank'){
		var firstEvent = skillset[0]
	} else { // get "first event" of the "current" section of the db
		var firstEvent = null;
		var srankOldSkill = 1.;
		for (ei=0;ei<skillset.length;ei++){
			if (firstEvent == null && skillset[ei].present){
				firstEvent = skillset[ei];
				if (ei > 0){ // get the skill value at the final "non-current" event (as the "initial" skill) 
					srankOldSkill = skillset[ei-1].y;
				}
			}
		}
		if (firstEvent == null){ // handle error cases
			firstEvent = skillset[0]
		}
	}
	var lastEvent = skillset[skillset.length-1];
	var initialDate = new Date(firstEvent.t.getFullYear(),Math.max(firstEvent.t.getMonth()-1,0),1);
	var yBounds = getYAxisBounds(gameId,type);
	var datasetTooltipIndices = [0];

	var srankPointBackgrounds = [];
	var srankPointBackgrounds = [];
	var srankCurrentBackgrounds = [];
	var srankUnrankedBackgrounds = [];
	var srankBgs = [srankPointBackgrounds,srankPointBackgrounds,srankCurrentBackgrounds,srankUnrankedBackgrounds];
	// fill in "skill" before being placed,ranked (dashed line)
	if (type == 'srank'){
		initialSkillset.push({'t':initialDate,'y':srankOldSkill,'label':'','present':false});
		initialSkillset.push({'t':firstEvent.t,'y':firstEvent.y,'label':'','present':true});
	} else if (type == 'elo' || type == 'glicko' || type == 'trueskill'){
		initialSkillset.push({'t':initialDate,'y':1500,'label':'','present':false})
		initialSkillset.push({'t':firstEvent.t,'y':firstEvent.y,'label':'','present':true});
	}
	initialSkillset.sort(function(a,b){
		return a.t-b.t;
	})
	// separate out the period before being ranked from the rest of the sets
	if (type == 'srank'){
		//console.log(skillset)
		if (srankOldSkill == 1){
			var showRankPeriod = true;
			var datasetTooltipIndices = [0,3]
		} else {
			var showRankPeriod = false;
			var datasetTooltipIndices = [0]
		}
		var maxRankLen = 3;
		var rankLen = Math.min(maxRankLen,skillset.length);
		r_i = 0;
		for (i=0;i<rankLen;i++){
			// in the event they are not done being ranked yet
			if (skillset.length == 0){
				continue;
			} else {
				// if present at this event, add to "rank period"
				if (skillset[0].present){
					if (i<rankLen-1){
						var rankEvent = skillset.shift();
						rankPeriod.push({'t':rankEvent.t,'y':rankEvent.y,'label':rankEvent.label,'present':rankEvent.present});
					} else {
						rankPeriod.push({'t':skillset[0].t,'y':skillset[0].y,'label':skillset[0].label,'present':skillset[0].present});
					}
				// otherwise add other events and extend "rank period" (so we get [rankLen] "present" events to complete ranking period)
				} else {
					i -= 1;
					if (i<rankLen-1){
						var rankEvent = skillset.shift();
						//rankPeriod.push({'t':rankEvent.t,'y':rankEvent.y,'label':rankEvent.label,'present':rankEvent.present});
					} else {
						rankPeriod.push({'t':skillset[0].t,'y':skillset[0].y,'label':skillset[0].label,'present':skillset[0].present});
					}
				}
			}
		}
		// if they already had a ranked skill, shift them back into skillset (had to do it this way for some reason)
		if (!(showRankPeriod)){
			for (i=0;i<rankLen;i++){
				if (rankPeriod.length > 0){
					skillset.unshift(rankPeriod.pop());
				}
			}
		}
	}
	//const rankPeriodCopy = Object(rankPeriod)
	//console.log(rankPeriodCopy)
	// add a dotted line from their last event to today's date
	if (skillset.length == 0){
		if (rankPeriod.length == 0){
			return null; // if both are empty, this is an inactive player
		} else {
			lastEvent = rankPeriod[rankPeriod.length-1];
		}
	} else {
		lastEvent = skillset[skillset.length-1];
	}
	if (type != 'mainrank'){
		postPeriod.push({'t':lastEvent.t,'y':lastEvent.y,'label':'','present':lastEvent.present})
		postPeriod.push({'t':todayDate,'y':postPeriod[0].y,'label':'','present':false})
	}

	var myChart = new Chart(ctx, {
		type: 'line',
		data: {
			datasets: [{
				label: chartLabelFromType(type,gameId),
				backgroundColor: legendColors[0][1],
				borderColor: legendColors[0][0],
				pointBackgroundColor: srankBgs[0],
				//pointBorderColor: srankBgs[0],
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
				pointBackgroundColor: srankBgs[3],
				//pointBorderColor: srankBgs[3],
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
				mode: 'point',
				onlyShowForDatasetIndex: datasetTooltipIndices,
				displayColors: false,
				callbacks: {
					title: function(tooltipItem,data){
						labelString = tooltipItem[0].xLabel;
						var eventDate = new Date(labelString.slice(0,labelString.length-17));
						var eventDateString = eventDate.toDateString();
						return eventDateString.slice(0,eventDateString.length-4);
					},
					beforeLabel: function(tooltipItem,data){
						var eventName = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].label;
						var currSkill = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y;
						// avoid repeat tooltips where datasets transition (unranked -> ranked)
						if (tooltipItem.datasetIndex == 3){
							if (tooltipItem.index == data.datasets[3].data.length-1){
								if (data.datasets[0].data.length >= 1){
									return null;
								}
							}
						}
						if (type == 'srank'){
							currSkill = Math.round(currSkill*1000.0)/1000.0;
						} else {
							currSkill = Math.round(currSkill);
						}
						return eventName+"\n"+currSkill;
					},
					label: function(tooltipItem,data){
						// avoid repeat tooltips where datasets transition (unranked -> ranked)
						if (tooltipItem.datasetIndex == 3){
							if (tooltipItem.index == data.datasets[3].data.length-1){
								if (data.datasets[0].data.length >= 1){
									return null;
								}
							}
							return '[Unranked]'
						}
						if (tooltipItem.index == 0){
							if (type == 'srank'){
								var oldSkill = srankOldSkill;
							} else if (type == 'mainrank'){
								return 'NEW!'
								var oldSkill = getMainrankSize(gameId);
							} else {
								var oldSkill = 1500.0;
							}
						} else {
							var oldSkill = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index-1].y;
						}
						var skillDel = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y - oldSkill;
						if (type == 'srank'){
							skillDel = Math.round(1000.0*skillDel)/1000.0;
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
								return 'rgb(255,255,255)';
								var oldSkill = 999999;
							}else if (type == 'srank'){
								var oldSkill = srankOldSkill;
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
							return 'rgb(252,86,86)';
						} else if (skillDel == 0) {
							//return 'rgb(96,96,242)';
							return 'rgb(255,255,255)';
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
	                    unit: timeScale,
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
	if (type == 'srank'){
		// change fill for "not present" events for s-rank
		datasetsToUpdate = [0,3];
		for (ds = 0; ds<datasetsToUpdate.length; ds++){
			ds_i = datasetsToUpdate[ds];
			bgArr = srankBgs[ds_i];
			for (p_i=0; p_i<myChart.data.datasets[ds_i].data.length; p_i++){
				if (myChart.data.datasets[ds_i].data[p_i].present){
					bgArr.push(legendColors[ds_i][1]);
					//myChart.data.datasets[ds_i].data[p_i]
				} else {
					bgArr.push('rgb(255, 255, 255, 1)')
				}
			}
		}
	} else { // everyone gets default bg if not srank
		bgArr = srankBgs[0]
		for (p_i=0; p_i<myChart.data.datasets[0].data.length; p_i++){
			if (myChart.data.datasets[0].data[p_i].present){
				bgArr.push(legendColors[0][1]);
				//myChart.data.datasets[0].data[p_i]
			} else {
				bgArr.push('rgb(255, 255, 255, 1)')
			}
		}
	}
	return myChart;
}

// draw winprobs/sigmoid regression chart
function sigmoidChart(PlayerSnapshot,infoRefStr,sigmoid,winprobs,pSkill){
	// sigmoid = [x0,g,c,k]
	var ctx = $('#srank_sigmoid')[0].getContext('2d');
	//console.log(sigmoid)
	if (pSkill==1 && sigmoid[0]==0.5 && sigmoid[1]==0 && sigmoid[2]==1 && sigmoid[3]==5){
		var rankedSigmoid = false;
		var sigmoidBorderDash = [5,5];
	} else {
		var rankedSigmoid = true;
		var sigmoidBorderDash = [5,0];
	}

	var winprobPromises = winprobsToChartArray(infoRefStr,winprobs);

	Promise.all(winprobPromises).then(function(winprobDataset){

		winprobDataset.sort(function(a,b){
			return a.x-b.x;
		})

		var myChart = new Chart(ctx, {
			plugins: [funcPlugin],
			type: 'mixed',
			data: {
				datasets: [{
					label: 'H2H',
					type: 'scatter',
					//backgroundColor: legendColors[0][1],
					//borderColor: legendColors[0][0],
					pointBackgroundColor: 'rgb(0,0,240,1)',
					pointBorderColor: 'rgb(0,0,240,1)',
					fill: false,
					//function: function(x){
					//	return x
					//},
					showLine: false,
					data: winprobDataset
					//data: [{x:1,y:1},{x:0,y:0}]
				},{
					label: 'Sigmoid',
					type: 'line',
					backgroundColor: 'rgb(0,200,50,0.1)',
					borderColor: 'rgb(0,200,50,1)',
					borderDash: sigmoidBorderDash,
					pointRadius: 0,
					//pointBackgroundColor: srankBgs[0],
					//pointBorderColor: srankBgs[0],
					fill: rankedSigmoid,
					function: function(x){
						return (sigmoid[2] / (1 + Math.pow(Math.E,-sigmoid[3]*10*(x-sigmoid[0])))) + sigmoid[1]*(1-sigmoid[2]);
					},
					data: []
				}]
			},
			options: {
				responsive: true,
				legend: false,
				title: {
					display: true,
					text: 'S-Rank Win Probability'
				},
				tooltips: {
					onlyShowForDatasetIndex: [0],
					displayColors: false,
					itemSort: function(a,b){
						// sorts tooltip items by x value (s-rank)
						return a.x < b.x;
					},
					callbacks: {
						title: function(tooltipItem,data){
							// currently never hits the 'else' statement
							if (tooltipItem.length >= 1){
								return 'Winrate: '+Math.round(data.datasets[tooltipItem[0].datasetIndex].data[tooltipItem[0].index].y*100) + '%';
							} else {
								return data.datasets[tooltipItem[0].datasetIndex].data[tooltipItem[0].index].label;
							}
						},
						/*beforeLabel: function(tooltipItem,data){
							return data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].label;
							// never reaches below
							return 'S-Rank: ' + Math.round(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].x*1000)/1000;
						},*/
						label: function(tooltipItem,data){
							if (tooltipItem.datasetIndex <= 0){
								var oppTag = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].label;
								var winrate = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].y;
								var n = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].n;
								var skill = Math.round(data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index].x*1000)/1000;
								return ''+skill+': '+oppTag+' ('+ winrate*n + '-' + (n-(winrate*n))+ ')';
							}
						}
					},
					mode: 'point'//,
					//intersect: true
				},
		        scales: {
		            xAxes: [{
		                type: 'linear',
		            	ticks: {
		            		suggestedMin: -0.1,
		            		suggestedMax: 1.1
		            	}
		            }],
		            yAxes: [{
		            	type: 'linear',
		            	ticks: {
		            		suggestedMin: -0.1,
		            		suggestedMax: 1.1
		            	}
		            }]
		        }
			}
		});
		return myChart;
	});
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

function winprobsFromH2H(h2h){
	var winps = {};
	var oppList = Object.keys(h2h)

	for(i=0;i<oppList.length;i++){
		var oppId = oppList[i];
		var winCount = h2h[oppId][0];
		var setCount = h2h[oppId][0]+h2h[oppId][1];
		winps[oppId] = [winCount/setCount,setCount];
	}
	return winps;
}

function winprobsFromRecords(playerWins,playerLosses){
  var h2hAll = {};

  if (playerWins != null){
  	var wOppIds = Object.keys(playerWins);
  	for(j=0;j<wOppIds.length;j++){
  	  var winOpp = wOppIds[j];
      if (!(h2hAll.hasOwnProperty(winOpp))){
        h2hAll[winOpp] = [0.0,0.0];
      }
      // for each event they've beaten opp at
      Object.keys(playerWins[winOpp]).forEach(function(oppMatchupEventId){
      	// add number of sets won
      	h2hAll[winOpp][0] += Object.keys(playerWins[winOpp][oppMatchupEventId]).length;
      });
  	}
  }
  if (playerLosses != null){
  	var lOppIds = Object.keys(playerLosses);
  	for(k=0;k<lOppIds.length;k++){
  	  var lossOpp = lOppIds[k];
      if (!(h2hAll.hasOwnProperty(lossOpp))){
        h2hAll[lossOpp] = [0.0,0.0];
      }
      // for each event they've lost to opp at
      Object.keys(playerLosses[lossOpp]).forEach(function(oppMatchupEventId){
      	// add number of sets lost
      	h2hAll[lossOpp][1] += Object.keys(playerLosses[lossOpp][oppMatchupEventId]).length;
      });
  	}
  }
  return winprobsFromH2H(h2hAll);
}

function winprobsToChartArray(infoRefStr,winprobs){
	var returnArr = [];
	var oppIds = Object.keys(winprobs);
	var testArr = [];

	/*for(i=0;i<oppIds.length;i++){
		var oppId = oppIds[i];
		var oppInfoRefStr = infoRefStr + oppId;
		var oppInfoRef = firebase.database().ref(oppInfoRefStr);
		//returnArr.push({'y':winprobs[oppId][0],'p_id':oppId})
		oppInfoQuery = oppInfoRef.once('value').then(function(oppSnapshot){
			testArr.push(oppSnapshot);
			//returnArr[i]['x'] = oppSnapshot.child('srank').val();
			//returnArr[i]['label'] = oppSnapshot.child('tag').val();
			//returnArr[i]['active'] = oppSnapshot.child('active').val();
			returnArr.push({'x':oppSnapshot.child('srank').val(), 'y':winprobs[oppSnapshot.key][0], 'label':oppSnapshot.child('tag').val(), 'active':oppSnapshot.child('active').val(), 'p_id':oppSnapshot.key});
		});
	}*/

	var datasetPromise = oppIds.map(oppId => {
		var oppInfoRefStr = infoRefStr + oppId;
		var oppInfoRef = firebase.database().ref(oppInfoRefStr);
		var oppInfoQuery = oppInfoRef.once('value').then(function(oppSnapshot){
			testArr.push(oppSnapshot);
			//returnArr[i]['x'] = oppSnapshot.child('srank').val();
			//returnArr[i]['label'] = oppSnapshot.child('tag').val();
			//returnArr[i]['active'] = oppSnapshot.child('active').val();
			return{'x':oppSnapshot.child('srank').val(), 'y':winprobs[oppSnapshot.key][0], 'n':winprobs[oppSnapshot.key][1], 'label':oppSnapshot.child('tag').val(), 'active':oppSnapshot.child('active').val(), 'p_id':oppSnapshot.key};
		});
		returnArr.push(oppInfoQuery);
	});
	return returnArr;
}