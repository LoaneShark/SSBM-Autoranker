## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
#import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
#import json
import argparse
#import shutil
from timeit import default_timer as timer
## UTIL IMPORTS
from db_utils import read_majors,set_db_args,save_db,load_db,delete_tourney
from analysis_utils import *

## TODO: 
##	Shortterm
## 		 - Figure out what to do with the data // what data do we want
## 		 - ignore irrelevant/side/casual/exhibition brackets (like at summit, e.g.)
## 		 - ensure scraper is JUST SINGLES unless otherwise specified
## 		 - use 'state' to check for status of bracket (1: unscheduled, 4: called, 2: in progress, 3: completed)
## 		 - allow analysis_utils to write to file (csv?)
## 		 - error logs
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 		 - Multi-year support
## 		 - GUI/standalone executable tool/webapp
##


# Tourney shitlist:
# 	- Valhalla (no placements for pools)
# 	- DPOTG (redemption ladder)
# 	- Heir 5 (so many side brackets)
# 	- Full Bloom 4 (amateur bracket counts?)


## ARGUMENT PARSING
parser = argparse.ArgumentParser()
parser.add_argument('-v','--verbosity',help='verbosity',default=0)
parser.add_argument('-s','--save',help='save db/cache toggle (default True)',default=True)
parser.add_argument('-l','--load',help='load db/cache toggle (default True)',default=True)
parser.add_argument('-ls','--load_slugs',help='load slugs toggle (default True)',default=True)
parser.add_argument('-ff','--force_first',help='force the first criteria-matching event to be the only event',default=True)
parser.add_argument('-g','--game',help='Melee=1, P:M=2, Wii U=3, 64=4, Ultimate=1386',default=1)
parser.add_argument('-fg','--force_game',help='force the game id to be used, even if not a smash event (cannot scrape)',default=False)
parser.add_argument('-y','--year',help='The year you want to analyze (for ssbwiki List of majors scraper)',default=2018)
parser.add_argument('-t','--teamsize',help='1 for singles bracket, 2 for doubles',default=1)
parser.add_argument('-d','--displaysize',help='lowest placing shown on pretty printer output (or -1 for all entrants)',default=64)
parser.add_argument('-sl','--slug',help='tournament URL slug',default=None)
parser.add_argument('-ss','--short_slug',help='shorthand tournament URL slug',default=None)
parser.add_argument('-p','--print',help='print tournament final results to console as they are read in',default=False)
parser.add_argument('-c','--collect_garbage',help='delete phase data after tournament is done being read in',default=True)
parser.add_argument('-ar','--use_arcadians',help='count arcadian events',default=False)
args = parser.parse_args()

game_idx = int(args.game)
year = int(args.year)
to_load_db = args.load
if args.load == "False":
	to_load_db = False
to_load_slugs = args.load_slugs
if args.load_slugs == "False":
	to_load_slugs = False
maxpl = int(args.displaysize)

def main():
	set_db_args(args)
	tourneys,ids,p_info,records = load_db(game_idx)
	#tourneys,ids,p_info,records = read_majors(game_idx,year)
	#print(list_tourneys((tourneys,ids,p_info,records)))
	tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='don-t-park-on-the-grass-2018-1')
	tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='valhalla')
	tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='heir-5')
	#tourneys,ids,p_info,records = delete_tourney((tourneys,ids,p_info,records),None,slug='full-bloom-4')
	#print(list_tourneys((tourneys,ids,p_info,records)))

	#dicts = delete_tourney((tourneys,ids,p_info,records),None,'valhalla')

	print_event((tourneys,ids,p_info,records),tourneys['slugs']['full-bloom-4'])
	return True

if __name__ == "__main__":
	main()
