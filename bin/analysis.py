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
from db_utils import read_majors,set_db_args,save_db,load_db
from analysis_utils import *

## TODO: 
##	Shortterm
## 		 - Figure out what to do with the data // what data do we want
## 		 - ignore irrelevant/side/casual/exhibition brackets (like at summit, e.g.)
## 		 - ensure scraper is JUST SINGLES unless otherwise specified
## 		 - support for ladders (DPOTG redemption ladder?)
## 		 - groupTypeId and state should be used? -- account for really weird bracket structure? (DPOTG18)
## 		 - allow analysis_utils to write to file (csv?)
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 		 - Multi-year support
##

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

game_idx = int(args.game)
year = int(args.year)
to_load_db = args.load
if args.load == "False":
	to_load_db = False
maxpl = int(args.displaysize)

def main():
	set_db_args(args)
	tourneys,ids,p_info,records = read_majors(game_idx,year)
	#tourneys,ids,p_info,records = load_db(game_idx)
	print_id = tourneys['slugs'][args.slug]
	print_result((tourneys,ids,p_info,records),print_id,res_filt={'maxplace':64,'place':5})
	return True

if __name__ == "__main__":
	main()