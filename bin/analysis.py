## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
from statistics import mean 
from math import *
import numpy as np 
#import scipy as sp 
import os,sys,pickle,time,csv
#import json
import argparse
import configargparse
#import shutil
from timeit import default_timer as timer
## UTIL IMPORTS
from arg_utils import *
from db_utils import *
from dict_utils import *
from calc_utils import *
from analysis_utils import *
from webdb import *
from nn_utils import *

## TODO: 
##	Shortterm
##		HIGH PRIORITY:
## 		 - !!! Finish // smooth out S-Rank !!!
## 		 - add fully offline mode toggle  // prefer offline argument
##		 - fix errors with player ids being inconsistent somehow? (lookin' at you, We Tech Those 3 PM Singles [Pool PMA2])
## 		 - query mode
## 		 - !!!! MIGRATE TO NEW API !!!!
##
##		MEDIUM PRIORITY:
## 		 - Leagues support
## 		 - how to match players that don't have smash.gg accounts/consistent player ids (mostly japanese players)
## 			- also match players that have multiple accounts // remade accounts // use them inconsistently (???)
## 		 - Can we filter out sandbags somehow? intelligent decisionmaking?
## 			- Maybe drop worst N results from each player? does this take away from consistency as a virtue?
## 		 - SKILL TIERSSSSS
## 		 - Fix crashes on repeated web calls
## 		 - Kickscore algorithm/library
##
## 		LOWER PRIORITY:
## 		 - filter out invitationals for certain metrics (like % of bracket complete, etc.)
## 		 - Add support for non-roman scripts (besides japanese)
## 		 - error logs
## 		 - use res_filt format more universally for queries and such // expand get_result
## 		 - General doubles / crews support (see: scraper support/filtering out by event type)
## 			- static team support pls
## 		 - Character data / matchup analysis
## 		    - Weighted by player skill? Does one depend on the other?
## 		 - Upcoming tournament support / preloading
## 		 - Ongoing / Live tournament support 
##
##	Longterm
## 		 - Challonge support (player matching by tag maybe needed -- no player ids provided!)
## 		 - pre-smash.gg era support (see: challonge support)
## 				- wtf do i do about evo's bitch-ass paper brackets
## 		 - allow analysis_utils to write to file for some queries, etc. (csv?)
## 		 - GUI/standalone executable tool/webapp
## 		 - Intelligent clustering of players by region
## 		 - Migrate ML stack from TensorFlow to PyTorch
##

## ELO BALANCING:
##	- debug?
## 		- do invitationals/summit/alternate brackets mess with this?
## 		- what K values to use? 
## 		- how do we instantiate elo scores?
## 			- SSBMRank scores from the previous year? Normal distribution using avg tourney placing?
## 		- decay over time?
## 	- fit Glicko-2 (?)

## SIMRANK TODO:
##  - make it work (lmao)
##	- Fourier analysis ??????
##  - Try doing a two-step fit where first they are blanked to get into the right "bins" of skill, 
## 		and then are measured by bins/running bins? Worth a shot
##  - Display bins (for top 10,20,30 etc // for skill clusters/tiers once decided) on sigrank/winprobs chart

## TOURNEY SHITLIST:
## 	- We Tech Those 3: PM Pool PMA2
##  - The Kid, the Goat, and the Mang0: Ultimate Singles Pool D3
##
##	- DPOTG 2018: Redemption ladder (kinda)
##  - Glitch 6: Event filtering misses Ultimate Singles (but reads in side events instead)
##  - Smash N' Splash 5: Divisions 2&3 marked as exhibition???? why????
## 	- Hyrule Saga: incomplete, top32 full of weird placeholders
##
## 	- Dismantle 2: marked as not yet started
## 	- EVO 2016 Melee Teams: keeps getting checked by other games (and for singles)

## ARGUMENT PARSING
args = get_args()

game_idx = int(args.game)
if args.force_game:
	game_idx = int(args.force_game)
year = int(args.year)
year_count = int(args.year_count)
to_load_db = args.load
to_load_slugs = args.cache_slugs
maxpl = int(args.display_size)
min_act = int(args.min_activity)

def main():
	dicts = main_read()
	tourneys,ids,p_info,records,skills,meta = dicts
	if int(args.verbosity) >= 5:
		print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')

	if False:
		ps = dicts_to_nn(dicts,seed='last')
		main_nn(ps)
		return True

	#if 121567 in tourneys:
	#	print(calc_tourney_stack_score(dicts,121567,plot_res=True))
	# ==========================================================================================

	#tourneys,ids,p_info,records,skills,meta = load_db(str(game_idx)+"/"+yearstr)
	#tourneys,ids,p_info,records,skills,meta = load_db(str(game_idx)+"/"+str(year))

	#print(get_result((tourneys,ids,p_info,records),36179,res_filt={'player':1000}))
	#for p_id in p_info:
	#	p_info[p_id]['srank_sig'] = list(p_info[p_id]['srank_sig'])
	#	skills['srank_sig'][p_id] = list(skills['srank_sig'][p_id])

	#resume = get_resume(dicts,None,tags=['Iago','Jobbo','Jobboman','Crimock','CrimockLyte'])
	#resume = get_resume(dicts,None,tags=['Draxsel','iModerz','TehGuitarLord','Joe-J','San','PikaPika!','K.I.D. Goggles','K.I.D.Goggles','Dom','Fun China'])
	#resume = get_resume(dicts,None,tags=['VoiD','Axe','Iago'])
	resume = get_resume(dicts,None,tags=['Nightmare','N','Mafia','Hyuga','Ally','D1','xD1x','Nairo','Keitaro','Cinnpie','Static Manny','Anti','DJ Nintendo','La Luna'])
	resume = get_resume(dicts,None,tags=['Armada','ZeRo'])
	#print_resume(dicts,resume,g_key='player',s_key='event')
	#print(get_social_media(dicts,1004))
	
	#print_tourney_ratings(dicts)

	#if game_idx == 1:
		#print(tourneys[6076])
		#delete_tourney(dicts,6076)
		#dicts = read_majors(1,2017,base=dicts)
		#tourneys,ids,p_info,records,skills,meta = dicts
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
	#resume = get_resume(dicts,None,tags=['Hungrybox','Mang0','Leffen'])
	#resume = get_resume(dicts,None,tags=['Surfero','kla','ZENT','FriedLizard','Katsu','Bread'])
	#print_resume(dicts,resume,g_key='player',s_key='event')
	#print_resume(dicts,resume,g_key='player',s_key='event')
	#disp_all(dicts,key='elo',dispnum=10,min_activity=min_act,tier_tol=-1,plot_skills=False)
	#if game_idx == 1386 or game_idx == 3:
	if False:
		print('ELO')
		disp_elos(dicts)
		print('GLICKO')
		disp_glickos(dicts)
		print('TRUESKILL')
		disp_trueskills(dicts)
		print('GLIXARE')
		disp_glixares(dicts)
		print('SRANK')
		disp_sranks(dicts)

	if False:
		top100_sranks = sorted([[p_info[p_id]['tag'],p_info[p_id]['srank']] for p_id in p_info if is_active(dicts,p_id)],key=lambda l:l[1])[:100]
		i = 1
		for line in top100_sranks:
			if i >= 100: i_buff = ""
			elif i >= 10: i_buff = " "
			else: i_buff = "  "
			print(''+str(i)+str(i_buff)+str(line))
			i+=1

	# find optimum hyperparameters (higher learnrate is better, >0.2 needed for convergence)
	if False:
		opts = find_opt_hyperparams(dicts,20,9,key_ids=[1000,19554])

	to_calc_sigrank = False
	if to_calc_sigrank:
		array_t = timer()
		if game_idx == 1:
			iagorank_params = calc_sigrank(dicts,min_req=min_act,max_iter=200,learn_decay=True,disp_size=100,verbosity=5,print_res=True,plot_ranks=False,\
				mode='array',seed='average',sig_mode='alt',score_by='intsig',fit_mode='winprobs',\
				alpha=0.5,fit_corners=False,pad_zeros=False,combine_unranked=False)
		else:
			iagorank_params = calc_sigrank(dicts,min_req=min_act,max_iter=1000,learn_decay=True,disp_size=100,verbosity=5,print_res=True,plot_ranks=False,\
				mode='array',seed='blank',sig_mode='alt',score_by='intsig',fit_mode='winprobs')
		array_time = timer()-array_t
		print('Sigrank calc time elapsed:','{:.3f}'.format(array_time) + ' s')
		ISR = {'params': iagorank_params}
		save_dict(ISR,'ISR_'+generate_db_str(),None,'..\\lib')
	else:
		iagorank_param_dict = load_dict('ISR_'+generate_db_str(),None,'..\\lib')
		if 'params' in iagorank_param_dict:
			iagorank_params = iagorank_param_dict['params']
		else:
			iagorank_params = None

	if False:
		iagoranks,winprobs,sigmoids,data_hist,id_list = iagorank_params
		print('N: %d'%len(id_list))
		if v >= 4:
			if not to_calc_sigrank or to_calc_sigrank:
				charmap = load_dict('characters',None,'..\\lib')
				if game_idx in charmap:
					charmap = charmap[game_idx]
				else:
					charmap = {}
				charmap[''] = ''
				i = 1
				print('Rank | Tag        Avg  Int  Y-0  Split   p_id   N    Main')
				data_res = [[iagoranks[p_id][0],round((iagoranks[p_id][2]+iagoranks[p_id][1])/2.,3),round(iagoranks[p_id][1],3),round(iagoranks[p_id][2],3),round(iagoranks[p_id][2]-iagoranks[p_id][1],3),p_id,len([opp_id for opp_id in winprobs[p_id]]),charmap[get_main(p_id,p_info)]] for p_id in id_list]
				for line in sorted(data_res,key=lambda l: l[2])[:100]:
					print('{:>3.3}'.format(str(i)),'|','  '.join([str(item) for item in line]))
					if True and i <= 5:
						plot_winprobs(iagoranks,winprobs,sigmoids,id_list,line[5],plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
						plot_hist(data_hist,p_id=line[5],plot_delta=True)
					i += 1
					#print(line.join(' '))
		iter_num = len(data_hist[id_list[0]])
		#print('Dict time elapsed:','{:.3f}'.format(dict_time) + ' s')
		if game_idx == 1 and False:
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1004,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=1004,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,4692,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=4692,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1037,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=1037,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,16393,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=16393,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,4127,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=4127,plot_delta=True)

			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,6189,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=6189,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,16342,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=16342,plot_delta=True)
			plot_winprobs(iagoranks,winprobs,sigmoids,id_list,32097,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
			plot_hist(data_hist,p_id=32097,plot_delta=True)
			if 1 < 0:
				# plot mango
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1000,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=1000,plot_delta=True)
				# plot hbox
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1004,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=1004,plot_delta=True)
				# plot ibdw
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,19554,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=19554,plot_delta=True)
				# plot gahtzu
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1077,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=1077,plot_delta=True)
				# plot jerry
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,32097,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=32097,plot_delta=True)
				# plot absentpage
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,37339,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=37339,plot_delta=True)
				# plot trif
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,22900,plot_tags=True,sig_mode='alt')
				plot_hist(data_hist,p_id=22900,plot_delta=True)
				if 1 < 0:
					# plot dizz
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,3915,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=3915,plot_delta=True)
					# plot colbol
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1009,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=1009,plot_delta=True)
					# plot surfero
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,16054,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=16054,plot_delta=True)
					# plot ZENT
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,10905,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=10905,plot_delta=True)
					# plot Mova
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,6176,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=6176,plot_delta=True)
					# plot Jagerbombsoldier
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,6653,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=6653,plot_delta=True)
					# plot AKO
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,19677,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=19677,plot_delta=True)
					# plot Neeco
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23466,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=23466,plot_delta=True)
					# plot Loscar
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,44674,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=44674,plot_delta=True)
					'''# plot Funke Master Flex
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,67075,plot_tags=True)
					plot_hist(data_hist,p_id=67075,plot_delta=True)
					# plot ShineSpike
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,60617,plot_tags=True)
					plot_hist(data_hist,p_id=60617,plot_delta=True)'''
					'''
					# plot Offendors
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23466,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=23466,plot_delta=True)
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,3939,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=3939,plot_delta=True)
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,565971,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=565971,plot_delta=True)
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,33499,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=33499,plot_delta=True)
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,44674,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=44674,plot_delta=True)
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,411867,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=411867,plot_delta=True)'''

					#print([p_id for p_id in id_list if sigmoids[p_id][2] > 1.1])


		#if (game_idx == 3 or game_idx == 1386):
		if game_idx == 1386 and False:
			#running_winprobs(iagoranks,winprobs,7648)
			#running_winprobs(iagoranks,winprobs,15768)
			#running_winprobs(iagoranks,winprobs,57924)
			#running_winprobs(iagoranks,winprobs,65445)
			#running_winprobs(iagoranks,winprobs,4465)

			if 1 > 0:
				# plot samsora
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,7648,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
				plot_hist(data_hist,p_id=7648,plot_delta=True)
				# plot tweek
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,15768,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
				plot_hist(data_hist,p_id=15768,plot_delta=True)
				# plot larry lurr
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,23277,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
				plot_hist(data_hist,p_id=23277,plot_delta=True)
				# plot nairo
				plot_winprobs(iagoranks,winprobs,sigmoids,id_list,16104,plot_tags=True,sig_mode='alt',plot_running_sigmoid=True)
				plot_hist(data_hist,p_id=16104,plot_delta=True)
				if game_idx == 1386:
					# plot radda radda
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,65445,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=65445,plot_delta=True)
					# plot schrader the toolbag
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,432879,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=432879,plot_delta=True)
					# plot blank
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,57924,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=57924,plot_delta=True)
				# plot swedish delight (only for -ma 2)
				if 1055 in id_list:
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,1055,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=1055,plot_delta=True)
				if 4465 in id_list:
					# plot leffen
					plot_winprobs(iagoranks,winprobs,sigmoids,id_list,4465,plot_tags=True,sig_mode='alt')
					plot_hist(data_hist,p_id=4465,plot_delta=True)

		#return True

	if args.web_upload:

		db_str_key = generate_db_str()
		update_db(dicts,db_str_key,force_update=True)
	#update_db(dicts,db_str_key,force_update=False)


	if args.character_matchups:
		generate_matchup_chart(dicts,game_idx,year,year_count,id_list=id_list,label_mode='ones',v=int(args.verbosity),infer_characters=True,n_bins=10000)
	
	if args.make_tier_list:
		tl = generate_tier_list(dicts,game_idx,year,year_count,id_list=id_list)
		for line in tl:
			print(line)

def main_read():
	verstr = get_db_verstr()
	tourneys,ids,p_info,records,skills,meta = easy_load_db(verstr)
	preprocess((tourneys,ids,p_info,records,skills,meta))

	tourneys,ids,p_info,records,skills,meta = read_year(game_idx,year,base=(tourneys,ids,p_info,records,skills,meta))
	for i in range(1,year_count+1):
		if i == year_count:
			#tourneys,ids,p_info,records,skills,meta = read_year(game_idx,year+i,base=(tourneys,ids,p_info,records,skills,meta),to_update_socials=True)
			tourneys,ids,p_info,records,skills,meta = read_year(game_idx,year+i,base=(tourneys,ids,p_info,records,skills,meta))
		else:
			tourneys,ids,p_info,records,skills,meta = read_year(game_idx,year+i,base=(tourneys,ids,p_info,records,skills,meta))

	if game_idx == 1386:
		filename = 'ultimate_mains.csv'
	elif game_idx == 1:
		filename = 'melee_mains.csv'
	if game_idx in [1386,1]:
		print('Importing %s mains~'%filename.split('_')[0])
		chardata = load_dict('characters',None,'../lib')[game_idx]
		reverse_charmap = {chardata[key]: key for key in chardata}
		with open('../lib/%s'%filename) as filedata:
			main_reader = csv.reader(filedata)
			for line in main_reader:
				if len(line) > 3:
					if line[3] not in ['',' ',',',None,'None']:
						charname = line[3]
						char_id = reverse_charmap[charname]
						p_id = int(line[2])
						if p_id in p_info:
							if 'characters' in p_info[p_id]:
								if sum(p_info[p_id]['characters'][char_id]) <= 0 or p_info[p_id]['characters'][char_id] is None:
									p_info[p_id]['characters'][char_id][0] += 10
									p_info[p_id]['characters'][char_id][1] += 10
						else:
							print(p_id,'-',p_id in p_info.keys())

	return tourneys,ids,p_info,records,skills,meta

def preprocess(dicts):
	tourneys,ids,p_info,records,skills,meta = dicts

	# update character list in case of DLC
	if True and game_idx in [1386,24,5]:

		chardict = load_dict('characters',None,loc='../lib')

		if game_idx in chardict:
			for abs_id in p_info:
				for char_id in chardict[game_idx]:
					if char_id not in p_info[abs_id]['characters']:
						p_info[abs_id]['characters'][char_id] = [0,0]

	# sanitize current dicts for web upload
	if False:
		for abs_id in p_info:
			#print(p_info[abs_id]['trueskill'])
			if type(p_info[abs_id]['trueskill']) is not dict:
				p_info[abs_id]['trueskill'] = {'mu': p_info[abs_id]['trueskill'].mu, 'sigma': p_info[abs_id]['trueskill'].sigma}
			if type(p_info[abs_id]['trueskill_peak']) is not dict:
				p_info[abs_id]['trueskill_peak'] = {'mu': p_info[abs_id]['trueskill']['mu'], 'sigma': p_info[abs_id]['trueskill']['sigma']}
				if 'expose' in p_info[abs_id]['trueskill']:
					p_info[abs_id]['trueskill_peak']['expose'] = float(p_info[abs_id]['trueskill']['expose'])
				else:
					p_info[abs_id]['trueskill_peak']['expose'] = float(0.)

			p_info[abs_id]['glixare'] = float(p_info[abs_id]['glixare'])
			p_info[abs_id]['glixare_peak'] = float(p_info[abs_id]['glixare_peak'])
			p_info[abs_id]['srank_peak'] = float(p_info[abs_id]['srank_peak'])
			p_info[abs_id]['trueskill_peak'] = {key: float(p_info[abs_id]['trueskill_peak'][key]) for key in p_info[abs_id]['trueskill_peak']}

		verstr = get_db_verstr()
		save_dict(p_info,'p_info',verstr)
		save_dict(skills,'skills',verstr)

	## delete sns 5
	#delete_tourney((tourneys,ids,p_info,records,skills,meta),72577)

	return dicts

def find_opt_hyperparams(dicts,a_rng=20,ma_rng=9,plot_res=True,key_ids=[1000]):
	tourneys,ids,p_info,records,skills,meta = dicts

	#a_rng = 2
	#ma_rng = 2
	#a_rng = 20
	#ma_rng = 9
	res = np.empty((ma_rng,a_rng),dtype='object')
	opts = np.empty((ma_rng,2))
	for ma in range(11,11-ma_rng,-1):
		opt_iter_num = 100		
		for a in range(1,a_rng+1):
			alpha = 1./float(a)

			start_t = timer()
			iagorank_params = calc_simbrack(dicts,None,min_req=ma,max_iter=500,disp_size=100,print_res=False,plot_ranks=False,alpha=alpha,mode='array')
			runtime = timer()-start_t
			iagoranks,winprobs,sigmoids,data_hist,id_list = iagorank_params
			N = len(id_list)
			iter_num = len(data_hist[id_list[0]])

			if iter_num < opt_iter_num:
				opt_iter_num = iter_num
				#opts[ma-3,0] = a
				#opts[ma-3,1] = alpha
				opts[ma-(12-ma_rng),0] = a
				opts[ma-(12-ma_rng),1] = alpha

			#if 19554 in data_hist:
			#	codyhist = data_hist[19554]
			#else:
				#codyhist = None
			#res[ma-3,a-1] = [alpha,N,runtime,iter_num,data_hist[1000],codyhist]
			res[ma-(12-ma_rng),a-1] = [alpha,N,runtime,iter_num,{p_id: data_hist[p_id] if p_id in data_hist else None for p_id in key_ids}]

	#m_hists = []
	#c_hists = []
	# for each N
	#for row in res:
	if plot_res:
		for i in range(ma_rng):
			# x = learnrate
			#print(res[i])
			#print(res[i,:])
			xs = [run[0] for run in res[i,:]]
			# y = convergence iterations
			ys = [run[3] for run in res[i,:]]

			# plot their histories
			#m_hist = [run[4] for run in row]
			#m_hists.append(m_hist)
			#c_hist = [run[5] for run in row if run[5] is not None]
			#c_hists.append(c_hist)

			plt.plot(xs,ys,label=str(res[i,0][1]))
		plt.xlabel('learn rate')
		plt.ylabel('num iterations')
		plt.legend(title='N')
		plt.show()
	
		# plot designated key players skill fitting
		for key_id in key_ids:
			for i in range(a_rng):
				#opt_a, opt_learnrate = opts[i,:]
				hist = res[0,i][4][key_id]
				if type(hist) != type(None) and len(hist) > 0:
					plt.plot(range(len(hist)),hist,label=str(res[0,i][0]))
			plt.title('%s history for N: %d'%(p_info[key_id]['tag'],res[0,0][1]))
			plt.xlabel('iteration')
			plt.ylabel('skill_rank')
			plt.legend(title='learn rate')
			plt.show()

	print(opts)

	return opts

if __name__ == '__main__':
	main()