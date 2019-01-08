## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
import json
import argparse
import shutil
from timeit import default_timer as timer
from copy import deepcopy as dcopy
import country_converter as coco
from geopy.geocoders import Nominatim
from math import *
## UTIL IMPORTS
from readin import readin,set_readin_args
from readin_utils import *
import scraper

## ARGUMENT PARSING
parser = argparse.ArgumentParser()
parser.add_argument('-v','--verbosity',help='verbosity [0-9]',default=0)
parser.add_argument('-s','--save',help='save db/cache toggle (default True)',default=True)
parser.add_argument('-l','--load',help='load db/cache toggle (default True)',default=True)
parser.add_argument('-ls','--load_slugs',help='load slugs toggle (default True)',default=True)
parser.add_argument('-ff','--force_first',help='force the first criteria-matching event to be the only event (default True)',default=True)
parser.add_argument('-g','--game',help='game id to be used: Melee=1, P:M=2, Wii U=3, 64=4, Ultimate=1386 (default melee)',default=1)
parser.add_argument('-fg','--force_game',help='game id to be used, force use (cannot scrape non-smash slugs)',default=False)
parser.add_argument('-y','--year',help='The year you want to analyze (for ssbwiki List of Majors scraper)(default 2018)',default=2018)
parser.add_argument('-yc','--year_count',help='How many years to analyze from starting year',default=0)
parser.add_argument('-t','--teamsize',help='1 for singles bracket, 2 for doubles, 4+ for crews (default 1)',default=1)
parser.add_argument('-d','--displaysize',help='lowest placing shown on pretty printer output, or -1 to show all entrants (default 64)',default=64)
parser.add_argument('-sl','--slug',help='tournament URL slug',default=None)
parser.add_argument('-ss','--short_slug',help='shorthand tournament URL slug',default=None)
parser.add_argument('-p','--print',help='print tournament final results to console as they are read in (default False)',default=False)
parser.add_argument('-c','--collect_garbage',help='delete phase data after tournament is done being read in (default True)',default=True)
parser.add_argument('-ar','--use_arcadians',help='count arcadian events (default False)',default=False)
args = parser.parse_args()

collect = args.collect_garbage
v = int(args.verbosity)
if not args.short_slug == None:
	args.slug = get_slug(args.short_slug)
to_save_db = args.save
to_load_db = args.load
if args.load == "False":
	args.load == False
	to_load_db = False
if args.save == "False":
	args.save == False
	to_save_db = False
to_load_slugs = args.load_slugs
if args.load_slugs == "False":
	to_load_slugs = False
db_slug = args.slug
db_game = int(args.game)
if args.force_game:
	db_game = int(args.force_game)
db_year = int(args.year)
db_year_count = int(args.year_count)
if db_year_count == 0:
	db_yearstr = str(db_year)
else:
	db_yearstr = str(db_year)+"-"+str(db_year+db_year_count)
count_arcadians = args.use_arcadians
if count_arcadians == -1:
	only_arcadians = True
else:
	only_arcadians = False
teamsize = int(args.teamsize)

# main loop. calls scraper to get slugs for every major that happened
# in the specified year for the specified game (per smash.gg numeric id value)
# returns in the form of 4 dicts: tourneys,ids,p_info,records
def read_majors(game_id=int(db_game),year=int(db_year),base=None):
	set_readin_args(args)
	#slugs = ["genesis-5","summit6","shine2018","tbh8","summit7"]
	fails = []
	scrape_load = False
	slug_given = False
	if db_slug == None:
		if to_load_slugs:
			scrape_load = True
			if v >= 3:
				print("Loading saved slugs...")
			slugs = load_slugs(game_id,year)
			if slugs == False or slugs == []:
				if v >= 3:
					print("Saved slugs not found.")
				slugs = scraper.scrape(game_id,year,v)
				scrape_load = False
		else:
			slugs = scraper.scrape(game_id,year,v)
		fails = [event[1] for event in slugs if type(event) is tuple]
		slugs = [event for event in slugs if type(event) is str]
	elif type(db_slug) is list:
		slugs = db_slug
		slug_given = True
	else:
		#print(type(db_slug))
		slugs = [db_slug]
		slug_given = True
	if v >= 3 and not scrape_load and not slug_given:
		print("Scraped the following slugs:")
		print(slugs)
	if not fails == [] and v > 0:
		print("The following majors could not be read (no smash.gg bracket found)")
		print(fails)
	if to_save_db and not scrape_load and not slug_given:
		save_slugs(slugs,game_id,year,to_save_db=to_save_db)
	return(read_tourneys(slugs,ver=game_id,year=year,base=base))

def set_db_args(args):
	collect = args.collect_garbage
	v = int(args.verbosity)
	if not args.short_slug == None:
		args.slug = get_slug(args.short_slug)
	to_save_db = args.save
	to_load_db = args.load
	if args.load == "False":
		args.load == False
		to_load_db = False
	if args.save == "False":
		args.save == False
		to_save_db = False
	db_slug = args.slug
	db_game = args.game
	db_year = args.year

## AUXILIARY FUNCTIONS
# loads database and stores any tournament data not already present given the url slug
def read_tourneys(slugs,ver='default',year=None,base=None):
	if year != None:
		verstr = '%s/%s'%(ver,db_yearstr)
	else:
		verstr = ver

	if base == None:
		[tourneys,ids,p_info,records] = easy_load_db(verstr)
	else:
		tourneys,ids,p_info,records = base

	if v >= 4 and len(tourneys.keys())>1:
		print("Loaded Tourneys: " + str([tourneys[t_id]['name'] for t_id in tourneys if not t_id == 'slugs']))
	#print(tourneys)
	#dicts = (tourneys,ids,p_info,records)
	#print(tourneys,ids,p_info,records)

	for slug in slugs:
		if slug not in tourneys['slugs']:
			readins = readin(slug)
			if readins:
				if v >= 4:
					print("Importing to DB...")
				if store_data(readins,(tourneys,ids,p_info,records),slug):
					if to_save_db:
						save_db((tourneys,ids,p_info,records),verstr)
					t_id = tourneys['slugs'][readins[0][2]]
					if collect:
						delete_tourney_cache(t_id)
	return tourneys,ids,p_info,records

# helper function to store all data from a call to readin
def store_data(readins,dicts,slug):
	t_info,entrants,names,paths,wins,losses = readins
	tourneys,ids,p_info,records = dicts
	if len(entrants.keys()) > 1:
		if store_players(entrants,names,t_info,dicts):
			if store_records(wins,losses,paths,t_info,dicts):
				if store_tourney(slug,t_info,names['groups'],dicts):
					return True
	return False

# stores data through absolute player IDs (converting from entrant IDs)
def store_players(entrants,names,t_info,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records = dicts
	if t_id not in tourneys:
		# store teams/crews instead if this is a teams competition
		#if teamsize == 2 or teamsize == 3:
		#	return store_teams(entrants,names,t_info,dicts)
		#elif teamsize > 3:
		#	return store_crews(entrants,names,t_info,dicts)
		# store all entrant/player-specific info from this tournament
		for e_id in entrants:
			#e_id = entrant[2]
			for abs_id in entrants[e_id][1]:
				idx = entrants[e_id][1].index(abs_id)
				# store matrix to get entrant ids for each tourney given absolute id'
				# (and also to get the reverse)
				if abs_id not in ids:
					ids[abs_id] = {}
				ids[abs_id][t_id] = e_id
				if t_id not in ids:
					ids[t_id] = {}
				ids[t_id][e_id] = abs_id

				# store dict for each player with keys for:
				# team, tag, firstname, lastname, state, country
				if abs_id not in p_info:
					p_info[abs_id] = {}
				if names[e_id][0][idx] == None:
					if 'team' not in p_info[abs_id]:
						p_info[abs_id]['team'] = names[e_id][0][idx]
				else:
					p_info[abs_id]['team'] = names[e_id][0][idx]
				if 'aliases' not in p_info[abs_id]:
					p_info[abs_id]['aliases'] = []
				if names[e_id][1][idx] not in p_info[abs_id]['aliases']:
					p_info[abs_id]['aliases'].extend([names[e_id][1][idx]])
				p_info[abs_id]['tag'] = names[e_id][1][idx]
				for key,info in zip(['firstname','lastname','state','country','city'],entrants[e_id][3][idx]):
					if key in p_info[abs_id]:
						if not (info == 'N/A' or info == '' or info == "" or info == None):
							p_info[abs_id][key] = info
					else:
						p_info[abs_id][key] = info
				if 'region' not in p_info[abs_id]:
					p_info[abs_id]['region'] = get_region(dicts,abs_id,granularity=2)
				else:
					if p_info[abs_id]['region'] == 'N/A' or p_info[abs_id]['region'] == None:
						p_info[abs_id]['region'] = get_region(dicts,abs_id,granularity=2)

				# store ranking data, with initial values if needed
				if 'elo' not in p_info[abs_id]:
					p_info[abs_id]['elo'] = 1500.
				# glicko stores a tuple with (rating,RD,volatility)
				if 'glicko' not in p_info[abs_id]:
					p_info[abs_id]['glicko'] = (1500.,350.,0.06)
				if 'iagorank' not in p_info[abs_id]:
					p_info[abs_id]['iagorank'] = -9999.
				if 'sets_played' not in p_info[abs_id]:
					p_info[abs_id]['sets_played'] = 0

			#print(ids[abs_id])
	#else:
		#print(t_id)
		#print(tourneys)
		#print(tourneys[t_id])
	return True

# stores win/loss records
def store_records(wins,losses,paths,t_info,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records = dicts
	#print(t_id)
	for abs_id in ids:
		if not (abs_id in tourneys or abs_id == t_id):			# ignore id for present or past tournaments
			if t_id in ids[abs_id]:								# ignore id if not an entrant in this tourney
				e_id = ids[abs_id][t_id]

				if abs_id not in records:
					records[abs_id] = {}
					records[abs_id]['wins'] = {}
					records[abs_id]['losses'] = {}
					records[abs_id]['placings'] = {}
					records[abs_id]['performances'] = {}
					records[abs_id]['paths'] = {}

				# store final placement by tourney id
				records[abs_id]['placings'][t_id] = paths[e_id][0]
				# store path through bracket by tourney id
				records[abs_id]['paths'][t_id] = paths[e_id][1]

				# used for elo
				expected_score = 0.
				actual_score = 0.
				# used for glicko
				glicko_scores = []

				# store wins and losses
				if e_id in wins:
					for win in wins[e_id]:
						l_id = ids[t_id][win[0]]
						if l_id not in records[abs_id]['wins']:
							records[abs_id]['wins'][l_id] = {}
							records[abs_id]['wins'][l_id] = [t_id]
						else:
							records[abs_id]['wins'][l_id].extend([t_id])

						p_info[abs_id]['sets_played'] += 1
						actual_score += 1.
						expected_score += exp_score(p_info[abs_id]['elo'],p_info[l_id]['elo'])

						glicko_scores.extend([(1.,l_id)])
				if e_id in losses:
					for loss in losses[e_id]:
						w_id = ids[t_id][loss[0]]
						if w_id not in records[abs_id]['losses']:
							records[abs_id]['losses'][w_id] = {}
							records[abs_id]['losses'][w_id] = [t_id]
						else:
							records[abs_id]['losses'][w_id].extend([t_id])

						p_info[abs_id]['sets_played'] += 1
						actual_score += 0.
						expected_score += exp_score(p_info[abs_id]['elo'],p_info[w_id]['elo'])

						glicko_scores.extend([(0.,w_id)])

				# update elo ratings after event
				p_info[abs_id]['elo'] = update_elo(p_info[abs_id]['elo'],expected_score,actual_score,p_info[abs_id]['sets_played'])

				# store event performance by tourney id
				records[abs_id]['performances'][t_id] = calc_performance(records,p_info,abs_id,t_id)
				#records[abs_id]['performances'][t_id] = calc_performance(ids,records,wins,losses,e_id,t_id)
	p_info[abs_id]['glicko'] = update_glicko(p_info,ids,glicko_scores,t_id)

	return True

# stores tourney meta info and marks tournament as imported
def store_tourney(slug,t_info,group_names,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records = dicts
	tourneys[t_id] = {}
	tourneys[t_id]['name'] = t_name
	tourneys[t_id]['slug'] = t_slug
	tourneys[t_id]['shortSlug'] = t_ss
	tourneys[t_id]['type'] = t_type
	tourneys[t_id]['date'] = t_date
	tourneys[t_id]['region'] = t_region
	tourneys[t_id]['numEntrants'] = t_size
	if 'slugs' not in tourneys:
		tourneys['slugs'] = {}
	tourneys['slugs'][t_slug] = t_id
	tourneys['slugs'][t_ss] = t_id
	tourneys['slugs'][slug] = t_id
	if 'groups' not in tourneys[t_id]:
		tourneys[t_id]['groups'] = {}
	tourneys[t_id]['groups'] = group_names
		
	return True

# delete all data imported from a tourney
# (keeps absolute player data such as ID, meta info)
# **does NOT save db automatically**
def delete_tourney(dicts,t_id,slug=None):
	tourneys,ids,p_info,records = dicts
	if not slug == None:
		t_id = tourneys['slugs'][slug]

	if t_id in tourneys:
		for abs_id in dcopy(ids):
			if abs_id in ids:
				if t_id in ids[abs_id] and t_id in ids:
					# remove entrant ids/data
					del ids[abs_id][t_id]
					del ids[t_id]

				if abs_id in records and t_id in records[abs_id]['placings']:
					# remove player records for this tourney
					del records[abs_id]['placings'][t_id]
					del records[abs_id]['paths'][t_id]

					for loss in records[abs_id]['losses']:
						if t_id in records[abs_id]['losses'][loss]:
							records[abs_id]['losses'][loss] = [tempid for tempid in records[abs_id]['losses'][loss] if not tempid == t_id]
					for win in records[abs_id]['wins']:
						if t_id in records[abs_id]['wins'][win]:
							records[abs_id]['wins'][win] = [tempid for tempid in records[abs_id]['wins'][win] if not tempid == t_id]

				# remove tournament records for this tourney
				for t_s in dcopy(tourneys['slugs']):
					if tourneys['slugs'][t_s] == t_id:
						del tourneys['slugs'][t_s]
				if t_id in tourneys:
					del tourneys[t_id]
	return tourneys,ids,p_info,records

# delete all data associated with a given player
# (player id, meta info, tourney results/records are deleted!!!)
# **does NOT save db automatically**
def delete_player(dicts,p_id,tag=None):
	tourneys,ids,p_info,records = dicts
	abs_id,p_meta,p_records,p_ids = get_player(dicts,p_id,tag)

	# delete player records
	del records[abs_id]
	del p_info[abs_id]
	del ids[abs_id]
	# delete instances of player from other players' records
	for l_id in p_records['losses']:
		del[records][l_id]['wins'][abs_id]
	for w_id in p_records['wins']:
		del[records][w_id]['losses'][abs_id]

	return tourneys,ids,p_info,records

# creates a blank db and writes over any existing one in the given directory
def clear_db(ver,loc='db'):
	dicts = load_db(None,force_blank=True)
	save_db(dicts,ver,loc=loc)
	return dicts

# used to save datasets/hashtables
def save_db(dicts,ver,loc='db'):
	if int(args.teamsize) == 2:
		ver = str(ver) + " (DUBS)"
	if int(args.teamsize) >= 4:
		ver = str(ver) + " (CREWS)"
	if only_arcadians:
		ver = str(ver)+" (ARC)"
	if to_save_db:
		if v >= 3:
			print("Saving DB...")
		for data,name in zip(dicts,['tourneys','ids','p_info','records']):
			save_dict(data,name,ver,loc)
	else:
		return False

# used to load datasets/hashtables
def load_db(ver,loc='db',force_blank=False):
	#if args.teamsize == 2:
	#	ver = str(ver) + " (DUBS)"
	#if only_arcadians:
	#	ver = str(ver)+" (ARC)"
	if to_load_db and not force_blank:
		if v >= 3:
			print("Loading DB...")
		return [load_dict(name,ver,loc) for name in ['tourneys','ids','p_info','records']]
	else:
		return [load_dict(name,'blank',loc='db') for name in ['tourneys','ids','p_info','records']]

# used to load datasets/hashtables; auto-fills ver modifiers based on args
def easy_load_db(ver,loc='db',force_blank=False):
	if int(args.teamsize) == 2:
		ver = str(ver) + " (DUBS)"
	if int(args.teamsize) >= 4:
		ver = str(ver) + " (CREWS)"
	if int(only_arcadians):
		ver = str(ver)+" (ARC)"
	return load_db(ver,loc,force_blank)

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
		#print(p_info[p_id])
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

## ELO CALCULATION UTILS
# Calculates the event performance rating for a single event
# using the FIDE "rule of 400" PR estimator
def calc_performance(records,p_info,abs_id,t_id):
	w_count,l_count = 0.,0.
	skills = 0.

	wins = records[abs_id]['wins']
	losses = records[abs_id]['losses']

	for l_id in wins:
		#l_abs_id = ids[t_id][wins[e_id][0]]

		skills += p_info[l_id]['elo']
		w_count += wins[l_id].count(t_id)
	for w_id in losses:
		#w_abs_id = ids[t_id][losses[e_id][0]]

		skills += p_info[w_id]['elo']
		l_count += losses[w_id].count(t_id)

	if (w_count + l_count) == 0:
		return 0
	return (skills + 400.*(w_count-l_count))/(w_count+l_count)

# returns the player's K-factor
# (used in Elo calculations)
def calc_k_factor(elo,n_played):

	# FIDE K-factor method of calculation
	if n_played < 30:
		if elo < 2400:
			return 40
		else:
			return 20
	else:
		if elo < 2400:
			return 20
		else:
			return 10

	# not used (old)
	if elo >= 2400:
		return 16.
	elif elo >= 2100:
		return 24.
	else:
		return 32.

# returns the player's expected score for a match
# (used in Elo calculations)
def exp_score(elo_a,elo_b):
	return 1.0/(1. + 10.**((float(elo_a)-float(elo_b))/400.))

# updates the player's elo score given their expected and actual results of the event
def update_elo(elo,expected,actual,N):
	K = calc_k_factor(elo,N)

	return elo + K*(actual-expected)

## GLICKO CALCULATION UTILS
# (from glicko.net's algorithm)
glicko_tau = 0.5
# returns mu,phi given r,RD (and vice versa)
def glicko_scale(rating,RD):
	return (rating-1500.)/173.7178,RD/173.7178
def glicko_unscale(mu_p,phi_p):
	return 173.7178*mu_p+1500.,phi_p*173.7178

# returns the estimated variance of the player's rating
# mu = target player's glicko-2 rating
# mus, phis = opponent players' glicko-2 ratings and rating deviations
def glicko_variance(mu,matches):
	mus = [match[1] for match in matches]
	phis = [match[2] for match in matches]
	return 1./sum([(glicko_g(phi_j)**2.) * glicko_E(mu,mu_j,phi_j) * (1-glicko_E(mu,mu_j,phi_j)) for mu_j,phi_j in zip(mus,phis)])

# returns the estimated improvement in rating
def glicko_delta(mu,matches):
	#scores = [match[0] for match in matches]
	#mus = [match[1] for match in matches]
	#phis = [match[2] for match in matches]
	return glicko_variance(mu,matches)*sum([glicko_g(phi_j)*(s_j-glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in matches])
	
# helper function for glicko
def glicko_g(phi):
	return 1./(sqrt(1.+(3.*phi**2.)/(pi**2.)))

# helper function for glicko
def glicko_E(mu,mu_j,phi_j):
	return 1./(1.+exp(-1.*glicko_g(phi_j)*(mu-mu_j)))

# iterative algorithm to update the glicko-2 volatility
# mu = glicko-2 rating
# phi = glicko-2 rating deviation
# sigma = glicko-2 rating volatility
def glicko_update_vol(mu,phi,sigma,matches,delta,v_g):
	mus = [match[1] for match in matches]
	phis = [match[2] for match in matches]
	# step 1 (definitions)
	a = log(sigma**2.)
	tol = 0.000001
	tau = glicko_tau
	f = lambda x: ((exp(x)*(delta**2.-phi**2.-v_g-exp(x)))/(2.*(phi**2.+v_g+exp(x))**2.))-((x-a)/(tau**2.))

	# step 2 (initial values)
	A = a
	if delta**2. > (phi**2.+v_g):
		B = log(delta**2.-phi**2.-v_g)
	else:
		k = 1.
		while f(a-k*tau) < 0.:
			k += 1.
		B = a-k*tau

	# step 3 (iteration)
	f_A = f(A)
	f_B = f(B)
	while(abs(f_B-f_A) > tol):
		#3a
		C = A + (A-B)*f_A/(f_B-f_A)
		f_C = f(C)

		#3b
		if f_C*f_B < 0.:
			A = B
			f_A = f_B
		else:
			f_A = f_A/2.

		#3c
		B = C 
		f_B = f_C

	# step 4 (completion)
	sigma_prime = exp(A/2.)

	return sigma_prime

# updates the glicko ratings for all players that entered,
# after a given tournament
def update_glicko(p_info,ids,matches,t_id):
	# step 1 (instantiate starting values)
	# converts match information to (s_j,mu_j,phi_j) format
	matches = [(match[0],p_info[match[1]]['glicko']) for match in matches]
	matches = [(match[0],glicko_scale(match[1][0],match[1][1])) for match in matches]
	matches = [(match[0],match[1][0],match[1][1]) for match in matches]
	#p_info_old = dcopy(p_info)

	for abs_id in p_info:
		if t_id in ids[abs_id]:

			# step 2 (scale values)
			r,RD,sigma = p_info[abs_id]['glicko']
			mu,phi = glicko_scale(r,RD)

			# step 3 (compute v)
			# step 4 (compute delta)
			v_g = glicko_variance(mu,matches)
			delta = glicko_delta(mu,matches)

			# step 5 (compute sigma')
			sigma_prime = glicko_update_vol(mu,phi,sigma,matches,delta,v_g)

			# step 6 (update phi to new pre-rating value)
			phi_star = sqrt(phi**2. + sigma_prime**2.)

			# step 7 (update mu and phi)
			phi_prime = 1./sqrt(1./(phi_star**2) + 1./v_g)
			mu_prime = mu + (phi_prime**2)*sum([glicko_g(phi_j)*(s_j - glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in matches])

		else:
			phi_prime = sqrt(phi**2 + sigma**2)
			mu_prime = mu
			sigma_prime = sigma

		# step 8 (unscale values)
		r_prime,RD_prime = glicko_unscale(mu_prime,phi_prime)
		p_info[abs_id]['glicko'] = (r_prime,RD_prime,sigma_prime)



if __name__ == "__main__":
	read_majors()