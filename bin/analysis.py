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
##	- how do I calculate uncertainty in original winprobs
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
	#resume = get_resume(dicts,[1000,4465,1004])
	#resume = get_resume(dicts,None,tags=['Surfero','kla','ZENT','FriedLizard','Katsu','Bread'])
	#print_resume(dicts,resume,g_key='player',s_key='event')
	#disp_all(dicts,key='elo',dispnum=10,min_activity=min_act,tier_tol=-1,plot_skills=False)
	#if game_idx == 1386 or game_idx == 3:
	
	res = np.empty((9,20),dtype='object')
	opts = np.empty((9,2))
	for ma in range(11,3,-1):
		opt_iter_num = 100		
		for a in range(1,21):
			alpha = 1./float(a)

			start_t = timer()
			iagorank_params = calc_simbrack(dicts,None,min_req=ma,max_iter=500,disp_size=300,print_res=False,plot_ranks=False,alpha=alpha,mode='array')
			runtime = timer()-start_t
			iagoranks,winprobs,sigmoids,data_hist,id_list = iagorank_params
			N = len(id_list)
			iter_num = len(data_hist[id_list[0]])

			if iter_num < opt_iter_num:
				opt_iter_num = iter_num
				opts[ma-3,0] = a
				opts[ma-3,1] = alpha

			if 19554 in data_hist:
				codyhist = data_hist[19554]
			else:
				codyhist = None
			res[ma-3,a-1] = [alpha,N,runtime,iter_num,data_hist[1000],codyhist]

	print(opts)
	#m_hists = []
	#c_hists = []
	# for each N
	for row in res:
		# x = learnrate
		xs = [run[0] for run in row]
		# y = convergence iterations
		ys = [run[3] for run in row]

		# plot their histories
		#m_hist = [run[4] for run in row]
		#m_hists.append(m_hist)
		#c_hist = [run[5] for run in row if run[5] is not None]
		#c_hists.append(c_hist)

		plt.plot(xs,ys,label=row[0][1])
	plt.xlabel('learn rate')
	plt.ylabel('num iterations')
	plt.legend()
	plt.show()
	
	# plot mango history over learnrate (for ma=3)
	for i in range(20):
		#opt_a, opt_learnrate = opts[i,:]
		hist = res[0,i][4]
	plt.title('mang0 history for N: %d'%res[0,0][1])
	plt.xlabel('iteration')
	plt.ylabel('skill_rank')
	plt.legend()
	plt.show()

	# plot cody history over learnrate (for ma=3)
	for i in range(20):
		#opt_a, opt_learnrate = opts[i,:]
		hist = res[0,i][5]
		if hist != None:
			plt.plot(np.linspace(0,len(hist)),hist,label=str(res[0,i][0]))
	plt.title('ibdw history for N: %d'%res[0,0][1])
	plt.xlabel('iteration')
	plt.ylabel('skill_rank')
	plt.legend()
	plt.show()



	to_calc_simbrack = False
	if to_calc_simbrack:
		array_t = timer()
		iagorank_params = calc_simbrack(dicts,None,min_req=min_act,max_iter=100,disp_size=300,print_res=True,plot_ranks=False,mode='array')
		array_time = timer()-array_t
		print('Array time elapsed:','{:.3f}'.format(array_time) + ' s')
		ISR = {'params': iagorank_params}
		save_dict(ISR,'ISR_%d_%d_%d'%(game_idx,year,year_count),None,'..\\lib')
	else:
		iagorank_params = load_dict('ISR_%d_%d_%d'%(game_idx,year,year_count),None,'..\\lib')['params']


	iagoranks,winprobs,sigmoids,data_hist,id_list = iagorank_params
	print('N: %d'%len(id_list))
	iter_num = len(data_hist[id_list[0]])
	#print('Dict time elapsed:','{:.3f}'.format(dict_time) + ' s')

	if game_idx == 1:
		# plot mango
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1000,plot_tags=True)
		plot_hist(data_hist,p_id=1000,plot_delta=True)
		# plot hbox
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1004,plot_tags=True)
		plot_hist(data_hist,p_id=1004,plot_delta=True)
		# plot ibdw
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,19554,plot_tags=True)
		plot_hist(data_hist,p_id=19554,plot_delta=True)
		# plot gahtzu
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1077,plot_tags=True)
		plot_hist(data_hist,p_id=1077,plot_delta=True)
		# plot army
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23458,plot_tags=True)
		plot_hist(data_hist,p_id=23458,plot_delta=True)
		if 1 < 0:
			'''# plot surfero
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,16054,plot_tags=True)
			plot_hist(data_hist,p_id=16054,plot_delta=True)
			# plot ZENT
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,10905,plot_tags=True)
			plot_hist(data_hist,p_id=10905,plot_delta=True)
			# plot Bread
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,597196,plot_tags=True)
			plot_hist(data_hist,p_id=597196,plot_delta=True)
			# plot kla
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,153070,plot_tags=True)
			plot_hist(data_hist,p_id=153070,plot_delta=True)
			# plot FriedLizard
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,262266,plot_tags=True)
			plot_hist(data_hist,p_id=262266,plot_delta=True)
			# plot Katsu
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,126476,plot_tags=True)
			plot_hist(data_hist,p_id=126476,plot_delta=True)'''
			'''# plot Funke Master Flex
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,67075,plot_tags=True)
			plot_hist(data_hist,p_id=67075,plot_delta=True)
			# plot ShineSpike
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,60617,plot_tags=True)
			plot_hist(data_hist,p_id=60617,plot_delta=True)'''

			# plot Offendors
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23466,plot_tags=True)
			plot_hist(data_hist,p_id=23466,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,3939,plot_tags=True)
			plot_hist(data_hist,p_id=3939,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,565971,plot_tags=True)
			plot_hist(data_hist,p_id=565971,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,33499,plot_tags=True)
			plot_hist(data_hist,p_id=33499,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,44674,plot_tags=True)
			plot_hist(data_hist,p_id=44674,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,411867,plot_tags=True)
			plot_hist(data_hist,p_id=411867,plot_delta=True)

			#print([p_id for p_id in id_list if sigmoids[p_id][2] > 1.1])

	if game_idx == 3 or game_idx == 1386:
		# plot void
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,15768,plot_tags=True)
		plot_hist(data_hist,p_id=15768,plot_delta=True)
		# plot larry lurr
		plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23277,plot_tags=True)
		plot_hist(data_hist,p_id=23277,plot_delta=True)
		if game_idx == 1386:
			# plot schrader the toolbag
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,432879,plot_tags=True)
			plot_hist(data_hist,p_id=432879,plot_delta=True)
			# plot calvin
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,6546,plot_tags=True)
			plot_hist(data_hist,p_id=6546,plot_delta=True)
		# plot swedish delight (only for -ma 2)
		if 1055 in id_list:
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1055,plot_tags=True)
			plot_hist(data_hist,p_id=1055,plot_delta=True)
		if 4465 in id_list:
			# plot leffen
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,4465,plot_tags=True)
			plot_hist(data_hist,p_id=4465,plot_delta=True)

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