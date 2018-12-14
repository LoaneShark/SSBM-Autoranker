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
from readin_utils import *

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

v = int(args.verbosity)
# verbosity threshold for save/load statements
lv = 6
save_res = args.save
load_res = args.load
if args.save == "False":
	save_res = False
if args.load == "False":
	load_res = False
force_first_event = args.force_first
teamsize = int(args.teamsize)
game = int(args.game)
if game not in [1,2,3,4,5,1386]:		#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386
	print("Invalid game number provided. Forcing melee (id=1) instead.")
	game = 1
disp_num = int(args.displaysize)
t_slug_a = args.slug
t_ss_a = args.short_slug
if t_ss_a == None:
	t_slug_a = t_slug_a
else:
	t_slug_a = get_slug(t_ss_a)
print_res = args.print
count_arcadians = args.use_arcadians

## MAIN FUNCTIONS
def readin(tourney,t_type="slug"):
	if t_type == "slug":
		slug = tourney
	elif t_type == "ss":
		slug = get_slug(tourney)
	else:
		print("Error: invalid tourney identifier type")
		return None

	out = read_phases(slug)

	if out:
		t,ps,pdata = out

		tid = t[0]
		es,ws,ls,rs,ns = read_groups(tid,ps,pdata)

		if print_res:
			print_results(rs,ns,es,ls,max_place=disp_num)
		return t,es,ns,rs,ws,ls
	else:
		return False

def set_readin_args(args):
	v = int(args.verbosity)
	# verbosity for save/load statements
	lv = 6
	save_res = args.save
	load_res = args.load
	force_first_event = args.force_first
	teamsize = int(args.teamsize)
	game = int(args.game)
	if game not in [1,2,3,4,5,1386] and False:		#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386
		print("Invalid game number provided. Forcing melee (id=1) instead.")
		game = 1
	disp_num = int(args.displaysize)
	t_slug_a = args.slug
	t_ss_a = args.short_slug
	if t_ss_a == None:
		t_slug_a = t_slug_a
	else:
		t_slug_a = get_slug(t_ss_a)
	print_res = args.print

# reads the match data for a given phase
def read_groups(t_id,groups,phase_data):
	entrants = {}
	wins = {}
	losses = {}
	paths = {}
	bracket = {}
	names = {}
	end_buff = False

	if load_res and v >= 3:
		print("Loading cached files...")

	for group in groups:
		pstart = timer()
		load_succ = False
		if load_res and not end_buff:
			try:
				if v >= lv:
					print("Loading %d..."%group)
				entrants,wins,losses,paths,names = load_all(t_id,group)
				load_succ = True
			except FileNotFoundError:
				if v >= lv:
					print("Phase group %d not found locally"%group)
				end_buff = True
				load_succ = False

		if not load_succ:

			data = json.loads(pull_phase(group))

			read_entrants(data,phase_data,entrants,names,paths)
			read_sets(data,phase_data,wins,losses,paths)

			if save_res:
				if v >= lv:
					print("Saving %d..."%group)
				save_all(t_id,group,[entrants,wins,losses,paths,names])

			if v >= 4:
				print("{:.0f}".format(1000*(timer()-pstart)) + " ms")
	return entrants,wins,losses,paths,names

# reads in and returns data for all entrants in a given phase group
def read_entrants(data,phase_data,entrants,names,xpath):
	group = data['entities']['groups']['id']
	wave_id = data['entities']['groups']['phaseId']

	if phase_data[wave_id][1] == 1:
		groupname = phase_data[wave_id][0]
	else:
		groupname = data['entities']['groups']['displayIdentifier']
	names['g_%d'%group] = groupname
	if v >= 4:
		print("Reading group: %s | %d"%(groupname,group)) 
	seedata = data['entities']['seeds']

	for x in seedata:
		e_id,abs_id,tag,prefix,metainfo = read_names(x)
		names[e_id] = (prefix,tag)

		res = 9000
		if v >= 8:
			print(e_id,tag)
		if v >= 9 and e_id in xpath:
			print(xpath[e_id])

		if e_id in xpath:
			if v >= 9:
				print(xpath[e_id][1])
			xpath[e_id][0] = res
			xpath[e_id][1].extend([group])
		else:
			xpath[e_id] = [res,[group]]

		#entrants[i] = (names[i], player_id[i])
		entrants[e_id] = (names[e_id],abs_id,e_id,metainfo)
	return entrants,names,xpath
		
# returns sponsor, gamertag, and player meta info for a given entrant	
def read_names(x):
	e_id = x['entrantId']
	part_id = x['mutations']['entrants'][str(e_id)]['participantIds'][0]
	abs_id = x['mutations']['entrants'][str(e_id)]['playerIds'][str(part_id)]
	tag = x['mutations']['participants'][str(part_id)]['gamerTag']
	prefix = x['mutations']['participants'][str(part_id)]['prefix']

	continfo = x['mutations']['participants'][str(part_id)]['contactInfo']
	if 'nameFirst' in continfo:
		f_name = continfo['nameFirst']
	else:
		f_name = "N/A"
	if 'nameLast' in continfo:
		l_name = continfo['nameLast']
	else:
		l_name = "N/A"
	if 'state' in continfo:
		state = continfo['state']
	else:
		state = "N/A"
	if 'country' in continfo:
		country = continfo['country']
	else:
		country = 'N/A'
	metainfo = (f_name,l_name,state,country)

	return e_id,abs_id,tag,prefix,metainfo

# reads the sets for a given phase group and returns match results
def read_sets(data,phase_data,wins,losses,xpath):
	setdata = data['entities']['sets']
	group = data['entities']['groups']['id']

	for match in setdata:
		e1,e2 = match['entrant1Id'],match['entrant2Id']
		w_id,l_id = match['winnerId'],match['loserId']
		set_id = match['id']
		is_bye = False

		if w_id == None or l_id == None:
			is_bye = True

		if not is_bye:
			if v >= 6:
				print(set_id,match['phaseGroupId'],match['identifier'],[w_id,l_id],[e1,e2])
			if w_id not in wins:
				wins[w_id] = [(l_id,[set_id,group])]
			else:
				wins[w_id].extend([(l_id,[set_id,group])])
			if l_id not in losses:
				losses[l_id] = [(w_id,[set_id,group])]
			else:
				losses[l_id].extend([(w_id,[set_id,group])])

			# always update final placement (assume they progressed -- people can't backtrack in bracket)
			if not match['wOverallPlacement'] == None:
				xpath[w_id][0] = match['wOverallPlacement']
			if not match['lOverallPlacement'] == None:
				xpath[l_id][0] = match['lOverallPlacement']
		else:
			if v >= 6:
				print(set_id,match['phaseGroupId'],match['identifier'],["bye","bye"],[e1,e2])

	return wins,losses

# reads the phase data for a given tournament
def read_phases(tourney):
	if v >= 2 and v < 4:
		start = timer()
	waves = {}
	#with open(filepath) as f:
	#	data = json.loads(f.read())

	phaselink ="https://api.smash.gg/tournament/%s?expand[]=event&expand[]=groups&expand[]=phase"%tourney
	try:
		tfile = urlopen(phaselink).read()
		tdata = json.loads(tfile.decode("UTF-8"))

		t_id = tdata['entities']['tournament']['id']
		t_name = tdata['entities']['tournament']['name']
		t_ss = tdata['entities']['tournament']['shortSlug']
		t_slug = tdata['entities']['tournament']['slug'].split('/')[1]
		t_type = tdata['entities']['tournament']['tournamentType']
		# date tuple in (year, month, day) format
		t_date = time.localtime(tdata['entities']['tournament']['startAt'])[:3]
		t_region = (tdata['entities']['tournament']['addrState'],tdata['entities']['tournament']['countryCode'])
		t_info = (t_id,t_name,t_slug,t_ss,t_type,t_date,t_region)

		if v >= 1:
			print("Reading tournament: %s | %d"%(tdata['entities']['tournament']['name'],t_id))

		# can't read a tourney's results if it hasn't happened yet!
		day_after = datetime.datetime(t_date[0],t_date[1],t_date[2])
		while day_after.weekday() >= 4:
			day_after += datetime.timedelta(days=1)
		if day_after > datetime.datetime.today():
			if v >= 1:
				print("Cannot read %s: Tournament hasn't happened yet!"%t_name)
			return False

		# get all event_id's for events that are gametype=1 (melee) and entrantcount=1 (singles) (or whatever criteria specified)
		event_ids = [[event['id'],(event['name'],event['description'])] for event in tdata['entities']['event'] if event['videogameId'] == game and event['entrantSizeMin'] == teamsize]
		#event_ids = [event['id'] for event in tdata['entities']['event'] if event['videogameId'] == game and event['entrantSizeMin'] == teamsize]
		
		if v >= 7:
			print("only looking for brackets of game type: " + str(game))
			print("event_ids pre filtering: " + str(len(event_ids)))
		# filters out events that don't list melee in description, to filter out stuff like low tiers/ironmans/crews etc (only melee so far)
		ssbm_events = [event_id[0] for event_id in event_ids if has_melee(event_id[1][0]) or has_melee(event_id[1][1])]
		amateur_events = [event_id[0] for event_id in event_ids if is_amateur(event_id[1][0]) or is_amateur(event_id[1][1])]
		if not count_arcadians:
			arcadian_events = [event_id[0] for event_id in event_ids if is_arcadian(event_id[1][0]) or is_arcadian(event_id[1][1])]
		if len(ssbm_events) >= 1 and game == 1:
			event_ids = ssbm_events
		else:
			event_ids = [event_id[0] for event_id in event_ids]
		# filters out events that have 'amateur' or 'arcadian' in the description
		event_ids = [event_id for event_id in event_ids if not event_id in amateur_events]
		if not count_arcadians:
			event_ids = [event_id for event_id in event_ids if not event_id in arcadian_events]

		if v >= 7:
			print("event_ids post filtering: " + str(len(event_ids)))
		if force_first_event:
			event_ids = event_ids[:1]
		# get all phases (waves) for each event (ideally filtered down to 1 by now)
		phase_ids = [phase['id'] for phase in tdata['entities']['phase'] if phase['eventId'] in event_ids]
		# get all groups (pools) for each phase
		group_ids = [group['id'] for group in tdata['entities']['groups'] if group['phaseId'] in phase_ids]

		for w in tdata['entities']['phase']:
			if w['id'] not in waves:
				waves[w['id']] = [w['name'],w['groupCount'],w['phaseOrder'],w['eventId'],w['typeId'],w['isExhibition']]
		#print(t_id)
		#print(event_ids)
		#print(phase_ids)
		#print(group_ids)
		if v >= 2 and v < 4:
			print("{:.3f}".format(timer()-start) + " s")
		
		return (t_info,group_ids,waves)

	except HTTPError:
		print("Error 404: tourney [%s] not found"%tourney)
		return False
	

if __name__ == "__main__":
	readin(t_slug_a)

	#readin('summit7',type='ss')
	#print(get_slug('tbh8'))

	#read_sets("sets.txt")
	#pull_phase(764818)

	#clean_data("hbox tbh raw.txt","hbox tbh.txt")
	#clean_data("hbox s7 raw.txt","hbox s7.txt")
	#clean_data("dpotg2018.txt","g5top8.txt")