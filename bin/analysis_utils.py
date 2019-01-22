## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
from statistics import mean 
from math import *
import numpy as np 
#import scipy as sp 
import os,sys,pickle,time
## UTIL IMPORTS
from calc_utils import *
from readin_utils import *

# gets a the "score" for each player, calculated as the average percentage of bracket completed
# (average number of rounds made through the bracket, normalized to [0,1])
def get_scores(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	scores = {}
	for p_id in p_info:
		if p_id in records and is_active(dicts,p_id,min_req=activity):
			scores[p_id] = round(mean([score(dicts,records[p_id]['placings'][t_id],t_id) for t_id in tourneys if type(t_id) is int if t_id in records[p_id]['placings']]),acc)
	if scale_vals:
		maxval = max([scores[p_id] for p_id in scores])
		minval = min([scores[p_id] for p_id in scores])
		for p_id in scores:
			scores[p_id] = round(((scores[p_id] - minval)/(maxval-minval))*10,acc)
	return scores

# displays the above scores for the given number of people
def disp_scores(dicts,dispnum=20,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	scores = get_scores(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],scores[p_id]] for p_id in scores],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_elos(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	elos = {}
	for p_id in p_info:
		if p_id in records and is_active(dicts,p_id,min_req=activity):
			#elos[p_id] = mean([score(dicts,records[p_id]['placings'][t_id],t_id) for t_id in tourneys if type(t_id) is int if t_id in records[p_id]['placings']])
			elos[p_id] = round(p_info[p_id]['elo'],acc)
	if scale_vals:
		maxval = max([elos[p_id] for p_id in elos])
		minval = min([elos[p_id] for p_id in elos])
		for p_id in elos:
			elos[p_id] = round(((elos[p_id] - minval)/(maxval-minval))*10,acc)
	return elos

def disp_elos(dicts,dispnum=20,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	elos = get_elos(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],elos[p_id]] for p_id in elos],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_glickos(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	glickos = {}
	for p_id in p_info:
		if p_id in records and is_active(dicts,p_id,min_req=activity):
			glickos[p_id] = round(p_info[p_id]['glicko'][0],acc)
	if scale_vals:
		maxval = max([glickos[p_id] for p_id in glickos])
		minval = min([glickos[p_id] for p_id in glickos])
		for p_id in glickos:
			glickos[p_id] = round(((glickos[p_id] - minval)/(maxval-minval))*10,acc)
	return glickos

def disp_glickos(dicts,dispnum=20,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	elos = get_glickos(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],glickos[p_id]] for p_id in glickos],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_iagorank(dicts,acc=3,scale_vals=True,activity=3):
	tourneys,ids,p_info,records,skills = dicts
	return True

def get_avg_performances(dicts,acc=3,scale_vals=False):
	tourneys,ids,p_info,records,skills = dicts
	avg_perfs = {}

	for p_id in p_info:
		if p_id in skills['perf']:
		#print(records[p_info])
			perfs = []
			for t_id in skills['perf'][p_id]:
				#print(records[p_id]['performances'])
				perfs.extend([skills['perf'][p_id][t_id]])

			avg_perfs[p_id] = round(mean(perfs),acc)

	if scale_vals:
		maxval = max([avg_perfs[p_id] for p_id in avg_perfs])
		minval = min([avg_perfs[p_id] for p_id in avg_perfs])
		for p_id in avg_perfs:
			avg_perfs[p_id] = round(((avg_perfs[p_id] - minval)/(maxval-minval))*10,acc)

	return avg_perfs

def get_best_performances(dicts,use_names=False,acc=3,scale_vals=False):
	tourneys,ids,p_info,records,skills = dicts
	#print(len(records))
	best_perfs = {}

	for p_id in p_info:
		if p_id in skills['perf'] and not skills['perf'][p_id] == {}:
			#print(p_info[p_id])
			#print(records[p_id])
			#print(skills['elo'][p_id],'\n',skills['glicko'][p_id],'\n',skills['sim'][p_id],'\n',skills['perf'][p_id])
			best = -9999.
			maxperf = [[round(skills['perf'][p_id][t_id],acc),t_id,records[p_id]['placings'][t_id], \
						round(skills['elo_del'][p_id][t_id],acc),round(skills['glicko_del'][p_id][t_id][0],acc)] for t_id in skills['perf'][p_id]]
			#print(skills['perf'][p_id])
			maxperf = sorted(maxperf,key=lambda l: l[0],reverse=True)[0]
			#maxperf = list(maxperf)
			if use_names:
				maxperf[1] = tourneys[maxperf[1]]['name']
				#perfs.extend([records[p_id]['performances'][t_id]])

			best_perfs[p_id] = maxperf
	if scale_vals:
		maxval = max([best_perfs[p_id] for p_id in best_perfs])
		minval = min([best_perfs[p_id] for p_id in best_perfs])
		for p_id in best_perfs:
			best_perfs[p_id] = round(((best_perfs[p_id] - minval)/(maxval-minval))*10,acc)

	return best_perfs

def disp_all(dicts,dispnum=20,key='elo',trans_cjk=True,avg_perf=False,scale_vals=False,min_activity=3,tier_tol=-1,plot_skills=False):
	tourneys,ids,p_info,records,skills = dicts
	key_idx = 1
	if key == 'norm_all':
		scale_vals = True
		key_idx = 1
	elos = get_elos(dicts,scale_vals=scale_vals,activity=min_activity)
	scores = get_scores(dicts,activity=min_activity)
	glickos = get_glickos(dicts,scale_vals=scale_vals,activity=min_activity)
	if avg_perf:
		perfs = get_avg_performances(dicts)
		perfstr = 'Mean Performance'
		perfstr_len = 16
	else:
		perfs = get_best_performances(dicts,use_names=True)
		perfstr = 'Best Performance'
		perfstr_len = 36 + max([len(perfs[p_id][1]) for p_id in perfs])

	if key == 'bracket':
		key_idx = 3
	if key == 'elo':
		key_idx = 1
	if key == 'performance':
		key_idx = 4
	if key == 'simbrac':
		key_idx = None #5
	if key == 'glicko':
		key_idx = 2

	# print block
	print('==========================================================================')
	if key == 'norm_all':
		for p_id in elos:
			elos[p_id] = round((elos[p_id]+glickos[p_id])/2.,3)
		players = sorted([[str(p_info[p_id]['tag']),elos[p_id],scores[p_id],perfs[p_id]] for p_id in p_info if p_id in elos if p_id in scores if p_id in perfs],key=lambda x: x[key_idx],reverse=True)
		print('\n{:<7.7}'.format('Place'),'{:<20.20}'.format('Player'),'{:<18.18}'.format('Combo Score [0,10]'),'{:<9.9}'.format('Mean %'),('{:<%d.%d}'%(perfstr_len,perfstr_len)).format(perfstr),'\n')
	else:
		players = sorted([[str(p_info[p_id]['tag']),elos[p_id],glickos[p_id],scores[p_id],perfs[p_id]] for p_id in p_info if p_id in elos if p_id in scores if p_id in perfs],key=lambda x: x[key_idx],reverse=True)
		print('\n{:<7.7}'.format('Place'),'{:<20.20}'.format('Player'),'{:<9.9}'.format('Elo'),'{:<9.9}'.format('Glicko-2'),'{:<9.9}'.format('Mean %'),('{:<%d.%d}'%(perfstr_len,perfstr_len)).format(perfstr),'\n')
	players = players[:dispnum]
	#print(players)

	#print("\n{:<20.20}".format("Player"),"{:<9.9}".format("Elo"),"{:<9.9}".format("Glicko-2"),"{:<9.9}".format("Mean %"),("{:<%d.%d}"%(perfstr_len,perfstr_len)).format(perfstr),"\n")
	last = None
	rank = 0
	for player in players:
		tagstr_len = 20
		rank += 1
		if tier_tol > 0:
			val = player[key_idx]
			if last != None:
				if abs(last-val) >= tier_tol:
					print('--------------------------------------------------------------------------')
			last = val
		if trans_cjk:
			if has_cjk(player[0]):
				player[0] = '<'+transliterate(player[0])+'>'
		for tag_ch in player[0]:
			if is_emoji(tag_ch):
				tagstr_len -= 1
		if key == 'norm_all':
			print('{:<7.7}'.format(' '+str(rank)),('{:<%s.%s}'%(tagstr_len,tagstr_len)).format(player[0]),'{:<18.18}'.format(str(player[1])), \
				'{:<9.9}'.format(player[2]),('{:<%d.%d}'%(perfstr_len,perfstr_len)).format(str(player[3])))
		else:
			print('{:<7.7}'.format(' '+str(rank)),('{:<%s.%s}'%(tagstr_len,tagstr_len)).format(player[0]),'{:<9.9}'.format(str(player[1])), \
				'{:<9.9}'.format(player[2]),'{:<9.9}'.format(player[3]),('{:<%d.%d}'%(perfstr_len,perfstr_len)).format('['+', '.join(str(s) for s in player[4])+']'))
	if plot_skills:
		N = len(players)
		xs = range(N)
		ys = [player[key_idx] for player in players]
		labels = [player[0] for player in players]

		fig = plt.figure()
		ax = plt.axes()
		ax.plot(xs,ys,'.')
		ax.set(xlabel='Player Rank',ylabel='Player Skill Rating [%s]'%key,title='The Top %d'%N)
		ax.grid()
		plt.show()