// SEARCHBAR FUNCTIONS //
// create searchbar for player breakdowns
function buildPlayerSearchbar(gameId,prefetch=true){
  if (prefetch){
    var prefetchFileLoc = '/assets/js/prefetch/'+gameId+'_2016_3_c_prefetch.json'
    // GET FILE DATA
    $.getJSON(prefetchFileLoc, function(searchbarData){
      makePlayerSearchbar(searchbarData)
    });
  } else {
    //var searchbar_ref = firebase.database().ref('/'+gameId+'_2018_1/p_info');
    var searchbar_ref = firebase.database().ref('/'+gameId+'_2016_3_c/p_info');
    var searchbar_query = searchbar_ref.orderByChild('srank').limitToFirst(2000);
    var searchbar_contents = searchbar_query.once('value').then(function(PlayerInfoSnapshot) {
      if (PlayerInfoSnapshot.exists()) {
        var searchbar_players = snapshotToPlayerSearchbar(PlayerInfoSnapshot);
        // custom tokenizer, so that search is sensetive to gamertag, player id, prefix/sponsor, or any known aliases
        makePlayerSearchbar(searchbar_players)
      }
    });
  }
}

function makePlayerSearchbar(sbarData){
  function customTokenizer(datum) {
    var nameTokens = Bloodhound.tokenizers.whitespace(datum.name);
    var idTokens = Bloodhound.tokenizers.whitespace(datum.id);
    var teamTokens = Bloodhound.tokenizers.whitespace(datum.team);
    var returnTokens = nameTokens.concat(idTokens);
    returnTokens = returnTokens.concat(teamTokens);
    for (i=0;i<datum.aliases.length;i++){
      returnTokens = returnTokens.concat(Bloodhound.tokenizers.whitespace(handleTransTagEN(datum.aliases[i])))
    }
    return returnTokens
  }
  var searchbar_engine = new Bloodhound({
    datumTokenizer: customTokenizer,
    //datumTokenizer: Bloodhound.tokenizers.whitespace,
    queryTokenizer: Bloodhound.tokenizers.whitespace,
    identify: function(obj) {return obj.id},
    local: sbarData
  });
  searchbarTypeahead = $('#player_searchbar .typeahead').typeahead({
    hint: true,
    highlight: true,
    minLength: 1
  },{
    name: 'players',
    display: function(context){
      if (context.team != null && context.team.includes(context.query)){
        return context.name+' ('+context.team+')';
      } else {
        return context.name;
      }
    },
    displayKey: 'name',
    //limit: 10,
    source: searchbar_engine,
    templates: {
      //suggestion: ,
      notFound: ['<div class="text-muted p-2">No player found...</div>'],
      pending: ['<div class="text-muted p-2">Fetching...</div>']
    }
  });


  // progress icon BROKEN
  searchbarTypeahead.on('typeahead:initialized', function (event, data) {
     // After initializing, hide the progress icon.
     $('.tt-hint').css('background-image', '');
  });
  // Show progress icon while loading.
  $('.tt-hint').css('background-image', 'url("/assets/images/social_icons/pizza-600px.png")');
}

// returns a dataset of players to feed to searchbar
function snapshotToPlayerSearchbar(snapshot){
  var returnArr = [];
  snapshot.forEach(function(childSnapshot) {
    var player = {name: childSnapshot.child('tag').val(),
            id: childSnapshot.key,
            team: childSnapshot.child('team').val(),
            fullname: ''+childSnapshot.child('firstname').val() + ' ' + childSnapshot.child('lastname').val(),
            aliases: childSnapshot.child('aliases').val()};

    returnArr.push(player)
  });
  return returnArr;
}
// PLAYER INFO FUNCTIONS //

// populate primary player information (tag, sponsor, name, region, aliases, profile picture, activity status)
function populatePrimaryInfo(PlayerSnapshot){
    var p_tag = PlayerSnapshot.child('tag').val();
    $('#player_tag').html(p_tag);
    $('#player_team').html(PlayerSnapshot.child('team').val());
    var p_region = PlayerSnapshot.child('region').val();
    console.log(p_region)
    if (p_region[2] != 'N/A'){
      $('#player_region_div').removeClass('invisible');
      $('#player_region').html(p_region[2]);
      // draw country flag in region box
      if (p_region[1] == 'Europe' || p_region[1] == 'America'){
        var c_code = countryNameToCC(p_region[2])
      } else if (p_region[1] == 'USA'){
        var c_code = countryNameToCC('United States')
      } else {
        var c_code = countryNameToCC(p_region[1]);
      }
      if (c_code){
        $('#player_region_flag').addClass('flag-'+c_code.toLowerCase());
      } else {
        $('#player_region_flag').addClass('invisible');
      }
      if (p_region[2] == 'MD/VA'){
        $('#player_region_map').attr('src','/assets/images/region_maps/map_mdva.png')
      }
    }
    
    var propic_url = PlayerSnapshot.child('propic').val();
    // handle placeholder propic generation if they don't have one
    if (propic_url == null){
      var propic_color = PlayerSnapshot.child('color').val();
      if (!propic_color){
        //propic_color = '81daea';
        //propic_color = '40e0d0';
        propic_color = '8DB0C0';
      } else {
        if (propic_color.slice(0,1) == '#'){
          propic_color = propic_color.substr(1);
        }
      }
      // get text color based on background color
      rgb_color = hexToRGB('#'+propic_color);
      text_color = textColorFromBG(rgb_color);
      propic_url = 'https://via.placeholder.com/100/'+propic_color+'/'+text_color+'?text='+p_tag.slice(0,1);
    }
    $('#player_propic_div').html('<img src="'+propic_url+'" alt="'+p_tag+'" class="rounded-circle"/>');

    player_firstname = PlayerSnapshot.child('firstname').val();
    player_lastname = PlayerSnapshot.child('lastname').val();
    if (player_firstname){
      if (player_lastname){
        $('#player_name').html(player_firstname+' '+player_lastname);
      } else {
        $('#player_name').html(player_firstname);
      }
    } else {
      if (player_lastname){
        $('#player_name').html(player_lastname);
      } else {
        $('#player_name_div').addClass('invisible');
      }
    }
    
    var player_active = PlayerSnapshot.child('active');
    if (player_active.exists()) {
      if (player_active.val()){
        $('#player_status').html('Active');
        $('#player_status').addClass('text-success');
      } else {
        $('#player_status').html('Inactive');
        $('#player_status').addClass('text-danger');
      }
    }
    var p_aliases = PlayerSnapshot.child('aliases').val();
    if (p_aliases.length > 1){
      // filter out main tag from alias list
      p_aliases = p_aliases.filter(function(value, index, arr){
        return value != p_tag;
      });
      // convert transliterated tags to compatible format
      for (a_i=0,a_n=p_aliases.length; a_i<a_n; a_i++){
        p_aliases[a_i] = handleTransTag(p_aliases[a_i]);
      }
      $('#player_aliases').html(p_aliases.join());
      $('#player_aliases_div').removeClass('invisible');
    }
}

function populatePrimaryStatsInfo(PlayerSnapshot){
  // tag & team info
  var p_tag = PlayerSnapshot.child('tag').val();
  $('#player_tag').html(p_tag);
  $('#player_team').html(PlayerSnapshot.child('team').val());
  // create profile picture
  var propic_url = PlayerSnapshot.child('propic').val();
  var propic_color = PlayerSnapshot.child('color').val();
  if (!propic_color){
    propic_color = 'f2f2f2'
  }
  if (propic_url == null){
    propic_url = 'https://via.placeholder.com/100/81daea/'+propic_color+'?text='+p_tag.slice(0,1)
  }
  $('#player_propic_div').html('<img src="'+propic_url+'" alt="'+p_tag+'" class="rounded-circle"/>');
  // populate real name info
  player_firstname = PlayerSnapshot.child('firstname').val();
  player_lastname = PlayerSnapshot.child('lastname').val();
  if (player_firstname){
    if (player_lastname){
      $('#player_name').html(player_firstname+' '+player_lastname);
    } else {
      $('#player_name').html(player_firstname);
    }
  } else {
    if (player_lastname){
      $('#player_name').html(player_lastname);
    } else {
      $('#player_name_div').addClass('invisible');
    }
  }
  // draw country flag
  var p_region = PlayerSnapshot.child('region').val();
  console.log(p_region)
  if (p_region[2] != 'N/A'){
    $('#player_region_div').removeClass('invisible');
    $('#player_region').html(p_region[2]);
    // draw country flag in region box
    if (p_region[1] == 'Europe' || p_region[1] == 'America'){
      var c_code = countryNameToCC(p_region[2])
    } else if (p_region[1] == 'USA'){
      var c_code = countryNameToCC('United States')
    } else {
      var c_code = countryNameToCC(p_region[1]);
    }
    if (c_code){
      $('#player_region_flag').addClass('flag-'+c_code.toLowerCase());
    } else {
      $('#player_region_flag').addClass('invisible');
    }
    if (p_region[2] == 'MD/VA'){
      $('#player_region_map').attr('src','/assets/images/region_maps/map_mdva.png')
    }
  }
}

// populate social media accounts that are linked, create icons that link to them
function populateSocialMedia(PlayerSnapshot, playerId){
	acctNames = ['twitter','twitch','smashboards','ssbwiki','youtube','discord','reddit'];
    acctIcons = ['twt-512px.png','ttv-322px.jpg','sb-280px.jpg','sw-200px.png','ytb-800px.png','dcd-800px.png','rdt-256px.png']
    acctStubs = ['twitter.com/','twitch.tv/','smashboards.com/members/','ssbwiki.com/Smasher:','youtube.com/channel/','','reddit.com/u/']
    for (i=0,n=acctNames.length;i<n;i++){
      if (PlayerSnapshot.child(acctNames[i]).exists()){
        $('#player_social').append('<a href="https://'+acctStubs[i]+PlayerSnapshot.child(acctNames[i]).val()+'" target="_blank"><img src="/assets/images/social_icons/'+acctIcons[i]+'" alt="'+PlayerSnapshot.child(acctNames[i]).val()+'" style="width:32px;height:32px;padding:1px;" class="rounded"></a>');
        // show social media links section
        $('#player_social_div').removeClass('invisible')
      }
    }
    // pi KAPOW er
    if (playerId == 16342){
      var showPizza = true;
      $('#player_social').append('<a href="//axe.pizza" target="_blank"><img src="/assets/images/social_icons/pizza-600px.png" alt="axe.pizza" style="width:32px;height:32px;padding:1px;" class="rounded img-fluid"></a>')
    }
}

// populate player's presence in other game DBs
function populateOtherGames(PlayerSnapshot, playerId, gameId){
	var player_otherGamesPromise = otherGameActivity(playerId,gameId);
	player_otherGamesPromise.then(function(player_otherGames){
	  if (player_otherGames.length > 1) {
	    for (i=0,n=player_otherGames.length;i<n;i++){
	      if (player_otherGames[i] != gameId){
	        $('#player_games').append('<a href="/games/'+getGameTitle(player_otherGames[i]).toLowerCase()+'/players/#'+playerId+'"><img src="'+getGameIconPath(player_otherGames[i])+'"  alt="'+player_otherGames[i]+'" style="width:30px;height:30px;" data-toggle="tooltip" title="'+getGameTitle(player_otherGames[i])+'"></a>');
	      }
	    }
	    $('#player_games_div').removeClass('invisible');
	    $('[data-toggle="tooltip"]').tooltip();
	  }
	});
}

// populate character usage and add stock icons with usage percentage as tooltips
function populateCharacters(PlayerSnapshot, gameId){
	if (PlayerSnapshot.child('characters').exists()) {
	  var p_characters = PlayerSnapshot.child('characters').val();
	  var p_character_keys = Object.keys(p_characters);
	  var p_used_characters = [];
	  for (i=0, n=p_character_keys.length; i<n; i++){
	    var k = p_character_keys[i];
	    if (p_characters[k][0] + p_characters[k][1] > 0){
	      p_used_characters.push([k,p_characters[k][0] + p_characters[k][1]]);
	    }
	  }
	  // sort by usage
	  p_used_characters.sort(function(a,b){
	    return b[1]-a[1];
	  });
	  // get total N
	  var totalSets = p_used_characters.reduce(function(total,num){
	    return total + num[1];
	  },0);
	  // draw icons
	  if (p_used_characters.length > 0){
	    for (i=0, n=p_used_characters.length;i<n;i++){
	      // assign usage percents as tooltips
	      usagePct = Math.round(p_used_characters[i][1]*10000.0/totalSets)/100.0;
	      $('#player_characters').append(
	        '<span id="char_'+p_used_characters[i][0]+'_span" data-toggle="tooltip" title="'+usagePct+'%">' +
	          '<img id="char_'+p_used_characters[i][0]+'_img" src="'+getStockIconPath(gameId,p_used_characters[i][0])+'" alt="'+p_used_characters[i][0]+'" style="width:26px;height:26px;padding:1px;">' +
	        '</span>');
	      if (i > 0){
	        var newLine = '\n';
	      } else {
	        var newLine = '';
	      }
	      //$('#player_characters_div').attr('title',$('#player_characters_div').attr('title')+newLine+usagePct+'%')
	    }
	    $('#player_characters_div').removeClass('invisible');
	    $('[data-toggle="tooltip"]').tooltip();
	  }
	}
}

// PLAYER SKILL FUNCTIONS //

// populate skills-at-a-glance
function populateSkills(PlayerSnapshot, playerId, eloVal, eloRnkVal, glickoVal, glickoRnkVal, srankVal, srankRnkVal, mainrankVal, mainrankText){
    $('#player_elo').html(eloVal);
    $('#player_glicko').html(glickoVal);
    $('#player_srank').html(srankVal);
    $('#player_mainrank').html(mainrankText);
    //$('#player_trueskill').html(Math.round(PlayerSnapshot.child('trueskill').val()));

    // highlight skill button if top 10/100/500
    $('#mainrank_trophy').css('width',$('#player_mainrank_button').css('width'));
    $('#elo_trophy').css('width',$('#player_elo_button').css('width'));
    $('#glicko_trophy').css('width',$('#player_glicko_button').css('width'));
    $('#srank_trophy').css('width',$('#player_srank_button').css('width'));

    var skillRankVals = [eloRnkVal,glickoRnkVal,srankRnkVal,mainrankVal];
    var skillRankNames = ['elo','glicko','srank','mainrank'];
    var skillRankTiers = [5,10,20,50,100,500];
    for (i=0, n_i=skillRankVals.length;i<n_i;i++){
      for (k=0,n_k=skillRankTiers.length;k<n_k;k++){
        var rank_i = skillRankVals[i];
        var tier_k = skillRankTiers[k];

        if (tier_k <= 1){
          var icon_name = 'fa-award'
        } else {
          var icon_name = 'fa-star'
        }

        if (rank_i <= tier_k){
          $('#'+skillRankNames[i]+'_trophy').html('<i class="fas fa-xs '+icon_name+' text-sr-top'+tier_k+'"></i> Top '+tier_k);
          break;
        }
      }
    }
}
// draws the skill-over-time charts in the collapsed section of skills
function drawSkillGraphs(RecordSnapshot, playerId, skillRefStr, tourneyRefStr){
    var tourneyRef = firebase.database().ref(tourneyRefStr);
    var tourneyQuery = tourneyRef.once('value').then(function(TourneySnapshot){
      if (TourneySnapshot.exists()){

        skillTypes = ['mainrank','elo','glicko','srank'];

        var skillPromises = snapshotToSkillHistory(skillRefStr,playerId,skillTypes)
        Promise.all(skillPromises).then(function(PlayerSkills){
          for (i=0;i<skillPromises.length;i++){
            skillHistory = PlayerSkills[i];
            if (skillHistory != null){
              var timeChart = skillChart(skillHistory,TourneySnapshot,RecordSnapshot.child('placings'),gameId,skillTypes[i]);
              if (timeChart != null){
                timeChart.update();
              } else {
                // disable buttons/charts if they are inactive
                $('#player_'+skillTypes[i]+'_button').addClass('disabled');
                $('#'+skillTypes[i]+'_chart_container').addClass('invisible');
              }
            } else {
              $('#player_'+skillTypes[i]+'_button').addClass('disabled');
              $('#player_'+skillTypes[i]).html('N/A');
              $('#'+skillTypes[i]+'_chart_container').addClass('invisible');
              console.log(skillTypes[i]+' skillHistory does not exist!');
            }
          }// endfor
        });
      } else {
        console.log('TourneySnapshot does not exist!');
      }
    });
}

// HEAD TO HEAD TABLE FUNCTIONS //

// Formatting function for H2H row details 
function childFormat(childData,childOppId,eventMap,tableLabel) {
	var tableHTML = '<table id="'+tableLabel+'_vs_'+childOppId+'" class="display" style="margin:0px;">';
  tableHTML += '<thead><tr><th>Date</th><th>Result</th><th>Event</th><th>Group</th></tr></thead><tbody>'
	if ('wins' in childData[childOppId]){
    var childEventIds = Object.keys(childData[childOppId]['wins']);
		for (m=0,m_n=childEventIds.length; m<m_n; m++){
      var childEventId = childEventIds[m];
      //var eventDateStr = eventMap[childEventId]['date'].getFullYear()+'-'+eventMap[childEventId]['date'].getMonth()+'-'+eventMap[childEventId]['date'].getDay();
      var eventDateStr = eventMap[childEventId]['date'].toISOString().slice(0,10);
			tableHTML += '<tr>'+
                    '<td>'+eventDateStr+'</td>' +
                    '<td class="bg-success font-weight-bold text-light">W</td>' +
                    '<td>' + eventMap[childEventId]['name'] + '</td>' +
                    '<td></td>' +
                    '</tr>';
		}
	}
	if ('losses' in childData[childOppId]){
    var childEventIds = Object.keys(childData[childOppId]['losses']);
		for (m=0,m_n=childEventIds.length; m<m_n; m++){
      childEventId = childEventIds[m];
      //eventDateStr = eventMap[childEventId]['date'].getFullYear()+'-'+eventMap[childEventId]['date'].getMonth()+'-'+eventMap[childEventId]['date'].getDay();
      eventDateStr = eventMap[childEventId]['date'].toISOString().slice(0,10);
      tableHTML += '<tr>'+
                    '<td>'+eventDateStr+'</td>' +
                    '<td class="bg-danger font-weight-bold text-light">L</td>' +
                    '<td>' + eventMap[childEventId]['name'] + '</td>' +
                    '<td></td>' +
                    '</tr>';
		}
	}

	tableHTML += '</tbody></table>'

	return tableHTML
}

function formatPlayerEvents(PlayerEvents){
	var returnMap = {};
	for (i=0, n=PlayerEvents.length; i<n; i++){
		tourneyId = PlayerEvents[i][6];
		returnMap[tourneyId] = {};

		returnMap[tourneyId]['name'] = PlayerEvents[i][0];
		returnMap[tourneyId]['date'] = PlayerEvents[i][1];
		returnMap[tourneyId]['active'] = PlayerEvents[i][3];
		returnMap[tourneyId]['propic'] = PlayerEvents[i][4];

	}
	return returnMap;
}

// generate the h2h table and populate/enable the record-at-a-glance buttons
function populateH2H(nom=10,PlayerSnapshot, RecordSnapshot, PlayerEvents, playerRefStr, playerWins, playerLosses){
  ////var noms = [10,100,500];
  //var noms = [10,100];
  var h2h = {};

  //for (n_i=0,n_n=noms.length;n_i<n_n;n_i++){
    //var nom = noms[n_i];
    var childData = {};
    h2h['top'+nom+'w'] = 0;
    h2h['top'+nom+'l'] = 0;

    if (playerWins != null || playerLosses != null){
      var topPlayerRecords = RecordSnapshot.child('top_'+nom).val();

      // if they have any h2h records in this skill stratum
      if (topPlayerRecords){
        var topPlayerIds = Object.keys(topPlayerRecords);
        var topPlayerInfo = [];
        var nomPromise = new Promise(function(resolve,reject){
          setTimeout(function() {
            resolve(nom);
          }, 100);
        });
        topPlayerInfo.push(nomPromise);
        // iterate through records
        for (p_i=0,n=topPlayerIds.length; p_i<n; p_i++){
          var oppId = topPlayerIds[p_i];
          childData[oppId] = {'winCount':topPlayerRecords[oppId]['winCount'],'lossCount':topPlayerRecords[oppId]['lossCount']};

          // get relevant opponent p_info
          var oppInfoRefStr = playerRefStr+'/'+oppId;
          var oppInfoRef = firebase.database().ref(oppInfoRefStr);
          var oppInfoQuery = oppInfoRef.once('value').then(function(OppSnapshot){
            var tempOppId = OppSnapshot.key;
            //childData[tempOppId]['tag'] = OppSnapshot.child('tag').val();
            //childData[tempOppId]['rank'] = OppSnapshot.child('srank-rnk').val();
            return {'tag':OppSnapshot.child('tag').val(), 'id':tempOppId, 'rank':OppSnapshot.child('srank-rnk').val()}
          });
          childData[oppId]['p_info'] = oppInfoQuery
          topPlayerInfo.push(oppInfoQuery);

          //oppSkillRank = childSnapshot.child('srank-rnk').val();
          //if (playerWins != null){
          //  if (oppId in playerWins){
          if (childData[oppId]['winCount'] > 0){
            var oppWinCount = childData[oppId]['winCount']
            childData[oppId]['wins'] = playerWins[oppId];

            h2h['top'+nom+'w'] += oppWinCount
            addH2HRow('wins','top'+nom,childData,oppId);
          } else {
            var oppWinCount = 0;
          }
          if (childData[oppId]['lossCount'] > 0){
            var oppLossCount = childData[oppId]['lossCount']
            childData[oppId]['losses'] = playerLosses[oppId];

            h2h['top'+nom+'l'] += oppLossCount
            addH2HRow('losses','top'+nom,childData,oppId);
          } else {
            var oppLossCount = 0;
          }
        }
        // populate the button
        $('#top'+nom+'_h2h').html('<span class="text-success">'+h2h['top'+nom+'w']+'</span>' +
                              '<span class="text-secondary">-</span>' +
                              '<span class="text-danger">'+h2h['top'+nom+'l']+'</span>');
        // populate the percentage subtext
        var nom_winrate = h2h['top'+nom+'w']/(h2h['top'+nom+'w']+h2h['top'+nom+'l'])
        if (nom_winrate >= 0.5){
          var wr_color = 'text-success'
        } else {
          var wr_color = 'text-danger'
        }
        $('#top'+nom+'_wr').html('<span class="'+wr_color+'">'+Math.round(nom_winrate*1000)/10+'%</span>')

      // build the table
      Promise.all(topPlayerInfo).then(function(oppInfo){
        console.log('generating table: top '+oppInfo[0])
        generateH2HTable('top'+nom,PlayerEvents,childData);
        // enable the button if there is a table to view
        if (h2h['top'+nom+'w']+h2h['top'+nom+'l'] >= 0){
          $('#top'+nom+'_h2h_div').removeClass('disabled');
        }
      });

      } else { //endif records exist
        $('#top'+nom+'_h2h').html('<span class="text-secondary">0-0</span>')
      }
    // if wins AND losses are both empty
    } else {
      $('#top'+nom+'_h2h').html('<span class="text-secondary">0-0</span>')
    }

  //}
}

// make generated html table into a DataTable, with child rows etc
function generateH2HTable(tableLabel,PlayerEvents,childData){
  console.log(tableLabel)
  console.log(childData)
  // make the table into a DataTable
  var topPlayerH2HTable = $('#'+tableLabel+'_chart').DataTable({
    paging: false,
    searching: false,
    info: false,
    autoWidth: false,
    stripeClasses: [],
    /*responsive: {
      details: {
        type: 'column'
      }
    },*/
    order: [[1, 'asc']],
    "columns":[
    {width: "7%", data: null, searchable: false, orderable: false, className: 'control', defaultContent: '<i class="fas fa-plus-square"></i>'},
    {width: "10%"},
    {width: "45%"},
    {width: "0%", visible: false},
    {width: "10%"},
    {width: "10%"},
    {width: "15%"}]
  });
  //$($.fn.dataTable.tables(true)).css('width','100%');
  $($.fn.dataTable.tables(true)).DataTable().columns.adjust().responsive.recalc();
  topPlayerH2HTable.columns.adjust().draw();

  // event listener for opening and closing H2H table details
  $('#'+tableLabel+'_chart tbody').on('click', 'td.control', function () {
      // toggle icon state (plu/minus)
      $(this).find('[data-fa-i2svg]').toggleClass('fa-plus-square').toggleClass('fa-minus-square');
      var tr = $(this).closest('tr');
      var row = topPlayerH2HTable.row(tr);
      var childOppId = row.data()[3];

      if (row.child.isShown()) {
          // This row is already open - close it
          row.child.hide();
          tr.removeClass('shown');
      }
      else {
          eventMap = formatPlayerEvents(PlayerEvents);
          //console.log(eventMap)
          row.child(childFormat(childData,childOppId,eventMap,tableLabel)).show();
          // instantiate child table
          
          $('#'+tableLabel+'_vs_'+childOppId).DataTable({
            searching: false,
            info: false,
            order: [[0, 'asc']],
            "columns":[
            {width: '15%'},
            {width: '10%', orderable: false, className: "text-center"},
            {orderable: false},
            // change once I have group/phase data
            {visible: false}],
            // hide pagination if only 1 page needed
            initComplete: function() {
              if (this.api().page.info().pages === 1) {
                $('#'+tableLabel+'_vs_'+childOppId+'_length').hide();
                $('#'+tableLabel+'_vs_'+childOppId+'_paginate').hide();
                $('#'+tableLabel+'_vs_'+childOppId+'.dataTables_length').hide();
                $('#'+tableLabel+'_vs_'+childOppId+'.dataTables_paginate').hide();
              }
            }/*,
            fnDrawCallback: function (oSettings){
              //if(oSettings.fnRecordsDisplay() < oSettings._iDisplayLength){
              if (oSettings.fnRecordsTotal < 10){
                $('#vs_'+childOppId+'.dataTables_length').hide();
                $('#vs_'+childOppId+'.dataTables_paginate').hide();
              } else {
                $('#vs_'+childOppId+'.dataTables_length').show();
                $('#vs_'+childOppId+'.dataTables_paginate').show();
              }
            }*/
          });

          tr.addClass('shown');

          $($.fn.dataTable.tables(true)).DataTable().columns.adjust().responsive.recalc();
      }
  });
}

// generate a single row/record of a h2h table
function addH2HRow(rowType,tableLabel,childData,oppId){
  var oppInfo = childData[oppId]['p_info'].then(function(PlayerInfo){
    var oppSkillRank = PlayerInfo['rank'];
    var oppTag = PlayerInfo['tag'];

    // add row to H2H at a glance table
    //var oppSkillRank = childData['rank'];
    h2hWinrate = Math.round(10000*childData[oppId]['winCount']/(childData[oppId]['winCount']+childData[oppId]['lossCount']))/100
    if (rowType == 'wins'){
      $('#'+tableLabel+'_chart_body').append('<tr id="'+tableLabel+'_row_' + oppSkillRank + '">'+
                                    '<td><i class="fas fa-plus-square"></i></td>' + 
                                    '<td>' + oppSkillRank + '</td>'+
                                    '<td><a style="color:inherit;" href="../players/#'+oppId+'">' + oppTag + '</a></td>' +
                                    '<td>' + oppId + '</td>' +
                                    '<td id="'+tableLabel+'_row_' + oppSkillRank + '_wins">' + childData[oppId]['winCount'] + '</td>' +
                                    '<td id="'+tableLabel+'_row_'+oppSkillRank+'_losses">0</td>' +
                                    '<td id="'+tableLabel+'_row_' + oppSkillRank + '_winrate">100</td>' + 
                                    '</tr>');
    } else if (rowType == 'losses'){
      // if row already exists, add loses & update winrate only
      if ($('#'+tableLabel+'_row_'+oppSkillRank).length > 0){
        $('#'+tableLabel+'_row_'+oppSkillRank+'_losses').html(childData[oppId]['lossCount'])
        $('#'+tableLabel+'_row_'+oppSkillRank+'_winrate').html(h2hWinrate)
      } else {
        $('#'+tableLabel+'_chart_body').append('<tr id="'+tableLabel+'_row_' + oppSkillRank + '">'+
                                      '<td><i class="fas fa-plus-square"></i></td>' + 
                                      '<td>' + oppSkillRank + '</td>'+
                                    '<td><a style="color:inherit;" href="../players/#'+oppId+'">' + oppTag + '</a></td>' +
                                      '<td>' + oppId + '</td>' +
                                      '<td id="'+tableLabel+'_row_'+oppSkillRank+'_wins">0</td>' +
                                      '<td id="'+tableLabel+'_row_' + oppSkillRank + '_losses">' + childData[oppId]['lossCount'] + '</td>' +
                                      '<td id="'+tableLabel+'_row_' + oppSkillRank + '_winrate">0</td>' + 
                                      '</tr>');
      }
    } else {
      console.log('Invalid H2H rowType: '+rowType);
    }
  });
}

// EVENT CARD FUNCTIONS

// populates event cards with most recent event info, making them visible
function populateEventCards(PlayerSnapshot,PlayerEvents, placements, playerWins, playerLosses, pInfoRefStr){
  console.log(playerWins)
  // sort chronologically
  PlayerEvents.sort(function(a,b){
    return b[1]-a[1];
  });
  for (i=0, n=placements.length;i<n;i++){
    placements[i].idx = PlayerEvents.findIndex(function(p_event){
      return p_event[6] == placements[i].key
    });
  }
  placements.sort(function(a,b){
    return a.idx-b.idx;
  });
  console.log(placements)
  for (i=0;i<4;i++){
    var eventRes = placements[i];
    if (eventRes != null){
      $('#event_card_'+i).removeClass('invisible')
      var eventId = parseInt(eventRes.key);
      var eventWins = [];
      var eventLosses = [];

      if (playerWins){
       var winKeys = Object.keys(playerWins);
      } else {
        var winKeys = [];
      }
      if (playerLosses){
       var lossKeys = Object.keys(playerLosses);
      } else {
        var lossKeys = [];
      }

      for (j=0, w_n=winKeys.length;j<w_n;j++){
        if (eventId in playerWins[winKeys[j]]){
          for (s=0,s_n=Object.keys(playerWins[winKeys[j]][eventId]).length;s<s_n;s++){
            eventWins.push(winKeys[j]);
          }
        }
      }
      for (j=0, l_n=lossKeys.length;j<l_n;j++){
        if (eventId in playerLosses[lossKeys[j]]){
          for (s=0,s_n=Object.keys(playerLosses[lossKeys[j]][eventId]).length;s<s_n;s++){
            eventLosses.push(lossKeys[j]);
          }
        }
      }
      // eventInfo = [eventName,eventDate,numEntrants,isActive,bannerUrl,slug,eventId]
      var eventInfo = PlayerEvents[i];
      var smashggUrl = 'http://www.smash.gg/tournament/'+eventInfo[5];
      
      $('#event_card_title_'+i).html('<a style="color:inherit;" href="../events/full/#'+eventId+'">'+eventInfo[0]+'</a>');
      $('#event_card_image_'+i).attr('src',eventInfo[4]);
      $('#event_card_image_'+i).attr('alt',eventId);
      $('#event_card_image_link_'+i).attr('href',smashggUrl);
      eventDate = new Date(eventInfo[1]).toJSON().slice(0,10).replace(/-/g,'/');
      eventDate = eventDate.slice(5,10)+'/'+eventDate.slice(0,4);
      $('#event_card_footer_text_'+i).html(eventDate);
      if (!eventInfo[3]){
        $('#event_card_footer_text_'+i).addClass('text-danger');
      }
      if ('seedNum' in eventRes.val){
        var eventSeedText = '<span class="text-muted">(Seed: '+eventRes.val.seedNum +')</span>';
      } else {
        var eventSeedText = ''
      }
      $('#event_card_text_'+i).html('<p><strong>'+eventRes.val.placing+'</strong>'+' / '+ eventInfo[2]+'</p>'+eventSeedText);

      // populate wins/losses in event cards
      if (eventWins.length > 0 || eventLosses.length > 0){
        $('#event_card_text_'+i).append('<hr style="padding:0px;">')
      } else {
        $('#event_card_text_'+i).append('<hr style="padding:0px;"><p class="text-danger">DQ</p>')
      }
      var eventTags = getOppInfoFromRecords(eventWins,eventLosses,pInfoRefStr,i);
      // populate wins
      if (eventWins && eventWins.length > 0){
        $('#event_card_text_'+i).append('<p>' +
                                          '<a class="btn font-italic" data-toggle="collapse" role="button" onclick="$(\'#wins_'+i+'_collapsed_chevron\').toggleClass(\'fa-rotate-180\')" aria-expanded="false" href="#event_card_wins_'+i+'" style="box-shadow:none;">'+
                                          '<i class="fas fa-chevron-circle-down" id="wins_'+i+'_collapsed_chevron" aria-hidden="true"></i>&nbsp;' +
                                          'Wins <span class="text-muted">('+eventWins.length+')</span></a></p>');
        $('#event_card_text_'+i).append('<div class="collapse" id="event_card_wins_'+i+'"></div>');

        Promise.all(eventTags['wins']).then(function(eventWinPromises){
          //var win_card_idx = eventTags['i'];
          var win_card_idx = eventWinPromises[0];
          for (wi=1,ew_n=eventWinPromises.length; wi<ew_n; wi++){
            if (eventWinPromises[wi]['rank'] < PlayerSnapshot.child('srank-rnk').val()){
              var eventWinClass = '';
              var eventWinIcon = '<span class="text-success"><i class="fas fa-exclamation-circle"></i></span>'
            } else {
              var eventWinClass = 'class="font-weight-light"';
              var eventWinIcon = '<span class="invisible"><i class="fas fa-exclamation-circle"></i></span>'
            }
            $('#event_card_wins_'+win_card_idx).append('<p '+eventWinClass+' style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'+eventWinIcon+
                                                            '&nbsp;<span class="text-sr-dark"><a style="color:inherit;" href="../players/#'+eventWinPromises[wi]['id']+'">'+eventWinPromises[wi]['tag']+'</a></span></p>');
          }
        });
      }

      // populate losses
      if (eventLosses && eventLosses.length > 0){
        $('#event_card_text_'+i).append('<p>' +
                                          '<a class="btn font-italic" data-toggle="collapse" role="button" onclick="$(\'#losses_'+i+'_collapsed_chevron\').toggleClass(\'fa-rotate-180\')" aria-expanded="false" href="#event_card_losses_'+i+'" style="box-shadow:none;">'+
                                          '<i class="fas fa-chevron-circle-down" id="losses_'+i+'_collapsed_chevron" aria-hidden="true"></i>&nbsp;' +
                                          'Losses <span class="text-muted">('+eventLosses.length+')</span></a></p>');
        $('#event_card_text_'+i).append('<div class="collapse" id="event_card_losses_'+i+'"></div>');

        Promise.all(eventTags['losses']).then(function(eventLossPromises){
          var loss_card_idx = eventLossPromises[0];
          for (li=1,el_n=eventLossPromises.length; li<el_n; li++){
            if (eventLossPromises[li]['rank'] < PlayerSnapshot.child('srank-rnk').val()){
              var eventLossClass = 'class="font-weight-light"';
              var eventLossIcon = '<span class="invisible"><i class="fas fa-exclamation-circle"></i></span>'
            } else {
              var eventLossClass = '';
              var eventLossIcon = '<span class="text-danger"><i class="fas fa-exclamation-circle"></i></span>'
            }
            $('#event_card_losses_'+loss_card_idx).append('<p '+eventLossClass+' style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'+eventLossIcon+
                                                                '&nbsp;<span class="text-sr-dark"><a style="color:inherit;" href="../players/#'+eventLossPromises[li]['id']+'">'+eventLossPromises[li]['tag']+'</a></span></p>');
          }
        });
      }
    }
  }
}

function getTagsFromIds(playerIds,refStr){
  var returnArr = [];
  //console.log('GETTING_TAGS__')
  for (i=0,n=playerIds.length; i<n; i++){
    //console.log('GETTING_TAGS__'+i)
    var firebaseRef = firebase.database().ref(refStr+playerIds[i]+'/tag');
    var firebaseQuery = firebaseRef.once('value').then(function(PlayerTag){
      console.log('TAG_EXISTS__'+PlayerTag.val());
      return PlayerTag.val();
    });
    returnArr.push(firebaseQuery);
  }
  return returnArr;
}

// gets p_info from win/loss records (to populate H2H info)
function getOppInfoFromRecords(playerWins,playerLosses,refStr,card_idx){
  var returnObj = {'i':card_idx, 'wins':[card_idx], 'losses': [card_idx]};

  for (w_i=0,w_n=playerWins.length; w_i<w_n; w_i++){
    var firebaseWinRef = firebase.database().ref(refStr+playerWins[w_i]);
    var firebaseWinQuery = firebaseWinRef.once('value').then(function(PlayerWin){
      return {'tag':handleTransTag(PlayerWin.child('tag').val()), 'rank':PlayerWin.child('srank-rnk').val(), 'id':PlayerWin.key};
    });
    returnObj['wins'].push(firebaseWinQuery);
  }

  for (l_i=0,l_n=playerLosses.length; l_i<l_n; l_i++){
    var firebaseLossRef = firebase.database().ref(refStr+playerLosses[l_i]);
    var firebaseLossQuery = firebaseLossRef.once('value').then(function(PlayerLoss){
      return {'tag':handleTransTag(PlayerLoss.child('tag').val()), 'rank':PlayerLoss.child('srank-rnk').val(),'id':PlayerLoss.key};
    });
    returnObj['losses'].push(firebaseLossQuery);
  }
  return returnObj;
}