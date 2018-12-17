## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
#import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
import re
from timeit import default_timer as timer
## UTIL IMPORTS
from readin_utils import print_results

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
		player_losses.extend([temp_l])
	for p_id in player_ids:
		temp_w = []
		for w_id in records[p_id]['wins']:
			for i in range(records[p_id]['wins'][w_id].count(t_id)):
				temp_w.extend([w_id])
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
	roundslen = sum([len(str(name)) for name in roundnames]) + 4*num_rounds

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
				sp = sp + " |"
		# format player tag
		if len(tag) > 24:
			tag = tag[:21]+"..."
		# format losses
		if losses == None or losses == []:
			losses = None
		else:
			losses = [p_info[loss_id]['tag'] for loss_id in losses]

		print("{:>13.13}".format(sp),"{:<24.24}".format(tag),"{:>7.7}".format(str(p_id)), \
			"  {:<5.5}".format(str(placement)),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format(str([t_labels[group] for group in path])),losses)

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
	players = sorted(entrants,key=lambda l: (len(l[3]),0-l[4]), reverse=True)

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
					sp = sp + " |"
			# format player tag
			if len(tag) > 24:
				tag = tag[:21]+"..."
			# format losses
			if losses == None or losses == []:
				losses = None
			else:
				losses = [p_info[loss_id]['tag'] for loss_id in losses]
			# format spacing
			#if len(path) > maxlen:
			#	maxlen = len(path)
			#lsbuff = "\t"*(maxlen-len(path)+1)
			print("{:>13.13}".format(sp),"{:<24.24}".format(tag),"{:>7.7}".format(str(p_id)), \
				"  {:<5.5}".format(str(placement)),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format(str([t_labels[group] for group in path])),losses)