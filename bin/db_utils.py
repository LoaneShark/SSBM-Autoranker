## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
import os,sys,pickle,time,datetime
import json
import argparse
import shutil
from timeit import default_timer as timer
from copy import deepcopy as dcopy
from math import *
from trueskill import Rating as ts_Rating
from smashggpy.util.QueryQueueDaemon import QueryQueueDaemon
## UTIL IMPORTS
from arg_utils import *
from readin import readin,set_readin_args
from readin_utils import *
from calc_utils import *
from region_utils import *
from dict_utils import *
import scraper


## ARGUMENT PARSING
args = get_args()

cache_res = args.cache_results
v = int(args.verbosity)
if not args.short_slug == None:
	args.slug = get_slug(args.short_slug)
to_save_db = args.save
to_load_db = args.load
if args.load == 'False':
	args.load == False
	to_load_db = False
if args.save == 'False':
	args.save == False
	to_save_db = False
to_load_slugs = args.cache_slugs
if args.cache_slugs == 'False':
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
	db_yearstr = str(db_year)+'-'+str(db_year+db_year_count)
if args.current_db:
	db_yearstr += '_c'
count_arcadians = args.use_arcadians
if count_arcadians == -1:
	only_arcadians = True
else:
	only_arcadians = False
if args.current_db == 'False':
	db_current = False
elif args.current_db:
	db_current = True
else:
	db_current = args.current_db
if args.season_db == 'False':
	db_season = False
elif args.season_db:
	db_season = True
else:
	db_season = args.season_db
teamsize = int(args.teamsize)
glicko_tau = float(args.glicko_tau)

# main loop. calls scraper to get slugs for every major that happened
# in the specified year for the specified game (per smash.gg numeric id value)
# returns in the form of 4 dicts: tourneys,ids,p_info,records
def read_year(game_id=int(db_game),year=int(db_year),base=None,current=db_current):
	#set_readin_args(args)
	#slugs = ["genesis-5","summit6","shine2018","tbh8","summit7"]
	fails = []
	scrape_load = False
	slug_given = False
	if db_slug == None:
		if to_load_slugs:
			scrape_load = True
			if v >= 3 and year == int(db_year):
				print('Loading saved slugs...')
			slugs = load_slugs(game_id,year)
			if slugs == False or slugs == []:
				if v >= 3:
					print('Saved slugs not found.')
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
		if len(slugs) <= 0:
			print('No slugs found for game %d in year %d:'%(game_id,year))
		else:
			print('Scraped the following slugs for game %d in year %d:'%(game_id,year))
			print(slugs)
	if not fails == [] and v > 0:
		print('The following majors could not be read (no smash.gg bracket found)')
		print(fails)
	if to_save_db and not scrape_load and not slug_given:
		save_slugs(slugs,game_id,year,to_save_db=to_save_db)
	dicts = read_tourneys(slugs,ver=game_id,year=year,base=base,current=current)
	update_official_ranks(dicts,game_id,year)
	return dicts

def set_db_args(db_args):
	cache_res = db_args.cache_results
	v = int(db_args.verbosity)
	if not db_args.short_slug == None:
		db_args.slug = get_slug(db_args.short_slug)
	to_save_db = db_args.save
	to_load_db = db_args.load
	if db_args.load == 'False':
		db_args.load == False
		to_load_db = False
	if db_args.save == 'False':
		db_args.save == False
		to_save_db = False
	db_slug = db_args.slug
	db_game = int(db_args.game)
	db_year = int(db_args.year)
	if db_args.current_db == 'False':
		db_current = False
	elif db_args.current_db:
		db_current = True

## AUXILIARY FUNCTIONS
# loads database and stores any tournament data not already present given the url slug
def read_tourneys(slugs,ver='default',year=None,base=None,current=False,to_update_socials=False):
	'''if year != None:
		verstr = '%s/%s'%(ver,db_yearstr)
	else:
		verstr = ver'''
	verstr = get_db_verstr()

	if base == None:
		[tourneys,ids,p_info,records,skills,meta] = easy_load_db(verstr)
	else:
		tourneys,ids,p_info,records,skills,meta = base

	if v >= 4 and len(tourneys.keys())>1 and year == db_year:
		print('Loaded Tourneys: ' + str([tourneys[t_id]['name'] for t_id in tourneys if not t_id == 'slugs' if tourneys[t_id]['active']]))
	#print(tourneys)
	#dicts = (tourneys,ids,p_info,records)
	#print(tourneys,ids,p_info,records)

	for slug in slugs:
		slug_date = get_tournament_date(slug)
		if slug_date is None or slug_date == False:
			if v >= 4:
				print('Could not import %s: no date available'%slug)
		else:
			date_list = sorted([tourneys[old_id]['date'] for old_id in tourneys if old_id != 'slugs'])
			# ensure it's not before the last imported event (or that it's the first event in the db)
			if len(date_list) <= 0 or (slug_date[0] > date_list[0][0]) or (slug_date[0] == date_list[0][0] and slug_date[1] >= date_list[0][1]):
				if slug not in meta['slugs']:
					try:
						readins = readin(slug)
					except Exception as e:
						QueryQueueDaemon.kill_daemon()
						raise e
					if readins:
						if current:
							clean_old_tourneys((tourneys,ids,p_info,records,skills,meta),readins[0])
						if v >= 4:
							print('Importing to DB...')
						if store_data(readins,(tourneys,ids,p_info,records,skills,meta),slug,year):
							if to_save_db:
								save_db((tourneys,ids,p_info,records,skills,meta),verstr)
								save_db_sets(readins[6],verstr)
							t_id = meta['slugs'][readins[0][2]]
							if not cache_res:
								delete_tourney_cache(t_id)
			else:
				if v >= 4:
					print('Skipping %s: more recent events already present'%slug)

	if to_update_socials:
		update_social_media((tourneys,ids,p_info,records,skills,meta),None,v)
	return tourneys,ids,p_info,records,skills,meta

# helper function to store all data from a call to readin
def store_data(readins,dicts,slug,year):
	t_info,entrants,names,paths,wins,losses,sets = readins
	tourneys,ids,p_info,records,skills,meta = dicts
	if len(entrants.keys()) > 1:
		if store_players(entrants,names,t_info,dicts):
			if store_records(wins,losses,paths,sets,t_info,dicts):
				if store_tourney(slug,t_info,names['groups'],entrants,sets,dicts):
					if store_meta((tourneys,ids,p_info,records,skills,meta),t_info,year):
						return True
	return False

# stores data through absolute player IDs (converting from entrant IDs)
# entrants = ([name],[abs_id],e_id,[metainfo],propic_url) where name, abs_id, metainfo are a list for each member of the team
# and name = (sponsor, tag, teamname (or None))
# and metainfo = [firstname, lastname, state, country, city]
def store_players(entrants,names,t_info,dicts,translate_cjk=True):
	t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_size,t_images,t_coords,t_bracket,t_hashtag = t_info
	tourneys,ids,p_info,records,skills,meta = dicts
	if t_id not in tourneys:
		# store teams/crews instead if this is a teams competition
		#if teamsize == 2 or teamsize == 3:
		#	return store_teams(entrants,names,t_info,dicts)
		#elif teamsize > 3:
		#	return store_crews(entrants,names,t_info,dicts)
		# store all entrant/player-specific info from this tournament
		for e_id in entrants:
			print(e_id)
			if e_id == 2232043:
				print(e_id)
				print(entrants[e_id])
				print(entrants[e_id][1][0].id)
			#e_id = entrant[2]
			for user in entrants[e_id][1]:
				idx = entrants[e_id][1].index(user)
				if 't_'+str(t_id) not in ids:
					ids['t_'+str(t_id)] = {}
				if user is not None and user.id is not None:
					abs_id = user.id
					to_update_socials = False
					# store matrix to get entrant ids for each tourney given absolute id'
					# (and also to get the reverse)
					if abs_id not in ids:
						ids[abs_id] = {}
					ids[abs_id][t_id] = e_id
					ids['t_'+str(t_id)][e_id] = abs_id

					# store dict for each player with keys for:
					# team, tag, firstname, lastname, state, country
					if abs_id not in p_info:
						p_info[abs_id] = {}
						to_update_socials = True
						p_info[abs_id]['status'] = handle_player_status(abs_id,'active')
						p_info[abs_id]['first_event'] = t_id

					# basic User info
					p_info[abs_id]['active'] = True
					p_info[abs_id]['id'] = abs_id
					p_info[abs_id]['teamsize'] = args.teamsize
					p_info[abs_id]['name'] = user.name
					p_info[abs_id]['slug'] = user.slug
					p_info[abs_id]['pronouns'] = user.gender_pronoun

					# handle tag and sponsor
					if names[e_id][0][idx] == None:
						if 'team' not in p_info[abs_id]:
							p_info[abs_id]['team'] = names[e_id][0][idx]
					else:
						p_info[abs_id]['team'] = names[e_id][0][idx]
					if 'aliases' not in p_info[abs_id]:
						p_info[abs_id]['aliases'] = []
					p_tag = names[e_id][1][idx]
					trans_tag = p_tag
					if p_tag not in p_info[abs_id]['aliases']:
						p_info[abs_id]['aliases'].extend([p_tag])
						if p_tag != None and any([is_cjk(tag_c) for tag_c in p_tag]):
							trans_tag_base = transliterate(p_tag)
							trans_tag = '<'+transliterate(p_tag)+'>'
							if trans_tag not in p_info[abs_id]['aliases']:
								p_info[abs_id]['aliases'].extend([trans_tag])
								p_info[abs_id]['en_tag'] = trans_tag_base
						else:
							p_info[abs_id]['en_tag'] = trans_tag
					if translate_cjk:
						p_info[abs_id]['tag'] = trans_tag
					else:
						p_info[abs_id]['tag'] = p_tag

					# handle region
					if user.location is not None:
						for key in ['id','city','country','countryId','state','stateId']:
							info = user.location[key]
							if key == 'id':
								key = 'location_id'
							if key in p_info[abs_id]:
								if not info in ['N/A','',"",None]:
									p_info[abs_id][key] = info
							else:
								p_info[abs_id][key] = info
						if 'region' not in p_info[abs_id] or p_info[abs_id]['region'] == None:
							p_info[abs_id]['region'] = {}
							for r_i in range(0,6):
								p_info[abs_id]['region'][r_i] = get_region(dicts,abs_id,granularity=r_i,to_calc=True)
								p_info[abs_id]['region_'+str(r_i)] = get_region(dicts,abs_id,granularity=r_i,to_calc=True) # store it separately too for firebase querying
						else:
							if p_info[abs_id]['region'] == {} or any([r_idx not in p_info[abs_id]['region'] for r_idx in range(0,6)]) or any([p_info[abs_id]['region'][r_idx] == 'N/A' for r_idx in range(0,6)]):
								#p_info[abs_id]['region'] = get_region(dicts,abs_id,granularity=2,to_calc=True)
								for r_i in range(0,6):
									p_info[abs_id]['region'][r_i] = get_region(dicts,abs_id,granularity=r_i,to_calc=True)
									p_info[abs_id]['region_'+str(r_i)] = get_region(dicts,abs_id,granularity=r_i,to_calc=True) # store it separately too for firebase querying
					else:
						p_info[abs_id]['region'] = {}
						for r_i in range(0,6):
							p_info[abs_id]['region'][r_i] = None
							p_info[abs_id]['region_'+str(r_i)] = None # store it separately too for firebase querying


					# store smash.gg profile picture url
					p_info[abs_id]['propic'] = entrants[e_id][4]

					# store W/L record per character
					if 'characters' not in p_info[abs_id]:
						chardict = load_dict('characters',None,loc='../lib')
						if db_game in chardict:
							chardict = chardict[db_game]
							p_info[abs_id]['characters'] = {char_id: [0,0] for char_id in chardict}
						else:
							p_info[abs_id]['characters'] = {}

					# store their current main // make a slot for it
					if 'main' not in p_info[abs_id]:
						p_info[abs_id]['main'] = None

					# handle external account connections and authorizations
					if to_update_socials and user.authorizations is not None:
						#for key in ['twitter','twitch','reddit','youtube','smashboards','ssbwiki','discord','name_display','color']:
						#for key in ['TWITTER','TWITCH','MIXER','DISCORD']:
						for key in user.authorizations.keys():
							auth_info = user.authorizations[key]
							if key == 'id':
								key = 'auth_id'
							p_info[abs_id][key] = auth_info

					# store ranking data, with initial values if needed
					if 'elo' not in skills or 'elo-rnk' not in skills:
						for key in ['elo','elo-rnk','elo-pct','elo_del',\
									'glicko','glicko-rnk','glicko-pct','glicko_del',\
									'srank','srank-rnk','srank-pct','srank_del','srank_sig',\
									'trueskill','trueskill-rnk','trueskill-pct','trueskill_del',\
									'glixare','glixare-rnk','glixare-pct','glixare_del', 'perf',\
									'mainrank']:
							skills[key] = {}
					if 'elo' not in p_info[abs_id]:
						p_info[abs_id]['elo'] = float(args.elo_init_value)
						p_info[abs_id]['elo_peak'] = p_info[abs_id]['elo']
						skills['elo'][abs_id] = {}
						skills['elo-rnk'][abs_id] = {}
						skills['elo-pct'][abs_id] = {}
						skills['elo_del'][abs_id] = {}
					# glicko stores a tuple with (rating,RD,volatility)
					if 'glicko' not in p_info[abs_id]:
						p_info[abs_id]['glicko'] = (float(args.glicko_init_value),float(args.glicko_init_rd),float(args.glicko_init_sigma))
						p_info[abs_id]['glicko_peak'] = p_info[abs_id]['glicko'][0]
						skills['glicko'][abs_id] = {}
						skills['glicko-rnk'][abs_id] = {}
						skills['glicko-pct'][abs_id] = {}
						skills['glicko_del'][abs_id] = {}
					if 'srank' not in p_info[abs_id]:
						p_info[abs_id]['srank'] = int(1)
						#p_info[abs_id]['srank'] = 0.5
						p_info[abs_id]['srank_sig'] = (0.5,0.,1.,4.)
						p_info[abs_id]['srank_last'] = int(1)
						p_info[abs_id]['srank_peak'] = int(1)
						skills['srank'][abs_id] = {}
						skills['srank-rnk'][abs_id] = {}
						skills['srank-pct'][abs_id] = {}
						skills['srank_del'][abs_id] = {}
						skills['srank_sig'][abs_id] = {}
					if 'trueskill' not in p_info[abs_id]:
						p_info[abs_id]['trueskill'] = {'mu':args.trueskill_init_mu,'sigma':args.trueskill_init_sigma,'expose':0.}
						p_info[abs_id]['trueskill_peak'] = p_info[abs_id]['trueskill']
						if 'trueskill' not in skills:
							skills['trueskill'] = {}
							skills['trueskill-rnk'] = {}
							skills['trueskill-pct'] = {}
							skills['trueskill_del'] = {}
						skills['trueskill'][abs_id] = {}
						skills['trueskill-rnk'][abs_id] = {}
						skills['trueskill-pct'][abs_id] = {}
						skills['trueskill_del'][abs_id] = {}
					if 'glixare' not in p_info[abs_id]:
						p_info[abs_id]['glixare'] = 0
						p_info[abs_id]['glixare_peak'] = p_info[abs_id]['glixare']
						skills['glixare'][abs_id] = {}
						skills['glixare-rnk'][abs_id] = {}
						skills['glixare-pct'][abs_id] = {}
						skills['glixare_del'][abs_id] = {}
					if 'sets_played' not in p_info[abs_id]:
						p_info[abs_id]['sets_played'] = 0
					if 'events_entered' not in p_info[abs_id]:
						p_info[abs_id]['events_entered'] = 0
					p_info[abs_id]['events_entered'] += 1
					if 'last_event' not in p_info[abs_id]:
						p_info[abs_id]['last_event'] = None
					p_info[abs_id]['prev_event'] = p_info[abs_id]['last_event']
					p_info[abs_id]['last_event'] = t_id
					if abs_id not in skills['perf']:
						skills['perf'][abs_id] = {}
				else:
					ids['t_'+str(t_id)][e_id] = None

	else:
		if v >= 5:
			print('Skipping',t_name,': already in DB')

	return True

# stores win/loss records, updates player skills/rankings if enabled
# ranking period in months (only used by sigmoid ranking)
def store_records(wins,losses,paths,sets,t_info,dicts,to_update_ranks=True,to_update_sigmoids=True,ranking_period=2):
	t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_size,t_images,t_coords,t_bracket,t_hashtag = t_info
	tourneys,ids,p_info,records,skills,meta = dicts
	old_p_info = dcopy(p_info)
	glicko_matches = {}
	trueskill_matches = {}

	elo_history = skills['elo']
	elo_deltas = skills['elo_del']
	#glicko_history = skills['glicko']
	#glicko_deltas = skills['glicko_del']
	simrank_history = skills['srank']
	simrank_deltas = skills['srank_del']
	sigmoid_history = skills['srank_sig']
	#performance_history = skills['perf']

	# convert all entrant ids in set data to abs ids
	for set_id in sets:
		#print (set_id)
		if (not sets[set_id]['w_id'] in ids['t_'+str(t_id)]) or (ids['t_'+str(t_id)][sets[set_id]['w_id']] is None) or \
		   (not sets[set_id]['l_id'] in ids['t_'+str(t_id)]) or (ids['t_'+str(t_id)][sets[set_id]['l_id']] is None):
			print('t_'+str(t_id))
			print('crash set_id',set_id)
			print(sets[set_id])
			print(ids['t_'+str(t_id)][sets[set_id]['w_id']]) 
			print(ids['t_'+str(t_id)][sets[set_id]['l_id']]) ### crahes here for some reason
		if 'w_id' in sets[set_id] and type(sets[set_id]['w_id']) is int:
			sets[set_id]['w_id'] = ids['t_'+str(t_id)][sets[set_id]['w_id']]
		if 'l_id' in sets[set_id] and type(sets[set_id]['l_id']) is int:
			sets[set_id]['l_id'] = ids['t_'+str(t_id)][sets[set_id]['l_id']]

		if 'games' in sets[set_id]:
			for game_id in sets[set_id]['games']:
				if 'w_id' in sets[set_id]['games'][game_id] and type(sets[set_id]['games'][game_id]['w_id']) is int:
					sets[set_id]['games'][game_id]['w_id'] = ids['t_'+str(t_id)][sets[set_id]['games'][game_id]['w_id']]
				if 'l_id' in sets[set_id]['games'][game_id] and type(sets[set_id]['games'][game_id]['l_id']) is int:
					sets[set_id]['games'][game_id]['l_id'] = ids['t_'+str(t_id)][sets[set_id]['games'][game_id]['l_id']]

				if 'characters' in sets[set_id]['games'][game_id]:
					temp_excluded_ids = []
					for temp_e_id in sets[set_id]['games'][game_id]['characters']:
						if temp_e_id not in temp_excluded_ids:
							temp_abs_id = ids['t_'+str(t_id)][temp_e_id]
							temp_excluded_ids.append(temp_abs_id)
							sets[set_id]['games'][game_id]['characters'][temp_abs_id] = sets[set_id]['games'][game_id]['characters'][temp_e_id]
							del sets[set_id]['games'][game_id]['characters'][temp_e_id]

	#print(t_id)
	for abs_id in ids:
		if not (type(abs_id) is str or abs_id == 't_'+str(t_id)):			# ignore id for present or past tournaments
			simrank_history[abs_id][t_id] = 1.
			simrank_deltas[abs_id][t_id] = 0.
			if t_id in ids[abs_id]:								# ignore id if not an entrant in this tourney
				e_id = ids[abs_id][t_id]

				if abs_id not in records:
					records[abs_id] = {}
					records[abs_id]['wins'] = {}
					records[abs_id]['losses'] = {}
					records[abs_id]['placings'] = {}
					records[abs_id]['paths'] = {}
					records[abs_id]['set_history'] = []

				# store final placement by tourney id
				records[abs_id]['placings'][t_id] = {'placing': paths[e_id]['placing'], 'isDQ': False , 'seedNum':paths[e_id]['seed']}
				# store path through bracket by tourney id
				records[abs_id]['paths'][t_id] = paths[e_id]['path']

				# used for elo
				expected_score = 0.
				actual_score = 0.
				# used for glicko
				glicko_scores = []
				trueskill_scores = []

				# store wins and losses
				if e_id in wins:
					for win in wins[e_id]:
						# store set id/data & character data if available
						set_id = win[1][0]
						group_id = win[1][1]
						set_games = None
						records[abs_id]['set_history'].extend([set_id])
						if 'games' in sets[set_id]:
							set_games = {}
							for game_id in sets[records[abs_id]['set_history'][-1]]['games']:
								game_data = sets[records[abs_id]['set_history'][-1]]['games'][game_id]
								set_games[game_id] = game_data
								if 'characters' in game_data:
									p_info[abs_id]['characters'][game_data['characters'][abs_id]][0] += 1
						# store opponent & event
						l_id = ids['t_'+str(t_id)][win[0]]
						if l_id not in records[abs_id]['wins']:
							records[abs_id]['wins'][l_id] = {}
						if t_id not in records[abs_id]['wins'][l_id]:
							records[abs_id]['wins'][l_id][t_id] = {}
						records[abs_id]['wins'][l_id][t_id][set_id] = {'id':set_id, 'group_id': group_id, 'games':set_games}

						p_info[abs_id]['sets_played'] += 1
						actual_score += 1.
						expected_score += exp_score(old_p_info[abs_id]['elo'],old_p_info[l_id]['elo'])

						glicko_scores.extend([(1.,l_id)])
						trueskill_scores.extend([(1.,l_id)])
				if e_id in losses:
					for loss in losses[e_id]:
						# store set id/data & character data if available
						set_id = loss[1][0]
						group_id = loss[1][1]
						set_games = None
						records[abs_id]['set_history'].extend([set_id])
						if 'games' in sets[records[abs_id]['set_history'][-1]]:
							set_games = {}
							for game_id in sets[records[abs_id]['set_history'][-1]]['games']:
								game_data = sets[records[abs_id]['set_history'][-1]]['games'][game_id]
								set_games[game_id] = game_data
								if 'characters' in game_data:
									if game_data['characters'][abs_id] not in p_info[abs_id]['characters']:
										p_info[abs_id]['characters'][game_data['characters'][abs_id]] = [0,0]
									p_info[abs_id]['characters'][game_data['characters'][abs_id]][1] += 1
						# store opponent & event
						w_id = ids['t_'+str(t_id)][loss[0]]
						if w_id not in records[abs_id]['losses']:
							records[abs_id]['losses'][w_id] = {}
						if t_id not in records[abs_id]['losses'][w_id]:
							records[abs_id]['losses'][w_id][t_id] = {}
						records[abs_id]['losses'][w_id][t_id][set_id] = {'id':set_id, 'group_id': group_id, 'games':set_games}

						p_info[abs_id]['sets_played'] += 1
						actual_score += 0.
						expected_score += exp_score(old_p_info[abs_id]['elo'],old_p_info[w_id]['elo'])

						glicko_scores.extend([(0.,w_id)])
						trueskill_scores.extend([(0.,w_id)])
				if not (e_id in wins or e_id in losses):
					records[abs_id]['placings'][t_id]['isDQ'] = True

				if to_update_ranks:
					# update elo ratings after event
					old_elo = p_info[abs_id]['elo']
					new_elo = update_elo(old_p_info[abs_id]['elo'],expected_score,actual_score,old_p_info[abs_id]['sets_played'])
					p_info[abs_id]['elo'] = new_elo
					p_info[abs_id]['elo_peak'] = max(p_info[abs_id]['elo_peak'],new_elo)
					glicko_matches[abs_id] = glicko_scores
					trueskill_matches[abs_id] = trueskill_scores
					# store skill ratings and event performance by tourney id
					elo_history[abs_id][t_id] = new_elo
					elo_deltas[abs_id][t_id] = new_elo - old_elo
					#performance_history[abs_id][t_id] = calc_performance((tourneys,ids,old_p_info,records,skills),abs_id,t_info)
					#records[abs_id]['performances'][t_id] = calc_performance(ids,records,wins,losses,e_id,t_id)
				else:
					# store new values & changes
					if p_info[abs_id]['last_event'] == t_id:
						glicko_history[abs_id][t_id] = p_info[abs_id]['glicko']
						simrank_history[abs_id][t_id] = p_info[abs_id]['srank']
						sigmoid_history[abs_id][t_id] = p_info[abs_id]['srank_sig']
					else:
						glicko_history[abs_id][t_id] = glicko_history[abs_id][p_info[abs_id]['last_event']]
						simrank_history[abs_id][t_id] = simrank_history[abs_id][p_info[abs_id]['last_event']]
						sigmoid_history[abs_id][t_id] = sigmoid_history[abs_id][p_info[abs_id]['last_event']]
					glicko_deltas[abs_id][t_id] = (0.,0.,0.)
					simrank_deltas[abs_id][t_id] = 0.
					performance_history[abs_id][t_id] = 0.
			# if not an entrant in this event
			else:
				elo_history[abs_id][t_id] = p_info[abs_id]['elo']
				elo_deltas[abs_id][t_id] = 0.
				#performance_history[abs_id][t_id] = 0

			# update character usage // main statistics
			if 'main' not in records[abs_id]:
				records[abs_id]['main'] = {}
			curr_main = get_main(abs_id,p_info) 
			records[abs_id]['main'][t_id] = curr_main
			p_info[abs_id]['main'] = curr_main

	if to_update_ranks:
		if v >= 5:
			print('Updating Performances...')
		update_performances(dicts,t_info)
		if v >= 4:
			print('Updating Glicko...')
		update_glicko(dicts,t_info,glicko_matches,tau=glicko_tau,to_update_glixare=True)
		update_trueskill(dicts,t_info,trueskill_matches)
		if to_update_sigmoids:
			#update_sigmoids(dicts,t_info,max_iterations=500,v=v,ranking_period=ranking_period)
			sigrank_res = update_sigmoids(dicts,t_info,max_iterations=args.srank_max_iter,v=v,ranking_period=0,sig=args.srank_sig_mode)
			if sigrank_res:
				ISR = {'params': sigrank_res}
				save_dict(ISR,'ISR_%d_%d_%d'%(db_game,db_year,db_year_count),None,'..\\lib')
		# must be run after all skill values are updated
		update_percentiles(dicts, t_id)
		update_top_h2h(dicts)

	return True

# stores tourney meta info and marks tournament as imported
def store_tourney(slug,t_info,group_names,entrants,sets,dicts):
	t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_size,t_images,t_coords,t_bracket,t_hashtag = t_info
	tourneys,ids,p_info,records,skills,meta = dicts
	tourneys[t_id] = {}
	tourneys[t_id]['id'] = t_id
	tourneys[t_id]['name'] = t_name
	tourneys[t_id]['slug'] = t_slug
	tourneys[t_id]['shortSlug'] = t_ss
	#tourneys[t_id]['type'] = t_type
	tourneys[t_id]['date'] = t_date
	tourneys[t_id]['startDate'] = t_startdate
	#tourneys[t_id]['region'] = t_region
	tourneys[t_id]['region'] = calc_region(country=t_region[1],state=t_region[0])
	tourneys[t_id]['numEntrants'] = t_size
	tourneys[t_id]['newEntrants'] = 0
	tourneys[t_id]['url_prof'] = t_images[0]
	tourneys[t_id]['url_banner'] = t_images[1]
	tourneys[t_id]['active'] = True
	#tourneys[t_id]['email'] = t_social[0]
	#tourneys[t_id]['twitter'] = t_social[1]
	#tourneys[t_id]['hashtag'] = t_social[2]

	# store bracket structure/path
	tourneys[t_id]['phases'] = t_bracket['phases']
	tourneys[t_id]['events'] = t_bracket['events']
	tourneys[t_id]['groups'] = t_bracket['groups']
	group_names = {group_key:{'name':group_name} for group_key,group_name in group_names.items()}
	tourneys[t_id]['group_names'] = group_names

	# store list of attendees and set ids
	tourneys[t_id]['attendees'] = {}
	for e_id in entrants:
		for user in entrants[e_id][1]:
			if user is not None:
				abs_id = user.id
				tourneys[t_id]['attendees'][abs_id] = {'id':abs_id,'e_id':e_id,'placing':records[abs_id]['placings'][t_id],'setsPlayed':[],'charactersUsed':{}}
				if 'first_event' in p_info[abs_id] and p_info[abs_id]['first_event'] == t_id:
					tourneys[t_id]['newEntrants'] += 1

	tourneys[t_id]['setIds'] = []
	for set_id in sets:
		tourneys[t_id]['setIds'].append(set_id)
		if 'w_id' in sets[set_id] and sets[set_id]['w_id'] is not None:
			w_id = sets[set_id]['w_id']
			tourneys[t_id]['attendees'][w_id]['setsPlayed'].append(set_id)
			tourneys[t_id]['attendees'][w_id]['charactersUsed'] = get_character_usage_by_set(dicts,sets[set_id],w_id,char_history=tourneys[t_id]['attendees'][w_id]['charactersUsed'])

		if 'l_id' in sets[set_id] and sets[set_id]['l_id'] is not None:
			l_id = sets[set_id]['l_id']
			tourneys[t_id]['attendees'][l_id]['setsPlayed'].append(set_id)
			tourneys[t_id]['attendees'][l_id]['charactersUsed'] = get_character_usage_by_set(dicts,sets[set_id],l_id,char_history=tourneys[t_id]['attendees'][l_id]['charactersUsed'])
	tourneys[t_id]['numSets'] = len(tourneys[t_id]['setIds'])

	if 'slugs' not in meta:
		meta['slugs'] = {}
	meta['slugs'][t_slug] = t_id
	meta['slugs'][t_ss] = t_id
	meta['slugs'][slug] = t_id
	if 'numEvents' not in meta:
		meta['numEvents'] = 0
		tourneys[t_id]['index'] = 0
	else:
		tourneys[t_id]['index'] = meta['numEvents']

	tourneys[t_id]['imported'] = True
	tourneys[t_id]['upcoming'] = False

	t_rating,t_sigmoid = calc_tourney_stack_score(dicts,t_id)
	if t_rating is None:
		tourneys[t_id]['rating'] = None
	else:
		tourneys[t_id]['rating'] = float(t_rating)
	if t_sigmoid is None:
		tourneys[t_id]['sigmoid'] = None
	else:
		tourneys[t_id]['sigmoid'] = list(t_sigmoid)
		
	return True

# stores db meta info
def store_meta(dicts,t_info,year):
	tourneys,ids,p_info,records,skills,meta = dicts
	t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_size,t_images,t_coords,t_bracket,t_hashtag = t_info

	# store basic info on the db
	meta['gameId'] = db_game
	meta['startYear'] = db_year
	meta['endYear'] = max(db_year,db_year+db_year_count)
	meta['yearCount'] = db_year_count
	meta['isCurrent'] = db_current
	meta['isSeason'] = db_season
	meta['isArcadian'] = only_arcadians
	meta['numEvents'] = len([temp_t_id for temp_t_id in tourneys if type(temp_t_id) is not str])
	meta['numEventsImported'] = len([temp_t_id for temp_t_id in tourneys if type(temp_t_id) is not str if tourneys[temp_t_id]['imported']])
	meta['numEventsActive'] = len([temp_t_id for temp_t_id in tourneys if type(temp_t_id) is not str if tourneys[temp_t_id]['active']])
	today_date = datetime.datetime.now()
	meta['dateBuilt'] = [today_date.year,today_date.month,today_date.day]
	if 'emptyAccts' not in meta:
		meta['emptyAccts'] = []
	# activity history date tracking setup
	if 'yearsActive' not in meta:
		meta['yearsActive'] = []
	if 'activityHistory' not in meta:
		meta['activityHistory'] = {}
	if t_date[0] not in meta['activityHistory']:
		meta['activityHistory'][t_date[0]] = {}
	if t_date[1] not in meta['activityHistory'][t_date[0]]:
		meta['activityHistory'][t_date[0]][t_date[1]] = {}

	# store info on last arguments
	if 'args' not in meta:
		meta['args'] = {}

	for arg in vars(args):
		meta['args'][arg] = getattr(args,arg)

	# instantiate min/max skill markers
	if 'srank_min' not in meta:
		meta['srank_min'] = 1.
		meta['elo_min'] = 1500
		meta['elo_max'] = 1500
		meta['glicko_min'] = 1500
		meta['glicko_max'] = 1500
	srank_min = meta['srank_min']
	elo_min = meta['elo_min']
	elo_max = meta['elo_max']
	glicko_min = meta['glicko_min']
	glicko_max = meta['glicko_max']

	# instantiate top 10/100/500 dicts if not already present
	if 'top10' not in meta:
		meta['top10'] = {}
		meta['top10']['srank'] = {k:{} for k in range(11)}
		meta['top10']['elo'] = {k:{} for k in range(11)}
		meta['top10']['glicko'] = {k:{} for k in range(11)}
		meta['top10']['mainrank'] = {k:{} for k in range(11)}
	if 'top50' not in meta:
		meta['top50'] = {}
		meta['top50']['srank'] = {k:{} for k in range(51)}
		meta['top50']['elo'] = {k:{} for k in range(51)}
		meta['top50']['glicko'] = {k:{} for k in range(51)}
		meta['top50']['mainrank'] = {k:{} for k in range(51)}
	if 'top100' not in meta:
		meta['top100'] = {}
		meta['top100']['srank'] = {k:{} for k in range(101)}
		meta['top100']['elo'] = {k:{} for k in range(101)}
		meta['top100']['glicko'] = {k:{} for k in range(101)}
		meta['top100']['mainrank'] = {k:{} for k in range(101)}
	if 'top500' not in meta:
		meta['top500'] = {}
		meta['top500']['srank'] = {k:{} for k in range(501)}
		meta['top500']['elo'] = {k:{} for k in range(501)}
		meta['top500']['glicko'] = {k:{} for k in range(501)}
		meta['top500']['mainrank'] = {k:{} for k in range(501)}
	n = 0
	m = 0
	for p_id in p_info:
		n += 1
		## check for account type (if nameDisplay is null, not a real user account)
		## TODO: some kind of verified thingy
		#if p_info[p_id]['name_display'] is None and p_id not in meta['emptyAccts']:
		#	meta['emptyAccts'].append(p_id)
		# check for activity level
		if p_info[p_id]['active']:
			m += 1
		# check for min/max elo
		p_elo = p_info[p_id]['elo']
		if p_elo < elo_min:
			elo_min = p_elo
		if p_elo > elo_max:
			elo_max = p_elo
		# check for min/max glicko
		p_glicko = p_info[p_id]['glicko'][0]
		if p_glicko < glicko_min:
			glicko_min = p_glicko
		if p_glicko > glicko_max:
			glicko_max = p_glicko
		# check for min srank
		if p_info[p_id]['srank'] < srank_min:
			srank_min = p_info[p_id]['srank']
		# store top 10/100/500 player ids (by each skill)
		for skill_rnk in ['elo','glicko','srank']:
			for skill_div in [500,100,50,20,10]:
				# get skill values for top 10/20/50/100/500 cutoffs
				if p_info[p_id][skill_rnk+'-rnk'] == skill_div:
					if skill_rnk == 'glicko':
						meta[skill_rnk+'_'+str(skill_div)+'_cutoff'] = p_info[p_id][skill_rnk][0]
					else:
						meta[skill_rnk+'_'+str(skill_div)+'_cutoff'] = p_info[p_id][skill_rnk]
				# store top 10/100/500 player ids by each skill rank, with rank as key
				if skill_div in [500,100,50,10] and p_info[p_id][skill_rnk+'-rnk'] <= skill_div:
					# delete this after all dbs rebuilt
					if type(meta['top'+str(skill_div)][skill_rnk][p_info[p_id][skill_rnk+'-rnk']]) is int:
						meta['top'+str(skill_div)][skill_rnk][p_info[p_id][skill_rnk+'-rnk']] = {}
					meta['top'+str(skill_div)][skill_rnk][p_info[p_id][skill_rnk+'-rnk']]['id'] = p_id
					meta['top'+str(skill_div)][skill_rnk][p_info[p_id][skill_rnk+'-rnk']]['tag'] = p_info[p_id]['tag']
	# store new max/mins
	meta['srank_min'] = srank_min
	meta['elo_min'] = elo_min
	meta['elo_max'] = elo_max
	meta['glicko_min'] = glicko_min
	meta['glicko_max'] = glicko_max

	# activity metrics
	meta['numPlayers'] = n
	meta['numPlayersActive'] = m
	meta['isActiveGame'] = m > 100 and meta['numEventsActive'] > 10
	if meta['isActiveGame']:
		meta['lastActiveYear'] = year
		if year not in meta['yearsActive']:
			meta['yearsActive'].append(year)
	if t_date[0] not in meta['activityHistory'][t_date[0]][t_date[1]] or not meta['activityHistory'][t_date[0]][t_date[1]][t_date[0]]:
		meta['activityHistory'][t_date[0]][t_date[1]][t_date[0]] = meta['isActiveGame']
	meta['lastEvent'] = t_id

	return dicts

# delete all data imported from a tourney
# (keeps absolute player data such as ID, meta info)
# **does NOT save db automatically**
# does NOT delete players (in case they become active again, saves info/skills) or skill histories
def delete_tourney(dicts,t_id,slug=None,clean_slugs=False,clean_tourneys=True,clean_skills=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	if not slug == None:
		t_id = meta['slugs'][slug]

	if t_id in tourneys:
		if v >= 6:
			print('Deleting... %s | %d'%(tourneys[t_id]['name'],t_id))
		for abs_id in dcopy(ids):
			if abs_id in ids:
				# remove data from records & p_info
				if abs_id in records and t_id in records[abs_id]['placings']:
					# remove player records for this tourney
					del records[abs_id]['placings'][t_id]
					del records[abs_id]['paths'][t_id]

					# remove event count
					p_info[abs_id]['events_entered'] = max(p_info[abs_id]['events_entered']-1,0)

					# remove h2h losses
					for loss in records[abs_id]['losses']:
						if t_id in records[abs_id]['losses'][loss]:
							p_info[abs_id]['sets_played'] -= len([set_id for set_id in records[abs_id]['losses'][loss][t_id]])
							records[abs_id]['losses'][loss] = {tempid:records[abs_id]['losses'][loss][tempid] for tempid in records[abs_id]['losses'][loss] if not tempid == t_id}

					# remove h2h wins
					for win in records[abs_id]['wins']:
						if t_id in records[abs_id]['wins'][win]:
							p_info[abs_id]['sets_played'] -= len([set_id for set_id in records[abs_id]['wins'][win][t_id]])
							records[abs_id]['wins'][win] = {tempid:records[abs_id]['wins'][win][tempid] for tempid in records[abs_id]['wins'][win] if not tempid == t_id}

					# remove main character tracking
					del records[abs_id]['main'][t_id]

					yc_str = ''
					if db_year_count > 0:
						yc_str += '-'+str(db_year+db_year_count)
					if db_current:
						yc_str += '_c'
					sets = easy_load_db_sets(ver=str(db_game)+'/'+str(db_year)+yc_str)
					deleted_sets = [set_id for set_id in records[abs_id]['set_history'] if not set_id in sets]
					tourney_sets = [set_id for set_id in records[abs_id]['set_history'] if not set_id in deleted_sets if sets[set_id]['t_id'] == t_id]

					# remove character usage data for player and opponent
					for set_id in tourney_sets:
						if 'games' in sets[set_id]:
							for game_id in sets[set_id]['games']:
								g_w_id = sets[set_id]['games'][game_id]['w_id']
								g_l_id = sets[set_id]['games'][game_id]['l_id']
								if g_w_id is not None and g_l_id is not None:
									if 'characters' in sets[set_id]['games'][game_id]:
										if sets[set_id]['games'][game_id]['characters'] != {}:
											g_w_char_id = sets[set_id]['games'][game_id]['characters'][g_w_id]
											g_l_char_id = sets[set_id]['games'][game_id]['characters'][g_l_id]
											
											p_info[g_w_id]['characters'][g_w_char_id][0] = max(0,p_info[g_w_id]['characters'][g_w_char_id][0]-1)
											p_info[g_l_id]['characters'][g_l_char_id][1] = max(0,p_info[g_l_id]['characters'][g_l_char_id][1]-1)

					# remove sets from gameplay history
					records[abs_id]['set_history'] = [set_id for set_id in records[abs_id]['set_history'] if not set_id in deleted_sets if not set_id in tourney_sets]

					# update last_event if it was this one
					if p_info[abs_id]['last_event'] == t_id:
						event_history = sorted([(temp_id,tourneys[temp_id]['date']) for temp_id in records[abs_id]['placings'] if temp_id != t_id],key=lambda l:(l[1][0],l[1][1],l[1][2]))
						if len(event_history) > 0:
							p_info[abs_id]['last_event'] = event_history[0][0]
						else:
							p_info[abs_id]['last_event'] = None

					# mark players inactive if they are no longer in the db's ranking/anaylsis period
					if not is_active(dicts,abs_id,excluded_events=[t_id]):
						p_info[abs_id]['active'] = False
						p_info[abs_id]['status'] = handle_player_status(abs_id,'inactive')

				# remove entrant ids from player
				if t_id in ids[abs_id] and 't_'+str(t_id) in ids:
					
					del ids[abs_id][t_id]

			# update skills and skill histories (NOT IMPLEMENTED YET)
			if clean_skills:
				t_index = tourneys[t_id]['index']
				if t_index > 0:
					prev_event = sorted([temp_id for temp_id in tourneys],lambda l_id:tourneys[l_id]['index'])[tourneys[t_id]['index']-1]

		# remove entrant ids from event
		if clean_tourneys:
			del ids['t_'+str(t_id)]

		# remove tournament from imported slugs
		# (off by default)
		if clean_slugs:
			l_slugs = load_slugs(game_id,year)
			l_slugs = [l_slug for l_slug in l_slugs if meta['slugs'][slug] != t_id]
			save_slugs(l_slugs,game_id,year,to_save_db=to_save_db)

		# remove tournament (or mark inactive)
		if clean_tourneys:
			for t_s in dcopy(meta['slugs']):
				if meta['slugs'][t_s] == t_id:
					#slug = t_s
					del meta['slugs'][t_s]
		if t_id in tourneys:
			tourneys[t_id]['active'] = False
			if clean_tourneys:
				del tourneys[t_id]

		meta['lastDeleted'] = t_id

	return tourneys,ids,p_info,records,skills,meta

# cleans out tourneys over a year out from the currently importing one
def clean_old_tourneys(dicts,t_info,rank_period=args.srank_ranking_period,delete_data=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_size,t_images,t_coords,t_bracket,t_hashtag = t_info
	if v >= 6:
		print('Cleaning tourneys over: %d months out from %s'%(rank_period,t_date))

	for old_id in tourneys:
		if old_id != 'slugs' and tourneys[old_id]['active']:
			old_date = tourneys[old_id]['date']
			if v >= 8:
				print('Scanning... %s: %s'%(tourneys[old_id]['name'],old_date))
			if (((t_date[0]-2016)*12 + t_date[1]) - ((old_date[0]-2016)*12 + old_date[1])) > rank_period:
				if v >= 8:
					print('Outdated event found!')
				# if (curr_month - temp_month) > 12: delete tourney
				delete_tourney(dicts,old_id,clean_tourneys=delete_data)

	return dicts

# delete all data associated with a given player
# (player id, meta info, tourney results/records are deleted!!!)
# **does NOT save db automatically**
def delete_player(dicts,p_id,tag=None,delete_sets=True):
	tourneys,ids,p_info,records,skills,meta = dicts
	abs_id,p_meta,p_records,p_ids = get_player(dicts,p_id,tag)

	# delete player records
	del records[abs_id]
	del p_info[abs_id]
	del ids[abs_id]
	# delete instances of player from other players' records
	if delete_sets:
		for l_id in p_records['losses']:
			del [records][l_id]['wins'][abs_id]
		for w_id in p_records['wins']:
			del [records][w_id]['losses'][abs_id]

	return tourneys,ids,p_info,records,skills,meta

# creates a blank db and writes over any existing one in the given directory
def clear_db(ver,loc='db'):
	dicts = load_db(None,force_blank=True)
	save_db(dicts,ver,loc=loc)
	return dicts

# used to save datasets/hashtables
def save_db(dicts,ver,loc='db'):
	if int(args.teamsize) == 2:
		ver = str(ver) + ' (DUBS)'
	if int(args.teamsize) >= 4:
		ver = str(ver) + ' (CREWS)'
	if only_arcadians:
		ver = str(ver)+' (ARC)'
	if to_save_db:
		if v >= 3:
			print('Saving DB...')
		for data,name in zip(dicts,['tourneys','ids','p_info','records','skills','meta']):
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
			print('Loading DB...')
		return [load_dict(name,ver,loc) for name in ['tourneys','ids','p_info','records','skills','meta']]
	else:
		if v >= 3:
			print('Generating blank DB...')
		return [load_dict(name,'blank',loc='db') for name in ['tourneys','ids','p_info','records','skills','meta']]

# used to load datasets/hashtables; auto-fills ver modifiers based on args
def easy_load_db(ver,loc='db',force_blank=False):
	'''if int(args.teamsize) == 2:
		ver = str(ver) + ' (DUBS)'
	if int(args.teamsize) >= 4:
		ver = str(ver) + ' (CREWS)'
	if int(only_arcadians):
		ver = str(ver)+' (ARC)'
		'''
	return load_db(ver,loc,force_blank)

# saves full set of match results for db
def save_db_sets(sets,ver,loc='db',overwrite=False):
	if int(args.teamsize) == 2:
		ver = str(ver) + ' (DUBS)'
	if int(args.teamsize) >= 4:
		ver = str(ver) +'  (CREWS)'
	if only_arcadians:
		ver = str(ver)+' (ARC)'
	if to_save_db:
		if v >= 7:
			print('Saving DB sets...')
		# overwrite existing set db
		if overwrite:
			save_dict(sets,'sets',ver,loc)
		# add to existing set db
		else:
			base_dict = easy_load_db_sets(ver,loc)
			for set_id in sets:
				base_dict[set_id] = sets[set_id]
			save_dict(base_dict,'sets',ver,loc)

# loads full set of match results for db
def load_db_sets(ver,loc='db'):
	if v >= 7:
		print('Loading DB sets...')
	return load_dict('sets',ver,loc)

# used to load datasets/hashtables; auto-fills ver modifiers based on args
def easy_load_db_sets(ver,loc='db'):
	if int(args.teamsize) == 2:
		ver = str(ver) + ' (DUBS)'
	if int(args.teamsize) >= 4:
		ver = str(ver) + ' (CREWS)'
	if int(only_arcadians):
		ver = str(ver)+' (ARC)'
	return load_db_sets(ver,loc)


#if __name__ == '__main__':
	#read_majors()
	#print([[arg,getattr(args,arg)] for arg in vars(args)])