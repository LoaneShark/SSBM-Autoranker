// SEARCHBAR FUNCTIONS //
// create searchbar for tourney breakdowns
function createTournamentSearchbar(gameId){
  //var searchbar_ref = firebase.database().ref('/'+gameId+'_2016_3/tourneys');
  var searchbar_ref = firebase.database().ref('/'+gameId+'_2016_3_c/tourneys');
  var searchbar_query = searchbar_ref.orderByChild('numEntrants');
  var searchbar_contents = searchbar_query.once('value').then(function(EventInfoSnapshot) {
    if (EventInfoSnapshot.exists()) {
      var searchbar_events = snapshotToEventSearchbar(EventInfoSnapshot);
      // custom tokenizer, so that search is sensetive to gamertag, player id, prefix/sponsor, or any known aliases
      function customTokenizer(datum) {
        var nameTokens = Bloodhound.tokenizers.whitespace(datum.name);
        var idTokens = Bloodhound.tokenizers.whitespace(datum.id);
        var slugTokens = Bloodhound.tokenizers.whitespace(datum.slug);
        slugTokens = slugTokens.concat(Bloodhound.tokenizers.whitespace(datum.shortslug))
        var returnTokens = nameTokens.concat(idTokens);
        returnTokens = returnTokens.concat(slugTokens);
        return returnTokens
      }
      var searchbar_engine = new Bloodhound({
        datumTokenizer: customTokenizer,
        //datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        identify: function(obj) {return obj.id},
        local: searchbar_events
      });
      searchbarTypeahead = $('#event_searchbar .typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
      },{
        name: 'events',
        display: function(context){
          if (context.shortslug != null && context.shortslug.includes(context.query)){
            return context.name+' ('+context.shortslug+')';
          } else if (context.slug != null && context.slug.includes(context.query)){
            return context.name+' ('+context.slug+')';
          } else {
            return context.name;
          }
        },
        displayKey: 'name',
        //limit: 10,
        source: searchbar_engine,
        templates: {
          //suggestion: ,
          notFound: ['<div class="text-muted p-2">No event found...</div>'],
          pending: ['<div class="text-muted p-2">Fetching...</div>']
        }
      });

      // progress icon BROKEN
      searchbarTypeahead.on('typeahead:initialized', function (event, data) {
         // After initializing, hide the progress icon.
         $('.tt-hint').css('background-image', '');
      });
      // Show progress icon while loading.
      //$('.tt-hint').css('background-image', 'url("/assets/images/social_icons/pizza-600px.png")');
    }
  });
}

// returns a dataset of events to feed to searchbar
function snapshotToEventSearchbar(snapshot){
  var returnArr = [];
  snapshot.forEach(function(childSnapshot) {
    var event = {name: childSnapshot.child('name').val(),
            id: childSnapshot.key,
            slug: childSnapshot.child('slug').val(),
            shortslug: childSnapshot.child('shortSlug').val()};

    returnArr.push(event)
  });
  return returnArr;
}

// EVENT BREAKDOWN FUNCTIONS //
function populatePrimaryEventInfo(EventSnapshot){
  // populate event name
  var eventName = EventSnapshot.child('name').val()
  $('#event_name').html(eventName);
  // populate profile image
  propicUrl = EventSnapshot.child('url_prof').val();
  bannerUrl = EventSnapshot.child('url_banner').val();
  if (propicUrl){
    $('#event_propic_div').html('<img src="'+propicUrl+'" alt="" class="rounded"/>')
  } else {
    $('#event_propic_div').html('<img src="https://via.placeholder.com/100/81daea/f2f2f2?text='+eventName.slice(0,1)+'" alt="" class="rounded"/>')
  }
  //populate basic info
  $('#numEntrants').html('<span>'+EventSnapshot.child('numEntrants').val()+'</span><span class="text-muted"> Entrants</span>');
  var eventDate = new Date(EventSnapshot.child('date').val()).toJSON().slice(0,10).replace(/-/g,'/');
  var eventDateText = eventDate.slice(5,10)+'/'+eventDate.slice(0,4);
  $('#event_date').html(eventDateText);
  $('#event_region').html(EventSnapshot.child('region').val());

      // link to smash.gg page
  var eventShortSlug = EventSnapshot.child('shortSlug').val();
  var eventSlug = EventSnapshot.child('slug').val();
  if (!eventShortSlug){
    eventShortSlug = eventSlug;
  }
  $('#event_smashgg_link').html(
    '<a class="text-sr-link" target="_blank" href="https://smash.gg/tournament/'+eventSlug+'">' +
      'smash.gg/tournament/'+ eventShortSlug +
    '</a>')

  // activity status
    var event_active = EventSnapshot.child('active');
    if (event_active.exists()) {
      if (event_active.val()){
        $('#event_status').html('Active');
        $('#event_status').addClass('text-success');
      } else {
        $('#event_status').html('Inactive');
        $('#event_status').addClass('text-danger');
      }
    }
}

function getEventResults(EventSnapshot,gameId,tourneyId,N=64){
  var attendees = EventSnapshot.child('attendees').val();
  var attendeeKeys = Object.keys(attendees);
  attendeeKeys.sort(function(a,b){
    return attendees[a]['placing']['placing'] - attendees[b]['placing']['placing'];
  })
  var returnArr = []
  for (a_i=0,a_n=N;a_i<a_n;a_i++){

    var attId = attendeeKeys[a_i]
    var attRecordsRefStr = '/'+gameId+'_2016_3_c/records/'+attId
    var attRecordsRef = firebase.database().ref(attRecordsRefStr)
    var attRecordsQuery = attRecordsRef.once('value').then(function(AttSnapshot){
      if (AttSnapshot.exists()){
        attEventRes = AttSnapshot.child('placings/'+tourneyId+'/placing').val();

        if (attEventRes && attEventRes <= N){
          // get player meta info
          var attResId = AttSnapshot.key
          var attInfoRefStr = '/'+gameId+'_2016_3_c/p_info/'+attResId
          var attInfoRef = firebase.database().ref(attInfoRefStr)
          var attInfoQuery = attInfoRef.once('value').then(function(AttInfoSnapshot){
            if (AttInfoSnapshot.exists()){
              return {'tag':AttInfoSnapshot.child('tag').val(),'team':AttInfoSnapshot.child('team').val()}
            } else {
              return null
            }
          }).then(function(AttInfo){
            // get player's bracket path
            var attPath = AttSnapshot.child('paths/'+tourneyId).val();
            attPath.sort(function(a,b){
              return EventSnapshot.child('phases/'+EventSnapshot.child('groups/'+a+'/phaseId').val()+'/phaseOrder').val() - 
                     EventSnapshot.child('phases/'+EventSnapshot.child('groups/'+b+'/phaseId').val()+'/phaseOrder').val();
            });
            var attGroups = [];
            attPath.forEach(function(groupId){
              var groupIdentifier = EventSnapshot.child('groups/'+groupId+'/displayIdentifier').val();
              var phaseId = EventSnapshot.child('groups/'+groupId+'/phaseId').val();
              var displayName = EventSnapshot.child('phases/'+phaseId+'/name').val();
              if (EventSnapshot.child('phases/'+phaseId+'/groupCount').val() > 1){
                displayName += '<span class="text-muted"> ('+groupIdentifier+')</span>';
              }
              attGroups.push(displayName);
            });

            // return full player data row
            return {'id':AttSnapshot.key, 'placing':AttSnapshot.child('placings/'+tourneyId+'/placing').val(), 'path':attGroups, 'seed':AttSnapshot.child('placings/'+tourneyId+'/seedNum').val(), 
                    'wins':getEventRecordsFromSnapshot(AttSnapshot,tourneyId,'wins'),'losses':getEventRecordsFromSnapshot(AttSnapshot,tourneyId,'losses'),'p_info':AttInfo};
          });
          return attInfoQuery

        } else {
          return null;
        }
      } else {
        console.log('Error: '+attRecordsRefStr+' does not exist')
      }
    });
    if (attRecordsQuery){
      returnArr.push(attRecordsQuery);
    }
  }
  return returnArr
}

function getEventRecordsFromSnapshot(PlayerSnapshot,tourneyId,resType='losses'){
  playerRecords = PlayerSnapshot.child(resType).val();
  playerRecIds = Object.keys(playerRecords);
  eventRecords = [];

  playerRecIds.forEach(function(oppId){
    if (tourneyId in playerRecords[oppId]){
     eventRecords.push({'id':oppId,'sets':playerRecords[oppId][tourneyId]});
    }
  });

  return eventRecords;
}