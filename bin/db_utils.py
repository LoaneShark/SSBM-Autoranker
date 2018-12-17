## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
#import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
import json
import argparse
import shutil
from timeit import default_timer as timer
## UTIL IMPORTS
from readin import readin,set_readin_args
from readin_utils import get_slug
import scraper

## TODO: 
##	Shortterm
## 		 - Figure out what to do with the data // what data do we want
## 		 - ignore irrelevant/side/casual/exhibition brackets (like at summit, e.g.)
## 		 - ensure scraper is JUST SINGLES unless otherwise specified
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
##

## ARGUMENT PARSING
parser = argparse.ArgumentParser()
parser.add_argument('-v','--verbosity',help='verbosity',default=0)
parser.add_argument('-s','--save',help='save results toggle (default True)',default=True)
parser.add_argument('-l','--load',help='load results toggle (default True)',default=True)
parser.add_argument('-f','--force_first',help='force the first criteria-matching event to be the only event',default=True)
parser.add_argument('-g','--game',help='Melee=1, P:M=2, Wii U=3, 64=4, Ultimate=1386',default=1)
parser.add_argument('-y','--year',help='The year you want to analyze (for ssbwiki List of majors scraper)',default=2018)
parser.add_argument('-t','--teamsize',help='1 for singles bracket, 2 for doubles',default=1)
parser.add_argument('-d','--displaysize',help='lowest placing shown on pretty printer output (or -1 for all entrants)',default=64)
parser.add_argument('-sl','--slug',help='tournament URL slug',default=None)
parser.add_argument('-ss','--short_slug',help='shorthand tournament URL slug',default=None)
parser.add_argument('-p','--print',help='print tournament final results to console as they are read in',default=False)
parser.add_argument('-c','--collect_garbage',help='delete phase data after tournament is done being read in',default=True)
parser.add_argument('-ar','--use_arcadians',help='count arcadian events',default=False)
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
db_slug = args.slug
db_game = args.game
db_year = args.year
count_arcadians = args.use_arcadians
if count_arcadians == -1:
	only_arcadians = True
else:
	only_arcadians = False

# main loop. calls scraper to get slugs for every major that happened
# in the specified year for the specified game (per smash.gg numeric id value)
# returns in the form of 4 dicts: tourneys,ids,p_info,records
def read_majors(game_id=int(db_game),year=int(db_year)):
	set_readin_args(args)
	#slugs = ["genesis-5","summit6","shine2018","tbh8","summit7"]
	fails = []
	scrape_load = False
	slug_given = False
	if db_slug == None:
		if to_load_db:
			scrape_load = True
			if v >= 3:
				"Loading saved slugs..."
			slugs = load_slugs(int(db_game),int(db_year))
			if slugs == False or slugs == []:
				if v >= 3:
					"Saved slugs not found."
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
	if to_save_db:
		save_slugs(slugs,int(db_game),int(db_year))
	return(read_tourneys(slugs,ver=db_game))

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
def read_tourneys(slugs,ver='default'):
	[tourneys,ids,p_info,records] = load_db(ver)
	if v >= 4 and len(tourneys.keys())>1:
		print("Loaded Tourneys: " + str([tourneys[t_id]['name'] for t_id in tourneys if not t_id == 'slugs']))
	#print(tourneys)
	#dicts = (tourneys,ids,p_info,records)
	#print(tourneys,ids,p_info,records)

	for slug in slugs:
		if slug not in tourneys['slugs']:
			readins = readin(slug)
			if readins:
				if store_data(readins,(tourneys,ids,p_info,records),slug):
					if to_save_db:
						save_db((tourneys,ids,p_info,records),ver)
					t_id = tourneys['slugs'][readins[0][2]]
					if collect:
						delete_tourney(t_id)
	return tourneys,ids,p_info,records

# helper function to store all data from a call to readin
def store_data(readins,dicts,slug):
	t_info,entrants,names,paths,wins,losses = readins
	tourneys,ids,p_info,records = dicts

	if store_players(entrants,names,t_info,dicts):
		if store_records(wins,losses,paths,t_info,dicts):
			if store_tourney(slug,t_info,names['groups'],dicts):
				return True
	return False

# stores data through absolute player IDs (converting from entrant IDs)
def store_players(entrants,names,t_info,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region = t_info
	tourneys,ids,p_info,records = dicts

	if t_id not in tourneys:
		# store all entrant/player-specific info from this tournament
		for e_id in entrants:
			#e_id = entrant[2]
			abs_id = entrants[e_id][1]

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
			if names[e_id][0] == None:
				if 'team' not in p_info[abs_id]:
					p_info[abs_id]['team'] = names[e_id][0]
			else:
				p_info[abs_id]['team'] = names[e_id][0]
			if 'aliases' not in p_info[abs_id]:
				p_info[abs_id]['aliases'] = []
			if names[e_id][1] not in p_info[abs_id]['aliases']:
				p_info[abs_id]['aliases'].extend([names[e_id][1]])
			p_info[abs_id]['tag'] = names[e_id][1]
			for key,info in zip(['firstname','lastname','state','country'],entrants[e_id][3]):
				if key in p_info[abs_id]:
					if not info == 'N/A':
						p_info[abs_id][key] = info
				else:
					p_info[abs_id][key] = info
			#print(ids[abs_id])
	#else:
		#print(t_id)
		#print(tourneys)
		#print(tourneys[t_id])
	return True

# stores win/loss records
def store_records(wins,losses,paths,t_info,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region = t_info
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
					records[abs_id]['paths'] = {}

				# store final placement by tourney id
				records[abs_id]['placings'][t_id] = paths[e_id][0]
				# store path through bracket by tourney id
				records[abs_id]['paths'][t_id] = paths[e_id][1]

				# store wins and losses
				if e_id in wins:
					for win in wins[e_id]:
						l_id = ids[t_id][win[0]]
						if l_id not in records[abs_id]['wins']:
							records[abs_id]['wins'][l_id] = {}
							records[abs_id]['wins'][l_id] = [t_id]
						else:
							records[abs_id]['wins'][l_id].extend([t_id])
				if e_id in losses:
					for loss in losses[e_id]:
						w_id = ids[t_id][loss[0]]
						if w_id not in records[abs_id]['losses']:
							records[abs_id]['losses'][w_id] = {}
							records[abs_id]['losses'][w_id] = [t_id]
						else:
							records[abs_id]['losses'][w_id].extend([t_id])
	return True

# stores tourney meta info and marks tournament as imported
def store_tourney(slug,t_info,group_names,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region = t_info
	tourneys,ids,p_info,records = dicts
	tourneys[t_id] = {}
	tourneys[t_id]['name'] = t_name
	tourneys[t_id]['slug'] = t_slug
	tourneys[t_id]['shortSlug'] = t_ss
	tourneys[t_id]['type'] = t_type
	tourneys[t_id]['date'] = t_date
	tourneys[t_id]['region'] = t_region
	if 'slugs' not in tourneys:
		tourneys['slugs'] = {}
	tourneys['slugs'][t_slug] = t_id
	tourneys['slugs'][t_ss] = t_id
	tourneys['slugs'][slug] = t_id
	if 'groups' not in tourneys[t_id]:
		tourneys[t_id]['groups'] = {}
	tourneys[t_id]['groups'] = group_names
		
	return True

# used to save datasets/hashtables
def save_db(dicts,ver,loc='db'):
	if to_save_db:
		if v >= 3:
			print("Saving DB...")
		for data,name in zip(dicts,['tourneys','ids','p_info','records']):
			save_dict(data,name,ver,loc)
	else:
		return False

# used to load datasets/hashtables
def load_db(ver):
	if to_load_db:
		if v >= 3:
			print("Loading DB...")
		return [load_dict(name,ver) for name in ['tourneys','ids','p_info','records']]
	else:
		return [load_dict(name,'blank',loc='db') for name in ['tourneys','ids','p_info','records']]

# saves a single dict
def save_dict(data,name,ver,loc='db'):
	if only_arcadians:
		ver = str(ver)+" (ARC)"
	if not os.path.isdir('%s'%loc):
		os.mkdir(str('%s'%loc))
	if not os.path.isdir('%s/%s'%(loc,ver)):
		os.mkdir(str('%s/%s'%(loc,ver)))
	#if not os.path.isdir('%s/%s/%s'%(loc,ver,name)):
	#	os.mkdir(str('%s/%s/%s'%(loc,ver,name)))
	with open(str(loc)+'/'+str(ver)+'/'+name +'.pkl','wb') as f:
		pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

# loads a single dict
def load_dict(name,ver,loc='db'):
	try:
		with open(str(loc)+'/'+str(ver)+'/'+name+'.pkl','rb') as f:
			return pickle.load(f) 
	except FileNotFoundError:
		if name == 'tourneys':
			t = {}
			t['slugs'] = {}
			#t['groups'] = {}
			save_dict(t,name,ver,loc)
			return t
		else:
			save_dict({},name,ver,loc)
			return {}

# saves the slugs pulled by scraper to avoid having to rescrape every time
def save_slugs(slugs,game,year,loc='db'):
	if to_save_db:
		if v >= 4:
			print("Saving scraped slugs...")
		if not os.path.isdir('%s/%s'%(loc,game)):
			os.mkdir(str('%s/%s'%(loc,game)))
		if not os.path.isdir('%s/%s/slugs'%(loc,game)):
			os.mkdir(str('%s/%s/slugs'%(loc,game)))
		with open(str(loc)+'/'+str(game)+'/slugs/'+str(year) +'.pkl','wb') as f:
			pickle.dump(slugs, f, pickle.HIGHEST_PROTOCOL)
		return True
	else:
		return False

# loads the slugs pulled by scraper to avoid having to rescrape every time
def load_slugs(game,year,loc='db'):
	try:
		with open(str(loc)+'/'+str(game)+'/slugs/'+str(year)+'.pkl','rb') as f:
			return pickle.load(f) 
	except FileNotFoundError:
		return False

# deletes the json pulls and phase data stored by readin
# (for use once a tourney has been imported fully, to remove garbage files from accumulating)
def delete_tourney(t_id):
	if os.path.isdir('obj/%d'%t_id):
		shutil.rmtree('obj/%d'%t_id)

if __name__ == "__main__":
	read_majors()