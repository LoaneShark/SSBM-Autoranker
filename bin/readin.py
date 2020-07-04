## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError
import requests
import pathlib
import traceback
import logging
import numpy as np 
#import scipy as sp 
import json
import re
import argparse
from timeit import default_timer as timer
import os,pickle,time,datetime
## UTIL IMPORTS
from arg_utils import *
from readin_utils import *

## SMASH.GG IMPORTS
from smashggpy.util import Initializer
from smashggpy.util.QueryQueueDaemon import QueryQueueDaemon
from smashggpy.util.Query import Query
from smashggpy.util.NetworkInterface import NetworkInterface as NI
from queries import SmashranksQueries as queries

#from smashggAPI import client


## DESCRIPTION
# Reads in data using the old smash.gg API, and then extracts relevant information
# Old api query format, just sub in <SLUG> or <GROUP_ID> as needed
# Tourneys: https://api.smash.gg/tournament/<SLUG>?expand[]=event&expand[]=groups&expand[]=phase
#   Phases: https://api.smash.gg/phase_group/<GROUP_ID>?expand[]=seeds&expand[]=sets

## ARGUMENT PARSING
args = get_args()

v = int(args.verbosity)
# verbosity threshold for save/load statements
lv = 8
save_res = args.save
load_res = args.load
if args.save == 'False':
	save_res = False
if args.load == 'False':
	load_res = False
force_first_event = args.force_first
if args.force_first == 'False':
	force_first_event = True
teamsize = int(args.teamsize)
game = int(args.game)
if args.force_game:
	game = int(args.force_game)
if game not in [1,2,3,4,5,1386,24] and not force_game:		#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386 	RoA = 24
	print('Invalid game number provided. Forcing melee (id=1) instead.')
	game = 1
disp_num = int(args.display_size)
t_slug_a = args.slug
t_ss_a = args.short_slug
if t_ss_a == None:
	t_slug_a = t_slug_a
else:
	t_slug_a = get_slug(t_ss_a)
print_res = args.print
count_arcadians = args.use_arcadians
if count_arcadians == -1:
	only_arcadians = True
else:
	only_arcadians = False
current_db = args.current_db

def set_readin_args(r_args):
	v = int(r_args.verbosity)
	# verbosity for save/load statements
	lv = 6
	save_res = r_args.save
	load_res = r_args.cache_results
	force_first_event = r_args.force_first
	teamsize = int(r_args.teamsize)
	game = int(r_args.game)
	if game not in [1,2,3,4,5,1386,24] and False:		#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386 	RoA = 24
		print('Invalid game number provided. Forcing melee (id=1) instead.')
		game = 1
	disp_num = int(r_args.display_size)
	t_slug_a = r_args.slug
	t_ss_a = r_args.short_slug
	if t_ss_a == None:
		t_slug_a = t_slug_a
	else:
		t_slug_a = get_slug(t_ss_a)
	print_res = r_args.print
	current_db = r_args.current_d

def read_smashgg_api_key(path='../lib/API Token.txt'):
	try:
		print(path)
		with open(path) as f:
			print(f)
			api_token = f.read()
			if api_token in ['<INSERT SMASH.GG API TOKEN HERE>', None, '', ' ']:
				print('API Token file missing or path is invalid. Please check path or run setup.py')
				return None
	except FileNotFoundError:
		print('API Token file missing or path is invalid. Please check path or run setup.py')
		return None
	return api_token

def smashgg_login(token):
	Initializer.initialize(token,'error')
	return True

## MAIN FUNCTIONS
def readin(tourney,t_type='slug'):
	if t_type == 'slug':
		slug = tourney
	elif t_type == 'ss':
		slug = get_slug(tourney)
	else:
		print('Error: invalid tourney identifier type')
		return None

	# PM Pools have a db breaking bug
	if slug == 'we-tech-those-3' and game == 2:
		return None
	# Ultimate Pools have a db breaking bug
	if slug == 'the-kid-the-goat-and-the-mang0' and game == 1386:
		return None
	# Filter out EVO 2016 Melee Doubles when not applicable
	if slug == 'evo-2016-melee-doubles' and args.teamsize != 2:
		return None

	api_token = read_smashgg_api_key()
	if smashgg_login(api_token):
		if v >= 2 and v < 4:
			start = timer()

		try:
			out = read_tournament(slug)
		except Exception as e:
			logging.error(traceback.format_exc())
			QueryQueueDaemon.kill_daemon()
			return False


		if out:
			t_info = out
			t_id,t_name,t_slug,t_ss,t_date,t_sdate,t_region,t_images,t_coords,t_bracket,t_hashtag = t_info
			entrants,wins,losses,paths,names,sets = read_groups(t_id,t_bracket)

			if v >= 2 and v < 4:
				print('{:.3f}'.format(timer()-start) + ' s')

			t_info = (t_id,t_name,t_slug,t_ss,t_date,t_sdate,t_region,len(entrants.keys()),t_images,t_coords,t_bracket,t_hashtag)
			if print_res:
				print_results(paths,names,entrants,losses,sets,game=game,max_place=disp_num)

			QueryQueueDaemon.kill_daemon()
			return t_info,entrants,names,paths,wins,losses,sets
		else:					
			QueryQueueDaemon.kill_daemon()
			return False
	else:
		QueryQueueDaemon.kill_daemon()
		raise HTTPError

	QueryQueueDaemon.kill_daemon()

# imports the bracket and tournament metadata for a given tournament slug
def read_tournament(slug):
	gamemap = {1: ['melee','ssbm','ssbmelee'], 2: ['P:M','project: m','project melee','project m'], 3: ['ssb4','smash 4','ssb wii u','smash wii u','for wii u'], \
				4: ['smash 64','ssb64','64'], 5: ['brawl','ssbb'], 1386: ['ssbu','ultimate','for switch','nintendo switch','switch'], 24: ['roa','rivals','of aether']}
	waves = {}

	try:

		tdata = SR_Tournament.parse(NI.query(queries.SR_tournament_query, {'slug': slug})['data']['tournament'])

		t_id = tdata.id
		t_name = tdata.name
		t_slug = tdata.slug
		t_ss = tdata.short_slug
		# date tuple in (year, month, day) format
		t_date = time.localtime(tdata.end_time)[:3]
		t_startdate = time.localtime(tdata.start_time)[:3]
		t_region = (tdata.venue.state,tdata.venue.country_code)
		t_coords = [tdata.venue.latitude,tdata.venue.longitude]
		t_hashtag = tdata.hashtag
		t_images = [sorted([t_img for t_img in tdata.images if t_img['type'] == 'profile'],key=lambda i: i['width'])[0],
						sorted([t_img for t_img in tdata.images if t_img['type'] == 'banner'],key=lambda i: i['width'])[0]]

		## Tourney Image Handling
		if False:
			# 2-length list with the urls for the first profile image and banner images found (for the tourney)
			t_propic = [img['url'] for img in tdata['entities']['tournament']['images'] if img['type'] == 'profile']
			if len(t_propic)>0:
				t_propic = t_propic[0]
			else:
				t_propic = None
			t_bannerpic = [img['url'] for img in tdata['entities']['tournament']['images'] if img['type'] == 'banner']
			if len(t_bannerpic)>0:
				t_bannerpic = t_bannerpic[0]
			else:
				t_bannerpic = None
			t_images = [t_propic,t_bannerpic]

		if v >= 1:
			print('Reading tournament: %s | %d'%(t_name,t_id))

		# can't read a tourney's results if it hasn't happened yet!
		day_after = datetime.datetime(t_date[0],t_date[1],t_date[2])
		while day_after.weekday() >= 4:
			day_after += datetime.timedelta(days=1)
		if day_after > datetime.datetime.today():
			if v >= 1:
				print('Cannot read %s: Tournament hasn\'t happened yet!'%t_name)
			return False

		# get all event_id's for events that are specified gametype (default=1 [melee]) and entrantcount (default=1 [singles])
		events = tdata.get_events()
		event_ids = [event.id for event in events]
		phase_dict = {event.id: event.get_phases() for event in events}
		#events = [event for event in tdata.get_events() if event.videogame == game]
		#event_ids = [[event['id'],(event['name'],event['description'])] for event in tdata['entities']['event'] if event['videogameId'] == game] #and min(event['entrantSizeMin'],4) == min(teamsize,4)]
		#event_ids = [event['id'] for event in tdata['entities']['event'] if event['videogameId'] == game and event['entrantSizeMin'] == teamsize]
		
		if teamsize == 1:
			team_string = 'singles'
		elif teamsize == 2:
			team_string = 'doubles'
		elif teamsize > 2:
			team_string = 'crews'
		else:
			team_string = '[V O I D]'
		if not count_arcadians:
			pro_string = 'PRO'
		elif only_arcadians:
			pro_string = 'AMATEUR'
		else:
			pro_string = 'ALL'
		if v >= 6:
			print('only looking for brackets of game type: %s %s [%s]'%(gamemap[game][0], team_string, pro_string))
			print('events pre filtering: ' + str([(event.id,event.name) for event in events]))

		# filters out events that don't list the given game in description, to filter out stuff like low tiers/ironmans/crews etc
		events = [event for event in events if has_game(event.name,game)]# or has_game(event.description,game)]
		# filter out any events that are marked as exhibition
		if True:
			# returns true if an event is all exhibiton phases (not partially, to allow for brackets that feed into amateur/redemption brackets etc)
			is_exhibition = lambda ev_id: all([phase.is_exhibition for phase in phase_dict[ev_id]])
			exhibition_event_ids = [event.id for event in events if is_exhibition(event.id)]
			events = [event for event in events if event.id not in exhibition_event_ids]
		# catcher in case of poor event labeling (this happens for old events sometimes)
		if len(events) < 1:
			events = events = tdata.get_events()[0]

		# filters out events that have 'amateur', 'ladder' or 'arcadian' in the description
		amateur_event_ids = [event.id for event in events if is_amateur(event.name) ]#or is_amateur(event.description)]
		ladder_event_ids = [event.id for event in events if is_ladder(event.name) ]#or is_ladder(event.description)]
		if only_arcadians or not count_arcadians:
			arcadian_event_ids = [event.id for event in events if is_arcadian(event.name)]# or is_arcadian(event.description)]
		event_ids = [event_id for event_id in event_ids if not event_id in exhibition_event_ids]
		event_ids = [event_id for event_id in event_ids if not event_id in amateur_event_ids]
		event_ids = [event_id for event_id in event_ids if not event_id in ladder_event_ids]
		if not count_arcadians:
			event_ids = [event_id for event_id in event_ids if not event_id in arcadian_event_ids]
		elif only_arcadians:
			event_ids = arcadian_event_ids
		# apply above filtering
		events = [event for event in events if event.id in event_ids]

		# filter by teamsize
		if True:
			if teamsize > 1:
				team_event_ids = [event.id for event in events if is_teams(event.name,teamsize)]# or is_teams(event.description,teamsize)]
			elif teamsize <= 1:
				team_event_ids = [event.id for event in events if is_teams(event.name,2)]# or is_teams(event.description,2)]

			if teamsize > 1:
				events = [event for event in events if event.id in team_event_ids]
			else:
				events = [event for event in events if not event.id in team_event_ids]

		if v >= 6:
			print('event_ids post filtering: ' + str(len(events)))
		if len(events) <= 0 and v >= 1:
			print('** No suitable events found of form: %s %s [%s] at this tournament'%(gamemap[game][0], team_string, pro_string))

		if force_first_event:
			# events = [sorted(events,key=lambda ev: ev.num_entrants)[0]]
			events = [sorted(events,key=lambda ev: ev.id)[0]]

		# get all phases for each event (ideally filtered down to 1 by now)
		phases = flatten([sorted(phase_dict[event.id], key=lambda ph: ph.phase_order) for event in events])
		# get all groups for each phase
		groups = flatten([phase.get_phase_groups() for phase in phases])
		t_bracket = {'events':events, 'phases':phases, 'groups':groups}
		
		t_info = (t_id,t_name,t_slug,t_ss,t_date,t_startdate,t_region,t_images,t_coords,t_bracket,t_hashtag)
		return t_info

	except HTTPError:
		print('Error 404: tourney [%s] not found'%slug)
		return False

# reads the sets and bracket results for a given phase
def read_groups(t_id,t_bracket,translate_cjk=True):
	events = t_bracket['events']
	phases = t_bracket['phases']
	groups = t_bracket['groups']
	entrants = {}
	wins = {}
	losses = {}
	paths = {}
	bracket = {}
	names = {}
	sets = {}
	end_buff = False

	if load_res and v >= 3:
		print('Loading cached files...')

	for group in groups:
		pstart = timer()
		load_succ = False
		if load_res and not end_buff:
			try:
				if v >= lv:
					print('Loading %d...'%group.id)
				entrants,wins,losses,paths,names,sets = load_all(t_id,group.id)
				load_succ = True
			except FileNotFoundError:
				if v >= lv:
					print('Phase group %d not found locally'%group.id)
				end_buff = True
				load_succ = False

		if not load_succ:
			phase_id = group.phase['id']
			group_phase = [phase for phase in phases if phase.id == phase_id][0]
			is_exhibition = group_phase.is_exhibition
			phasename = group_phase.name
			groupname = group.display_identifier

			if translate_cjk:
				if has_cjk(groupname):
					groupname = '<'+transliterate(groupname)+'>'
			groupstate = int(group.state)
			grouptype = group.bracket_type

			# don't want exhibition brackets
			if not is_exhibition:
				# round 2 of filtering out amateur brackets
				if not(is_amateur(groupname) or (is_arcadian(groupname) and not count_arcadians)):
					# catch still-in-progress or not-yet updated brackets
					if groupstate is None or groupstate < 3:
						if v >= 4 :
							if groupstate == None:
								errstr = 'no group state!'
							if groupstate == 2:
								errstr = 'it is still in progress!'
							elif groupstate == 1:
								errstr = 'it hasn\'t started yet!'
							else:
								errstr = 'it doesn\'t exist yet!'

							print('ERROR: Could not read in group %s | %s | %d because %s'%(phasename,groupname,group,errstr))
					# use groupTypeId to check for bracket structure 
					# (1: single elim, 2: double elim, 3: round-robin, 4: swiss, 5: exhibition, 6: custom schedule, 7: ladder/matchmaking, 8: elimination rounds, 9: race)
					else:	
						if grouptype not in ['SINGLE_ELIMINATION','DOUBLE_ELIMINATION','ROUND_ROBIN','SWISS']:
							if v >= 5:
								errstr = '%d is an unsupported group format'%grouptype
								print('ERROR: Could not read in group %s | %s | %d because %s'%(phasename,groupname,group,errstr))
						else:
							read_entrants(group,group_phase,entrants,names,paths)
							read_sets(group,group_phase,t_id,wins,losses,paths,sets,entrants)

						if save_res:
							if v >= lv:
								print('Saving %d...'%group)
							save_all(t_id,group,[entrants,wins,losses,paths,names,sets])

					if v >= 4:
						print('{:.0f}'.format(1000*(timer()-pstart)) + ' ms')
				else:
					if v >= 6:
						print('Ignoring %s | %s | %d: is Amateur/Arcadian'%(phasename,groupname,group))
			else:
				if v >= 6:
					print('Ignoring %s | %s | %d: isExhibition'%(phasename,groupname,group))
		# sort paths according to proper bracket structure
		#for e_id in paths:

	return entrants,wins,losses,paths,names,sets

# reads in and returns data for all entrants in a given phase group
def read_entrants(group,group_phase,entrants,names,xpath):
	group_id = group.id
	phase_id = group_phase.id

	phasename = group_phase.name
	groupname = group.display_identifier
	num_groups = group_phase.group_count
	phaseorder = group_phase.phase_order

	# if not an exhibition wave
	if not group_phase.is_exhibition:
		if 'groups' not in names:
			names['groups'] = {}
		if str(groupname) == "1" and num_groups <= 1:
			names['groups'][group_id] = phasename
		elif num_groups == 1:
			names['groups'][group_id] = phasename
		else:
			names['groups'][group_id] = groupname
		if v >= 4:
			print('Reading: %s | %s | %d'%(phasename,groupname,group_id)) 

		entrant_data = group.get_entrants()

		for entrant in entrant_data:
			e_id,attendees,users,prefix,metainfo,team_name = read_user(entrant)
			tag = [attendee.gamer_tag for attendee in attendees]
			#print(e_id,'|',abs_id,'|',tag,'|',prefix,'|',metainfo,'|',team_name)
			#if type(abs_id) is list:
			names[e_id] = (prefix,tag,team_name)
			#else:
			#	names[e_id] = [(pr,tg) for pr,tg in zip(prefix,tag)]

			# store bracket placing/results
			res = entrant.placement
			if v >= 8:
				print(e_id,tag)
			if v >= 9 and e_id in xpath:
				print(xpath[e_id])

			if e_id in xpath:
				if v >= 9:
					print(xpath[e_id]['path'])
				xpath[e_id]['placing'] = res
				xpath[e_id]['path'].extend([group_id])
			else:
				xpath[e_id] = {'placing':res, 'path':[group_id], 'seed':entrant.seed_num}

			# store player image metadata
			propic = None
			
			if len(users) >= 1 and users[0] is not None:
				player_images = users[0].images
				propic = None
				if player_images and len(player_images) >= 0:
					for p_image in player_images:
						if p_image['type'] == 'profile':
							if p_image['height'] == 100:
								propic = p_image['url']
				else:
					propic = None
			else:
				propic = None

			if not all([user is None for user in users]):
				entrants[e_id] = (names[e_id],users,e_id,metainfo,propic)
	else:
		if v >= 5:
			print('Ignoring group: %s | %d. (Is Exhibition)'%(groupname,group_id))
	return entrants,names,xpath
		
# reads the sets for a given phase group and returns match results
def read_sets(group,group_phase,t_id,wins,losses,xpath,sets,entrants):
	setdata = group.get_sets()
	#setdata.reverse()
	group_id = group.id
	grp_count = group_phase.group_count
	if setdata != []:
		if group.progressions is not None:
			grp_num_prog = len(group.progressions)
		else:
			grp_num_prog = 0

	for match in setdata:
		if v >= 7:
			print('Reading', match)
		e1,e2 = match.entrant1,match.entrant2
		e1_id,e2_id = e1['id'],e2['id']
		w_id,l_id = match.winner_id,match.loser_id
		set_id = match.id
		is_bye = False
		get_loser_id = lambda x_id: e2_id if e1_id == x_id else e1_id
		get_game_loser_id = lambda x_id: e2_id if e1_id == x_id else e1_id
		'''
		if group.rounds:
			num_rounds = len(group.rounds)
			is_GF = match.round >= num_rounds-1
		else:
			num_rounds = None
			is_GF = False
		print(is_GF)
		print(match.round)
		print(num_rounds)
		print(group.rounds)
		print(group.progressions)
		print(group_phase.phase_order)
		'''
		is_GF = match.winner_placement == 1

		# Filter out DQs
		is_DQ = lambda e: e['score'] == -1 if not e['score'] == None else False
		e1_DQ,e2_DQ = is_DQ(e1),is_DQ(e2)
		if w_id == e1_id and l_id == e2_id:
			w_DQ = e1_DQ
			l_DQ = e2_DQ
		elif w_id == e2_id and l_id == e1_id:
			w_DQ = e2_DQ
			l_DQ = e1_DQ
		else:
			w_DQ,l_DQ = False,False

		# Move past byes
		if w_id == None or l_id == None or w_id == l_id:
			is_bye = True

		sets[set_id] = {}
		sets[set_id]['is_bye'] = is_bye
		sets[set_id]['w_id'] = w_id
		sets[set_id]['l_id'] = l_id
		sets[set_id]['w_dq'] = w_DQ
		sets[set_id]['l_dq'] = l_DQ
		sets[set_id]['t_id'] = t_id
		sets[set_id]['w_placement'] = match.winner_placement
		sets[set_id]['l_placement'] = match.loser_placement
		sets[set_id]['is_winners'] = match.round >= 0
		sets[set_id]['round_num'] = match.round
		sets[set_id]['round_text_long'] = match.full_round_text
		sets[set_id]['has_placeholder'] = match.has_placeholder
		if match.set_games_type >= 1:
			sets[set_id]['total_games'] = match.total_games
			sets[set_id]['best_of'] = -1
		else:
			sets[set_id]['total_games'] = len(match.games)
			sets[set_id]['best_of'] = group.rounds[np.where(group.rounds['number'] == match.round)]['bestOf']
		if v >= 8:
			print(sets[set_id])


		if not is_bye:
			# populate character data if available
			if match.games is not None and len(match.games) > 0:
				if len(match.games) > 0:
					sets[set_id]['games'] = {}
				for game in sorted(match.games,key=lambda g: g['orderNum']):
					game_id = game['id']
					sets[set_id]['games'][game_id] = {}
					if game['stage'] != None:
						sets[set_id]['games'][game_id]['stage_id'] = game['stage']['id']
					sets[set_id]['games'][game_id]['w_id'] = game['winnerId']
					sets[set_id]['games'][game_id]['l_id'] = get_game_loser_id(game['winnerId'])

					# if there are selections made
					if 'selections' in game and type(game['selections']) is not type(None):
						# and both entrants have selections
						if len(game['selections']) >= 2 and all([game_e_id in [g_sel['id'] for g_sel in game['selections']] for game_e_id in [e1_id,e2_id]]):
							sets[set_id]['games'][game_id]['characters'] = {}
							# store character selection for each entrant
							for selection in game['selections']:
								if 'CHARACTER' == selection['selectionType']:
									game_char_id = selection['selectionValue']
									sets[set_id]['games'][game_id]['characters'][game_e_id] = game_char_id
									'''
									if game_e_id not in characters:
										characters[game_e_id] = {}
									if game_char_id not in characters[game_e_id]:
										characters[game_e_id][game_char_id] = [0,0]
									# store wins and losses separately
									if game_e_id == w_id:
										characters[game_e_id][game_char_id][0] += 1
									else:
										characters[game_e_id][game_char_id][1] += 1'''

			# Don't count DQs for win/loss records (still do for placings)
			if not (w_DQ or l_DQ):
				if v >= 7:
					print(set_id,group_id,match.identifier,[w_id,l_id],[e1_id,e2_id])
				if w_id not in wins:
					wins[w_id] = [(l_id,[set_id,group_id])]
				else:
					wins[w_id].extend([(l_id,[set_id,group_id])])
				if l_id not in losses:
					losses[l_id] = [(w_id,[set_id,group_id])]
				else:
					losses[l_id].extend([(w_id,[set_id,group_id])])
			else:
				if v >= 7:
					print(set_id,group_id,match.identifier,[w_id,'DQ'],[e1_id,e2_id])

			# update final placement if it is further than their current one (people can't regress in bracket except for in GF)
			## update: isGF currently deprecated
			if not match.winner_placement == None:
				if type(xpath[w_id]['placing']) is list:
					xpath[w_id]['placing'] = match.winner_placement
				elif match.winner_placement < xpath[w_id]['placing'] or is_GF:
					xpath[w_id]['placing'] = match.winner_placement
			elif not match.winner_placement == None:
				if type(xpath[w_id]['placing']) is list:
					xpath[w_id]['placing'] = match.winner_placement
				elif match.winner_placement < xpath[w_id]['placing'] or is_GF:
					xpath[w_id]['placing'] = match.winner_placement
			else:
				if v >= 7:
					print('Error: Could not update winner placement (%d)'%w_id)

			if not match.loser_placement == None:
				if type(xpath[l_id]['placing']) is list:
					xpath[l_id]['placing'] = match.loser_placement
				elif match.loser_placement < xpath[l_id]['placing'] or is_GF:
					xpath[l_id]['placing'] = match.loser_placement
			elif not match.loser_placement == None:
				if type(xpath[l_id]['placing']) is list:
					xpath[l_id]['placing'] = match.loser_placement
				elif match.loser_placement < xpath[l_id]['placing'] or is_GF:
					xpath[l_id]['placing'] = match.loser_placement
			else:
				if v >= 7:
					print('Error: Could not update loser placement (%d)'%l_id)
		else:
			if v >= 7:
				print(set_id,group_id,match.identifier,['bye','bye'],[e1_id,e2_id])

	# populate overall final bracket placements if not already provided
	for e_id in sorted([e_x for e_x in entrants if type(xpath[e_x]['placing']) is list],key=lambda p_id: xpath[p_id]['placing'][0]):
		if type(xpath[e_id]['placing']) is list:
			pool_place = xpath[e_id]['placing'][0]

			spots_missed = max((pool_place-grp_num_prog)-1,0)
			people_missed = grp_num_prog*grp_count

			final_place = 1 + people_missed + spots_missed*grp_count
			xpath[e_id]['placing'] = final_place

	return wins,losses,xpath,sets

# returns sponsor, gamertag, and user meta info for a given entrant	
def read_user(entrant,translate_cjk=False):
	entrant_id = entrant.id
	attendees = entrant.attendee_data
	users = [SR_User.parse(attendee.user) for attendee in attendees]

	if translate_cjk:
		for user in users:
			if user is not None and any([is_cjk(tag_c) for tag_c in user.player['gamerTag']]):
				#'『' '』'
				user.player['gamerTag'] = '<'+transliterate(user.player['gamerTag'])+'>'

	prefixes = [user.player['prefix'] if user is not None else None for user in users]
	if len(attendees) > 1:
		team_name = entrant.name
	else:
		team_name = None

	cont_infos = [attendee.contact_info for attendee in attendees]
	metainfo = [[0,0,0,0,0,0]]
	for cont_info in cont_infos:
		if cont_info:
			if 'nameFirst' in cont_info:
				f_name = cont_info['nameFirst']
			else:
				f_name = None
			if 'nameLast' in cont_info:
				l_name = cont_info['nameLast']
			else:
				l_name = None
			if 'state' in cont_info:
				state = cont_info['state']
			else:
				state = None
			if 'country' in cont_info:
				country = cont_info['country']
			else:
				country = None
			if 'city' in cont_info:
				city = cont_info['city']
			else:
				city = None
			if 'region' in cont_info:
				declared_region = cont_info['region']
			else:
				declared_region = None
			metainfo.extend([[f_name,l_name,state,country,city,declared_region]])
		else:
			metainfo.extend([None,None,None,None,None,None])
	metainfo = metainfo[1:]

	if team_name != None:
		return entrant_id,attendees,users,prefixes,metainfo,team_name
	return entrant_id,attendees,users,prefixes,metainfo,None

if __name__ == '__main__':
	try:
		#readin('smash-summit-8')
		readin('genesis-5')
	except Exception as e:
		logging.error(traceback.format_exc())
	QueryQueueDaemon.kill_daemon()