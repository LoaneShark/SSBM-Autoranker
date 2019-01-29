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
##		HIGH PRIORITY:
## 		 - Fix regions
## 			- Make it faster, i slowed it down a lot with the new system
## 				- build up the cache I guess
## 			- Find out how to avoid query limits / breaking terms of use
## 			- restructure data to be stored in a single dict / one dict per country (cities folder is messy)
## 		 - Use numpy arrays / vectorize to speed up computations
## 		 - add optional caching of tournament data / json files?
## 		 - add fully offline mode toggle  // prefer offline argument
## 		 - add a 'tourney memory' duration (default 1 year) -- delete all events that are older than this from DB, including records etc.
## 		     - elo etc still calculated this way, but only recent events 'count' (???)
## 		 - config file
##		 - fix errors with player ids being inconsistent somehow? (lookin' at you, We Tech Those 3 PM Singles [Pool PMA2])
## 		 - query mode
## 		 - MIGRATE TO NEW API
##
##		MEDIUM PRIORITY:
## 		 - how to match players that don't have smash.gg accounts/consistent player ids (mostly japanese players)
## 			- also match players that have multiple accounts // remade accounts // use them inconsistently
## 		 - debug elo/glicko (how?)
## 		 - Filter out DQs somehow (if a palyer didn't attend don't penalize them for "going 0-2")
## 			- Can we filter out sandbags somehow? intelligent decisionmaking?
## 			- Maybe drop lowest N results from each player? does this take away from consistency as a virtue?
## 		 - SKILL TIERSSSSS
## 		 - Fix crashes on repeated web calls
##
## 		LOWER PRIORITY:
## 		 - filter out invitationals for certain metrics (like % of bracket complete, etc.)
## 		 - Add support for non-roman scripts (besides japanese)
## 		 - error logs
## 		 - make elo/glicko calculations faster/more efficient somehow
## 		 - use res_filt format more universally for queries and such // expand get_result
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 			- static team support pls
## 		 - Rework regions to use cached geopy results for better consistency // accuracy // granularity
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
## 	- fit Glicko-2 (?)

## SIMBRACK TODO:
##  - do I need to simbrack? Can I just use sigmoid integral / y-intercept?
##	- track deltas to ensure convergence
##	- how do I calculate uncertainty in original winps
##	
##	- Fourier analysis lmao

## TOURNEY SHITLIST:
## 	- We Tech Those 3: PM Pool PMA2
##	- DPOTG 2018: Redemption ladder (kinda)


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
min_act = int(args.min_activity)

def main():
	dicts = main_read()
	tourneys,ids,p_info,records,skills = dicts
	# ==========================================================================================

	#tourneys,ids,p_info,records,skills = load_db(str(game_idx)+"/"+yearstr)
	#tourneys,ids,p_info,records,skills = load_db(str(game_idx)+"/"+str(year))

	#print(get_result((tourneys,ids,p_info,records),36179,res_filt={'player':1000}))

	#resume = get_resume(dicts,None,tags=['Iago','Jobbo','Jobboman','Crimock','CrimockLyte'])
	#resume = get_resume(dicts,None,tags=['Draxsel','iModerz','TehGuitarLord','Joe-J','San','PikaPika!','K.I.D. Goggles','K.I.D.Goggles','Dom','Fun China'])
	
	#if game_idx == 1:
		#print(tourneys[6076])
		#delete_tourney(dicts,6076)
		#dicts = read_majors(1,2017,base=dicts)
		#tourneys,ids,p_info,records,skills = dicts
		#print(tourneys[5643])
		#print(p_info[5643])
		#print(records[5643])
		#print(records[5643]['paths'])
		#resume = get_resume(dicts,5643)
		#resume = get_resume(dicts,None,tags=['Mang0','Armada','Leffen','Wizzrobe','Rishi','PPMD','Axe','S2J','Zain','n0ne','Mew2King','Hungrybox','Plup','aMSa','SFAT','PewPewU','Swedish Delight'])
		#print_resume(dicts,resume,g_key='player',s_key='event')
	#if game_idx == 3:
		#print(p_info[14514])
		#print(p_info[490223])
		#print(len(get_players_by_region(dicts,'SoCal')))
		#print(get_region(dicts,14514,to_calc=True))
		#resume = get_resume(dicts,14514)
		#print_resume(dicts,resume,g_key='player',s_key='event')
	#disp_all(dicts,key='elo',dispnum=10,min_activity=min_act,tier_tol=-1,plot_skills=False)
	#if game_idx == 1386 or game_idx == 3:
	calc_simbrack(dicts,None,min_req=min_act,max_iter=100,rank_size=1000)

	return True

def main_read():
	set_db_args(args)
	if year_count == 0:
		yearstr = str(year)
	else:
		yearstr = str(year)+'-'+str(year+year_count)
	tourneys,ids,p_info,records,skills = easy_load_db(str(game_idx)+'/'+yearstr)
	tourneys,ids,p_info,records,skills = read_majors(game_idx,year,base=(tourneys,ids,p_info,records,skills))
	for i in range(1,year_count+1):
		tourneys,ids,p_info,records,skills = read_majors(game_idx,year+i,base=(tourneys,ids,p_info,records,skills))

	return tourneys,ids,p_info,records,skills

if __name__ == '__main__':
	main()