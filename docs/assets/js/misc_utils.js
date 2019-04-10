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
			return "/assets/images/game_icons/36px-SSBM_Icon.png";
			break;
		case 2:
			return "/assets/images/game_icons/36px-PM_Icon.png";
			break;
		case 3:
			return "/assets/images/game_icons/36px-SSB4_Icon.png";
			break;
		case 4:
			return "/assets/images/game_icons/36px-SSB64_Icon.png";
			break;
		case 5:
			return "/assets/images/game_icons/36px-SSBB_Icon.png";
			break;
		case 1386:
			return "/assets/images/game_icons/36px-SSBU_Icon.png";
			break;
	}
}

function getStockIconPath(gameId,charId){
	return "/assets/images/stock_icons/"+gameId+"/"+charId+".png";
}

function snapshotToArray(snapshot,attr="val") {
    var returnArr = [];
    snapshot.forEach(function(childSnapshot) {
    	if (attr == "val") {
	        var item = childSnapshot.val();
		} else if (attr == "key") {
        	var item = childSnapshot.key;
        } else if (attr == "both") {
        	var item = {val: childSnapshot.val()};
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
			//var refStr = "/" + gameIds[i] + "_2018_1/p_info/" + p_id + "/";
			var refStr = "/" + gameIds[i] + "_2016_3_c/p_info/" + p_id + "/";
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
		for (j=0;j<gameIds.length;j++){
			if(results[j]){
				otherGames.push(gameIds[j]);
			}
		}
		return otherGames;
	});
	return otherGamesPromise;
}

function placementsToEvents(placements,gameId){
	var eventPromises = [];
	for (i=0;i<placements.length;i++){
		eventId = placements[i].key;
		//var refStr = "/"+gameId+"_2018_1/tourneys/"+eventId;
		var refStr = "/"+gameId+"_2016_3_c/tourneys/"+eventId;

		var eventRef = firebase.database().ref(refStr)
		var eventQuery = eventRef.once('value').then(function(EventSnapshot){
			pyDate = EventSnapshot.child('date').val()
			jsDate = new Date(pyDate[0],pyDate[1]-1,pyDate[2])
			return [EventSnapshot.child('name').val(),jsDate,EventSnapshot.child('numEntrants').val(),EventSnapshot.child('active').val(),EventSnapshot.child('url_banner').val(),EventSnapshot.child('slug').val(),EventSnapshot.key];
		});
		eventPromises.push(eventQuery);
	}
	return eventPromises;
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

// returns the specified css property of a given page element
function css( element, property ) {
    return window.getComputedStyle( element, null ).getPropertyValue( property );
}

// returs the ordinal suffix of a number (-st,-nd,-rd,-th)
function ordinalSuffixOf(i) {
    var j = i % 10,
        k = i % 100;
    if (j == 1 && k != 11) {
        return "st";
    }
    if (j == 2 && k != 12) {
        return "nd";
    }
    if (j == 3 && k != 13) {
        return "rd";
    }
    return "th";
}

function countryNameToCC(countryName){
	if (countryName == 'America'){
		countryName = 'United States'
	}
	var isoCountries1 = [
		{'ccode' : 'AF', 'cname' : 'Afghanistan'},
		{'ccode' : 'AX', 'cname' : 'Aland Islands'},
		{'ccode' : 'AL', 'cname' : 'Albania'},
		{'ccode' : 'DZ', 'cname' : 'Algeria'},
		{'ccode' : 'AS', 'cname' : 'American Samoa'},
		{'ccode' : 'AD', 'cname' : 'Andorra'},
		{'ccode' : 'AO', 'cname' : 'Angola'},
		{'ccode' : 'AI', 'cname' : 'Anguilla'},
		{'ccode' : 'AQ', 'cname' : 'Antarctica'},
		{'ccode' : 'AG', 'cname' : 'Antigua And Barbuda'},
		{'ccode' : 'AR', 'cname' : 'Argentina'},
		{'ccode' : 'AM', 'cname' : 'Armenia'},
		{'ccode' : 'AW', 'cname' : 'Aruba'},
		{'ccode' : 'AU', 'cname' : 'Australia'},
		{'ccode' : 'AT', 'cname' : 'Austria'},
		{'ccode' : 'AZ', 'cname' : 'Azerbaijan'},
		{'ccode' : 'BS', 'cname' : 'Bahamas'},
		{'ccode' : 'BH', 'cname' : 'Bahrain'},
		{'ccode' : 'BD', 'cname' : 'Bangladesh'},
		{'ccode' : 'BB', 'cname' : 'Barbados'},
		{'ccode' : 'BY', 'cname' : 'Belarus'},
		{'ccode' : 'BE', 'cname' : 'Belgium'},
		{'ccode' : 'BZ', 'cname' : 'Belize'},
		{'ccode' : 'BJ', 'cname' : 'Benin'},
		{'ccode' : 'BM', 'cname' : 'Bermuda'},
		{'ccode' : 'BT', 'cname' : 'Bhutan'},
		{'ccode' : 'BO', 'cname' : 'Bolivia'},
		{'ccode' : 'BA', 'cname' : 'Bosnia And Herzegovina'},
		{'ccode' : 'BW', 'cname' : 'Botswana'},
		{'ccode' : 'BV', 'cname' : 'Bouvet Island'},
		{'ccode' : 'BR', 'cname' : 'Brazil'},
		{'ccode' : 'IO', 'cname' : 'British Indian Ocean Territory'},
		{'ccode' : 'BN', 'cname' : 'Brunei Darussalam'},
		{'ccode' : 'BG', 'cname' : 'Bulgaria'},
		{'ccode' : 'BF', 'cname' : 'Burkina Faso'},
		{'ccode' : 'BI', 'cname' : 'Burundi'},
		{'ccode' : 'KH', 'cname' : 'Cambodia'},
		{'ccode' : 'CM', 'cname' : 'Cameroon'},
		{'ccode' : 'CA', 'cname' : 'Canada'},
		{'ccode' : 'CV', 'cname' : 'Cape Verde'},
		{'ccode' : 'KY', 'cname' : 'Cayman Islands'},
		{'ccode' : 'CF', 'cname' : 'Central African Republic'},
		{'ccode' : 'TD', 'cname' : 'Chad'},
		{'ccode' : 'CL', 'cname' : 'Chile'},
		{'ccode' : 'CN', 'cname' : 'China'},
		{'ccode' : 'CX', 'cname' : 'Christmas Island'},
		{'ccode' : 'CC', 'cname' : 'Cocos (Keeling) Islands'},
		{'ccode' : 'CO', 'cname' : 'Colombia'},
		{'ccode' : 'KM', 'cname' : 'Comoros'},
		{'ccode' : 'CG', 'cname' : 'Congo'},
		{'ccode' : 'CD', 'cname' : 'Congo, Democratic Republic'},
		{'ccode' : 'CK', 'cname' : 'Cook Islands'},
		{'ccode' : 'CR', 'cname' : 'Costa Rica'},
		{'ccode' : 'CI', 'cname' : "Cote D'Ivoire"},
		{'ccode' : 'HR', 'cname' : 'Croatia'},
		{'ccode' : 'CU', 'cname' : 'Cuba'},
		{'ccode' : 'CY', 'cname' : 'Cyprus'},
		{'ccode' : 'CZ', 'cname' : 'Czech Republic'},
		{'ccode' : 'DK', 'cname' : 'Denmark'},
		{'ccode' : 'DJ', 'cname' : 'Djibouti'},
		{'ccode' : 'DM', 'cname' : 'Dominica'},
		{'ccode' : 'DO', 'cname' : 'Dominican Republic'},
		{'ccode' : 'EC', 'cname' : 'Ecuador'},
		{'ccode' : 'EG', 'cname' : 'Egypt'},
		{'ccode' : 'SV', 'cname' : 'El Salvador'},
		{'ccode' : 'GQ', 'cname' : 'Equatorial Guinea'},
		{'ccode' : 'ER', 'cname' : 'Eritrea'},
		{'ccode' : 'EE', 'cname' : 'Estonia'},
		{'ccode' : 'ET', 'cname' : 'Ethiopia'},
		{'ccode' : 'FK', 'cname' : 'Falkland Islands (Malvinas)'},
		{'ccode' : 'FO', 'cname' : 'Faroe Islands'},
		{'ccode' : 'FJ', 'cname' : 'Fiji'},
		{'ccode' : 'FI', 'cname' : 'Finland'},
		{'ccode' : 'FR', 'cname' : 'France'},
		{'ccode' : 'GF', 'cname' : 'French Guiana'},
		{'ccode' : 'PF', 'cname' : 'French Polynesia'},
		{'ccode' : 'TF', 'cname' : 'French Southern Territories'},
		{'ccode' : 'GA', 'cname' : 'Gabon'},
		{'ccode' : 'GM', 'cname' : 'Gambia'},
		{'ccode' : 'GE', 'cname' : 'Georgia'},
		{'ccode' : 'DE', 'cname' : 'Germany'},
		{'ccode' : 'GH', 'cname' : 'Ghana'},
		{'ccode' : 'GI', 'cname' : 'Gibraltar'},
		{'ccode' : 'GR', 'cname' : 'Greece'},
		{'ccode' : 'GL', 'cname' : 'Greenland'},
		{'ccode' : 'GD', 'cname' : 'Grenada'},
		{'ccode' : 'GP', 'cname' : 'Guadeloupe'},
		{'ccode' : 'GU', 'cname' : 'Guam'},
		{'ccode' : 'GT', 'cname' : 'Guatemala'},
		{'ccode' : 'GG', 'cname' : 'Guernsey'},
		{'ccode' : 'GN', 'cname' : 'Guinea'},
		{'ccode' : 'GW', 'cname' : 'Guinea-Bissau'},
		{'ccode' : 'GY', 'cname' : 'Guyana'},
		{'ccode' : 'HT', 'cname' : 'Haiti'},
		{'ccode' : 'HM', 'cname' : 'Heard Island & Mcdonald Islands'},
		{'ccode' : 'VA', 'cname' : 'Holy See (Vatican City State)'},
		{'ccode' : 'HN', 'cname' : 'Honduras'},
		{'ccode' : 'HK', 'cname' : 'Hong Kong'},
		{'ccode' : 'HU', 'cname' : 'Hungary'},
		{'ccode' : 'IS', 'cname' : 'Iceland'},
		{'ccode' : 'IN', 'cname' : 'India'},
		{'ccode' : 'ID', 'cname' : 'Indonesia'},
		{'ccode' : 'IR', 'cname' : 'Iran, Islamic Republic Of'},
		{'ccode' : 'IQ', 'cname' : 'Iraq'},
		{'ccode' : 'IE', 'cname' : 'Ireland'},
		{'ccode' : 'IM', 'cname' : 'Isle Of Man'},
		{'ccode' : 'IL', 'cname' : 'Israel'},
		{'ccode' : 'IT', 'cname' : 'Italy'},
		{'ccode' : 'JM', 'cname' : 'Jamaica'},
		{'ccode' : 'JP', 'cname' : 'Japan'},
		{'ccode' : 'JE', 'cname' : 'Jersey'},
		{'ccode' : 'JO', 'cname' : 'Jordan'},
		{'ccode' : 'KZ', 'cname' : 'Kazakhstan'},
		{'ccode' : 'KE', 'cname' : 'Kenya'},
		{'ccode' : 'KI', 'cname' : 'Kiribati'},
		{'ccode' : 'KR', 'cname' : 'Korea'},
		{'ccode' : 'KW', 'cname' : 'Kuwait'},
		{'ccode' : 'KG', 'cname' : 'Kyrgyzstan'},
		{'ccode' : 'LA', 'cname' : "Lao People's Democratic Republic"},
		{'ccode' : 'LV', 'cname' : 'Latvia'},
		{'ccode' : 'LB', 'cname' : 'Lebanon'},
		{'ccode' : 'LS', 'cname' : 'Lesotho'},
		{'ccode' : 'LR', 'cname' : 'Liberia'},
		{'ccode' : 'LY', 'cname' : 'Libyan Arab Jamahiriya'},
		{'ccode' : 'LI', 'cname' : 'Liechtenstein'},
		{'ccode' : 'LT', 'cname' : 'Lithuania'},
		{'ccode' : 'LU', 'cname' : 'Luxembourg'},
		{'ccode' : 'MO', 'cname' : 'Macao'},
		{'ccode' : 'MK', 'cname' : 'Macedonia'},
		{'ccode' : 'MG', 'cname' : 'Madagascar'},
		{'ccode' : 'MW', 'cname' : 'Malawi'},
		{'ccode' : 'MY', 'cname' : 'Malaysia'},
		{'ccode' : 'MV', 'cname' : 'Maldives'},
		{'ccode' : 'ML', 'cname' : 'Mali'},
		{'ccode' : 'MT', 'cname' : 'Malta'},
		{'ccode' : 'MH', 'cname' : 'Marshall Islands'},
		{'ccode' : 'MQ', 'cname' : 'Martinique'},
		{'ccode' : 'MR', 'cname' : 'Mauritania'},
		{'ccode' : 'MU', 'cname' : 'Mauritius'},
		{'ccode' : 'YT', 'cname' : 'Mayotte'},
		{'ccode' : 'MX', 'cname' : 'Mexico'},
		{'ccode' : 'FM', 'cname' : 'Micronesia, Federated States Of'},
		{'ccode' : 'MD', 'cname' : 'Moldova'},
		{'ccode' : 'MC', 'cname' : 'Monaco'},
		{'ccode' : 'MN', 'cname' : 'Mongolia'},
		{'ccode' : 'ME', 'cname' : 'Montenegro'},
		{'ccode' : 'MS', 'cname' : 'Montserrat'},
		{'ccode' : 'MA', 'cname' : 'Morocco'},
		{'ccode' : 'MZ', 'cname' : 'Mozambique'},
		{'ccode' : 'MM', 'cname' : 'Myanmar'},
		{'ccode' : 'NA', 'cname' : 'Namibia'},
		{'ccode' : 'NR', 'cname' : 'Nauru'},
		{'ccode' : 'NP', 'cname' : 'Nepal'},
		{'ccode' : 'NL', 'cname' : 'Netherlands'},
		{'ccode' : 'AN', 'cname' : 'Netherlands Antilles'},
		{'ccode' : 'NC', 'cname' : 'New Caledonia'},
		{'ccode' : 'NZ', 'cname' : 'New Zealand'},
		{'ccode' : 'NI', 'cname' : 'Nicaragua'},
		{'ccode' : 'NE', 'cname' : 'Niger'},
		{'ccode' : 'NG', 'cname' : 'Nigeria'},
		{'ccode' : 'NU', 'cname' : 'Niue'},
		{'ccode' : 'NF', 'cname' : 'Norfolk Island'},
		{'ccode' : 'MP', 'cname' : 'Northern Mariana Islands'},
		{'ccode' : 'NO', 'cname' : 'Norway'},
		{'ccode' : 'OM', 'cname' : 'Oman'},
		{'ccode' : 'PK', 'cname' : 'Pakistan'},
		{'ccode' : 'PW', 'cname' : 'Palau'},
		{'ccode' : 'PS', 'cname' : 'Palestinian Territory, Occupied'},
		{'ccode' : 'PA', 'cname' : 'Panama'},
		{'ccode' : 'PG', 'cname' : 'Papua New Guinea'},
		{'ccode' : 'PY', 'cname' : 'Paraguay'},
		{'ccode' : 'PE', 'cname' : 'Peru'},
		{'ccode' : 'PH', 'cname' : 'Philippines'},
		{'ccode' : 'PN', 'cname' : 'Pitcairn'},
		{'ccode' : 'PL', 'cname' : 'Poland'},
		{'ccode' : 'PT', 'cname' : 'Portugal'},
		{'ccode' : 'PR', 'cname' : 'Puerto Rico'},
		{'ccode' : 'QA', 'cname' : 'Qatar'},
		{'ccode' : 'RE', 'cname' : 'Reunion'},
		{'ccode' : 'RO', 'cname' : 'Romania'},
		{'ccode' : 'RU', 'cname' : 'Russian Federation'},
		{'ccode' : 'RW', 'cname' : 'Rwanda'},
		{'ccode' : 'BL', 'cname' : 'Saint Barthelemy'},
		{'ccode' : 'SH', 'cname' : 'Saint Helena'},
		{'ccode' : 'KN', 'cname' : 'Saint Kitts And Nevis'},
		{'ccode' : 'LC', 'cname' : 'Saint Lucia'},
		{'ccode' : 'MF', 'cname' : 'Saint Martin'},
		{'ccode' : 'PM', 'cname' : 'Saint Pierre And Miquelon'},
		{'ccode' : 'VC', 'cname' : 'Saint Vincent And Grenadines'},
		{'ccode' : 'WS', 'cname' : 'Samoa'},
		{'ccode' : 'SM', 'cname' : 'San Marino'},
		{'ccode' : 'ST', 'cname' : 'Sao Tome And Principe'},
		{'ccode' : 'SA', 'cname' : 'Saudi Arabia'},
		{'ccode' : 'SN', 'cname' : 'Senegal'},
		{'ccode' : 'RS', 'cname' : 'Serbia'},
		{'ccode' : 'SC', 'cname' : 'Seychelles'},
		{'ccode' : 'SL', 'cname' : 'Sierra Leone'},
		{'ccode' : 'SG', 'cname' : 'Singapore'},
		{'ccode' : 'SK', 'cname' : 'Slovakia'},
		{'ccode' : 'SI', 'cname' : 'Slovenia'},
		{'ccode' : 'SB', 'cname' : 'Solomon Islands'},
		{'ccode' : 'SO', 'cname' : 'Somalia'},
		{'ccode' : 'ZA', 'cname' : 'South Africa'},
		{'ccode' : 'GS', 'cname' : 'South Georgia And Sandwich Isl.'},
		{'ccode' : 'ES', 'cname' : 'Spain'},
		{'ccode' : 'LK', 'cname' : 'Sri Lanka'},
		{'ccode' : 'SD', 'cname' : 'Sudan'},
		{'ccode' : 'SR', 'cname' : 'Suriname'},
		{'ccode' : 'SJ', 'cname' : 'Svalbard And Jan Mayen'},
		{'ccode' : 'SZ', 'cname' : 'Swaziland'},
		{'ccode' : 'SE', 'cname' : 'Sweden'},
		{'ccode' : 'CH', 'cname' : 'Switzerland'},
		{'ccode' : 'SY', 'cname' : 'Syrian Arab Republic'},
		{'ccode' : 'TW', 'cname' : 'Taiwan'},
		{'ccode' : 'TJ', 'cname' : 'Tajikistan'},
		{'ccode' : 'TZ', 'cname' : 'Tanzania'},
		{'ccode' : 'TH', 'cname' : 'Thailand'},
		{'ccode' : 'TL', 'cname' : 'Timor-Leste'},
		{'ccode' : 'TG', 'cname' : 'Togo'},
		{'ccode' : 'TK', 'cname' : 'Tokelau'},
		{'ccode' : 'TO', 'cname' : 'Tonga'},
		{'ccode' : 'TT', 'cname' : 'Trinidad And Tobago'},
		{'ccode' : 'TN', 'cname' : 'Tunisia'},
		{'ccode' : 'TR', 'cname' : 'Turkey'},
		{'ccode' : 'TM', 'cname' : 'Turkmenistan'},
		{'ccode' : 'TC', 'cname' : 'Turks And Caicos Islands'},
		{'ccode' : 'TV', 'cname' : 'Tuvalu'},
		{'ccode' : 'UG', 'cname' : 'Uganda'},
		{'ccode' : 'UA', 'cname' : 'Ukraine'},
		{'ccode' : 'AE', 'cname' : 'United Arab Emirates'},
		{'ccode' : 'GB', 'cname' : 'United Kingdom'},
		{'ccode' : 'US', 'cname' : 'United States'},
		{'ccode' : 'UM', 'cname' : 'United States Outlying Islands'},
		{'ccode' : 'UY', 'cname' : 'Uruguay'},
		{'ccode' : 'UZ', 'cname' : 'Uzbekistan'},
		{'ccode' : 'VU', 'cname' : 'Vanuatu'},
		{'ccode' : 'VE', 'cname' : 'Venezuela'},
		{'ccode' : 'VN', 'cname' : 'Viet Nam'},
		{'ccode' : 'VG', 'cname' : 'Virgin Islands, British'},
		{'ccode' : 'VI', 'cname' : 'Virgin Islands, U.S.'},
		{'ccode' : 'WF', 'cname' : 'Wallis And Futuna'},
		{'ccode' : 'EH', 'cname' : 'Western Sahara'},
		{'ccode' : 'YE', 'cname' : 'Yemen'},
		{'ccode' : 'ZM', 'cname' : 'Zambia'},
		{'ccode' : 'ZW', 'cname' : 'Zimbabwe'}
	];

  for(var prop in isoCountries1){
      if(isoCountries1.hasOwnProperty(prop)){
          if(isoCountries1[prop]['cname'].toLowerCase() == countryName.toLowerCase()) {
              return isoCountries1[prop]['ccode'];
              break;
          }
      }
  }
}

function getNAMap(){
	return [
			  {
			    "name": "New England",
			    "color": chart.colors.getIndex(0),
			    "data": [
			      {
			        "title": "Massachusetts",
			        "id": "US-MA", // With MapPolygonSeries.useGeodata = true, it will try and match this id, then apply the other properties as custom data
			        "customData": "New England"
			      }, {
			        "title": "Maine",
			        "id": "US-ME",
			        "customData": "New England"
			      }, {
			        "title": "Vermont",
			        "id": "US-VT",
			        "customData": "New England"
			      }, {
			        "title": "New Hampshire",
			        "id": "US-NH",
			        "customData": "New England"
			      }, {
			        "title": "Rhode Island",
			        "id": "US-RI",
			        "customData": "New England"
			      }, {
			        "title": "Connecticut",
			        "id": "US-CT",
			        "customData": "New England"
			      }
			    ]
			  },{
			    "name": "Tristate",
			    "color": chart.colors.getIndex(1),
			    "data": [
			      {
			        "title": "New York",
			        "id": "US-NY", 
			        "customData": ""
			      }, {
			        "title": "Pennsylvania",
			        "id": "US-PA",
			        "customData": ""
			      }, {
			        "title": "New Jersey",
			        "id": "US-NJ",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "MD/VA",
			    "color": chart.colors.getIndex(2),
			    "data": [
			      {
			        "title": "Maryland",
			        "id": "US-MD", 
			        "customData": ""
			      }, {
			        "title": "Virginia",
			        "id": "US-VA",
			        "customData": ""
			      }, {
			        "title": "West Virginia",
			        "id": "US-WV",
			        "customData": ""
			      }, {
			        "title": "Delaware",
			        "id": "US-DE",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "South Atlantic",
			    "color": chart.colors.getIndex(3),
			    "data": [
			      {
			        "title": "North Carolina",
			        "id": "US-NC", 
			        "customData": ""
			      }, {
			        "title": "South Carolina",
			        "id": "US-SC",
			        "customData": ""
			      }, {
			        "title": "Georgia",
			        "id": "US-GA",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Mideast",
			    "color": chart.colors.getIndex(4),
			    "data": [
			      {
			        "title": "Ohio",
			        "id": "US-OH", 
			        "customData": ""
			      }, {
			        "title": "Kentucky",
			        "id": "US-KY",
			        "customData": ""
			      }, {
			        "title": "Tennessee",
			        "id": "US-TN",
			        "customData": ""
			      }, {
			        "title": "Alabama",
			        "id": "US-AL",
			        "customData": ""
			      }, {
			        "title": "Mississippi",
			        "id": "US-MS",
			        "customData": ""
			      }, {
			        "title": "Indiana",
			        "id": "US-IN",
			        "customData": ""
			      }, {
			        "title": "Illinois",
			        "id": "US-IL",
			        "customData": ""
			      }, {
			        "title": "Michigan",
			        "id": "US-MI",
			        "customData": ""
			      }, {
			        "title": "Wisconsin",
			        "id": "US-WI",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Midwest",
			    "color": chart.colors.getIndex(5),
			    "data": [
			      {
			        "title": "North Dakota",
			        "id": "US-ND", 
			        "customData": ""
			      }, {
			        "title": "South Dakota",
			        "id": "US-SD",
			        "customData": ""
			      }, {
			        "title": "Minnesota",
			        "id": "US-MN",
			        "customData": ""
			      }, {
			        "title": "Iowa",
			        "id": "US-IA",
			        "customData": ""
			      }, {
			        "title": "Missouri",
			        "id": "US-MO",
			        "customData": ""
			      }, {
			        "title": "Arkansas",
			        "id": "US-AR",
			        "customData": ""
			      }, {
			        "title": "Louisiana",
			        "id": "US-LA",
			        "customData": ""
			      }, {
			        "title": "Nebraska",
			        "id": "US-NE",
			        "customData": ""
			      }, {
			        "title": "Kansas",
			        "id": "US-KS",
			        "customData": ""
			      }, {
			        "title": "Oklahoma",
			        "id": "US-OK",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Rockies",
			    "color": chart.colors.getIndex(6),
			    "data": [
			      {
			        "title": "Wyoming",
			        "id": "US-WY", 
			        "customData": ""
			      }, {
			        "title": "Colorado",
			        "id": "US-CO",
			        "customData": ""
			      }, {
			        "title": "Utah",
			        "id": "US-UT",
			        "customData": ""
			      }, {
			        "title": "Nevada",
			        "id": "US-NV",
			        "customData": ""
			      }, {
			        "title": "Montana",
			        "id": "US-MT",
			        "customData": ""
			      }, {
			        "title": "Idaho",
			        "id": "US-ID",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Southwest",
			    "color": chart.colors.getIndex(7),
			    "data": [
			      {
			        "title": "Arizona",
			        "id": "US-AZ", 
			        "customData": ""
			      }, {
			        "title": "New Mexico",
			        "id": "US-NM",
			        "customData": ""
			      }, {
			        "title": "Texas",
			        "id": "US-TX",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Pacific Northwest",
			    "color": chart.colors.getIndex(8),
			    "data": [
			      {
			        "title": "Washington",
			        "id": "US-WA", 
			        "customData": ""
			      }, {
			        "title": "Oregon",
			        "id": "US-OR",
			        "customData": ""
			      }, {
			        "title": "British Columbia",
			        "id": "CA-BC",
			        "customData": ""
			      }, {
			        "title": "Alberta",
			        "id": "CA-AB",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Arctic Circle",
			    "color": chart.colors.getIndex(9),
			    "data": [
			      {
			        "title": "Alaska",
			        "id": "US-AK", 
			        "customData": ""
			      }, {
			        "title": "Yukon Territory",
			        "id": "CA-YT",
			        "customData": ""
			      }, {
			        "title": "Northwest Territories",
			        "id": "CA-NT",
			        "customData": ""
			      }, {
			        "title": "Nunavut",
			        "id": "CA-NU",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Central Canada",
			    "color": chart.colors.getIndex(10),
			    "data": [
			      {
			        "title": "Saskatchewan",
			        "id": "CA-SK", 
			        "customData": ""
			      }, {
			        "title": "Manitoba",
			        "id": "CA-MB",
			        "customData": ""
			      }, {
			        "title": "Ontario",
			        "id": "CA-ON",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "Atlantic Canada",
			    "color": chart.colors.getIndex(11),
			    "data": [
			      {
			        "title": "Québec",
			        "id": "CA-QC", 
			        "customData": ""
			      }, {
			        "title": "New Brunswick",
			        "id": "CA-NB",
			        "customData": ""
			      }, {
			        "title": "Nova Scotia",
			        "id": "CA-NS",
			        "customData": ""
			      }, {
			        "title": "Prince Edward Island",
			        "id": "CA-PE",
			        "customData": ""
			      }, {
			        "title": "Newfoundland & Labrador",
			        "id": "CA-NL",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "U.S. Caribbean Islands",
			    "color": chart.colors.getIndex(12),
			    "data": [
			      {
			        "title": "Puerto Rico",
			        "id": "US-PR", 
			        "customData": ""
			      }, {
			        "title": "Virgin Islands",
			        "id": "US-VI",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "U.S. Pacific Islands",
			    "color": chart.colors.getIndex(13),
			    "data": [
			      {
			        "title": "Hawai'i",
			        "id": "US-HI", 
			        "customData": ""
			      }, {
			        "title": "Guam",
			        "id": "US-GU",
			        "customData": ""
			      }, {
			        "title": "Northern Mariana Islands",
			        "id": "US-MP",
			        "customData": ""
			      }, {
			        "title": "American Samoa",
			        "id": "US-AS",
			        "customData": ""
			      }, {
			        "title": "Marshall Islands",
			        "id": "MH",
			        "customData": ""
			      }, {
			        "title": "Federated States of Micronesia",
			        "id": "FM",
			        "customData": ""
			      }, {
			        "title": "Palau",
			        "id": "PW",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "SoCal",
			    "color": chart.colors.getIndex(14),
			    "data": [
			      {
			        "title": "Ventura",
			        "id": "06111",
			        "customData": ""
			      }, {
			        "title": "Santa Barbara",
			        "id": "06083",
			        "customData": ""
			      }, {
			        "title": "San Luis Obispo",
			        "id": "06079",
			        "customData": ""
			      }, {
			        "title": "San Diego",
			        "id": "06073",
			        "customData": ""
			      }, {
			        "title": "San Bernardino",
			        "id": "06071",
			        "customData": ""
			      }, {
			        "title": "Riverside",
			        "id": "06065",
			        "customData": ""
			      }, {
			        "title": "Orange",
			        "id": "06059",
			        "customData": ""
			      }, {
			        "title": "Los Angeles",
			        "id": "06037",
			        "customData": ""
			      }, {
			        "title": "Kern",
			        "id": "06029",
			        "customData": ""
			      }, {
			        "title": "Imperial",
			        "id": "06025",
			        "customData": ""
			      }
			    ]
			  },{
			    "name": "NorCal",
			    "color": chart.colors.getIndex(15),
			    "data": [
			      {
			        "title": "Yuba",
			        "id": "06115", 
			        "customData": ""
			      }, {
			        "title": "Yolo",
			        "id": "06113",
			        "customData": ""
			      }, {
			        "title": "Tuolumne",
			        "id": "06109",
			        "customData": ""
			      }, {
			        "title": "Tulare",
			        "id": "06107",
			        "customData": ""
			      }, {
			        "title": "Trinity",
			        "id": "06105",
			        "customData": ""
			      }, {
			        "title": "Tehama",
			        "id": "06103",
			        "customData": ""
			      }, {
			        "title": "Sutter",
			        "id": "06101",
			        "customData": ""
			      }, {
			        "title": "Stanislaus",
			        "id": "06099",
			        "customData": ""
			      }, {
			        "title": "Sonoma",
			        "id": "06097",
			        "customData": ""
			      }, {
			        "title": "Solano",
			        "id": "06095",
			        "customData": ""
			      }, {
			        "title": "Siskiyou",
			        "id": "06093",
			        "customData": ""
			      }, {
			        "title": "Sierra",
			        "id": "06091",
			        "customData": ""
			      }, {
			        "title": "Shasta",
			        "id": "06089",
			        "customData": ""
			      }, {
			        "title": "Santa Cruz",
			        "id": "06087",
			        "customData": ""
			      }, {
			        "title": "Santa Clara",
			        "id": "06085",
			        "customData": ""
			      }, {
			        "title": "San Mateo",
			        "id": "06081",
			        "customData": ""
			      }, {
			        "title": "San Joaquin",
			        "id": "06077",
			        "customData": ""
			      }, {
			        "title": "San Francisco",
			        "id": "06075",
			        "customData": ""
			      }, {
			        "title": "San Benito",
			        "id": "06069",
			        "customData": ""
			      }, {
			        "title": "Sacramento",
			        "id": "06067",
			        "customData": ""
			      }, {
			        "title": "Plumas",
			        "id": "06063",
			        "customData": ""
			      }, {
			        "title": "Placer",
			        "id": "06061",
			        "customData": ""
			      }, {
			        "title": "Nevada",
			        "id": "06057",
			        "customData": ""
			      }, {
			        "title": "Napa",
			        "id": "06055",
			        "customData": ""
			      }, {
			        "title": "Monterey",
			        "id": "06053",
			        "customData": ""
			      }, {
			        "title": "Mono",
			        "id": "06051",
			        "customData": ""
			      }, {
			        "title": "Modoc",
			        "id": "06049",
			        "customData": ""
			      }, {
			        "title": "Merced",
			        "id": "06047",
			        "customData": ""
			      }, {
			        "title": "Mendocino",
			        "id": "06045",
			        "customData": ""
			      }, {
			        "title": "Mariposa",
			        "id": "06043",
			        "customData": ""
			      }, {
			        "title": "Marin",
			        "id": "06041",
			        "customData": ""
			      }, {
			        "title": "Madera",
			        "id": "06039",
			        "customData": ""
			      }, {
			        "title": "Lassen",
			        "id": "06035",
			        "customData": ""
			      }, {
			        "title": "Lake",
			        "id": "06033",
			        "customData": ""
			      }, {
			        "title": "Kings",
			        "id": "06031",
			        "customData": ""
			      }, {
			        "title": "Inyo",
			        "id": "06027",
			        "customData": ""
			      }, {
			        "title": "Humboldt",
			        "id": "06023",
			        "customData": ""
			      }, {
			        "title": "Glenn",
			        "id": "06021",
			        "customData": ""
			      }, {
			        "title": "Fresno",
			        "id": "06019",
			        "customData": ""
			      }, {
			        "title": "El Dorado",
			        "id": "06017",
			        "customData": ""
			      }, {
			        "title": "Del Norte",
			        "id": "06015",
			        "customData": ""
			      }, {
			        "title": "Contra Costa",
			        "id": "06013",
			        "customData": ""
			      }, {
			        "title": "Colusa",
			        "id": "06011",
			        "customData": ""
			      }, {
			        "title": "Calaveras",
			        "id": "06009",
			        "customData": ""
			      }, {
			        "title": "Butte",
			        "id": "06007",
			        "customData": ""
			      }, {
			        "title": "Amador",
			        "id": "06005",
			        "customData": ""
			      }, {
			        "title": "Alpine",
			        "id": "06003",
			        "customData": ""
			      }, {
			        "title": "Alameda",
			        "id": "06001",
			        "customData": ""
			      }
			    ]
			  }
			];
}