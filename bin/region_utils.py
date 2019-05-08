import country_converter as coco
from geopy.geocoders import Nominatim,PickPoint
from copy import deepcopy as dcopy
from math import *
import re
from geopy.exc import GeocoderQuotaExceeded
import time
import glob

from readin_utils import save_dict,load_dict,delete_dict
from arg_utils import *

## REGION UTILS
# returns the region given a location and granularity
# granularity: 1 = country/continent, 2 = region/country, 3 = state, 4 = county/municipality, 5 = city/suburb
## Need to find a better consistent solution for this; keep exceeding query limits for APIs
def calc_region(country,state=None,city=None,granularity=2,force_new=False):
	cc = coco.CountryConverter()

	# handle empty/invalid inputs
	if city in ['N/A','n/a','',' ','  ','None']:
		city == None
	if state in ['N/A','n/a','',' ','  ','None']:
		state == None
	if country in ['N/A','n/a','',' ','  ','None']:
		country == None

	# filter certain countries/territories
	if country != None:
		# remove periods
		country.replace('.','')
		country_low = country.lower()
		if country_low in ['america','united states of america','usa','us','us of a','us of america']:
			country = 'United States'
		if 'virgin islands' in country_low:
			country = 'United States'
			state = 'VI'
		if 'guam' in country_low:
			country = 'United States'
			state = 'GU'
		if 'american samoa' in country_low or ('samoa' in country and any(['united states' in country,'us' in country,'u.s.' in country])):
			country = 'United States'
			state = 'AS'
		if 'marshall islands' in country_low:
			country = 'United States'
			state = 'MH'
		if 'micronesia' in country_low or 'micronesia' in str(state).lower():
			country = 'United States'
			state = 'FM'
		if 'northern marianas' in country_low:
			country = 'United States'
			state = 'MP'
		if 'palau' in country_low:
			country = 'United States'
			state = 'PW'
		if 'd.r.' == country_low:
			country = 'DR'
		if 'prc' == country_low:
			country = 'China'

	## generate a string identifying this general location, for hashing (this eases strain on geopy calls)
	locale_list = [city,state,country]
	# remove anything in parentheses or brackets from location names
	for l_idx in range(len(locale_list)):
		if locale_list[l_idx] != None:
			# remove parentheses and their contents
			locale_list[l_idx] = re.sub('[\(\[].*?[\)\]]', '', locale_list[l_idx])
			# remove slashes
			locale_list[l_idx] = ' '.join(locale_list[l_idx].split('/'))
			locale_list[l_idx] = ' '.join(locale_list[l_idx].split('\\'))
	city,state,country = locale_list
	locstr = ''
	dictstr = ''
	# organize into [city,state,country] format for location string
	# organize into [state,country] for dict string, or [city,country]//[city,state] if only one is available
	if city != None:
		locstr += city +', '
		if state == None or country == None:
			dictstr += city + ', '
	if state != None:
		locstr += state + ', '
		dictstr += state + ', '
	if country != None:
		locstr += country
		dictstr += country
	elif locstr == '':
		return 'N/A'
	else:
		if locstr[0] == ',':
			if locstr[1] == ' ':
				locstr = locstr[2:]
			else:
				locstr = locstr[1:]
		if locstr[-1] == ' ':
			locstr = locstr[:-1]
		if locstr[-1] == ',':
			locstr = locstr[:-1]
	if dictstr == '':
		return 'N/A'
	else:
		dictstr.replace('/',', ')
		dictstr.replace('\\',', ')
		# prune out leading/trailing commas and spaces
		if len(dictstr) > 2:
			if dictstr[0] == ' ':
				dictstr = dictstr[1:]
			if dictstr[0] == ',':
				if dictstr[1] == ' ':
					dictstr = dictstr[2:]
				else:
					dictstr = dictstr[1:]
			if dictstr[-1] == ' ':
				dictstr = dictstr[:-1]
			if dictstr[-1] == ',':
				dictstr = dictstr[:-1]
		elif dictstr == ', ' or dictstr == ' ' or dictstr == '':
			return 'N/A'

	# load region dict to ease strain on geopy
	if force_new:
		locdict = {}
	else:
		locdict = load_city_dict(dictstr)
	# calculate and look up region if not found in dict
	if locstr not in locdict:
		first_call_time = time.perf_counter()
		geocoder_name = 'Nominatim'
		try:
			geoloc = Nominatim(user_agent='SSBM_Autoranker',timeout=5)
			loc = geoloc.geocode(locstr,language='en',addressdetails=True)
		except (ValueError, GeocoderQuotaExceeded):
			geoloc = PickPoint(user_agent='SSBM_Autoranker',timeout=5,api_key='yeaJ8X8QQoJtB7Uo4TsL')
			loc = geoloc.geocode(locstr,language='en',addressdetails=True)
			geocoder_name = 'PickPoint'

		if loc == None:
			temp_locstr = ', '.join(locstr.split(', ')[1:])
			time.sleep(max(1.1-(time.perf_counter()-first_call_time),0.01))
			loc = geoloc.geocode(temp_locstr,language='en',addressdetails=True)
			if loc == None:
				#print('Location not found: %s'%locstr)
				locdict[locstr] = [city,state,None,country,cc.convert(names=[country],to='continent'),None]
				save_city_dict(dictstr,locdict)
				return 'N/A'
		loc = loc.raw['address']
		if 'city' in loc:
			l_city = loc['city']
		elif 'city_district' in loc:
			l_city = loc['city_district']
		elif 'suburb' in loc:
			l_city = loc['suburb']
		else:
			l_city = None
		if 'state' in loc:
			l_state = loc['state']
		else:
			l_state = None
		if 'county' in loc:
			l_county = loc['county']
		elif 'administrative' in loc:
			l_county = loc['administrative']
		elif 'region' in loc:
			l_county = l_state
			l_state = loc['region']
		elif 'suburb' in loc and 'city_district' in loc and not 'city' in loc:
			l_city = loc['suburb']
			l_county = loc['city_district']
		else:
			l_county = None
		# Can't believe I had to add this check but here we are
		if 'continent' in loc and loc['continent'] == 'Antarctica':
			l_country = None
		else:
			l_country = loc['country']
		if l_country == 'America':
			l_country = 'United States'
		l_continent = cc.convert(names=[l_country],to='continent')
		if 'latitude' in loc and 'longitude' in loc:
			l_coords = (loc['latitude'],loc['longitude'])
		else:
			l_coords = None
		locdict[locstr] = [l_city,l_state,l_county,l_country,l_continent,l_coords]
		# save new location
		save_city_dict(dictstr,locdict)
	else:
		[l_city,l_state,l_county,l_country,l_continent,l_coords] = locdict[locstr]

	# return latitude and longitude
	if granularity == 0:
		return l_coords
	# return continent (or country for US/CA)
	if granularity == 1:
		if l_country in ['United States','USA','U.S.A.','United States of America','Canada','Japan']:
			return l_country
		elif l_continent != None:
			return l_continent
		else:
			#country_alpha2 = pycountry.countries.get(name=country).alpha_2
			continent = cc.convert(names=[country],to='continent')
			if continent == 'E':
				return 'Europe'
			if continent == 'NA':
				return 'Central America'
			if continent == 'SA':
				return 'South America'
			if continent == 'A':
				return 'Asia'
			return continent
	# return greater region for US/CA, country otherwise
	if granularity == 2:
		#if state == None:
		#	return 'N/A'
		if l_country == 'Japan':
			return l_state
		elif l_country in ['United States','USA','U.S.A.','US','US of A','United States of America','America','Canada','CA','CAN'] or \
				country in ['United States','USA','U.S.A.','US','US of A','United States of America','America','Canada','CA','CAN']:
			if state in ['ME','VT','NH','MA','RI','CT'] or \
						l_state in ['Maine','Vermont','New Hampshire','Massachusetts','Rhode Island','Connecticut']:
				return 'New England'
			elif state in ['NY','PA','NJ'] or \
						l_state in ['New York','Pennsylvania','New Jersey']:
				return 'Tristate'
			elif state in ['MD','VA','WV','DE','DC','District of Columbia','Washington DC','Washington D.C.','D.C.'] or \
						l_state in ['Maryland','Virginia','West Virginia','Delaware','DC','District of Columbia','Washington DC','Washington D.C.','D.C.']:
				return 'MD/VA'
			elif state in ['NC','SC','GA'] or \
						l_state in ['North Carolina','South Carolina','Georgia']:
				return 'South Atlantic'
			elif state in ['PR','VI','P.R.'] or \
						l_state in ['Puerto Rico','Virgin Islands','PR','P.R.'] or \
						l_country in ['Puerto Rico','Virgin Islands','PR','P.R.']:
				return 'U.S. Caribbean Islands'
			elif state in ['OH','KY','TN','AL','MS','IN','IL','MI','WI'] or \
						l_state in ['Ohio','Kentucky','Tennessee','Alabama','Mississippi','Indiana','Illinois','Michigan','Wisconsin']:
				return 'Mideast'
			elif state in ['ND','SD','MN','IA','MO','AR','LA','NE','KS','OK'] or \
						l_state in ['North Dakota','South Dakota','Minnesota','Iowa','Missouri','Arkansas','Louisiana','Nebraska','Kansas','Oklahoma']:
				return 'Midwest'
			elif state in ['WY','CO','UT','NV','MT','ID'] or \
						l_state in ['Wyoming','Colorado','Utah','Nevada','Montana','Idaho']:
				return 'Rockies'
			elif state in ['WA','OR','BC','AB'] or \
						l_state in ['Washington','Oregon','British Columbia','Alberta']:
				return 'Pacific Northwest'
			elif state in ['AZ','NM','TX'] or \
						l_state in ['Arizona','New Mexico','Texas']:
				return 'Southwest'
			elif state in ['AK','YT','NT','NU'] or \
						l_state in ['Alaska','Yukon','Yukon Territory','Northwest Territories','Nunavut']:
				return 'Arctic Circle'
			elif state in ['HI','GU','MP','AS','MH','FM','PW'] or \
						l_state in ['Hawaii','Hawai\'i','Guam','Northern Marianas','Samoa','American Samoa','Marshall Islands','Micronesia','Northern Marianas','Palau'] or \
						l_country in ['Guam','Samoa','American Samoa','Marshall Islands','Micronesia','Northern Marianas','Palau'] or \
						country in ['Guam','Samoa','American Samoa','Marshall Islands','Micronesia','Northern Marianas','Palau']:
				return 'U.S. Pacific Islands'
			elif state in ['SK','MB','ON'] or \
						l_state in ['Saskatchewan','Manitoba','Ontario']:
				return 'Central Canada'
			elif state in ['QC','NB','NS','PE','NL'] or \
						l_state in ['Quebec','Québec','New Brunswick','Nova Scotia','Prince Edward Island','Newfoundland and Labrador','Newfoundland & Labrador','Newfoundland','Labrador']:
				return 'Atlantic Canada'
			elif state in ['CA']:
				if city == None:
					return 'Misc. Cali'
				city_l = city.lower()
				for qual in ['north ','south ','east ','west ','central ','outer ','new ','old ',', CA']:
					city_l = city_l.replace(qual,' ')
				city_l = city.strip()
				calidict = load_city_dict('CA_cities')
				if city_l in calidict:
					return calidict[city_l]
				elif city in calidict:
					return calidict[city]
				else:
					#print('Calcuforniating... [%s]'%city)
					try:
						geolocator = Nominatim(user_agent='SSBM_Autoranker',timeout=5)
						loc = geolocator.geocode(locstr,language='en')
					except (ValueError, GeocoderQuotaExceeded):
						geolocator = PickPoint(user_agent='SSBM_Autoranker',timeout=5,api_key='yeaJ8X8QQoJtB7Uo4TsL')
						loc = geolocator.geocode(locstr,language='en')
					city_loc = geolocator.geocode(city+', CA, USA')
					#city_low = geolocator.geocode(city_l+', CA, USA')
					if city_loc == None:
						calidict[city] = 'Misc. Cali'
						save_city_dict('CA_cities',calidict,to_load=False)
						return 'Misc. Cali'
					if is_socal(geolocator,city_loc): #or is_socal(geolocator,city_low):
						calidict[city] = 'SoCal'
						calidict[city_l] = 'SoCal'
						save_city_dict('CA_cities',calidict,to_load=False)
						return 'SoCal'
					else:
						calidict[city] = 'NorCal'
						calidict[city_l] = 'NorCal'
						save_city_dict('CA_cities',calidict,to_load=False)
						return 'NorCal'
			elif state in ['FL']:
				if city == None:
					return 'Misc. FL'
				city_l = city.lower()
				for qual in ['north ','south ','east ','west ','central ','outer ','new ','old ',', FL']:
					city_l = city_l.replace(qual,' ')
				city_l = city.strip()
				floridict = load_city_dict('FL_cities')
				if city_l in floridict:
					return floridict[city_l]
				elif city in floridict:
					return floridict[city]
				else:
					#print('Calcuforniating... [%s]'%city)
					try:
						geolocator = Nominatim(user_agent='SSBM_Autoranker',timeout=5)
						loc = geolocator.geocode(locstr,language='en')
					except (ValueError, GeocoderQuotaExceeded):
						geolocator = PickPoint(user_agent='SSBM_Autoranker',timeout=5,api_key='yeaJ8X8QQoJtB7Uo4TsL')
						loc = geolocator.geocode(locstr,language='en')
					city_loc = geolocator.geocode(city+', FL, USA')
					#city_low = geolocator.geocode(city_l+', FL, USA')
					if city_loc == None:
						floridict[city] = 'Misc. FL'
						save_city_dict('FL_cities',floridict,to_load=False)
						return 'Misc. FL'
					if is_sfl(geolocator,city_loc): #or is_sfl(geolocator,city_low):
						floridict[city] = 'SFL'
						floridict[city_l] = 'SFL'
						save_city_dict('FL_cities',floridict,to_load=False)
						return 'SFL'
					else:
						floridict[city] = 'CFL'
						floridict[city_l] = 'CFL'
						save_city_dict('FL_cities',floridict,to_load=False)
						return 'CFL'
			else:
				return 'N/A'
		else:
			return l_country
	# return state
	if granularity == 3:
		if l_state == None:
			if l_city == None:
				return 'N/A'
			else:
				#return l_city
				return 'N/A'
		#elif l_state in ['California','Florida']:
			#if l_city is not None:
			#	return l_city + '`'
			#else:
			#	return l_state
		else:
			return l_state
	# return county
	if granularity == 4:
		if l_county == None:
			return 'N/A'
		else:
			return l_county
	# return city
	if granularity == 5:
		if l_city == None:
			return 'N/A'
		else:
			return l_city

# returns True if geopy location is below dividing line
def is_socal(geoloc,location):
	#p1 = geoloc.geocode('Atascadero, CA')
	#x1,y1 = p1.longitude,p1.latitude
	x1,y1 = -120.6707255,35.4894169
	x_l,y_l = location.longitude,location.latitude
	if x1 == x_l and y1 == y_l:
		return True
	#p2 = geoloc.geocode('Fresno, CA')
	#x2,y2 = p2.longitude,p2.latitude
	x2,y2 = -119.708861260756,36.7295295
	if x2 == x_l and y2 == y_l:
		return True
	m = ((y2-y1)/(x2-x1))
	b = y1-m*x1
	return y_l < (m*x_l+b)

# returns True if geopy location is below dividing line
def is_sfl(geoloc,location):
	#p1 = geoloc.geocode('Jupiter, FL')
	#x1,y1 = p1.longitude,p1.latitude
	x1,y1 = -80.1210891406095,26.9260832
	x_l,y_l = location.longitude,location.latitude
	if x1 == x_l and y1 == y_l:
		return True
	#p2 = geoloc.geocode('Fort Myers, FL')
	#x2,y2 = p2.longitude,p2.latitude
	x2,y2 = -81.8723084,26.640628
	if x2 == x_l and y2 == y_l:
		return True
	m = ((y2-y1)/(x2-x1))
	b = y1-m*x1
	return y_l < (m*x_l+b)

# returns the regional grouping given either a player id or tag or location
def get_region(dicts,p_id,tag=None,country=None,state=None,city=None,granularity=2,to_calc=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	if not country == None:
		return calc_region(country,state,city,granularity)
	if not tag == None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if to_calc or not 'region' in p_info[p_id]:
		#print(p_info[p_id])
		if country == None and state == None and city == None:
			return calc_region(p_info[p_id]['country'],p_info[p_id]['state'],p_info[p_id]['city'],granularity)
		else:
			return calc_region(country,state,city,granularity)
	else:
		return p_info[p_id]['region'][granularity]

# returns a list of player ids (and their json data if requested) given a regional name
def get_players_by_region(dicts,region,granularity=2,get_data=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	if get_data:
		return [(abs_id,get_player(dicts,abs_id)) for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]
	else:
		return [abs_id for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]

def update_regions(dicts,players,granularities=range(1,6)):
	tourneys,ids,p_info,records,skills,meta = dicts
	for p_id in players:
		for gran in granularities:
			p_info[p_id]['region'][gran] = get_region((tourneys,ids,p_info,records,skills,meta),p_id,granularity=gran,to_calc=True)

# saves the given cities in additions, with the given classification (Socal, Norcal, or Misc)
def save_city_dict(state,cities={},to_load=True,hard_cali_load=False):
		#load_res = load_dict(state,'cities','obj')
	load_res = load_dict('cities',None,'..\\lib')

	if to_load:
		if state in load_res:
			city_load = load_res[state]
		else:
			city_load = {}
		if city_load == {} and state == 'CA_cities':
			hard_cali_load = True
		for key in city_load.keys():
			if key not in cities:
				cities[key] = city_load[key]
	if hard_cali_load:
		SC = ['Los Angeles','LA','San Diego','SD','Long Beach','Bakersfield','Anaheim','Santa Ana',\
					'Riverside','Chula Vista','Irvine','San Bernardino','Oxnard','Fontana','Moreno','Moreno Valley','SoCal','San Dimas',\
					'Huntington','Huntington Beach','Glendale','Santa Clarita','Garden Grove','Oceanside','Rancho Cucamonga','Claremont',\
					'Cucamonga','Ontario','Corona','Lancaster','Palmdale','Pomona','Escondido','Torrance','Pasadena','Glendora'\
					'Orange','Fullerton','Thousand Oaks','Simi','Simi Valley','Victorville','El Monte','Downey','Costa Mesa',\
					'Carlsbad','Inglewood','Ventura','Temecula','West Covina','Murrieta','Norwalk','Burbank','Santa Maria',\
					'Beverly Hills','Beverly','Hollywood','West Hollywood','Sunset Strip','Los Feliz','Westwood','Culver City',\
					'El Cajon','Rialto','Jurupa','Jurupa Valley','Compton','Vista','Mission Viejo','South Gate','Carson',\
					'Santa Monica','San Marcos','Hesperia','Westminster','Santa Barbara','Hawthorne','Whittier','Newport Beach',\
					'Indio','Alhambra','Menifee','Chino','Buena Park','Chino Hills','Upland','Perris','Lynwood','Apple Valley',\
					'Redlands','Redondo Beach','Yorba Linda','Camarillo','Laguna Niguel','Orange','San Clemente','Pico Rivera',\
					'Montebello','Encinitas','La Habra','Monterey Park','Gardena','National City','Lake Elsinore','Huntington Park',\
					'La Mesa','Arcadia','Santee','Eastvale','Fountain Valley','Diamond Bar','Fountain','Paramount','Rosemead','Highland'\
					'Midway City','Garden Grove','Tustin','Newport','Seal Beach','Manhattan Beach','Hawthorne','Lawndale','Gardena',\
					'Inglewood','Lynwood','Bel Air','Reseda','Van Nuys','Woodland Hills']
		for c in SC:
			if not c in cities:
				cities[c] = 'SoCal'

		NC = ['San Jose','San Francisco','SFO','SF','SJ','San Fran','SanFran','Sanfran','Fresno',\
					'Sacramento','Oakland','Stockton','Fremont','Modesto','Santa Rosa','Elk Grove','Salinas','Hayward','NorCal',\
					'Silicon Valley','Sunnyvale','Visalia','Concord','Roseville','Santa Clara','Vallejo','Berkeley','Newark',\
					'Fairfield','Richmond','Antioch','Daly City','San Mateo','Clovis','Vacaville','Redding','Chico','El Dorado Hills',\
					'San Leandro','Citrus Heights','Tracy','Livermore','Merced','Napa','Napa Valley','Redwood City','Foster',\
					'Redwood','Sequoia','Mountain View','Alameda','Folsom','San Ramon','Pleasanton','Union City','Foster City',\
					'Turlock','Manteca','Milpitas','Davis','Yuba City','Yuba','Union','Daly','Rancho Cordova','Palo Alto',\
					'Walnut Creek','South San Francisco','Pittsburg','Lodi','Madera','Santa Cruz','Tulare','Cupertino',\
					'Petaluma','San Rafael','Rocklin','Woodland','Porterville','Hanford','Novato','Brentwood','Watsonville',\
					'Pacifica','San Bruno','Montara','Brisbane']
		for c in NC:
			if c not in cities:
				cities[c] = 'NorCal'

	load_res[state] = cities

	#return save_dict(cities,state,'cities','obj')
	return save_dict(load_res,'cities',None,'..\\lib')
	

# loads city dicts
def load_city_dict(state):
	d = load_dict('cities',None,'..\\lib')
	if state in d:
		return d[state]
	else:
		return {}

# cleans up deprecated dict filenames, and merges subsequent duplicates
# moves all dicts from obj to new single city dict in lib
# (DEPRECATED)
def clean_city_dicts(delete_dirty=True):
	i = 0
	for dictfile in glob.iglob('.\\obj\\cities\\*.pkl'):
		i += 1
		#print (dictfile)
		dictname = dictfile.split('\\')[-1] # remove the directories
		#print(dictname)
		dictname = dictname[:-4] 	# remove the .pkl
		#print(dictname)

		tempname = str(dictname)
		clear_front = False
		while not clear_front:
			if len(tempname) == 0 or tempname == '' or tempname == None:
				clear_front = True
			elif tempname[0] in [' ',',']:
				tempname = tempname[1:]
			else:
				clear_front = True
		clear_back = False
		while not clear_back:
			if len(tempname) == 0 or tempname == '' or tempname == None:
				clear_back = True
			elif tempname[-1] in [' ',',']:
				tempname = tempname[:-1]
			elif tempname[-1] in ['.']:
				if tempname.count('.') == 1:
					tempname = tempname[:-1]
				else:
					print(tempname.count('.'))
			else:
				clear_back = True

		dictdata = load_city_dict(dictname)
		#print(dictname,'\t',tempname)
		save_city_dict(tempname,cities=dictdata)
		if delete_dirty:
			delete_dict(dictname,'cities',loc='obj')

if __name__ == '__main__':
	#geoloc = Nominatum(user_agent='SSBM_Autoranker',timeout=5)
	#geoloc = PickPoint(user_agent='SSBM_Autoranker',timeout=5,api_key='yeaJ8X8QQoJtB7Uo4TsL')
	#p1 = geoloc.geocode('Atascadero, CA')
	#p2 = geoloc.geocode('Fresno, CA')
	#x1,y1 = p1.longitude,p1.latitude
	#x2,y2 = p2.longitude,p2.latitude
	#print(x1,y1)
	#print(x2,y2)

	#p1 = geoloc.geocode('Jupiter, FL')
	#p2 = geoloc.geocode('Fort Myers, FL')
	#x1,y1 = p1.longitude,p1.latitude
	#x2,y2 = p2.longitude,p2.latitude
	#print(x1,y1)
	#print(x2,y2)

	#p = geoloc.geocode('Cardiff, UK',language='en',addressdetails=True)
	#print(p.raw)

	#clean_city_dicts()

	#d = load_dict('cities',None,'..\\lib')
	#print(d.keys())
	'''
	fl_dict = load_dict('FL_cities','cities','obj')

	print(save_city_dict('FL_cities',cities=fl_dict))
	print(save_city_dict('CA_cities',cities={},hard_cali_load=True))

	fl_dict = load_city_dict('FL_cities')
	ca_dict = load_city_dict('CA_cities')

	print(ca_dict['Los Angeles'])
	print(fl_dict['Miami'])'''
	for gran in range(1,6):
		print(gran)
		print(calc_region('Japan',city='Tokyo',granularity=gran))

	#save_dict(cities,state,'cities','obj')
