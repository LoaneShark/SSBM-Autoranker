## DEPENDENCY IMPORTS
import numpy as np
import matplotlib.pyplot as plt 
import os,sys,pickle,time,math
import re
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError
from timeit import default_timer as timer
from copy import deepcopy as dcopy
## UTIL IMPORTS
from arg_utils import *
from readin_utils import *
from region_utils import *
from scraper import scrape_ranks,check_ssbwiki,get_rank_name

flatten = lambda l: [item for sublist in l for item in sublist] if type(l) is list else []

args = get_args()

# return the (filtered) result(s) for a tourney
# format is a list of players sorted by final placement, with indexing:
# (p_id,p_team,p_tag,p_path,p_place,p_losses,p_wins)
def get_result(dicts,t_id,res_filt=None):
	tourneys,ids,p_info,records,skills,meta = dicts
	t = tourneys[t_id]
	t_labels = t['groups']

	# import all players from this event
	player_ids = [p_id for p_id in ids if (not type(p_id) is str and t_id in ids[p_id])]
	player_teams = [p_info[p_id]['team'] for p_id in player_ids]
	player_tags = [p_info[p_id]['tag'] for p_id in player_ids]
	player_paths = [records[p_id]['paths'][t_id] for p_id in player_ids]
	player_places = [records[p_id]['placings'][t_id]['placing'] for p_id in player_ids]
	player_losses = []
	player_wins = []
	player_skills = [[round(skills['elo'][p_id][t_id],3),round(skills['glicko'][p_id][t_id][0],3),round(skills['srank'][p_id][t_id]*100.,3)/100.] for p_id in player_ids]
	#player_skills = [[skills[key][p_id][t_id] for key in ['elo','glicko','sim']] for p_id in player_ids]
	player_chars = [sorted([p_char for p_char in p_info[p_id]['characters'] if sum(p_info[p_id]['characters'][p_char]) > 0],key=lambda c_id: sum(p_info[p_id]['characters'][c_id]),reverse=True)\
							 for p_id in player_ids]
	for p_id in player_ids:
		temp_l = []
		for l_id in records[p_id]['losses']:
			for i in range(len([set_id for set_id in records[p_id]['losses'][l_id][t_id] if t_id in records[p_id]['losses']])):
				temp_l.extend([l_id])
		temp_l.reverse()
		player_losses.extend([temp_l])
	for p_id in player_ids:
		temp_w = []
		for w_id in records[p_id]['wins']:
			for i in range(len([set_id for set_id in records[p_id]['wins'][w_id][t_id] if t_id in records[p_id]['wins']])):
				temp_w.extend([w_id])
		temp_w.reverse()
		player_wins.extend([temp_w])
	players = [player_ids,player_teams,player_tags,player_paths,player_places,player_losses,player_wins,player_skills,player_chars]
	#print(players)
	#print([len(attr) for attr in players])
	players = [[col[row] for col in players] for row in range(len(players[0]))]
	#print(len(players))

	if not res_filt == None:
		#print(res_filt['team'])
		for player in players.copy():
			p_id,p_team,p_tag,p_path,p_place,p_losses,p_wins,p_skills,p_chars = player
			if 'player' in res_filt:
				if not (p_id == res_filt['player'] and not (type(p_id) is str) and t_id in ids[p_id]):
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
				if not res_filt['loss_tag'] in flatten([[alias for alias in p_info[loss_id]['aliases']] for loss_id in p_losses]):
					players.remove(player)
					continue
			if 'win_id' in res_filt:
				if not res_filt['win_id'] in p_wins:
					players.remove(player)
					continue
			if 'win_tag' in res_filt:
				if not res_filt['win_tag'] in flatten([[alias for alias in p_info[win_id]['aliases']] for win_id in p_wins]):
					players.remove(player)
					continue
			if 'elo' in res_filt:
				if not res_filt['elo'] < p_skills[0]:
					players.remove(player)
					continue
			if 'glicko' in res_filt:
				if not res_filt['glicko'] < p_skills[1][0]:
					players.remove(player)
					continue
			if 'srank' in res_filt:
				if not res_filt['srank'] < p_skills[2]:
					players.remove(player)
					continue
			if 'character' in res_filt:
				if not res_filt['character'] in p_chars:
					players.remove(player)
					continue

	return players

# returns a copy of the database containing the dicts of info relating to a given player
# (filtered by event(s) if provided)
def get_player(dicts,p_id,tag=None,t_ids=None,slugs=None):
	tourneys,ids,p_info,records,skills,meta = dicts
	if not tag == None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if not slugs == None:
		t_ids = [meta['slugs'][slug] for slug in slugs]

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
			print('Error: Invalid form for t_ids in call to get_player(): %s'%type(t_ids))
			return False
	else:
		return p_id,p_info[p_id],records[p_id],ids[p_id],skills[p_id]

# return (filtered) results for a series of tourneys
def get_results(dicts,t_ids,res_filt=None):
	if type(t_ids) is str or type(t_ids) is None:
		if t_ids == 'all' or t_ids == None:
			t_ids = [t_id for t_id in tourneys if not t_id == 'slugs']
		elif t_ids == 'active':
			t_ids = [t_id for t_id in tourneys if not t_id == 'slugs' if tourneys[t_id]['active']]
		else:
			print('Error:: Invalid tournament id: %s'%t_ids)
	if type(t_ids) is list:
		return [[t_id,get_result(dicts,t_id,res_filt)] for t_id in t_ids]
	elif t_ids == None:
		return [[t_id,get_result(dicts,t_id,res_filt)] for t_id in tourneys if not t_id == 'slugs']
	else:
		return get_result(dicts,t_ids,res_filt)

# returns a list (in printing format) containing a player's final placing, bracket path, wins/losses, and metainfo
# for each tourney they attended (or only in those provided).
# can pull the results for a whole team as well
def get_resume(dicts,p_id,tags=None,t_ids=None,team=None,slugs=None,chars=None):
	tourneys,ids,p_info,records,skills,meta = dicts
	# recursion filtering
	if type(p_id) is list:
		return flatten([get_resume(dicts,pid,tags=tags,t_ids=t_ids,team=team,slugs=slugs,chars=chars) for pid in p_id])
	elif type(tags) is list:
		return flatten([get_resume(dicts,p_id,tags=tag,t_ids=t_ids,team=team,slugs=slugs,chars=chars) for tag in tags])
	elif type(team) is list:
		return flatten([get_resume(dicts,p_id,tags=tags,t_ids=t_ids,team=tm,slugs=slugs,chars=chars) for tm in team])
	elif type(chars) is list:
		return flatten([get_resume(dicts,p_id,tags=tags,t_ids=t_ids,team=team,slugs=slugs,chars=char) for char in chars])
	if tags == None:
		if type(p_id) is str:
			p_id = get_abs_id_from_tag(dicts,p_id)
		if not team == None:
			team_ids = get_players_from_team(dicts,team)
			return flatten([get_resume(dicts,team_id,tags=tags,t_ids=t_ids,slugs=slugs,chars=chars) for team_id in team_ids])
		if not chars == None:
			rep_ids = get_players_by_character(dicts,chars)
			return flatten([get_resume(dicts,rep_id,tags=tags,t_ids=t_ids,slugs=slugs,team=team) for rep_id in rep_ids])
	else:
		p_id = get_abs_id_from_tag(dicts,tags,first_only=False)
		if p_id == None:
			return []
		elif type(p_id) is list and len(p_id) == 1:
			p_id = p_id[0]
		elif type(p_id) is list:
			return flatten([get_resume(dicts,pid,tags=None,t_ids=t_ids,team=team,slugs=slugs,chars=chars) for pid in p_id])

	# break if player is not in database
	if p_id == None:
		return []

	#print(p_id)
	# tourney id filtering
	if t_ids == None:
		t_ids = []
	if type(slugs) is list:
		t_ids.extend([meta['slugs'][slug] for slug in slugs])
	#print(t_ids)
	if len(t_ids) > 0:
		res = [flatten([[t_id],get_result(dicts,t_id,res_filt={'player': p_id})]) for t_id in t_ids if not get_result(dicts,t_id,res_filt={'player': p_id}) == []]
	else:
		if p_id not in records:
			return []
		res = [flatten([[t_id],get_result(dicts,t_id,res_filt={'player': p_id})]) for t_id in ids[p_id] if not get_result(dicts,t_id,res_filt={'player': p_id}) == []]

		#t_losses = [records[p_id]['losses'][l_id] for l_id in records[p_id]['losses'] if t_id ]
		#t_res = (records[p_id]['placings'][t_id]['placing'],records[p_id]['paths'][t_id])
	return res

# returns player id given their tag in a string
# if multiple matches, returns first found result (by p_id or skill), unless first_only is disabled
def get_abs_id_from_tag(dicts,tag,first_only=True,sort_by_skill=False,leet_sensetive=True):
	tourneys,ids,p_info,records,skills,meta = dicts
	#print(tag)
	p_ids = [abs_id for abs_id in p_info if tag is not None if tag in p_info[abs_id]['aliases'] or \
											tag.lower().strip() in [p_alias.lower().strip() for p_alias in p_info[abs_id]['aliases'] if p_alias is not None]]

	if len(p_ids) <= 0 and not leet_sensetive:
		p_ids = [abs_id for abs_id in p_info if any([leet_tag.lower().strip() in [p_alias.lower().strip() for p_alias in p_info[abs_id]['aliases'] if p_alias is not None] for leet_tag in leetify(tag)])]
	if len(p_ids) > 0:
		if len(p_ids) > 1:
			if sort_by_skill:
				# sort by s-rank first, elo second
				#p_ids = sorted(p_ids,key=lambda p_id: (skills['srank'][p_id][p_info[p_id]['last_event']],skills['elo'][p_id][p_info[p_id]['last_event']]))
				p_ids = sorted(p_ids,key=lambda p_id: (p_info[p_id]['srank_last'],p_info[p_id]['elo']))
		if first_only:
			return p_ids[0]
		else:
			return p_ids
	else:
		return None
	#print(p_info[1000]['aliases'])

# returns an english tag either from cache or transliterated directly, given either p_id or japanese tag
def get_en_tag(dicts,tag=None,p_id=None):
	tourneys,ids,p_info,records,skills,meta = dicts

	# get p_id if not already provided
	if p_id == None:
		if tag == None:
			return None
		else:
			p_id = get_abs_id_from_tag(dicts,tag)
	# get tag if not already provided
	if tag == None:
		tag = p_info[p_id]['tag']

	# find transliterated aliases stored, or manually transliterate if not already provided
	if has_cjk(tag):
		if any([not(has_cjk(al)) for al in p_info[p_id]['aliases']]):
			for al in p_info[p_id]['aliases']:
				if not has_cjk(al):
					return al
		else:
			return transliterate(tag)
	else:
		return tag

# given a tag, returns all possible "leet" conversions of it, recursively
# e.g. Mango -> [Mango, Mang0, M4ngo, M4ng0, M@ngo, M@ng0]
# (this feature was added almost entirely because of mango/mang0)
def leetify(tag):
	res = set([])
	leetify_rec(tag,res,0)
	res.remove(None)
	return list(res)

# recursive subprocess for leetify
def leetify_rec(tag,convs,c_i):
	if c_i >= len(tag):
		return tag

	leet_chars = {'a':['4','@'],'e':['3'],'t':['7','+'],'i':['1','!'],'o':['0'],'s':['5','$'],'b':['8'],'l':['1'], \
				  '0':['o'],'1':['l','i'],'3':['e'],'4':['a'],'5':['s'],'7':['t'],'8':['b'],'!':['i'],'@':['4','a'],'$':['s','5']}
	
	tag_char = tag.lower()[c_i]
	if tag_char in leet_chars.keys():
		for alt_char in leet_chars[tag_char]:
			temp_tag = tag[:c_i] + alt_char + tag[c_i+1:]
			#temp_tag[c_i] = alt_char

			#convs.append(temp_tag)
			convs.add(leetify_rec(temp_tag,convs,c_i+1))
	convs.add(leetify_rec(tag,convs,c_i+1))

# returns a list of all player ids listed under this team
def get_players_from_team(dicts,team):
	tourneys,ids,p_info,records,skills,meta = dicts
	roster = [abs_id for abs_id in p_info if p_info[abs_id]['team'] == team]
	return roster

# returns a list of all player ids that have at least one recorded game with a given character
def get_players_by_character(dicts,character):
	tourneys,ids,p_info,records,skills,meta = dicts
	reps = [abs_id for abs_id in p_info if character in p_info['characters']]
	return reps

def get_character_usage_by_set(dicts,p_set,p_id,char_history={}):
	tourneys,ids,p_info,records,skills,meta = dicts
	if 'games' in p_set:
		chars_used = char_history
		if chars_used == None:
			chars_used = {}
		t_id = p_set['t_id']
		for game_id in p_set['games']:
			if 'characters' in p_set['games'][game_id]:

				g_w_id = p_set['games'][game_id]['w_id']
				g_l_id = p_set['games'][game_id]['l_id']

				if g_w_id is not None and ids['t_'+str(t_id)][g_w_id] == p_id:
					key_id = g_w_id
				elif g_l_id is not None and ids['t_'+str(t_id)][g_l_id] == p_id:
					key_id = g_l_id
				else:
					key_id = None

				if key_id is not None:
					if p_set['games'][game_id]['characters'] != {}:
						char_id = p_set['games'][game_id]['characters'][key_id]
						if char_id not in chars_used:
							chars_used[char_id] = 1
						else:
							chars_used[char_id] += 1

# lists all the tourneys in a given year/the entire dataset
def list_tourneys(dicts,year=None,list_ids=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	if year == None:
		if list_ids:
			return [[t_id,tourneys[t_id]['name']] for t_id in tourneys if t_id != 'slugs']
		else:
			return [tourneys[t_id]['name'] for t_id in tourneys if t_id != 'slugs']
	else:
		if list_ids:
			return [[t_id,tourneys[t_id]['name']] for t_id in tourneys if t_id != 'slugs' for t_date in tourney[t_id]['date'] if t_date[2] == year]
		else:
			return [tourneys[t_id]['name'] for t_id in tourneys if t_id != 'slugs' for t_date in tourney[t_id]['date'] if t_date[2] == year]

# gets the sets played by a player at a given tournament
def get_tournament_sets(dicts,p_id,t_id):
	tourneys,ids,p_info,records,skills,meta = dicts
	if t_id is not None:
		return [sets[set_id] for set_id in records[p_info][set_history] if sets[set_id]['t_id'] == t_id]

## db_utils helpers
# updates the main/official ranks for games (PGR, SSBMRank, etc.)
def update_official_ranks(dicts,game,year,year_half=1,lookback=False):
	tourneys,ids,p_info,records,skills,meta = dicts

	# get the url slug for this game's ranking // unique cache key
	rank_name_res = get_rank_name(game,year,year_half)
	if rank_name_res:
		rank_name,yearstr = rank_name_res
	else:
		return False
	if game == 3 or game == 2:
		rank_str = rank_name+yearstr
	else:
		rank_str = yearstr+rank_name

	# update the previous year if it wasn't already there (for first import)
	if lookback:
		update_official_ranks(dicts,game,year-1,lookback=False)
	# don't skip over winter-spring PGR
	if game == 3 and year_half == 1:
		update_official_ranks(dicts,game,year,year_half=0,lookback=False)
	# load cache if enabled
	if args.cache_mainranks:
		rank_cache = load_dict(rank_str,ver=get_db_verstr(),loc='db')
		if rank_cache:
			tags = rank_cache['tags']
			ratings = rank_cache['ratings']
			yearkey = rank_cache['yearkey']
			rank_list = rank_cache['p_list']
			scrape_res = (tags,ratings,yearkey)
		else:
			# scrape ranks if available
			scrape_res = scrape_ranks(game,year,rank_str,yearstr,year_half)
	else:
		# scrape ranks if available
		scrape_res = scrape_ranks(game,year,rank_str,yearstr,year_half)
	if not scrape_res:
		return False
	else:
		tags,ratings,yearkey = scrape_res
		if ratings is None:
			ratings = [None for i in range(len(tags))]

	if args.cache_mainranks and rank_cache:
		skills['mainrank_readin'][yearkey] = [[i+1,rate_bundle[0],rate_bundle[1],rank_list[i]] for i,rate_bundle in enumerate(zip(tags,ratings))]
	else:
		# populate this ranking in the cache in a nice array format
		# attempt to match tags to players in db
		skills['mainrank_readin'][yearkey] = [[i+1,rate_bundle[0],rate_bundle[1],get_abs_id_from_tag(dicts,rate_bundle[0],sort_by_skill=True,leet_sensetive=False)] for i,rate_bundle in enumerate(zip(tags,ratings))]

		# save rank -> p_id mappings
		if args.cache_mainranks:
			p_list = [y_line[3] for y_line in skills['mainrank_readin'][yearkey]]
			save_dict({'tags':tags,'ratings':ratings,'yearkey':yearkey,'p_list':p_list},rank_str,ver=get_db_verstr(),loc='db')

	# remove all current 'mainranks' in p_info
	for old_yearkey in skills['mainrank_readin']: # scan *all* previous years just to be safe
		if not old_yearkey == yearkey:
			#print(old_yearkey)
			#print(skills['mainrank_readin'][old_yearkey])
			for year_line in skills['mainrank_readin'][old_yearkey]:
				line_id = year_line[3]
				if line_id is not None:
					if 'mainrank' in p_info[line_id]:
						del p_info[line_id]['mainrank']

	# update skill histories
	for line in skills['mainrank_readin'][yearkey]:
		p_rank,p_tag,p_rating,p_id = line
		if p_id == None:
			# could not match player to db instance :c
			print('Player not found in DB: %s (#%d)'%(p_tag,p_rank))
		else:
			# players get this listed under skills per year key
			if p_id not in skills['mainrank']:
				skills['mainrank'][p_id] = {}
			if year not in skills['mainrank'][p_id]:
				skills['mainrank'][p_id][year] = {}
			skills['mainrank'][p_id][year][yearkey] = [p_rank,p_rating]
						
			# p_info is updated to contain the latest ranks
			if p_id in p_info:
				p_info[p_id]['mainrank'] = p_rank

def update_percentiles(dicts,t_id=None):
	tourneys,ids,p_info,records,skills,meta = dicts

	for skill_key in ['elo','glicko','srank']:
	#for skill_key in ['elo','glicko','srank','trueskill']:

		if skill_key == 'srank':
			p_data = np.array([[p_id,1.-p_info[p_id][skill_key]] for p_id in p_info])
		elif skill_key == 'glicko':
			p_data = np.array([[p_id,p_info[p_id][skill_key][0]] for p_id in p_info])
		else:
			p_data = np.array([[p_id,p_info[p_id][skill_key]] for p_id in p_info])
		# p_data = [p_id,skill]

		p_rank_data = [[i,p_sub[0],p_sub[1]] for i,p_sub in enumerate(sorted(p_data,key=lambda l: l[1],reverse=True),1)]
		# p_rank_data = [rank,p_id,skill]

		print('min/max ranks:',skill_key)
		if skill_key == 'srank':
			print([p_rank_data[0][0],p_rank_data[0][1],1.-p_rank_data[0][2]],p_info[p_rank_data[0][1]]['tag'])
			print([p_rank_data[-1][0],p_rank_data[-1][1],1.-p_rank_data[-1][2]],p_info[p_rank_data[-1][1]]['tag'])
		else:
			print(p_rank_data[0],p_info[p_rank_data[0][1]]['tag'])
			print(p_rank_data[-1],p_info[p_rank_data[-1][1]]['tag'])
		skillmax = float(p_rank_data[0][2])
		skillmin = float(p_rank_data[-1][2])

		for p_line in p_rank_data:
			# store rank
			p_info[int(p_line[1])][skill_key+'-rnk'] = p_line[0]
			# store precentile
			if (skillmax-skillmin) == 0: # if there is no skill range (e.g. srank for first few events of db), hardcode to 0th percentile
				p_info[int(p_line[1])][skill_key+'-pct'] = 0
			else:
				p_info[int(p_line[1])][skill_key+'-pct'] = int(((float(p_line[2])-skillmin)/(skillmax-skillmin))*100)

			# store peak rank/percentile
			if skill_key+'-rnk_peak' not in p_info[int(p_line[1])]:
				p_info[int(p_line[1])][skill_key+'-rnk_peak'] = p_info[int(p_line[1])][skill_key+'-rnk']
			if skill_key+'-pct_peak' not in p_info[int(p_line[1])]:
				p_info[int(p_line[1])][skill_key+'-pct_peak'] = p_info[int(p_line[1])][skill_key+'-pct']
			p_info[int(p_line[1])][skill_key+'-rnk_peak'] = min(p_info[int(p_line[1])][skill_key+'-rnk_peak'],9999999);
			p_info[int(p_line[1])][skill_key+'-pct_peak'] = max(p_info[int(p_line[1])][skill_key+'-pct_peak'],0);

			# store percentile/rank history in skills
			if t_id:
				skills[skill_key+'-rnk'][int(p_line[1])] = p_info[int(p_line[1])][skill_key+'-rnk']
				skills[skill_key+'-pct'][int(p_line[1])] = p_info[int(p_line[1])][skill_key+'-pct']

def update_top_h2h(dicts):
	tourneys,ids,p_info,records,skills,meta = dicts

	partial_set_list = lambda opp,set_res: [set_id for t_id in records[p_id][set_res][opp] for set_id in records[p_id][set_res][opp][t_id]] if opp in records[p_id][set_res] else []
	set_list = lambda opp: partial_set_list(opp,'wins') + partial_set_list(opp,'losses')
	#set_list = lambda opp: [set_data_w for set_data_w in records[p_id]['wins'][opp][t_id] for t_id in records[p_id]['wins'][opp] if opp in records[p_id]['wins'] if t_id in records[p_id]['wins'][opp]]  + \
	#					   [set_data_l for set_data_l in records[p_id]['losses'][opp][t_id] for t_id in records[p_id]['losses'][opp] if opp in records[p_id]['losses'] if t_id in records[p_id]['losses'][opp]]
	set_count = lambda opp,set_res: sum([len([set_id for set_id in records[p_id][set_res][opp][t_id]]) for t_id in records[p_id][set_res][opp] if t_id in records[p_id][set_res][opp]]) if opp in records[p_id][set_res] else 0
	opp_list = lambda player_id: [opp_id_w for opp_id_w in records[player_id]['wins']] + [opp_id_l for opp_id_l in records[player_id]['losses']]

	for p_id in p_info:
		for nom in [10,100,500]:
			'''print('H2H')
			print(p_id)
			print(records[p_id]['wins'])
			print(opp_list(p_id))
			print([set_list(opp) for opp in opp_list(p_id)])
			print([set_count(opp,'wins') for opp in opp_list(p_id)])'''
			h2h_list = {opp_id:{'id':opp_id, 'winCount':set_count(opp_id,'wins'), 'lossCount':set_count(opp_id,'losses'), 'sets':set_list(opp_id)} for opp_id in opp_list(p_id) if p_info[opp_id]['srank-rnk'] <= nom}

			records[p_id]['top_'+str(nom)] = h2h_list

# returns the number of times a player [p] used a given character [c] 
# (by id values)
def char_count(p,c,p_info):
	return abs(p_info[p]['characters'][c][0])+abs(p_info[p]['characters'][c][1])

# returns the character id that a player has used the most times
def get_main(p,p_info): 
	if 'characters' in p_info[p]:
		charlist = sorted([[c_id, char_count(p,c_id,p_info)] if char_count(p,c_id,p_info) > 0 else ['',0] for c_id in p_info[p]['characters']], \
									key=lambda c_l: c_l[1], \
									reverse=True)
		if len(charlist) > 0:
			return charlist[0][0]
		else:
			return ''
	else:
		return ''

def get_social_media(dicts,p_id,getAcctType=True):
	tourneys,ids,p_info,records,skills,meta = dicts
	player_url = 'https://api.smash.gg/player/%d'%p_id
	#print(p_id)
	aliases = p_info[p_id]['aliases']
	try:
		pfile = urlopen(player_url).read()
		pdata = json.loads(pfile.decode('UTF-8'))
		#print('opened file')
		if args.verbosity >= 6:
			print('Updating social media for:',p_info[p_id]['tag'],'|',p_id)

		player_data = pdata['entities']['player']

		if getAcctType and 'nameDisplay' in player_data:
			nameDisplay = player_data['nameDisplay']
		else:
			nameDisplay = None

		p_twitter = player_data['twitterHandle']
		p_twitch = player_data['twitchStream']
		p_reddit = player_data['redditUsername']
		p_youtube = player_data['youtube']
		if player_data['smashboardsLink'] is not None and player_data['smashboardsUserId'] is not None:
			p_smashboards = player_data['smashboardsLink']+'.'+str(player_data['smashboardsUserId'])
		else:
			p_smashboards = None
		p_ssbwiki = player_data['ssbwikiLink']
		# check ssbwiki manually if not provided
		if p_ssbwiki == None:
			if aliases is None:
				#print('..no aliases')
				tag = player_data['gamerTag']
				if has_cjk(tag):
					#print('..before tag: %s'%tag)
					tag = transliterate(tag).strip(' <>')
					#print('..after tag: %s'%tag)
				wiki_url = check_ssbwiki(dicts,p_id,tag)
				if wiki_url is not None:
					p_ssbwiki = wiki_url
				else:
					#print('..check failed')
					p_ssbwiki = None
			else:
				#print('..checking aliases')
				for tag in aliases:
					wiki_url = check_ssbwiki(dicts,p_id,tag)
					if wiki_url is not None:
						p_ssbwiki = wiki_url
						break
		if 'color' in player_data:
			p_color = player_data['color']
			if p_color:
				p_color = p_color[1:]
		else:
			p_color = None

		return {'twitter':p_twitter,'twitch':p_twitch,'reddit':p_reddit,'youtube':p_youtube,'smashboards':p_smashboards,\
				'ssbwiki':p_ssbwiki,'name_display':nameDisplay,'color':p_color}
	except HTTPError as e:
		print('Connection Error::',e)
		return False

# Imports linked social media accounts and smash.gg palyer acct info that we don't already have

# theoretically could be called at the end of a year instead of each tourney import, but
# name_display ==> account type is a necessary metric, and since we already make the API
# call, we might as well import social media too
def update_social_media(dicts,p_ids=None,v=0,use_cached_accts=args.cache_social_media,save_cached_accts=True):
	tourneys,ids,p_info,records,skills,meta = dicts

	if p_ids == None:
		if v >= 6:
			print('Updating all social media...')
		p_ids = [p_id for p_id in p_info]
	elif type(p_ids) is not list:
		p_ids = [p_ids]

	# cache is same regardless of db/game/year etc
	if use_cached_accts:
		social_dict = load_dict('socials',None,'..\\lib')

	for abs_id in p_ids:

		if use_cached_accts:
			# pull from cache if there
			if abs_id in social_dict:
				socials = social_dict[abs_id]
				if type(socials) is list:
					socials = get_social_media(dicts,abs_id)
					social_dict[abs_id] = socials
			else:
				# if not, write to cache
				socials = get_social_media(dicts,abs_id)
				if socials:
					social_dict[abs_id] = socials
		else:
			socials = get_social_media(dicts,abs_id)

		# if the player doesn't exist (???)
		if not socials:
			print('Error: %d (%s) not found on smash.gg player API'%(abs_id,p_info[abs_id]['tag']))
		else:
			#print(p_id)
			for s_key in ['twitter','twitch','reddit','youtube','smashboards','ssbwiki','discord','name_display','color']:
				if s_key in socials:
					p_info[abs_id][s_key] = socials[s_key]

	# save updated cache
	if use_cached_accts and save_cached_accts:
		save_dict(social_dict,'socials',None,'..\\lib')

# labels retired/banned players, to filter them out
def handle_player_status(p_id,activity='active'):
	if p_id in [6189]:
		return 'retired'
	elif p_id in []:
		return 'banned'
	else:
		return activity

# print (filtered) results for a given tourney
def print_result(dicts,t_id,res_filt=None,max_place=64):
	tourneys,ids,p_info,records,skills,meta = dicts
	res = get_result(dicts,t_id,res_filt)
	maxlen = 0
	t = tourneys[t_id]
	t_labels = t['groups']

	players = sorted(res,key=lambda l: (len(l[3]),0-l[4]), reverse=True)
	num_rounds = len(players[0][3])
	roundnames = [t_labels[group] for group in players[0][3]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 2*num_rounds

	print('%s Results | ID: %d'%(tourneys[t_id]['name'],t_id))
	print('\n{:>13.13}'.format('Sponsor |'),'{:<24.24}'.format('Tag'),'ID #\t','Place\t',('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('Bracket'),'Losses\n')

	for player in players:
		p_id,sp,tag,path,placement,losses,wins = player
		
		# format sponsor
		if sp == None or sp == '':
			sp = '  '
		else:
			if len(sp) > 12:
					sp = sp[:8] + '... |'
			else:
				if sp[-2:] != ' |':
					sp = sp + ' |'
		# format player tag
		if len(tag) > 24:
			tag = tag[:21]+'...'
		# format losses
		if losses == None or losses == []:
			loss_string = None
		else:
			loss_string = '['+', '.join(str(l) for l in [p_info[loss_id]['tag'] for loss_id in losses])+']'

		print('{:>13.13}'.format(sp),'{:<24.24}'.format(tag),'{:>7.7}'.format(str(p_id)), \
			'  {:<5.5}'.format(str(placement)),'\t',('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('['+', '.join(str(label) for label in [t_labels[group] for group in path])+']'),loss_string)

# print (filtered) results for multiple tourneys
def print_results(dicts,t_ids,res_filt=None,max_place=64):
	if type(t_ids) is str:
		if t_ids == 'all':
			t_ids = [t_id for t_id in tourneys if not t_id == 'slugs']
		else:
			print('Error:: Invalid tournament id: %s'%t_ids)
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

# print the tournaments in db, sorted by how "stacked" they are
def print_tourney_ratings(dicts):
	tourneys,ids,p_info,records,skills,meta = dicts

	tourneyRatings = sorted([[tourneys[t_id]['rating'],tourneys[t_id]['numEntrants'],tourneys[t_id]['name']] for t_id in tourneys if tourneys[t_id]['rating'] is not None],key=lambda l:l[0])
	print ('Rating\tN\tName')
	for line in tourneyRatings:
		print('\t'.join([str(line_item) for line_item in line]))

# prints the specified records, grouping by the g_key criteria
def print_resume(dicts,res,g_key='player',s_key=None,disp_raw=False,disp_wins=True):
	tourneys,ids,p_info,records,skills,meta = dicts
	#print(res)
	if not res or len(res) == 0 or res == []:
		print('Resume was not provided or could not be found')
		return False
	print('')
	if g_key == 'player':
		res = sorted(res,key=lambda r: (r[1][0],r[0]))
		h_idx = 1
		s_idx = 0
		print('RESUME BY PLAYER:')
	elif g_key == 'event':
		res = sorted(res,key=lambda r: (r[0],r[1][4],r[1][0]))
		h_idx = 0
		s_idx = 5
		print('RESUME BY EVENT:')
	elif g_key == 'team':
		res = sorted(res,key=lambda r: (r[1][1],r[0],r[1][4],r[1][0]))
		h_idx = 2
		s_idx = 0
		print('RESUME BY TEAM:')
	elif g_key == 'placing':
		res = sorted(res,key=lambda r: (r[1][4],r[1][0],r[0]))
		h_idx = 5
		s_idx = 1
		print('RESUME BY PLACING:')
	elif g_key == 'region':
		res = sorted(res,key=lambda r: (r[1][1],r[1][0],r[0]))
		h_idx = 4
		s_idx = 1
		print('RESUME BY REGION:')
	# default to player ID grouping
	else:
		res = sorted(res,key=lambda r: (r[1][0],r[0]))
		h_idx = 1
		print('RESUME BY PLAYER:')
	if not (s_key == None or s_key == g_key):
		if s_key == 'player':
			s_idx = 1
		if s_key == 'event':
			s_idx = 0
		if s_key == 'team':
			s_idx = 2
		if s_key == 'placing':
			s_idx = 5
		if s_key == 'region':
			s_idx = 4
	print('----------------')

	# flatten and replace ids with plaintext
	# also resort by provided secondary criteria (if any)
	res = [flatten([[line[0]],line[1]]) for line in res] 
	for line in res:
		if not disp_raw:
			line[4] = [tourneys[line[0]]['groups'][grp_id] for grp_id in line[4]]
			line[6] = [p_info[l_id]['tag'] for l_id in line[6]]
			line[7] = [p_info[w_id]['tag'] for w_id in line[7]]
			line[0] = tourneys[line[0]]['name']
		tempval = line[4]
		line[4] = line[5]
		line[5] = tempval
		line.insert(4,get_region(dicts,line[1]))
	#print(res[:,h_idx])
	#print(res[:,s_idx])
	res = sorted(res,key=lambda l: (l[h_idx],l[s_idx]))
	#print(res)

	# print first value/header
	oldval = res[0][h_idx]
	old_sval = res[0][s_idx]
	if h_idx == 1:
		tagstr = ''
		if res[0][2] != None and res[0][2] != ' ' and res[0][2] != '':
			tagstr += '%s | '%res[0][2]
		tagstr += res[0][3]
		print('%s (id: %d) || %s (Elo: %d, Glicko: %d, SigRank: %d)'%(tagstr,res[0][1],res[0][4],round(p_info[res[0][1]]['elo'],3),round(p_info[res[0][1]]['glicko'][0],3),p_info[res[0][1]]['srank']))
	else:
		print(str(oldval)+': ')
	s_tagstr = ''
	if s_idx == 1:
		if h_idx != 2:
			s_tagstr += str(res[0][2])+' | '
		s_tagstr += res[0][3]
		s_tagstr += ' ('+str(res[0][4])+')'
		print('\t'+s_tagstr)
	else:
		print('\t'+str(res[0][s_idx]))
	# iterate through list
	for line in res:
		# print header if on new section
		if line[h_idx] != oldval:
			if h_idx == 1:
				tagstr = ''
				if line[2] != None:
					tagstr += '%s | '%line[2]
				tagstr += line[3]
				print('%s (id: %d) || %s (Elo: %d, Glicko: %d, SigRank: %d)'%(tagstr,line[1],line[4],round(p_info[line[1]]['elo'],3),round(p_info[line[1]]['glicko'][0],3),p_info[res[0][1]]['srank']))
			else:
				print(str(line[h_idx])+': ')
		# print secondary header if on new subsection
		if line[s_idx] != old_sval or line[h_idx] != oldval:
			#temp_sline = []
			s_tagstr = ''
			if s_idx == 1:
				if h_idx != 2:
					s_tagstr += str(line[2])+' | '
				s_tagstr += line[3]
				s_tagstr += ' ('+str(line[4])+')'
				print('\t'+s_tagstr)
			else:
				print('\t'+str(line[s_idx]))

		old_sval = line[s_idx]
		oldval = line[h_idx]
		# print data line
		print_resume_line(line,h_idx,s_idx,disp_wins)

# helper for print_resume
def print_resume_line(line,h_idx,s_idx,disp_wins=True):
	temp_line = []
	if h_idx == 1:
		temp_line.extend([line[:h_idx]])
		temp_line.extend([line[h_idx+4:]])
	else:
		temp_line.extend([line[:h_idx]])
		temp_line.extend([line[h_idx+1:]])
	temp_line = flatten(temp_line)
	if s_idx == 1:
		if h_idx != 2:
			temp_line.remove(line[2])
		temp_line.remove(line[3])
		temp_line.remove(line[4])
	temp_line.remove(line[s_idx])
	del_lines = 0
	if not disp_wins:
		temp_line = temp_line[:-1]
		del_lines = 1
	print("\t\t"+'['+', '.join(str(val) for val in temp_line[:(del_lines-3)])+', '+', '.join('['+', '.join(str(item) for item in val)+']' for val in temp_line[(del_lines-3):])+']')

# print's an event's results (deprecated)
def old_print_event(dicts,t_id,max_place=64,translate_cjk=True):
	maxlen = 0
	tourneys,ids,p_info,records,skills,meta = dicts
	t = tourneys[t_id]
	t_labels = t['groups']

	player_ids = [p_id for p_id in ids if (not (type(p_id) is str) and t_id in ids[p_id])]
	player_teams = [p_info[p_id]['team'] for p_id in player_ids]
	player_tags = [p_info[p_id]['tag'] for p_id in player_ids]
	player_paths = [records[p_id]['paths'][t_id] for p_id in player_ids]
	player_places = [records[p_id]['placings'][t_id]['placing'] for p_id in player_ids]
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

	print('%s Results | ID: %d'%(tourneys[t_id]['name'],t_id))
	print('\n{:>13.13}'.format('Sponsor |'),'{:<24.24}'.format('Tag'),'ID #\t','Place\t',('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('Bracket'),'Losses\n')

	for player in players:
		p_id,sp,tag,path,placement,losses = player
		#print(player)

		if placement > max_place and max_place > 0:
			break
		else:
			# format sponsor
			if sp == None or sp == '' or sp == ' ':
				sp = '  '
			else:
				if len(sp) > 12:
						sp = sp[:8] + '... |'
				else:
					if sp[-2:] != ' |':
						sp = sp + ' |'
			sp_len = 13
			if translate_cjk and has_cjk(sp):
				sp = '<'+transliterate(sp)+'>'
			for ch in sp:
				if is_emoji(ch):
					sp_len -= 1
				elif is_cjk(ch):
					sp_len -= 1
			# format player tag
			tag_len = 24
			if translate_cjk and has_cjk(tag):
				tag = '<'+transliterate(tag)+'>'
			if len(tag) > tag_len:
				tag = tag[:tag_len-3]+'...'
			for ch in tag:
				if is_emoji(ch):
					tag_len -= 1
				elif is_cjk(ch):
					tag_len -= 1
			# format losses
			if losses == None or losses == []:
				losses = None
			else:
				losses = [p_info[loss_id]['tag'] for loss_id in losses]
			if translate_cjk:
				losses = ['<'+transliterate(loss_tag)+'>' for loss_tag in losses]
			# format spacing
			#if len(path) > maxlen:
			#	maxlen = len(path)
			#lsbuff = "\t"*(maxlen-len(path)+1)
			print(('{:>%d.%d}'%(sp_len,sp_len)).format(sp),('{:<%d.%d}'%(tag_len,tag_len)).format(tag),'{:>7.7}'.format(str(p_id)), \
				'  {:<5.5}'.format(str(placement)),'\t',('{:<%d.%d}'%(roundslen+5,roundslen+5)).format(str([t_labels[group] for group in path])),losses)

#if __name__ == '__main__':
	#print(leetify('Swedish Delight'))
	#print('asdf')