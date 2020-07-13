## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError
import requests
#import numpy as np 
#import scipy as sp 
import json
import re
import argparse
from timeit import default_timer as timer
import os,pickle,time,datetime
## UTIL IMPORTS
from arg_utils import *
from readin_utils import *

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

	if v >= 2 and v < 4:
		start = timer()

	out = read_phases(slug)

	if out:
		t,gs,pdata,gdata = out
		t_id,t_name,t_slug,t_ss,t_type,t_date,t_sdate,t_region,t_images,t_coords,t_bracket,t_social = t
		es,ws,ls,rs,ns,ms = read_groups(t_id,gs,pdata)

		if v >= 2 and v < 4:
			print('{:.3f}'.format(timer()-start) + ' s')

		t = (t_id,t_name,t_slug,t_ss,t_type,t_date,t_sdate,t_region,len(es.keys()),t_images,t_coords,t_bracket,t_social)
		if print_res:
			print_results(rs,ns,es,ls,ms,game=game,max_place=disp_num)
		return t,es,ns,rs,ws,ls,ms
	else:
		return False

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
	current_db = r_args.current_db

# reads the match data for a given phase
def read_groups(t_id,groups,phase_data,translate_cjk=True):
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
					print('Loading %d...'%group)
				entrants,wins,losses,paths,names,sets = load_all(t_id,group)
				load_succ = True
			except FileNotFoundError:
				if v >= lv:
					print('Phase group %d not found locally'%group)
				end_buff = True
				load_succ = False

		if not load_succ:

			try:
				data = json.loads(pull_phase(group))
			except HTTPError:
				time.sleep(3)
				data = json.loads(pull_phase(group))

			wave_id = data['entities']['groups']['phaseId']
			is_exhibition = phase_data[wave_id]['isExhibition']
			phasename = phase_data[wave_id]['name']
			groupname = data['entities']['groups']['displayIdentifier']
			if translate_cjk:
				if has_cjk(groupname):
					groupname = '<'+transliterate(groupname)+'>'
			if 'state' in data['entities']['groups']:
				groupstate = int(data['entities']['groups']['state'])
			else:
				groupstate = None
			grouptype = int(data['entities']['groups']['groupTypeId'])

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
						if grouptype not in [1,2,3,4]:
							if v >= 5:
								errstr = '%d is an unsupported group format'%grouptype
								print('ERROR: Could not read in group %s | %s | %d because %s'%(phasename,groupname,group,errstr))
						else:
							read_entrants(data,phase_data,entrants,names,paths)
							read_sets(data,phase_data,wins,losses,paths,sets)

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
def read_entrants(data,phase_data,entrants,names,xpath):
	group = data['entities']['groups']['id']
	wave_id = data['entities']['groups']['phaseId']

	phasename = phase_data[wave_id]['name']
	groupname = data['entities']['groups']['displayIdentifier']
	num_groups = phase_data[wave_id]['groupCount']
	phaseorder = phase_data[wave_id]['phaseOrder']

	# if not an exhibition wave
	if not phase_data[wave_id]['isExhibition']:
		if 'groups' not in names:
			names['groups'] = {}
		if str(groupname) == "1" and num_groups <= 1:
			names['groups'][group] = phasename
		elif num_groups == 1:
			names['groups'][group] = phasename
		else:
			names['groups'][group] = groupname
		if v >= 4:
			print('Reading: %s | %s | %d'%(phasename,groupname,group)) 
		seedata = data['entities']['seeds']

		for x in seedata:
			e_id,abs_id,tag,prefix,metainfo,team_name = read_names(x)
			#print(e_id,'|',abs_id,'|',tag,'|',prefix,'|',metainfo,'|',team_name)
			#if type(abs_id) is list:
			names[e_id] = (prefix,tag,team_name)
			#else:
			#	names[e_id] = [(pr,tg) for pr,tg in zip(prefix,tag)]

			# store bracket placing/results
			res = [x['placement']]
			if v >= 8:
				print(e_id,tag)
			if v >= 9 and e_id in xpath:
				print(xpath[e_id])

			if e_id in xpath:
				if v >= 9:
					print(xpath[e_id]['path'])
				xpath[e_id]['placing'] = res
				xpath[e_id]['path'].extend([group])
			else:
				xpath[e_id] = {'placing':res, 'path':[group], 'seed':x['seedNum']}

			# store player image metadata
			if len(abs_id) >= 1:
				player_images = x['mutations']['players'][str(abs_id[0])]['images']
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

			entrants[e_id] = (names[e_id],abs_id,e_id,metainfo,propic)
	else:
		if v >= 5:
			print('Ignoring group: %s | %d. (Is Exhibition)'%(groupname,group))
	return entrants,names,xpath
		
# returns sponsor, gamertag, and player meta info for a given entrant	
def read_names(x,translate_cjk=False):
	e_id = x['entrantId']
	part_ids = x['mutations']['entrants'][str(e_id)]['participantIds']
	abs_ids = [x['mutations']['entrants'][str(e_id)]['playerIds'][str(part_id)] for part_id in part_ids]
	tags = [x['mutations']['participants'][str(part_id)]['gamerTag'] for part_id in part_ids]

	if translate_cjk:
		#tags = ['『'+translate(tag)+'』' for tag in tags if any([is_cjk(tag_c) for tag_c in tag])]
		#tags = ['<'+translate(tag,to='ja').pronunciation+'>' if any([is_cjk(tag_c) for tag_c in tag]) else tag for tag in tags]
		tags = ['<'+transliterate(tag)+'>' if any([is_cjk(tag_c) for tag_c in tag]) else tag for tag in tags]

	prefixes = [x['mutations']['participants'][str(part_id)]['prefix'] for part_id in part_ids]
	if len(part_ids) > 1:
		team_name = x['mutations']['entrants'][str(e_id)]['name']
	else:
		team_name = None

	continfos = [x['mutations']['participants'][str(part_id)]['contactInfo'] for part_id in part_ids]
	metainfo = [[0,0,0,0,0,0]]
	for continfo in continfos:
		if 'nameFirst' in continfo:
			f_name = continfo['nameFirst']
		else:
			f_name = None
		if 'nameLast' in continfo:
			l_name = continfo['nameLast']
		else:
			l_name = None
		if 'state' in continfo:
			state = continfo['state']
		else:
			state = None
		if 'country' in continfo:
			country = continfo['country']
		else:
			country = None
		if 'city' in continfo:
			city = continfo['city']
		else:
			city = None
		if 'region' in continfo:
			declared_region = continfo['region']
		else:
			declared_region = None
		metainfo.extend([[f_name,l_name,state,country,city,declared_region]])
	metainfo = metainfo[1:]

	#if len(part_ids) == 1:
	#	return e_id,abs_ids[0],tags[0],prefixes[0],metainfo[0]
	if team_name != None:
		return e_id,abs_ids,tags,prefixes,metainfo,team_name
	return e_id,abs_ids,tags,prefixes,metainfo,None

# reads the sets for a given phase group and returns match results
def read_sets(data,phase_data,wins,losses,xpath,sets):
	setdata = data['entities']['sets']
	group = data['entities']['groups']['id']
	#print(phase_data)
	#print(group)
	wave_data = phase_data[data['entities']['groups']['phaseId']]
	grp_count = wave_data['groupCount']
	if setdata != []:
		grp_num_prog = data['entities']['groups']['numProgressing']

	for match in setdata:
		e1,e2 = match['entrant1Id'],match['entrant2Id']
		w_id,l_id = match['winnerId'],match['loserId']
		set_id = match['id']
		is_bye = False

		# Filter out DQs
		is_DQ = lambda n: match['entrant%dScore'%n] == -1 if not match['entrant%dScore'%n] == None else False
		e1_DQ,e2_DQ = is_DQ(1),is_DQ(2)
		if w_id == e1 and l_id == e2:
			w_DQ = e1_DQ
			l_DQ = e2_DQ
		elif w_id == e2 and l_id == e1:
			w_DQ = e2_DQ
			l_DQ = e1_DQ
		else:
			w_DQ,l_DQ = False,False
		#print(e1_DQ,e2_DQ,match['entrant1Score'],match['entrant2Score'])

		# Move past byes
		if w_id == None or l_id == None or w_id == l_id:
			is_bye = True

		sets[set_id] = {}
		sets[set_id]['is_bye'] = is_bye
		sets[set_id]['w_id'] = w_id
		sets[set_id]['l_id'] = l_id
		sets[set_id]['w_dq'] = w_DQ
		sets[set_id]['l_dq'] = l_DQ
		sets[set_id]['t_id'] = wave_data['tourney']
		sets[set_id]['w_placement'] = match['wOverallPlacement']
		sets[set_id]['l_placement'] = match['lOverallPlacement']
		sets[set_id]['is_winners'] = match['round'] > 0
		sets[set_id]['round_num'] = match['round']
		sets[set_id]['round_text_long'] = match['fullRoundText']
		sets[set_id]['round_text_med'] = match['midRoundText']
		sets[set_id]['round_text_short'] = match['shortRoundText']
		# not sure which one of these matters
		sets[set_id]['bestOf'] = match['bestOf']
		#sets[set_id]['bestOf'] = match['totalGames']
		#sets[set_id]['games'] = None
		if v >= 8:
			print(sets[set_id])

		if not is_bye:
			# populate character data if available
			if 'games' in match:
				if len(match['games']) > 0:
					sets[set_id]['games'] = {}
				for game in match['games']:
					#print(game['selections'])
					#if 'stageId' in game:
					#	stage = game['stageId']
					game_id = game['id']
					sets[set_id]['games'][game_id] = {}
					if game['stageId'] != None:
						sets[set_id]['games'][game_id]['stage_id'] = game['stageId']
					sets[set_id]['games'][game_id]['w_id'] = game['winnerId']
					sets[set_id]['games'][game_id]['l_id'] = game['loserId']

					# if there are selections made
					if 'selections' in game and type(game['selections']) is not type(None):
						# and both entrants have selections
						if all([str(game_e_id) in game['selections'] for game_e_id in [e1,e2]]):
							sets[set_id]['games'][game_id]['characters'] = {}
							# store character selection for each entrant
							for game_e_id in [e1,e2]:
								if 'character' in game['selections'][str(game_e_id)]:
									game_char_id = game['selections'][str(game_e_id)]['character'][0]['selectionValue']
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
					print(set_id,match['phaseGroupId'],match['identifier'],[w_id,l_id],[e1,e2])
				if w_id not in wins:
					wins[w_id] = [(l_id,[set_id,group])]
				else:
					wins[w_id].extend([(l_id,[set_id,group])])
				if l_id not in losses:
					losses[l_id] = [(w_id,[set_id,group])]
				else:
					losses[l_id].extend([(w_id,[set_id,group])])
			else:
				if v >= 7:
					print(set_id,match['phaseGroupId'],match['identifier'],[w_id,'DQ'],[e1,e2])

			# update final placement if it is further than their current one (people can't regress in bracket except for in GF)
			if not match['wOverallPlacement'] == None:
				if type(xpath[w_id]['placing']) is list:
					xpath[w_id]['placing'] = match['wOverallPlacement']
				elif match['wOverallPlacement'] < xpath[w_id]['placing'] or match['isGF']:
					xpath[w_id]['placing'] = match['wOverallPlacement']
			elif not match['wPlacement'] == None:
				if type(xpath[w_id]['placing']) is list:
					xpath[w_id]['placing'] = match['wPlacement']
				elif match['wPlacement'] < xpath[w_id]['placing'] or match['isGF']:
					xpath[w_id]['placing'] = match['wPlacement']
			else:
				if v >= 7:
					print('Error: Could not update winner placement (%d)'%w_id)

			if not match['lOverallPlacement'] == None:
				if type(xpath[l_id]['placing']) is list:
					xpath[l_id]['placing'] = match['lOverallPlacement']
				elif match['lOverallPlacement'] < xpath[l_id]['placing'] or match['isGF']:
					xpath[l_id]['placing'] = match['lOverallPlacement']
			elif not match['lPlacement'] == None:
				if type(xpath[l_id]['placing']) is list:
					xpath[l_id]['placing'] = match['lPlacement']
				elif match['lPlacement'] < xpath[l_id]['placing'] or match['isGF']:
					xpath[l_id]['placing'] = match['lPlacement']
			else:
				if v >= 7:
					print('Error: Could not update loser placement (%d)'%l_id)
		else:
			if v >= 7:
				print(set_id,match['phaseGroupId'],match['identifier'],['bye','bye'],[e1,e2])

	# populate overall final bracket placements if not already provided
	for x_id in sorted([x['entrantId'] for x in data['entities']['seeds'] if type(xpath[x['entrantId']]['placing']) is list],key=lambda p_id: xpath[p_id]['placing'][0]):
		if type(xpath[x_id]['placing']) is list:
			pool_place = xpath[x_id]['placing'][0]

			spots_missed = max((pool_place-grp_num_prog)-1,0)
			people_missed = grp_num_prog*grp_count

			final_place = 1 + people_missed + spots_missed*grp_count
			xpath[x_id]['placing'] = final_place

	return wins,losses,xpath,sets

# reads the phase data for a given tournament
def read_phases(slug):
	gamemap = {1: ['melee','ssbm','ssbmelee'], 2: ['P:M','project: m','project melee','project m'], 3: ['ssb4','smash 4','ssb wii u','smash wii u','for wii u'], \
				4: ['smash 64','ssb64','64'], 5: ['brawl','ssbb'], 1386: ['ssbu','ultimate','for switch','nintendo switch','switch'], 24: ['roa','rivals','of aether']}
	waves = {}
	#with open(filepath) as f:
	#	data = json.loads(f.read())

	phaselink ='https://api.smash.gg/tournament/%s?expand[]=event&expand[]=groups&expand[]=phase'%slug
	try:
		tfile = urlopen(phaselink).read()
		tdata = json.loads(tfile.decode('UTF-8'))

		t_id = tdata['entities']['tournament']['id']
		t_name = tdata['entities']['tournament']['name']
		t_ss = tdata['entities']['tournament']['shortSlug']
		t_slug = tdata['entities']['tournament']['slug'].split('/')[1]
		t_type = tdata['entities']['tournament']['tournamentType']
		# date tuple in (year, month, day) format
		t_date = time.localtime(tdata['entities']['tournament']['endAt'])[:3]
		t_startdate = time.localtime(tdata['entities']['tournament']['startAt'])[:3]
		t_region = (tdata['entities']['tournament']['addrState'],tdata['entities']['tournament']['countryCode'])
		# 2-length list with the urls for the first profile image and banner images found (for the tourney)
		t_propic = [img['url'] for img in tdata['entities']['tournament']['images'] if img['type'] == 'profile']
		t_coords = [tdata['entities']['tournament']['lat'],tdata['entities']['tournament']['lng']]
		# social media/contact info
		t_email = tdata['entities']['tournament']['contactEmail']
		t_twitter = tdata['entities']['tournament']['contactTwitter']
		t_hashtag = tdata['entities']['tournament']['hashtag']
		t_social = (t_email,t_twitter,t_hashtag)

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
		event_ids = [[event['id'],(event['name'],event['description'])] for event in tdata['entities']['event'] if event['videogameId'] == game] #and min(event['entrantSizeMin'],4) == min(teamsize,4)]
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
			print('event_ids pre filtering: ' + str([(event_id[0],event_id[1][0]) for event_id in event_ids]))

		# returns true if an event is all exhibiton phases (not partially, to allow for brackets that feed into amateur/redemption brackets etc)
		is_exhibition = lambda ev_id: all([phase['isExhibition'] for phase in tdata['entities']['phase'] if phase['eventId'] == ev_id])
		# filters out events that don't list the given game in description, to filter out stuff like low tiers/ironmans/crews etc
		game_events = [event_id[0] for event_id in event_ids if has_game(event_id[1][0],game) or has_game(event_id[1][1],game)]
		exhibition_events = [event_id[0] for event_id in event_ids if is_exhibition(event_id)]
		'''for event_id in event_ids:
			print(event_id[0],event_id[1][0],is_exhibition(event_id[0]))'''
		if teamsize > 1:
			team_events = [event_id[0] for event_id in event_ids if is_teams(event_id[1][0],teamsize) or is_teams(event_id[1][1],teamsize)]
		if teamsize <= 1:
			team_events = [event_id[0] for event_id in event_ids if is_teams(event_id[1][0],2) or is_teams(event_id[1][1],2)]
		amateur_events = [event_id[0] for event_id in event_ids if is_amateur(event_id[1][0]) or is_amateur(event_id[1][1])]
		ladder_events = [event_id[0] for event_id in event_ids if is_ladder(event_id[1][0]) or is_ladder(event_id[1][1])]
		if only_arcadians or not count_arcadians:
			arcadian_events = [event_id[0] for event_id in event_ids if is_arcadian(event_id[1][0]) or is_arcadian(event_id[1][1])]
		if len(game_events) >= 1:
			event_ids = game_events
		else:
			event_ids = [event_id[0] for event_id in event_ids]
		# filters out events that have 'amateur', 'ladder' or 'arcadian' in the description
		#event_ids = game_events
		#event_ids = [event_id for event_id in event_ids if not event_id in exhibition_events]
		event_ids = [event_id for event_id in event_ids if not event_id in amateur_events]
		event_ids = [event_id for event_id in event_ids if not event_id in ladder_events]
		if teamsize > 1:
			event_ids = [event_id for event_id in event_ids if event_id in team_events]
		else:
			event_ids = [event_id for event_id in event_ids if not event_id in team_events]
		if not count_arcadians:
			event_ids = [event_id for event_id in event_ids if not event_id in arcadian_events]
		elif only_arcadians:
			event_ids = arcadian_events

		if v >= 6:
			print('event_ids post filtering: ' + str(len(event_ids)))
		if len(event_ids) <= 0 and v >= 1:
			print('** No suitable events found of form: %s %s [%s] at this tournament'%(gamemap[game][0], team_string, pro_string))

		if force_first_event:
			#event_ids = sorted(event_ids,key=lambda i: tdata['entities']['event'][i]['numEntrants'])
			event_ids = sorted(event_ids)
			#print(event_ids[0])
			event_ids = event_ids[:1]

		# get all phases (waves) for each event (ideally filtered down to 1 by now)
		phase_ids = [phase['id'] for phase in tdata['entities']['phase'] if phase['eventId'] in event_ids]
		# get all groups (pools) for each phase
		group_ids = [(group['id'],group['phaseId']) for group in tdata['entities']['groups'] if group['phaseId'] in phase_ids]
		groups = {group['id']:{keystr:group[keystr] if keystr in group else None \
					for keystr in ['id','phaseId','groupTypeId','numRounds','numProgressing','identifier','displayIdentifier','state','winnersTargetPhaseId','losersTargetPhaseId']} \
					for group in tdata['entities']['groups'] if group['phaseId'] in phase_ids}

		for w in tdata['entities']['phase']:
			if w['id'] not in waves:
				waves[w['id']] = {'id':w['id'], 'name': w['name'], 'groupCount':w['groupCount'], 'phaseOrder':w['phaseOrder'],\
								  'eventId':w['eventId'], 'typeId':w['typeId'], 'isExhibition':w['isExhibition'], 'tourney':t_id}
		# sort groups to be read in proper bracket structure order		
		group_ids = sorted(group_ids,key=lambda l: waves[l[1]]['phaseOrder'])
		group_ids = [group_id[0] for group_id in group_ids]
		#print(t_id)
		if v >= 6:
			tdata_dict = {'events':{event_data['id']:event_data for event_data in tdata['entities']['event'] if event_data['id'] in event_ids},\
						'phases':{phase_data['id']:phase_data for phase_data in tdata['entities']['phase'] if phase_data['id'] in phase_ids},\
						'groups':{group_data['id']:group_data for group_data in tdata['entities']['groups'] if group_data['id'] in group_ids}}
			print('Events')
			for event_id in event_ids:
				print('\t',event_id,'|',tdata_dict['events'][event_id]['name'])
			print('Phases')
			for phase_id in phase_ids:
				phase_event_id = tdata_dict['phases'][phase_id]['eventId']
				print('\t',phase_id,'|',tdata_dict['phases'][phase_id]['name'],'(',tdata_dict['events'][phase_event_id]['name'],')')
			print('Groups')
			for group_id in group_ids:
				group_phase_id = tdata_dict['groups'][group_id]['phaseId']
				group_event_id = tdata_dict['phases'][group_phase_id]['eventId']
				print('\t',group_id,'|',tdata_dict['groups'][group_id]['displayIdentifier'],'(',tdata_dict['events'][group_event_id]['name'],'>',tdata_dict['phases'][group_phase_id]['name'],')')
		t_bracket = {'events':event_ids, 'phases':waves, 'groups':groups}
		
		t_info = (t_id,t_name,t_slug,t_ss,t_type,t_date,t_startdate,t_region,t_images,t_coords,t_bracket,t_social)
		return (t_info,group_ids,waves,groups)

	except HTTPError:
		print('Error 404: tourney [%s] not found'%slug)
		return False
		

if __name__ == '__main__':
	#print(save_character_dicts(to_load=False))
	#print(save_videogame_dicts())

	readin(t_slug_a)
	#print(translate(translate("Zackray",to='ja').text,to='ja').pronunciation)
	#readin('summit7',type='ss')
	#print(get_slug('tbh8'))

	#read_sets("sets.txt")
	#pull_phase(764818)

	#clean_data("./old/glitch6phasesraw.txt","./old/glitch6phasesclean.txt")
	#clean_data("./old/genesis6top64setsraw.txt","./old/genesis6top64setsclean.txt")
	#clean_data("./old/paxarenaraw.txt","./old/paxarenaclean.txt")
	#clean_data("./old/crewsraw.txt","./old/crewsclean.txt")
	#clean_data("cextop8raw.txt","cextop8clean.txt")
	#clean_data("valhallasetsraw.txt","valhallasetsclean.txt")