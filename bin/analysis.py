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

## TODO: 
##	Shortterm
## 		 - Figure out what to do with the data // what data do we want
## 		 - ignore irrelevant/side/casual/exhibition brackets (like at summit, e.g.)
## 		 - ensure scraper is JUST SINGLES unless otherwise specified
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
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

game_idx = args.game
to_load_db = args.load
if args.load == "False":
	to_load_db = False

def main():
	set_db_args(args)
	tourneys,ids,p_info,records = read_majors(args.game,args.year)
	return True

if __name__ == "__main__":
	main()