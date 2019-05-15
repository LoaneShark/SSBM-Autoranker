function generatePlayerMap(){
	am4core.useTheme(am4themes_material);
	am4core.useTheme(am4themes_animated);

	var chart = am4core.create("player_chart_div",am4maps.MapChart);
	//chart.geodata = am4geodata_usaLow;
	chart.geodata = am4geodata_usacanLow;
	chart.projection = new am4maps.projections.Miller();

	setNav(chart);

	var groupData = getNAMap(chart);

	// The rest of the world.
	var worldSeries = chart.series.push(new am4maps.MapPolygonSeries());
	//var worldSeriesName = "world";
	//worldSeries.name = worldSeriesName;
	worldSeries.useGeodata = true;
	//worldSeries.fillOpacity = 0.8;
	worldSeries.hiddenInLegend = true;
	//worldSeries.mapPolygons.template.nonScalingStroke = true;


	// Create image series (for player dots)
	var imageSeries = chart.series.push(new am4maps.MapImageSeries());

	// Create a template "image" for image series, using a circle
	var imageSeriesTemplate = imageSeries.mapImages.template;
	var circle = imageSeriesTemplate.createChild(am4core.Circle);
	circle.radius = 4;
	circle.fill = am4core.color("#B27799");
	circle.stroke = am4core.color("#FFFFFF");
	circle.strokeWidth = 2;
	circle.nonScaling = true;
	circle.tooltipText = "{title}";

	setLegend(chart);
}

function generateRegionMap(continent){
	if (continent == 'NA'){
		am4core.useTheme(am4themes_material);
		am4core.useTheme(am4themes_animated);

		var chart = am4core.create("region_chart_div",am4maps.MapChart);
		//chart.geodata = am4geodata_usaLow;
		chart.geodata = am4geodata_usacanLow;
		chart.projection = new am4maps.projections.Miller();
		//chart.exporting.menu = new am4core.ExportMenu();
		chart.zoomControl = new am4maps.ZoomControl();

		var homeButton = new am4core.Button();
		homeButton.events.on("hit", function(){
		  chart.goHome();
		});

		homeButton.icon = new am4core.Sprite();
		homeButton.padding(7, 5, 7, 5);
		homeButton.width = 30;
		homeButton.icon.path = "M16,8 L14,8 L14,16 L10,16 L10,10 L6,10 L6,16 L2,16 L2,8 L0,8 L8,0 L16,8 Z M16,8";
		homeButton.marginBottom = 10;
		homeButton.parent = chart.zoomControl;
		homeButton.insertBefore(chart.zoomControl.plusButton);

		// Center on the groups by default
		chart.homeZoomLevel = 1.5;
		chart.homeGeoPoint = { longitude: -109, latitude: 49 };

		var groupData = getNARegionMap(chart);

		// This array will be populated with country IDs to exclude from the world series
		var excludedCountries = ["AQ"];

		// Create a series for each group, and populate the above array
		groupData.forEach(function(group) {
		  var series = chart.series.push(new am4maps.MapPolygonSeries());
		  series.name = group.name;
		  series.useGeodata = true;
		  var includedCountries = [];
		  group.data.forEach(function(country){
		    includedCountries.push(country.id);
		    excludedCountries.push(country.id);
		  });
		  series.include = includedCountries;

		  series.fill = am4core.color(group.color);
		  
		  // By creating a hover state and setting setStateOnChildren to true, when we
		  // hover over the series itself, it will trigger the hover SpriteState of all
		  // its countries (provided those countries have a hover SpriteState, too!).
		  series.setStateOnChildren = true;
		  var seriesHoverState = series.states.create("hover");  
		  
		  // Country shape properties & behaviors
		  var mapPolygonTemplate = series.mapPolygons.template;
		  // Instead of our custom title, we could also use {name} which comes from geodata  
		  mapPolygonTemplate.fill = am4core.color(group.color);
		  mapPolygonTemplate.fillOpacity = 0.8;
		  mapPolygonTemplate.nonScalingStroke = true;
		  
		  // States  
		  var hoverState = mapPolygonTemplate.states.create("hover");
		  hoverState.properties.fill = am4core.color("#CC0000");
		  
		  // Tooltip
		  mapPolygonTemplate.tooltipText = "{customData} ({name})"; // enables tooltip
		  // series.tooltip.getFillFromObject = false; // prevents default colorization, which would make all tooltips red on hover
		  // series.tooltip.background.fill = am4core.color(group.color);
		  
		  // MapPolygonSeries will mutate the data assigned to it, 
		  // we make and provide a copy of the original data array to leave it untouched.
		  // (This method of copying works only for simple objects, e.g. it will not work
		  //  as predictably for deep copying custom Classes.)
		  series.data = JSON.parse(JSON.stringify(group.data));
		});

		// The rest of the world.
		var worldSeries = chart.series.push(new am4maps.MapPolygonSeries());
		var worldSeriesName = "world";
		worldSeries.name = worldSeriesName;
		worldSeries.useGeodata = true;
		worldSeries.exclude = excludedCountries;
		worldSeries.fillOpacity = 0.8;
		worldSeries.hiddenInLegend = true;
		worldSeries.mapPolygons.template.nonScalingStroke = true;

		// This auto-generates a legend according to each series' name and fill
		var legendContainer = am4core.create("region_legend_div",am4core.Container);
		legendContainer.width = am4core.percent(100);
		legendContainer.height = am4core.percent(100);
		chart.legend = new am4maps.Legend();

		// Legend styles
		chart.legend.parent = legendContainer;
		chart.legend.paddingLeft = 0;
		chart.legend.paddingRight = 0;
		chart.legend.marginBottom = 0;
		chart.legend.marginTop = 0;
		legendContainer.layout = "vertical";
		//chart.legend.maxColumns = 1;
		//chart.legend.width = am4core.percent(90);
		chart.legend.valign = "bottom";
		chart.legend.contentAlign = "left";
		//chart.legend.responsive = true;

		// Legend items
		//chart.legend.itemContainers.template.interactionsEnabled = false;
	}
}

function setNav(chart){
	chart.zoomControl = new am4maps.ZoomControl();

	var homeButton = new am4core.Button();
	homeButton.events.on("hit", function(){
	  chart.goHome();
	});

	homeButton.icon = new am4core.Sprite();
	homeButton.padding(7, 5, 7, 5);
	homeButton.width = 30;
	homeButton.icon.path = "M16,8 L14,8 L14,16 L10,16 L10,10 L6,10 L6,16 L2,16 L2,8 L0,8 L8,0 L16,8 Z M16,8";
	homeButton.marginBottom = 10;
	homeButton.parent = chart.zoomControl;
	homeButton.insertBefore(chart.zoomControl.plusButton);

	// Center on the groups by default
	chart.homeZoomLevel = 1.5;
	chart.homeGeoPoint = { longitude: -109, latitude: 49 };
}

function setLegend(chart){
	// This auto-generates a legend according to each series' name and fill
	var legendContainer = am4core.create("player_legend_div",am4core.Container);
	legendContainer.width = am4core.percent(100);
	legendContainer.height = am4core.percent(100);
	chart.legend = new am4maps.Legend();

	// Legend styles
	chart.legend.parent = legendContainer;
	chart.legend.paddingLeft = 0;
	chart.legend.paddingRight = 0;
	chart.legend.marginBottom = 0;
	chart.legend.marginTop = 0;
	legendContainer.layout = "vertical";
	//chart.legend.maxColumns = 1;
	//chart.legend.width = am4core.percent(90);
	chart.legend.valign = "bottom";
	chart.legend.contentAlign = "left";
	//chart.legend.responsive = true;

	// Legend items
	//chart.legend.itemContainers.template.interactionsEnabled = false;
}

function playersToCoords(gameId){
	var currYear = new Date().getFullYear();

	playerRefStr = '/'+gameId+'_2016_'+(currYear-2016)+'_c/p_info';
	var playerRef = firebase.database().ref(playerRefStr);
	var playerQuery = playerRef.orderByChild('srank').limitToFirst(100)
	playerQuery.once('value').then(function(PlayerSnapshot) {
		if (PlayerSnapshot.exists()) {
			playerArr = []
			PlayerSnapshot.forEach(function(childSnapshot){
				playerArr.push(childSnapshot.child('region').val());
			});
			return playerArr;
		} else {
			return [];
		}
	});
}

function countryNameToCC(countryName){
	if (!countryName){
		return 'N/A';
	}
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

function getNAMap(chart){
	return null;
}

function getNARegionMap(chart){
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