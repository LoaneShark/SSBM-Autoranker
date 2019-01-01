## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
import json
import argparse
import shutil
from timeit import default_timer as timer
from copy import deepcopy as dcopy
## UTIL IMPORTS
from readin import readin,set_readin_args
from readin_utils import *
from analysis_utils import get_player, get_region
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
parser.add_argument('-t','--teamsize',help='1 for singles bracket, 2 for doubles (default 1)',default=1)
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
		[tourneys,ids,p_info,records] = load_db(verstr)
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
			for key,info in zip(['firstname','lastname','state','country','city'],entrants[e_id][3]):
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
			if 'elo' not in p_info[abs_id]:
				p_info[abs_id]['elo'] = 1500.
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

				expected_score = 0.
				actual_score = 0.

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

				# update elo ratings after event
				p_info[abs_id]['elo'] = update_elo(p_info[abs_id]['elo'],expected_score,actual_score,p_info[abs_id]['sets_played'])

				# store event performance by tourney id
				records[abs_id]['performances'][t_id] = calc_performance(records,p_info,abs_id,t_id)
				#records[abs_id]['performances'][t_id] = calc_performance(ids,records,wins,losses,e_id,t_id)
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
	if args.teamsize == 2:
		ver = str(ver) + " (DUBS)"
	if args.teamsize >= 4:
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
	if args.teamsize == 2:
		ver = str(ver) + " (DUBS)"
	if args.teamsize >= 4:
		ver = str(ver) + " (CREWS)"
	if only_arcadians:
		ver = str(ver)+" (ARC)"
	if to_load_db and not force_blank:
		if v >= 3:
			print("Loading DB...")
		return [load_dict(name,ver,loc) for name in ['tourneys','ids','p_info','records']]
	else:
		return [load_dict(name,'blank',loc='db') for name in ['tourneys','ids','p_info','records']]

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


if __name__ == "__main__":
	read_majors()