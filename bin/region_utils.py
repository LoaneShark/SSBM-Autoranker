import country_converter as coco
from geopy.geocoders import Nominatim
from copy import deepcopy as dcopy
from math import *
from readin_utils import save_dict,load_dict

## REGION UTILS
# returns the region given a location and granularity
# granularity: 1 = country/continent, 2 = region/country, 3 = state
## What to do for small countries in smallest granularity? (e.g. European countries)
## What to do for Japan? (big enough to be level 1 but not divisible going down)
def calc_region(country,state=None,city=None,granularity=2):
	cc = coco.CountryConverter()

	if granularity == 1:
		if country in ["United States","Canada","Japan"]:
			return country
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
	if granularity == 2:
		#if state == None:
		#	return "N/A"
		if country == "Japan":
			return country
		elif country in ["United States","Canada"]:
			if state in ['ME','VT','NH','MA','RI','CT']:
				return 'New England'
			elif state in ['NY','PA','NJ']:
				return 'Tristate'
			elif state in ['MD','VA','WV','DE','DC','District of Columbia']:
				return 'MD/VA'
			elif state in ['NC','SC','GA']:
				return 'South Atlantic'
			elif state in ['FL','PR','VI']:
				return 'Florida & Caribbean'
			elif state in ['OH','KY','TN','AL','MS','IN','IL','MI','WI']:
				return 'Mideast'
			elif state in ['ND','SD','MN','IA','MO','AR','LA','NE','KS','OK']:
				return 'Midwest'
			elif state in ['WY','CO','UT','NV','MT']:
				return 'Rockies'
			elif state in ['WA','OR','BC','AB','ID']:
				return 'Pacific Northwest'
			elif state in ['AZ','NM','TX']:
				return 'Southwest'
			elif state in ['AK','YT','NT','NU']:
				return 'Arctic Circle'
			elif state in ['HI','GU','MP']:
				return 'U.S. Pacific Islands'
			elif state in ['SK','MB','ON']:
				return 'Central Canada'
			elif state in ['QC','NB','NS','PE','NL']:
				return 'Atlantic Canada'
			elif state in ['CA']:
				if city == None:
					return "Misc. Cali"
				city_l = city.lower()
				for qual in ["north ","south ","east ","west ","central ","outer ","new ","old ",", CA"]:
					city_l = city_l.replace(qual," ")
				city_l = city.strip()
				calidict = load_cali_cities()
				if city_l in calidict:
					return calidict[city_l]
				elif city in calidict:
					return calidict[city]
				else:
					#print("Calcuforniating... [%s]"%city)
					geolocator = Nominatim(user_agent="SSBM_Autoranker",timeout=5)
					city_loc = geolocator.geocode(city+", CA, USA")
					city_low = geolocator.geocode(city_l+", CA, USA")
					if city_loc == None:
						calidict[city] = "Misc. Cali"
						save_cali_cities(calidict,to_load=False)
						return "Misc. Cali"
					if is_socal(geolocator,city_loc) or is_socal(geolocator,city_low):
						calidict[city] = "SoCal"
						calidict[city_l] = "SoCal"
						save_cali_cities(calidict,to_load=False)
						return "SoCal"
					else:
						calidict[city] = "NorCal"
						calidict[city_l] = "NorCal"
						save_cali_cities(calidict,to_load=False)
						return "NorCal"
			else:
				return 'N/A'
		else:
			return country
	if granularity == 3:
		if state == None:
			if city == None:
				return "N/A"
			else:
				return city
		elif country in ["United States","Canada","Japan"]:
			if state == 'CA':
				if city is not None:
					return city
			return state
		else:
			return state

# returns True if geopy location is below dividing line
def is_socal(geoloc,location):
	p1 = geoloc.geocode("Atascadero, CA")
	x1,y1 = p1.longitude,p1.latitude
	x_l,y_l = location.longitude,location.latitude
	if x1 == x_l and y1 ==y_l:
		return True
	p2 = geoloc.geocode("Fresno, CA")
	x2,y2 = p2.longitude,p2.latitude
	if x2 == x_l and y2 == y_l:
		return True
	m = ((y2-y1)/(x2-x1))
	b = y1-m*x1
	return y_l < (m*x_l+b)

# returns the regional grouping given either a player id or tag or location
def get_region(dicts,p_id,tag=None,country=None,state=None,city=None,granularity=2,to_calc=False):
	tourneys,ids,p_info,records,skills = dicts
	if not country == None:
		return calc_region(country,state,city,granularity)
	if not tag == None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if to_calc or not 'region' in p_info[p_id]:
		#print(p_info[p_id])
		return calc_region(p_info[p_id]['country'],p_info[p_id]['state'],p_info[p_id]['city'],granularity)
	else:
		return p_info[p_id]['region']

# returns a list of player ids (and their json data if requested) given a regional name
def get_players_by_region(dicts,region,granularity=2,get_data=False):
	tourneys,ids,p_info,records,skills = dicts
	if get_data:
		return [(abs_id,get_player(dicts,abs_id)) for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]
	else:
		return [abs_id for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]

def update_regions(dicts,players):
	tourneys,ids,p_info,records,skills = dicts
	for p_id in players:
		p_info[p_id]['region'] = get_region((tourneys,ids,p_info,records,skills),p_id,to_calc=True)

# saves the given cities in additions, with the given classification (Socal, Norcal, or Misc)
def save_cali_cities(cali={},to_load=True,hard_load=False):
	if to_load:
		cali_load = load_dict('cali','cities','obj')
		if cali_load == {}:
			hard_load = True
		for key in cali_load.keys():
			if key not in cali:
				cali[key] = cali_load[key]
	if hard_load:
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
			if not c in cali:
				cali[c] = 'SoCal'

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
			if c not in cali:
				cali[c] = 'NorCal'

		for c in additions:
			cali[c] = cali_class

	return save_dict(cali,'cali','cities','obj')

def load_cali_cities():
	return load_dict('cali','cities','obj')