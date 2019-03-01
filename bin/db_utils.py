## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
import os,sys,pickle,time
import json
import argparse
import shutil
from timeit import default_timer as timer
from copy import deepcopy as dcopy
from math import *
## UTIL IMPORTS
from readin import readin,set_readin_args
from readin_utils import *
from calc_utils import *
from region_utils import *
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
parser.add_argument('-st','--static_teams',help='store teams as static units, rather than strack skill of its members individually [WIP]',default=False)
parser.add_argument('-d','--displaysize',help='lowest placing shown on pretty printer output, or -1 to show all entrants (default 64)',default=64)
parser.add_argument('-sl','--slug',help='tournament URL slug',default=None)
parser.add_argument('-ss','--short_slug',help='shorthand tournament URL slug',default=None)
parser.add_argument('-p','--print',help='print tournament final results to console as they are read in (default False)',default=False)
parser.add_argument('-c','--collect_garbage',help='delete phase data after tournament is done being read in (default True)',default=True)
parser.add_argument('-ar','--use_arcadians',help='count arcadian events (default False)',default=False)
parser.add_argument('-gt','--glicko_tau',help='tau value to be used by Glicko-2 algorithm (default 0.5)',default=0.5)
parser.add_argument('-ma','--min_activity',help='minimum number of tournament appearances in order to be ranked. ELO etc still calculated.',default=3)
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
glicko_tau = float(args.glicko_tau)

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
			if v >= 3 and year == int(db_year):
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
		if len(slugs) <= 0:
			print("No slugs found for game %d in year %d:"%(game_id,year))
		else:
			print("Scraped the following slugs for game %d in year %d:"%(game_id,year))
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
	db_game = int(args.game)
	db_year = int(args.year)

## AUXILIARY FUNCTIONS
# loads database and stores any tournament data not already present given the url slug
def read_tourneys(slugs,ver='default',year=None,base=None):
	if year != None:
		verstr = '%s/%s'%(ver,db_yearstr)
	else:
		verstr = ver

	if base == None:
		[tourneys,ids,p_info,records,skills] = easy_load_db(verstr)
	else:
		tourneys,ids,p_info,records,skills = base

	if v >= 4 and len(tourneys.keys())>1 and year == db_year:
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
				if store_data(readins,(tourneys,ids,p_info,records,skills),slug):
					if to_save_db:
						save_db((tourneys,ids,p_info,records,skills),verstr)
						save_db_sets(readins[6],verstr)
					t_id = tourneys['slugs'][readins[0][2]]
					if collect:
						delete_tourney_cache(t_id)
	return tourneys,ids,p_info,records,skills

# helper function to store all data from a call to readin
def store_data(readins,dicts,slug):
	t_info,entrants,names,paths,wins,losses,sets = readins
	tourneys,ids,p_info,records,skills = dicts
	if len(entrants.keys()) > 1:
		if store_players(entrants,names,t_info,dicts):
			if store_records(wins,losses,paths,sets,t_info,dicts):
				if store_tourney(slug,t_info,names['groups'],dicts):
					return True
	return False

# stores data through absolute player IDs (converting from entrant IDs)
# entrants = ([name],[abs_id],e_id,[metainfo]) where name, abs_id, metainfo are a list for each member of the team
# and name = (sponsor, tag, teamname (or None))
# and metainfo = [firstname, lastname, state, country, city]
def store_players(entrants,names,t_info,dicts,translate_cjk=True):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records,skills = dicts
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
				if 't_'+str(t_id) not in ids:
					ids['t_'+str(t_id)] = {}
				ids['t_'+str(t_id)][e_id] = abs_id

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
				p_tag = names[e_id][1][idx]
				trans_tag = p_tag
				if p_tag not in p_info[abs_id]['aliases']:
					p_info[abs_id]['aliases'].extend([p_tag])
					if p_tag != None and any([is_cjk(tag_c) for tag_c in p_tag]):
						#trans_tag = '『'+translate(tag)+'』'
						#trans_tag = '<'+(translate(p_tag,to='ja')).pronunciation+'>'
						trans_tag = '<'+transliterate(p_tag)+'>'
						if trans_tag not in p_info[abs_id]['aliases']:
							p_info[abs_id]['aliases'].extend([trans_tag])
				if translate_cjk:
					p_info[abs_id]['tag'] = trans_tag
				else:
					p_info[abs_id]['tag'] = p_tag
				for key,info in zip(['firstname','lastname','state','country','city'],entrants[e_id][3][idx]):
					if key in p_info[abs_id]:
						if not (info == 'N/A' or info == '' or info == "" or info == None):
							p_info[abs_id][key] = info
					else:
						p_info[abs_id][key] = info
				if 'region' not in p_info[abs_id] or p_info[abs_id]['region'] == None:
					#p_info[abs_id]['region'] = get_region(dicts,abs_id,granularity=2,to_calc=True)
					p_info[abs_id]['region'] = {}
					for r_i in range(1,6):
						p_info[abs_id]['region'][r_i] = get_region(dicts,abs_id,granularity=r_i,to_calc=True)
				else:
					#print(p_info[abs_id]['region'])
					if any([p_info[abs_id]['region'][r_idx] == 'N/A' for r_idx in range(1,6)]) or p_info[abs_id]['region'] == {}:
						#p_info[abs_id]['region'] = get_region(dicts,abs_id,granularity=2,to_calc=True)
						for r_i in range(1,6):
							p_info[abs_id]['region'][r_i] = get_region(dicts,abs_id,granularity=r_i,to_calc=True)

				# store W/L record per character
				if 'characters' not in p_info[abs_id]:
					chardict = load_dict('characters',None,loc='../lib')
					if db_game in chardict:
						chardict = chardict[db_game]
						p_info[abs_id]['characters'] = {char_id: [0,0] for char_id in chardict}
					else:
						p_info[abs_id]['characters'] = {}
				'''for character in characters[e_id]:
					p_info[abs_id]['characters'] = characters[e_id]'''

				# store ranking data, with initial values if needed
				if 'elo' not in skills:
					for key in ['elo','elo_del','glicko','glicko_del','srank','srank_del','srank_sig','perf']:
						skills[key] = {}
				if 'elo' not in p_info[abs_id]:
					p_info[abs_id]['elo'] = 1500.
					skills['elo'][abs_id] = {}
					skills['elo_del'][abs_id] = {}
				# glicko stores a tuple with (rating,RD,volatility)
				if 'glicko' not in p_info[abs_id]:
					p_info[abs_id]['glicko'] = (1500.,350.,0.06)
					skills['glicko'][abs_id] = {}
					skills['glicko_del'][abs_id] = {}
				if 'srank' not in p_info[abs_id]:
					p_info[abs_id]['srank'] = int(1)
					#p_info[abs_id]['srank'] = 0.5
					p_info[abs_id]['srank_sig'] = (0.5,0.,1.,4.)
					skills['srank'][abs_id] = {}
					skills['srank_del'][abs_id] = {}
					skills['srank_sig'][abs_id] = {}
				if 'sets_played' not in p_info[abs_id]:
					p_info[abs_id]['sets_played'] = 0
				if 'events_entered' not in p_info[abs_id]:
					p_info[abs_id]['events_entered'] = 0
				#if 'last_event' not in p_info[abs_id]:
				#	p_info[abs_id]['last_event'] = t_id
				p_info[abs_id]['last_event'] = t_id
				if abs_id not in skills['perf']:
					skills['perf'][abs_id] = {}

			#print(ids[abs_id])
	#else:
		#print(t_id)
		#print(tourneys)
		#print(tourneys[t_id])
	return True

# stores win/loss records, updates player skills/rankings if enabled
# ranking period in months (only used by sigmoid ranking)
def store_records(wins,losses,paths,sets,t_info,dicts,to_update_ranks=True,to_update_sigmoids=True,ranking_period=2):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records,skills = dicts
	old_p_info = dcopy(p_info)
	glicko_matches = {}


	elo_history = skills['elo']
	elo_deltas = skills['elo_del']
	#glicko_history = skills['glicko']
	#glicko_deltas = skills['glicko_del']
	simrank_history = skills['srank']
	simrank_deltas = skills['srank_del']
	sigmoid_history = skills['srank_sig']
	#performance_history = skills['perf']

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
						# store set id/data & character data if available
						records[abs_id]['set_history'].extend([win[1][0]])
						if 'games' in sets[records[abs_id]['set_history'][-1]]:
							for game_id in sets[records[abs_id]['set_history'][-1]]['games']:
								game_data = sets[records[abs_id]['set_history'][-1]]['games'][game_id]
								if 'characters' in game_data:
									p_info[abs_id]['characters'][game_data['characters'][ids[abs_id][t_id]]][0] += 1
						# store opponent & event
						l_id = ids['t_'+str(t_id)][win[0]]
						if l_id not in records[abs_id]['wins']:
							records[abs_id]['wins'][l_id] = {}
							records[abs_id]['wins'][l_id] = [t_id]
						else:
							records[abs_id]['wins'][l_id].extend([t_id])

						p_info[abs_id]['sets_played'] += 1
						actual_score += 1.
						expected_score += exp_score(old_p_info[abs_id]['elo'],old_p_info[l_id]['elo'])

						glicko_scores.extend([(1.,l_id)])
				if e_id in losses:
					for loss in losses[e_id]:
						# store set id/data & character data if available
						records[abs_id]['set_history'].extend([loss[1][0]])
						if 'games' in sets[records[abs_id]['set_history'][-1]]:
							for game_id in sets[records[abs_id]['set_history'][-1]]['games']:
								game_data = sets[records[abs_id]['set_history'][-1]]['games'][game_id]
								if 'characters' in game_data:
									p_info[abs_id]['characters'][game_data['characters'][ids[abs_id][t_id]]][1] += 1
						# store opponent & event
						w_id = ids['t_'+str(t_id)][loss[0]]
						if w_id not in records[abs_id]['losses']:
							records[abs_id]['losses'][w_id] = {}
							records[abs_id]['losses'][w_id] = [t_id]
						else:
							records[abs_id]['losses'][w_id].extend([t_id])

						p_info[abs_id]['sets_played'] += 1
						actual_score += 0.
						expected_score += exp_score(old_p_info[abs_id]['elo'],old_p_info[w_id]['elo'])

						glicko_scores.extend([(0.,w_id)])

				if to_update_ranks:
					# update elo ratings after event
					old_elo = p_info[abs_id]['elo']
					new_elo = update_elo(old_p_info[abs_id]['elo'],expected_score,actual_score,old_p_info[abs_id]['sets_played'])
					p_info[abs_id]['elo'] = new_elo
					glicko_matches[abs_id] = glicko_scores
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
			else:
				elo_history[abs_id][t_id] = p_info[abs_id]['elo']
				elo_deltas[abs_id][t_id] = 0.
				#performance_history[abs_id][t_id] = 0

	if to_update_ranks:
		if v >= 5:
			print('Updating Performances...')
		update_performances((tourneys,ids,old_p_info,records,skills),t_info)
		if v >= 4:
			print('Updating Glicko...')
		update_glicko(dicts,glicko_matches,t_info,tau=glicko_tau)
		if to_update_sigmoids:
			#update_sigmoids(dicts,t_info,max_iterations=500,v=v,ranking_period=ranking_period)
			sigrank_res = update_sigmoids(dicts,t_info,max_iterations=1000,v=v,ranking_period=2,sig='alt')
			if sigrank_res:
				ISR = {'params': sigrank_res}
				save_dict(ISR,'ISR_%d_%d_%d'%(db_game,db_year,db_year_count),None,'..\\lib')

	return True

# stores tourney meta info and marks tournament as imported
def store_tourney(slug,t_info,group_names,dicts):
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	tourneys,ids,p_info,records,skills = dicts
	tourneys[t_id] = {}
	tourneys[t_id]['name'] = t_name
	tourneys[t_id]['slug'] = t_slug
	tourneys[t_id]['shortSlug'] = t_ss
	tourneys[t_id]['type'] = t_type
	tourneys[t_id]['date'] = t_date
	#tourneys[t_id]['region'] = t_region
	tourneys[t_id]['region'] = calc_region(country=t_region[1],state=t_region[0])
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
## POSSIBLY deprecated
def delete_tourney(dicts,t_id,slug=None):
	tourneys,ids,p_info,records,skills = dicts
	if not slug == None:
		t_id = tourneys['slugs'][slug]

	if t_id in tourneys:
		for abs_id in dcopy(ids):
			if abs_id in ids:
				if t_id in ids[abs_id] and t_id in ids:
					# remove entrant ids/data
					del ids[abs_id][t_id]
					del ids['t_'+str(t_id)]

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

		# remove tournament records for this tourney'
		for t_s in dcopy(tourneys['slugs']):
			if tourneys['slugs'][t_s] == t_id:
				#slug = t_s
				del tourneys['slugs'][t_s]
		if t_id in tourneys:
			del tourneys[t_id]

		# remove tournament from imported slugs

	return tourneys,ids,p_info,records,skills

# delete all data associated with a given player
# (player id, meta info, tourney results/records are deleted!!!)
# **does NOT save db automatically**
def delete_player(dicts,p_id,tag=None,delete_sets=True):
	tourneys,ids,p_info,records,skills = dicts
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

	return tourneys,ids,p_info,records,skills

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
		for data,name in zip(dicts,['tourneys','ids','p_info','records','skills']):
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
		return [load_dict(name,ver,loc) for name in ['tourneys','ids','p_info','records','skills']]
	else:
		return [load_dict(name,'blank',loc='db') for name in ['tourneys','ids','p_info','records','skills']]

# used to load datasets/hashtables; auto-fills ver modifiers based on args
def easy_load_db(ver,loc='db',force_blank=False):
	if int(args.teamsize) == 2:
		ver = str(ver) + ' (DUBS)'
	if int(args.teamsize) >= 4:
		ver = str(ver) + ' (CREWS)'
	if int(only_arcadians):
		ver = str(ver)+' (ARC)'
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


if __name__ == '__main__':
	read_majors()