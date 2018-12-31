## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
import re
from timeit import default_timer as timer
from copy import deepcopy as dcopy
import country_converter as coco
from geopy.geocoders import Nominatim
## UTIL IMPORTS
from readin_utils import *
from db_utils import load_dict,save_dict

# return the (filtered) result(s) for a tourney
def get_result(dicts,t_id,res_filt=None):
	tourneys,ids,p_info,records = dicts
	t = tourneys[t_id]
	t_labels = t['groups']

	# import all players from this event
	player_ids = [p_id for p_id in ids if (not (p_id in tourneys) and t_id in ids[p_id])]
	player_teams = [p_info[p_id]['team'] for p_id in player_ids]
	player_tags = [p_info[p_id]['tag'] for p_id in player_ids]
	player_paths = [records[p_id]['paths'][t_id] for p_id in player_ids]
	player_places = [records[p_id]['placings'][t_id] for p_id in player_ids]
	player_losses = []
	player_wins = []
	for p_id in player_ids:
		temp_l = []
		for l_id in records[p_id]['losses']:
			for i in range(records[p_id]['losses'][l_id].count(t_id)):
				temp_l.extend([l_id])
		temp_l.reverse()
		player_losses.extend([temp_l])
	for p_id in player_ids:
		temp_w = []
		for w_id in records[p_id]['wins']:
			for i in range(records[p_id]['wins'][w_id].count(t_id)):
				temp_w.extend([w_id])
		temp_w.reverse()
		player_wins.extend([temp_w])
	players = [player_ids,player_teams,player_tags,player_paths,player_places,player_losses,player_wins]
	#print(players)
	#print([len(attr) for attr in players])
	players = [[col[row] for col in players] for row in range(len(players[0]))]
	#print(len(players))

	if not res_filt == None:
		#print(res_filt['team'])
		for player in players.copy():
			p_id,p_team,p_tag,p_path,p_place,p_losses,p_wins = player
			if 'player' in res_filt:
				if not (p_id == res_filt['player'] and not (p_id in tourneys) and t_id in ids[p_id]):
					players.remove(player)
					continue
			if 'tag' in res_filt:
				if not res_filt['tag'] in p_info[p_id]['aliases']:
					players.remove(player)
					continue
			if 'maxplace' in res_filt:
				if p_place > int(res_filt['maxplace']):
					players.remove(player)
					continue
			if 'place' in res_filt:
				if not p_place == int(res_filt['place']):
					players.remove(player)
					continue
			if 'team' in res_filt:
				if not p_info[p_id]['team'] == res_filt['team']:
					players.remove(player)
					continue
			if 'group' in res_filt:
				if not res_filt['group'] in p_path:
					players.remove(player)
					continue
			if 'loss_id' in res_filt:
				if not res_filt['loss_id'] in p_losses:
					players.remove(player)
					continue
			if 'loss_tag' in res_filt:
				if not res_filt['loss_tag'] in [p_info[loss_id]['tag'] for loss_id in p_losses]:
					players.remove(player)
					continue
			if 'win_id' in res_filt:
				if not res_filt['win_id'] in p_wins:
					players.remove(player)
					continue
			if 'win_tag' in res_filt:
				if not res_filt['win_tag'] in [p_info[wins_id]['tag'] for wins_id in p_wins]:
					players.remove(player)
					continue
	return players

# returns a copy of the database containing the dicts of info relating to a given player
# (filtered by event(s) if provided)
def get_player(dicts,p_id,tag=None,t_ids=None,slugs=None):
	tourneys,ids,p_info,records = dicts
	if not tag == None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if not slugs == None:
		t_ids = [tourneys['slugs'][slug] for slug in slugs]

	if not t_ids == None:
		if type(t_ids) == int:
			t_ids = [t_ids]
		if type(t_ids) == list and not t_ids == []:
			reccopy = dcopy(records[p_id])
			for l_id in records[p_id]['losses']:
				temp_l = [t for t in reccopy['losses'][l_id] if t in t_ids]
				if temp_l == []:
					del reccopy['losses'][l_id]
				else:
					reccopy['losses'][l_id] = temp_l
			for w_id in records[p_id]['wins']:
				temp_w = [t for t in reccopy['wins'][w_id] if t in t_ids]
				if temp_w == []:
					del reccopy['wins'][w_id]
				else:
					reccopy['wins'][w_id] = temp_w
			for t_id in records[p_id]['placings']:
				if t_id not in t_ids:
					del reccopy['placings'][t_id]
			for t_id in records[p_id]['paths']:
				if t_id not in t_ids:
					del reccopy['paths'][t_id]
			idcopy = dcopy(ids[p_id])
			for t_id in ids[p_id]:
				if t_id not in t_ids:
					del idcopy[t_id]
			return p_id,p_info[p_id],reccopy,idcopy
		else:
			print("Error: Invalid form for t_ids in call to get_player(): %s"%type(t_ids))
			return False
	else:
		return p_id,p_info[p_id],records[p_id],ids[p_id]

# return (filtered) results for a series of tourneys
def get_results(dicts,t_ids,res_filt=None):
	if type(t_ids) is str:
		if t_ids == "all":
			t_ids = [t_id for t_id in tourneys if not t_id == 'slugs']
		else:
			print("Error:: Invalid tournament id: %s"%t_ids)
	if type(t_ids) is list:
		return [[t_id,get_result(dicts,t_id,res_filt)] for t_id in t_ids]
	else:
		return get_result(dicts,t_ids,res_filt)

def get_abs_id_from_tag(dicts,tag):
	tourneys,ids,p_info,records = dicts
	p_id = [abs_id for abs_id in p_info if tag in p_info[abs_id]['aliases']][0]
	#print(p_info[1000]['aliases'])
	return p_id

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
				return 'Florida/PR'
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
				else:
					#print("Calcuforniating... [%s]"%city)
					geolocator = Nominatim(user_agent="SSBM_Autoranker")
					city_loc = geolocator.geocode(city+", CA, USA")
					city_low = geolocator.geocode(city_l+", CA, USA")
					if city_loc == None:
						calidict[city] = "Misc. Cali"
						save_cali_cities(calidict,to_load=False)
						return "Misc. Cali"
					if is_socal(geolocator,city_loc) or is_socal(geolocator,city_low):
						calidict[city] = "SoCal"
						save_cali_cities(calidict,to_load=False)
						return "SoCal"
					else:
						calidict[city] = "NorCal"
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
	tourneys,ids,p_info,records = dicts
	if not country == None:
		return calc_region(country,state,city,granularity)
	if not tag == None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if to_calc or not 'region' in p_info[p_id]:
		return calc_region(p_info[p_id]['country'],p_info[p_id]['state'],p_info[p_id]['city'],granularity)
	else:
		return p_info[p_id]['region']

# returns a list of player ids (and their json data if requested) given a regional name
def get_players_by_region(dicts,region,granularity=2,get_data=False):
	tourneys,ids,p_info,records = dicts
	if get_data:
		return [(abs_id,get_player(dicts,abs_id)) for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]
	else:
		return [abs_id for abs_id in p_info if get_region(dicts,abs_id,granularity=granularity) == region]

def update_regions(dicts,players):
	tourneys,ids,p_info,records = dicts
	for p_id in players:
		p_info[p_id]['region'] = get_region((tourneys,ids,p_info,records),p_id,to_calc=True)

def list_tourneys(dicts,year=None):
	tourneys,ids,p_info,records = dicts
	if year == None:
		return [tourneys[t_id]['name'] for t_id in tourneys if t_id != 'slugs']
	else:
		return [tourneys[t_id]['name'] for t_id in tourneys if t_id != 'slugs' for t_date in tourney[t_id]['date'] if t_date[2] == year]

# print (filtered) results for a given tourney
def print_result(dicts,t_id,res_filt=None,max_place=64):
	tourneys,ids,p_info,records = dicts
	res = get_result(dicts,t_id,res_filt)
	maxlen = 0
	t = tourneys[t_id]
	t_labels = t['groups']

	players = sorted(res,key=lambda l: (len(l[3]),0-l[4]), reverse=True)
	num_rounds = len(players[0][3])
	roundnames = [t_labels[group] for group in players[0][3]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 2*num_rounds

	print("%s Results | ID: %d"%(tourneys[t_id]['name'],t_id))
	print("\n{:>13.13}".format("Sponsor |"),"{:<24.24}".format("Tag"),"ID #\t","Place\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("Bracket"),"Losses\n")

	for player in players:
		p_id,sp,tag,path,placement,losses,wins = player
		
		# format sponsor
		if sp == None or sp == "":
			sp = "  "
		else:
			if len(sp) > 12:
					sp = sp[:8] + "... |"
			else:
				if sp[-2:] != " |":
					sp = sp + " |"
		# format player tag
		if len(tag) > 24:
			tag = tag[:21]+"..."
		# format losses
		if losses == None or losses == []:
			loss_string = None
		else:
			loss_string = "["+", ".join(str(l) for l in [p_info[loss_id]['tag'] for loss_id in losses])+"]"

		print("{:>13.13}".format(sp),"{:<24.24}".format(tag),"{:>7.7}".format(str(p_id)), \
			"  {:<5.5}".format(str(placement)),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("["+", ".join(str(label) for label in [t_labels[group] for group in path])+"]"),loss_string)

# print (filtered) results for multiple tourneys
def print_results(dicts,t_ids,res_filt=None,max_place=64):
	if type(t_ids) is str:
		if t_ids == "all":
			t_ids = [t_id for t_id in tourneys if not t_id == 'slugs']
		else:
			print("Error:: Invalid tournament id: %s"%t_ids)
	if type(t_ids) is list:
		for t_id in t_ids:
			print_result(dicts,t_id,res_filt,max_place)
	else:
		print_result(dicts,t_ids,res_filt,max_place)

# print a single event (to console)
def print_event(dicts,t_id,max_place=64):
	print_result(dicts,t_id,res_filt={'maxplace':max_place})

# print multiple events (to console)
def print_events(dicts,t_ids,max_place=64):
	if type(t_ids) is list:
		for t_id in t_ids:
			print_result(dicts,t_id,res_filt={'maxplace':max_place})
	else:
		print_result(dicts,t_id,res_filt={'maxplace':max_place})

def old_print_event(dicts,t_id,max_place=64):
	maxlen = 0
	tourneys,ids,p_info,records = dicts
	t = tourneys[t_id]
	t_labels = t['groups']

	player_ids = [p_id for p_id in ids if (not (p_id in tourneys) and t_id in ids[p_id])]
	player_teams = [p_info[p_id]['team'] for p_id in player_ids]
	player_tags = [p_info[p_id]['tag'] for p_id in player_ids]
	player_paths = [records[p_id]['paths'][t_id] for p_id in player_ids]
	player_places = [records[p_id]['placings'][t_id] for p_id in player_ids]
	player_losses = []
	for p_id in player_ids:
		temp = []
		for l_id in records[p_id]['losses']:
			for i in range(records[p_id]['losses'][l_id].count(t_id)):
				temp.extend([l_id])
		player_losses.extend([temp])

	entrants = (player_ids,player_teams,player_tags,player_paths,player_places,player_losses)
	entrants = [[col[i] for col in entrants] for i in range(len(entrants[0]))]
	players = sorted(entrants,key=lambda l: (0-l[4],len(l[3])), reverse=True)

	num_rounds = len(players[0][3])

	roundnames = [t_labels[group] for group in players[0][3]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 4*num_rounds
	#lsbuff = "\t"*(numrounds-len(players[-1][2])+1)

	print("%s Results | ID: %d"%(tourneys[t_id]['name'],t_id))
	print("\n{:>13.13}".format("Sponsor |"),"{:<24.24}".format("Tag"),"ID #\t","Place\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("Bracket"),"Losses\n")

	for player in players:
		p_id,sp,tag,path,placement,losses = player
		#print(player)

		if placement > max_place and max_place > 0:
			break
		else:
			# format sponsor
			if sp == None or sp == "":
				sp = "  "
			else:
				if len(sp) > 12:
						sp = sp[:8] + "... |"
				else:
					if sp[-2:] != " |":
						sp = sp + " |"
			sp_len = 13
			for ch in sp:
				if is_emoji(sp):
					sp_len -= 1
			# format player tag
			tag_len = 24
			if len(tag) > tag_len:
				tag = tag[:tag_len-3]+"..."
			for ch in tag:
				if is_emoji(ch):
					tag_len -= 1
			# format losses
			if losses == None or losses == []:
				losses = None
			else:
				losses = [p_info[loss_id]['tag'] for loss_id in losses]
			# format spacing
			#if len(path) > maxlen:
			#	maxlen = len(path)
			#lsbuff = "\t"*(maxlen-len(path)+1)
			print(("{:>%d.%d}"%(sp_len,sp_len)).format(sp),("{:<%d.%d}"%(tag_len,tag_len)).format(tag),"{:>7.7}".format(str(p_id)), \
				"  {:<5.5}".format(str(placement)),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format(str([t_labels[group] for group in path])),losses)

# saves the given cities in additions, with the given classification (Socal, Norcal, or Misc)
def save_cali_cities(cali={},to_load=True,hard_load=False):
	if to_load:
		cali_load = load_dict('cali','cities','obj')
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

if __name__ == "__main__":
	save_cali_cities(hard_load=True)