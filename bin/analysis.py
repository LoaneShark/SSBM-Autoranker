## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
from statistics import mean 
from math import *
#import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
#import json
import argparse
#import shutil
from timeit import default_timer as timer
## UTIL IMPORTS
from db_utils import read_majors,set_db_args,save_db,load_db,delete_tourney,easy_load_db
from analysis_utils import *

## TODO: 
##	Shortterm
## 		 - ensure scraper is JUST SINGLES unless otherwise specified
## 			- Filter out "Teams" and "Doubles" events even if # of entrants is listed as 1
## 		 - doubles support
## 		 - use 'state' to check for status of bracket (1: unscheduled, 4: called, 2: in progress, 3: completed)
## 		 - error logs
## 		 - SKILL TIERSSSSS
## 		 - Error 502 bad gateway handling (retry after waiting)
## 		 - Find out why some players don't have results // win-loss records
## 		 - use res_filt format more universally for queries and such // expand get_result
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 		 - allow analysis_utils to write to file for some queries, etc. (csv?)
## 		 - GUI/standalone executable tool/webapp
## 		 - Intelligent clustering of players by region
##

## ELO BALANCING:
##	- debug?
## 		- do invitationals/summit/alternate brackets mess with this?
## 		- what K values to use? 
## 		- how do we instantiate elo scores?
## 			- SSBMRank scores from the previous year? Normal distribution using avg tourney placing?
## 	- aggregate/normalized?
## 	- add Glicko-2
## 	- add Iagorank
##  - min activity requirements

# Tourney shitlist:
# 	- DPOTG (redemption ladder)


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

game_idx = int(args.game)
if args.force_game:
	game_idx = int(args.force_game)
year = int(args.year)
year_count = int(args.year_count)
to_load_db = args.load
if args.load == "False":
	to_load_db = False
to_load_slugs = args.load_slugs
if args.load_slugs == "False":
	to_load_slugs = False
maxpl = int(args.displaysize)

def main():
	set_db_args(args)
	if year_count == 0:
		yearstr = str(year)
	else:
		yearstr = str(year)+"-"+str(year+year_count)
	#tourneys,ids,p_info,records = load_db(str(game_idx)+"/"+yearstr)
	tourneys,ids,p_info,records = easy_load_db(str(game_idx)+"/"+yearstr)
	#tourneys,ids,p_info,records = load_db(str(game_idx)+"/"+str(year))
	tourneys,ids,p_info,records = read_majors(game_idx,year,base=(tourneys,ids,p_info,records))
	#for i in range(1,year_count+1):
	#	tourneys,ids,p_info,records = read_majors(game_idx,year+i,base=(tourneys,ids,p_info,records))


	#print(get_result((tourneys,ids,p_info,records),36179,res_filt={'player':1000}))
	#resume = get_resume((tourneys,ids,p_info,records),None,team=['Liquid','TSM','Tempo'],slugs=['evo-2018','shine-2018','the-big-house-7'])
	#print_resume((tourneys,ids,p_info,records),resume,g_key='event',s_key='team')

	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='smash-summit-6')
	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='smash-summit-7')

	disp_all((tourneys,ids,p_info,records),key='elo')
	#xxx = 0
	#for t_id in tourneys:
	#	if 'name' in tourneys[t_id]:
	#		if 'Shine' in tourneys[t_id]['name']:
	#			xxx = t_id
	#print_result((tourneys,ids,p_info,records),xxx,{'tag':'Iago'})
	#print(p_info[65348]['elo'])

	#disp_elos((tourneys,ids,p_info,records))
	#print(list_tourneys((tourneys,ids,p_info,records)))
	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='don-t-park-on-the-grass-2018-1')
	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='heir-5')
	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='full-bloom-4')
	#print(list_tourneys((tourneys,ids,p_info,records)))

	#dicts = delete_tourney((tourneys,ids,p_info,records),None,'valhalla')
	#res = get_player((tourneys,ids,p_info,records),None,tag='Free Palestine')
	#out = get_players_by_region((tourneys,ids,p_info,records),'California',get_data=True)
	#for res in out:
	#	print(res[1][1]['tag'],"|",res[1][1]['city'],"|",res[1][1]['region']," (old) |",calc_region(res[1][1]['country'],res[1][1]['state'],res[1][1]['city']))
	#for seg in [out[(i-1)*10:i*10] for i in range(int(len(out)/10))]:
	#p_ids = [res[0] for res in out]
	#update_regions((tourneys,ids,p_info,records),p_ids)
	#print("Saving Updated DB...")
	#save_db((tourneys,ids,p_info,records),str(game_idx)+"/"+str(year))
	#print([res[1]['team'][0],res[1]['team'][0].encode()])
	#print([len(res[1]['team'][0]),len(res[1]['team'][0].encode())])
	#print(["hello","hello".encode()])
	#print([len("hello"),len("hello".encode())])
	#print_event((tourneys,ids,p_info,records),tourneys['slugs']['full-bloom-4'],max_place=int(args.displaysize))
	#print_event((tourneys,ids,p_info,records),tourneys['slugs']['valhalla'],max_place=int(args.displaysize))

	return True

def get_scores(dicts,acc=3):
	tourneys,ids,p_info,records = dicts
	scores = {}
	for p_id in p_info:
		if p_id in records:
			scores[p_id] = round(mean([score(dicts,records[p_id]['placings'][t_id],t_id) for t_id in tourneys if type(t_id) is int if t_id in records[p_id]['placings']]),acc)
	return scores

def disp_scores(dicts,dispnum=20):
	tourneys,ids,p_info,records = dicts
	scores = get_scores(dicts)

	players = sorted([[p_info[p_id]['tag'],scores[p_id]] for p_id in p_info],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_elos(dicts,acc=3):
	tourneys,ids,p_info,records = dicts
	elos = {}
	for p_id in p_info:
		if p_id in records:
			#elos[p_id] = mean([score(dicts,records[p_id]['placings'][t_id],t_id) for t_id in tourneys if type(t_id) is int if t_id in records[p_id]['placings']])
			elos[p_id] = round(p_info[p_id]['elo'],acc)
	return elos

def disp_elos(dicts,dispnum=20):
	tourneys,ids,p_info,records = dicts
	elos = get_elos(dicts)

	players = sorted([[p_info[p_id]['tag'],elos[p_id]] for p_id in p_info],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_iagorank(dicts):
	tourneys,ids,p_info,records = dicts
	return True

def get_performances(dicts,acc=3):
	tourneys,ids,p_info,records = dicts
	avg_perfs = {}

	for p_id in p_info:
		if p_id in records:
		#print(records[p_info])
			perfs = []
			for t_id in records[p_id]['performances']:
				#print(records[p_id]['performances'])
				perfs.extend([records[p_id]['performances'][t_id]])

			avg_perfs[p_id] = round(mean(perfs),acc)
	return avg_perfs

def disp_all(dicts,dispnum=20,key='elo'):
	tourneys,ids,p_info,records = dicts
	key_idx = 1
	elos = get_elos(dicts)
	scores = get_scores(dicts)
	perfs = get_performances(dicts)

	if key == 'bracket':
		key_idx = 2
	if key == 'elo':
		key_idx = 1
	if key == 'performance':
		key_idx = 3
	if key == 'simbrac':
		key_idx = 4
	if key == 'glicko':
		key_idx = 5
	players = sorted([[p_info[p_id]['tag'],elos[p_id],scores[p_id],perfs[p_id]] for p_id in p_info if p_id in elos if p_id in scores if p_id in perfs],key=lambda x: x[key_idx],reverse=True)
	players = players[:dispnum]

	print("\n{:<20.20}".format("Player"),"{:<9.9}".format("Elo"),"{:<9.9}".format("Mean %"),"{:<9.9}".format("Mean Perf"),"\n")
	for player in players:
		print("{:<20.20}".format(player[0]),"{:<9.9}".format(player[1]),"{:<9.9}".format(player[2]),"{:<9.9}".format(player[3]))

def score(dicts,placing,t_id):
	tourneys,ids,p_info,records = dicts

	num_entrants = tourneys[t_id]['numEntrants']
	percent = (log(num_entrants,2)-log(placing,2)+1)/log(num_entrants,2)
	return percent

def h2h(dicts,p1_id,p2_id):
	tourneys,ids,p_info,records = dicts

	w,l = 0,0

	if p2_id in records[p1_id]["wins"]:
		w = len(records[p1_id]["wins"][p2_id])
	if p2_id in records[p1_id]["losses"]:
		l = len(records[p1_id]["losses"][p2_id])

	return (w,l) 



if __name__ == "__main__":
	main()