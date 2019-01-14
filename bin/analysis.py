## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
from statistics import mean 
from math import *
import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
#import json
import argparse
#import shutil
from timeit import default_timer as timer
## UTIL IMPORTS
from db_utils import *
from dict_utils import *
from calc_utils import *
from analysis_utils import *

## TODO: 
##	Shortterm
## 		 - debug elo/glicko (how?)
## 		 - Add support for japanese character detection / americanized names
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 			- static team support pls
## 		 - filter out invitationals for certain metrics (like % of bracket complete, etc.)
## 		 - use res_filt format more universally for queries and such // expand get_result
## 		 - error logs
## 		 - SKILL TIERSSSSS
## 		 - use 'state' to check for status of bracket (1: unscheduled, 4: called, 2: in progress, 3: completed) [IF NOT ALREADY IMPLEMENTED]
## 		 - make elo/glicko calculations faster/more efficient somehow
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
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
## 		- decay over time?
## 	- fix Glicko-2
## 	- add Iagorank


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
	dicts = main_read()
	tourneys,ids,p_info,records,skills = dicts
	# ==========================================================================================

	#tourneys,ids,p_info,records,skills = load_db(str(game_idx)+"/"+yearstr)
	#tourneys,ids,p_info,records,skills = load_db(str(game_idx)+"/"+str(year))


	#print(get_result((tourneys,ids,p_info,records),36179,res_filt={'player':1000}))
	#resume = get_resume(dicts,None,tags=['Vist','Nicki','Trif','nebbii','Avalancer'])
	#update_regions((tourneys,ids,p_info,records),[1000])
	#print_resume(dicts,resume,g_key='player',s_key='event')
	#print(get_player(dicts,None,tag='Plup'))
	#print(ids[get_abs_id_from_tag(dicts,'Plup')])

	#tourneys,ids,p_info,records,skills = delete_tourney((tourneys,ids,p_info,records),None,slug='smash-summit-6')
	#tourneys,ids,p_info,records,skills = delete_tourney((tourneys,ids,p_info,records),None,slug='smash-summit-7')

	#disp_all(dicts,key='elo')
	#disp_all(dicts,key='elo',dispnum=20,min_activity=2)
	#disp_all(dicts,key='glicko',dispnum=20,min_activity=2)
	disp_all(dicts,key='norm_all',dispnum=20,min_activity=2,tier_tol=0.5)
	#print_event(dicts,tourneys['slugs']['smash-summit-5'])

	#disp_all(dicts,key='performance')
	#xxx = 0
	#for t_id in tourneys:
	#	if 'name' in tourneys[t_id]:
	#		if 'Shine' in tourneys[t_id]['name']:
	#			xxx = t_id
	#print_result((tourneys,ids,p_info,records),xxx,{'tag':'Iago'})
	#print(p_info[65348]['elo'])

	#disp_elos((tourneys,ids,p_info,records))
	#print(list_tourneys((tourneys,ids,p_info,records)))
	#tourneys,ids,p_info,records,skills = delete_tourney((tourneys,ids,p_info,records),None,slug='don-t-park-on-the-grass-2018-1')
	#tourneys,ids,p_info,records,skills = delete_tourney((tourneys,ids,p_info,records),None,slug='heir-5')
	#tourneys,ids,p_info,records,skills = delete_tourney((tourneys,ids,p_info,records),None,slug='full-bloom-4')
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

def main_read():
	set_db_args(args)
	if year_count == 0:
		yearstr = str(year)
	else:
		yearstr = str(year)+"-"+str(year+year_count)
	tourneys,ids,p_info,records,skills = easy_load_db(str(game_idx)+"/"+yearstr)
	tourneys,ids,p_info,records,skills = read_majors(game_idx,year,base=(tourneys,ids,p_info,records,skills))
	for i in range(1,year_count+1):
		tourneys,ids,p_info,records,skills = read_majors(game_idx,year+i,base=(tourneys,ids,p_info,records,skills))

	return tourneys,ids,p_info,records,skills

if __name__ == "__main__":
	main()