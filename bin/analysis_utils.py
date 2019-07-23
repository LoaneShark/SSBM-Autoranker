## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from statistics import mean 
from math import *
import numpy as np 
from six.moves.urllib.request import urlopen
#import scipy as sp 
import os,sys,pickle,time
## UTIL IMPORTS
from arg_utils import *
from calc_utils import *
from readin_utils import *
from dict_utils import *
from db_utils import load_db_sets,easy_load_db_sets

# gets a the "score" for each player, calculated as the average percentage of bracket completed
# (average number of rounds made through the bracket, normalized to [0,1])
def get_scores(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
	scores = {}
	for p_id in p_info:
		if p_id in records and is_active(dicts,p_id,min_req=activity):
			scores[p_id] = round(mean([score(dicts,records[p_id]['placings'][t_id]['placing'],t_id) for t_id in tourneys if type(t_id) is int if tourneys[t_id]['active'] if t_id in records[p_id]['placings']]),acc)
	if scale_vals:
		maxval = max([scores[p_id] for p_id in scores])
		minval = min([scores[p_id] for p_id in scores])
		for p_id in scores:
			scores[p_id] = round(((scores[p_id] - minval)/(maxval-minval))*10,acc)
	return scores

# displays the above scores for the given number of people
def disp_scores(dicts,dispnum=20,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
	scores = get_scores(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],scores[p_id]] for p_id in scores],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_elos(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
	elos = {}
	for p_id in p_info:
		if p_id in records and is_active(dicts,p_id,min_req=activity):
			#elos[p_id] = mean([score(dicts,records[p_id]['placings'][t_id]['placing'],t_id) for t_id in tourneys if type(t_id) is int if tourneys[t_id]['active'] if t_id in records[p_id]['placings']])
			elos[p_id] = round(p_info[p_id]['elo'],acc)
	if scale_vals:
		maxval = max([elos[p_id] for p_id in elos])
		minval = min([elos[p_id] for p_id in elos])
		for p_id in elos:
			elos[p_id] = round(((elos[p_id] - minval)/(maxval-minval))*10,acc)
	return elos

def disp_elos(dicts,dispnum=20,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
	elos = get_elos(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],elos[p_id]] for p_id in elos],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_glickos(dicts,acc=3,scale_vals=False,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
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
	tourneys,ids,p_info,records,skills,meta = dicts
	elos = get_glickos(dicts,scale_vals=scale_vals,activity=activity)

	players = sorted([[p_info[p_id]['tag'],glickos[p_id]] for p_id in glickos],key=lambda x: x[1],reverse=True)
	players = players[:dispnum]
	for player in players:
		print(player)

def get_iagorank(dicts,acc=3,scale_vals=True,activity=3):
	tourneys,ids,p_info,records,skills,meta = dicts
	return True

def get_avg_performances(dicts,acc=3,scale_vals=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	avg_perfs = {}

	for p_id in p_info:
		if p_id in skills['perf']:
		#print(records[p_info])
			perfs = []
			for t_id in skills['perf'][p_id] :
				if tourneys[t_id]['active']:
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
	tourneys,ids,p_info,records,skills,meta = dicts
	#print(len(records))
	best_perfs = {}

	for p_id in p_info:
		if p_id in skills['perf'] and not skills['perf'][p_id] == {}:
			#print(p_info[p_id])
			#print(records[p_id])
			#print(skills['elo'][p_id],'\n',skills['glicko'][p_id],'\n',skills['sim'][p_id],'\n',skills['perf'][p_id])
			best = -9999.
			maxperf = [[round(skills['perf'][p_id][t_id],acc),t_id,records[p_id]['placings'][t_id]['placing'], \
						round(skills['elo_del'][p_id][t_id],acc),round(skills['glicko_del'][p_id][t_id][0],acc)] for t_id in skills['perf'][p_id] if tourneys[t_id]['active']]
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

def generate_matchup_chart(dicts,game,year,year_count=0,id_list=None,winprobs=None,skill_weight=False,v=0,n_bins=20000,\
							infer_characters=False,label_mode='tens',use_icons=False,prune_sparse=True,save_figure=False,plot_fails=False):
	tourneys,ids,p_info,records,skills,meta = dicts
	if id_list == None:
		id_list = [p_id for p_id in records]
	if label_mode not in ['ones','fives','tens','split']:
		label_mode = 'tens'
	yc_str = ''
	if year_count > 0:
		yc_str += '-'+str(year+year_count)
	sets = easy_load_db_sets(ver=str(game)+'/'+str(year)+yc_str)
	checked_sets = []

	chars = load_dict('characters',None,'../lib')[int(game)]
	char_n = len(chars.keys())
	char_labels = np.array([chars[char_id] for char_id in chars],dtype='object')
	# for skill-difference, 10-50k bins is ideal
	##n_bins = 50000
	print(len(char_labels))
	#return True
	char_id_map = {c_id: i for i,c_id in enumerate([char_id for char_id in chars])}
	if use_icons:
		icons = load_dict('character_icons',None,'../lib')[int(game)]
		#char_icons = np.array([icons[char_id] for char_id in chars],dtype='object')
		char_icons = np.array([mpimg.imread('../lib/todd2.jpg') for char_id in chars],dtype=object)
		#plt.imshow(char_icons[0])
		#plt.show()

	if v >= 1:
		print('Generating Matchup chart (N: %d)...'%char_n)
	# scan all relevant sets and import character data where available
	char_h2h = np.full((char_n,char_n,n_bins+1),None,dtype='object')
	if v >= 4:
		print('Importing game results (%d bins)...'%n_bins)
	for p_id in id_list:
		p_skill = p_info[p_id]['srank']
		p_sets = records[p_id]['set_history']
		for set_id in p_sets:
			if set_id not in checked_sets:
				checked_sets.extend([set_id])
				t_id = sets[set_id]['t_id']
				if 'games' in sets[set_id]:
					for game_id in sets[set_id]['games']:
						g_w_id = sets[set_id]['games'][game_id]['w_id']
						g_l_id = sets[set_id]['games'][game_id]['l_id']
						if g_w_id is not None and g_l_id is not None:
							w_skill = 1.-p_info[g_w_id]['srank']
							l_skill = 1.-p_info[g_l_id]['srank']
							# scale skill ratio so that even skilled players ~ 0.5, still in [0,1]
							w_skill_bin = int(((w_skill-l_skill)/2. + 0.5)*n_bins)
							l_skill_bin = int(((l_skill-w_skill)/2. + 0.5)*n_bins)
							if 'characters' in sets[set_id]['games'][game_id]:
								if sets[set_id]['games'][game_id]['characters'] != {}:
									if g_w_id != None and g_l_id != None:
										g_w_char_id = char_id_map[sets[set_id]['games'][game_id]['characters'][g_w_id]]
										g_l_char_id = char_id_map[sets[set_id]['games'][game_id]['characters'][g_l_id]]
							elif infer_characters:
								g_w_main = get_main(g_w_id,p_info)
								g_l_main = get_main(g_l_id,p_info)
								if not (g_w_main == '' or g_l_main == ''):
									g_w_char_id = char_id_map[g_w_main]
									g_l_char_id = char_id_map[g_l_main]
							else:
								g_w_char_id = None; g_l_char_id = None
							if g_w_char_id is not None and g_l_char_id is not None:
								if char_h2h[g_w_char_id,g_l_char_id,w_skill_bin] == None:
									char_h2h[g_w_char_id,g_l_char_id,w_skill_bin] = [0,0]
								if char_h2h[g_l_char_id,g_w_char_id,l_skill_bin] == None:
									char_h2h[g_l_char_id,g_w_char_id,l_skill_bin] = [0,0]
								char_h2h[g_w_char_id,g_l_char_id,w_skill_bin][0] += 1
								char_h2h[g_l_char_id,g_w_char_id,l_skill_bin][1] += 1
							if v >= 7:
								if l_skill-w_skill < -0.75:
									print(w_skill)
									print(l_skill)
									print('UPSET: %s (%s) over %s (%s) at %s'%(p_info[g_w_id]['tag'],char_labels[g_w_char_id],p_info[g_l_id]['tag'],char_labels[g_l_char_id],tourneys[t_id]['name']))
				# if no game data is reported
				else:
					if not (sets[set_id]['w_dq'] or sets[set_id]['l_dq'] or sets[set_id]['is_bye']):
						s_w_id = sets[set_id]['w_id']
						s_l_id = sets[set_id]['l_id']
						w_skill = 1.-p_info[s_w_id]['srank']
						l_skill = 1.-p_info[s_l_id]['srank']
						# scale skill ratio so that even skilled players ~ 0.5, still in [0,1]
						w_skill_bin = int(((w_skill-l_skill)/2. + 0.5)*n_bins)
						l_skill_bin = int(((l_skill-w_skill)/2. + 0.5)*n_bins)

						s_w_main = get_main(s_w_id,p_info)
						s_l_main = get_main(s_l_id,p_info)
						if not (s_w_main == '' or s_l_main == ''):
							s_w_char_id = char_id_map[s_w_main]
							s_l_char_id = char_id_map[s_l_main]
						else:
							s_w_char_id = None; s_l_char_id = None
						if s_w_char_id is not None and s_l_char_id is not None:
							if char_h2h[s_w_char_id,s_l_char_id,w_skill_bin] == None:
								char_h2h[s_w_char_id,s_l_char_id,w_skill_bin] = [0,0]
							if char_h2h[s_l_char_id,s_w_char_id,l_skill_bin] == None:
								char_h2h[s_l_char_id,s_w_char_id,l_skill_bin] = [0,0]
							char_h2h[s_w_char_id,s_l_char_id,w_skill_bin][0] += 1
							char_h2h[s_l_char_id,s_w_char_id,l_skill_bin][1] += 1

	if v >= 4:
		print('Calculating win probabilities...')
	# change h2h records to win probabilities in [0,1]
	for char_idx in range(char_n):
		for opp_idx in range(char_n):
			for bin_id in range(n_bins+1):
				#n_games = char_h2h[char_idx,opp_idx]+char_h2h[opp_idx,char_idx]
				if char_h2h[char_idx,opp_idx,bin_id] == None:
					n_games = 0
				else:
					n_games = sum(char_h2h[char_idx,opp_idx,bin_id])
				if n_games <= 0:
					char_h2h[char_idx,opp_idx,bin_id] = -1.
					#char_h2h[opp_idx,char_idx,bin_id] = char_h2h[char_idx,opp_idx,bin_id]
					m_sigma = 0.
				else:
					char_h2h[char_idx,opp_idx,bin_id] = char_h2h[char_idx,opp_idx,bin_id][0] / n_games
					#char_h2h[opp_idx,char_idx,bin_id] = 1. - char_h2h[char_idx,opp_idx,bin_id]
					if n_games <= 2:
						m_sigma = 0.8
					else:
						m_sigma = 1./log(float(n_games),2)
				# store ratio as 2-long list with uncertainty
				char_h2h[char_idx,opp_idx,bin_id] = [char_h2h[char_idx,opp_idx,bin_id],m_sigma]
	if plot_fails:
		if v >= 6:
			print('Creating dict...')
		# copy into dict format (for plotting winprobs/sigmoids)
		char_h2h_dict = {char_idx: {opp_idx: {bin_id: char_h2h[char_idx,opp_idx,bin_id][0] for bin_id in range(n_bins+1) if char_h2h[char_idx,opp_idx,bin_id] != None} \
									for opp_idx in range(char_n)} \
									for char_idx in range(char_n)}
	if v >= 4:
		print('Fitting sigmoids...')
	char_matchups = np.zeros((char_n,char_n))
	char_sigs = np.full((char_n,char_n),None,dtype='object')
	for char_idx in range(char_n):
		for opp_idx in range(char_n):
			xs = [0.,1.]
			ys = [0.,1.]
			ss = [0.75,0.75]
			for bin_id in range(n_bins+1):
				ratio = char_h2h[char_idx,opp_idx,bin_id][0]
				if ratio >= 0.:
					xs.append(float(bin_id+0.5)/float(n_bins))
					ys.append(ratio)
					ss.append(char_h2h[char_idx,opp_idx,bin_id][1])
				# remove sigmas from winprobs array so that it can be passed to plot_winprobs
				char_h2h[char_idx,opp_idx,bin_id] = float(bin_id)/float(n_bins)

			# fit sigmoid for each character matchup across their histogram
			# must have more than 3 bins
			if len(xs) > 5:
				x = np.array(xs)
				y = np.array(ys)
				s = np.array(ss)

				v_b = get_fitsig_bounds(g=True)
				p0 = get_fitsig_guesses(g=True)
				try:
					p,cov = sp.optimize.curve_fit(alt_sigmoid,x,y,p0=p0,sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf',tr_solver='lsmr')

					char_matchups[char_idx,opp_idx] = integrate_alt_sigmoid([p],n_bins)[0]
					char_sigs[char_idx,opp_idx] = p
				except RuntimeError:
					if plot_fails:
						plot_winprobs(char_h2h[char_idx][opp_idx],char_h2h_dict[char_idx],None,range(n_bins+1),opp_idx,plot_rank=False,plot_sigmoid=False,char_data=(char_idx,char_labels),mode='array',sig_mode='alt')
					##plot_winprobs(char_h2h[char_idx],char_h2h_dict[char_idx],None,range(n_bins+1),char_idx,plot_rank=False,plot_sigmoid=False,mode='array',sig_mode='alt')
					char_matchups[char_idx,opp_idx] = -1.
					if v >= 6:
						print('Ejecting: [%s v %s] due to inability to fit sigmoid (N = %d)'%(char_labels[char_idx],char_labels[opp_idx],len(xs)))
			else:
				char_matchups[char_idx,opp_idx] = -1.
				if v >= 8:
					print('Ejecting: [%s v %s] due to insufficient data points (N = %d)'%(char_labels[char_idx],char_labels[opp_idx],len(xs)))

	
							#  peach/fox     falco/fox    fox/puff   fox dittos
	'''for char_idx,opp_idx in [(5,17),(17,5), (4,5),(5,4), (5,8),(8,5), (5,5)]:
		plot_matchup_sig = True
		if char_sigs[char_idx,opp_idx] is None:
			plot_matchup_sig = False
		plot_winprobs(char_h2h[char_idx][opp_idx],char_h2h_dict[char_idx],char_sigs[char_idx],range(n_bins+1),opp_idx,plot_rank=False,plot_sigmoid=plot_matchup_sig,char_data=(char_idx,char_labels),mode='array',sig_mode='alt')
	'''

	# prune out unwanted characters (not enough data to rank) (toggleable)
	if prune_sparse:
		#remove zero rows & columns from the chart
		char_labels = char_labels[~np.all(char_matchups == -1.,axis=1)]
		if use_icons:
			char_icons = char_icons[~np.all(char_matchups == -1.,axis=1)]
		char_matchups = char_matchups[~np.all(char_matchups == -1.,axis=1)]
		char_matchups = char_matchups[:, ~np.all(char_matchups == -1.,axis=0)]
		char_n = char_matchups.shape[0]

	## create plot
	if v >= 3:
		print(char_matchups.shape)
	fig,ax = plt.subplots(1,1)
	ax.matshow(char_matchups)
	## set labels and icons
	#ax.set_xticks(np.arange(char_n))
	#ax.set_yticks(np.arange(char_n))
	#ax.set_xticklabels(char_labels)
	#ax.set_yticklabels(char_labels)
	#plt.setp(ax.get_xticklabels(), rotation=45, ha='right', rotation_mode='anchor')
	plt.xticks(np.arange(char_n),char_labels,rotation='vertical')
	plt.yticks(np.arange(char_n),char_labels,rotation='horizontal')
	plt.gca().xaxis.tick_bottom()
	## annotate data
	for i in range(char_n):
		for j in range(char_n):
			if char_matchups[i,j] >= 0.:
				mu = round(100.*char_matchups[i, j])
				if label_mode == 'tens':
					# round to nearest multiple of 10 (display tens digit only)
					mu = round(mu/10.)
				if label_mode == 'fives':
					# round to nearest multiple of 5
					mu_t = floor(mu/10.)
					mu_o = mu-10.*mu_t
					if mu_o <= 2.5:
						mu_o = 0
					elif mu_o <= 7.5:
						mu_o = 5
					else:
						mu_o = 0
						mu_t += 1
					mu = mu_t*10 + mu_o
				if label_mode == 'split':
					# round to MU splits (0 is even, +1/-1 ~ 60/40, +2/-2 ~ 70/30, etc.)
					mu = round(mu/10.) - 5
				text = ax.text(j, i, int(mu), ha='center', va='center')
	# plot stock icons instead of character names
	if use_icons:
		img_ax = []
		xl, yl, xh, yh = np.array(ax.get_position()).ravel()
		#print(xl, yl, xh, yh)
		for i in range(char_n):
			w = xh-xl
			h = yh-yl
			xp = xl+w*(float(i)/float(char_n))
			#print(xp)
			size = 0.05

			img_ax.append(fig.add_axes([xp-size*0.5, yh, size, size]))
			img_ax[i].axison = False
			im_i = plt.imshow(char_icons[i],transform=ax.transAxes)

			#i += 1

	plt.title('Matchup chart for %s'%load_dict('videogames',None,'../lib')[int(game)]['displayName'])
	plt.xlabel('Defender')
	plt.ylabel('Attacker')
	#fig.tight_layout()
	if save_figure:
		plt.savefig('../lib/%s_matchups.png'%str(game))
	plt.show()

def generate_tier_list(dicts,game,year,year_count,id_list=None,skill_weight=True,use_icons=True):
	tourneys,ids,p_info,records,skills,meta = dicts
	if id_list == None:
		id_list = [p_id for p_id in records]
	yc_str = ''
	if year_count > 0:
		yc_str += '-'+str(year+year_count)
	# load set results
	sets = easy_load_db_sets(ver=str(game)+'/'+str(year)+yc_str)

	# load character data
	chars = load_dict('characters',None,'../lib')[int(game)]
	char_n = len(chars.keys())
	char_labels = np.array([chars[char_id] for char_id in chars],dtype='object')
	char_id_map = {c_id: i for i,c_id in enumerate([char_id for char_id in chars])}
	if use_icons:
		icons = load_dict('character_icons',None,'../lib')[int(game)]
		char_icons = np.array([icons[char_id] for char_id in chars],dtype='object')
		#char_icons = np.array([mpimg.imread('../lib/todd2.jpg') for char_id in chars],dtype=object)

	n_bins = 50
	char_h2h = np.zeros((char_n,n_bins+1))
	char_h2h = np.full_like(char_h2h,None,dtype='object')

	# import set results, record w/l record for each character as a function of opponent skill
	for set_id in sets:
		if 'games' in sets[set_id]:
			for game_id in sets[set_id]['games']:
				if 'characters' in sets[set_id]['games'][game_id]:
							if sets[set_id]['games'][game_id]['characters'] != {}:
								t_id = sets[set_id]['t_id']
								g_w_id = sets[set_id]['games'][game_id]['w_id']
								g_l_id = sets[set_id]['games'][game_id]['l_id']
								if g_w_id != None and g_l_id != None:
									g_w_char_id = char_id_map[sets[set_id]['games'][game_id]['characters'][g_w_id]]
									g_l_char_id = char_id_map[sets[set_id]['games'][game_id]['characters'][g_l_id]]
									w_skill_bin = int(p_info[g_w_id]['iagorank'] * n_bins)
									l_skill_bin = int(p_info[g_l_id]['iagorank'] * n_bins)
									if char_h2h[g_w_char_id,l_skill_bin] == None:
										char_h2h[g_w_char_id,l_skill_bin] = [0,0]
									if char_h2h[g_l_char_id,w_skill_bin] == None:
										char_h2h[g_l_char_id,w_skill_bin] = [0,0]
									char_h2h[g_w_char_id,l_skill_bin][0] += 1
									char_h2h[g_l_char_id,w_skill_bin][1] += 1

	# change all h2h records to be win probabilities in [0,1], stored as tuples alongside their uncertainty
	for char_idx in range(char_n):
		for opp_bin in range(n_bins+1):
			if char_h2h[char_idx,opp_bin] != None:
				ratio = float(char_h2h[char_idx,opp_bin][0])/float(char_h2h[char_idx,opp_bin][0]+char_h2h[char_idx,opp_bin][1])
				char_h2h[char_idx,opp_bin] = [ratio,1./log(float(char_h2h[char_idx,opp_bin][0]+char_h2h[char_idx,opp_bin][1]),2)]
			else:
				char_h2h[char_idx,opp_bin] = [-1.,0.]
				'''
				xs.append(float(opp_bin)/50.)
				ys.append(ratio)
				ss.append(1./float(char_h2h[char_idx,opp_bin][0]+char_h2h[char_idx,opp_bin][1]))'''

	# copy into dict format (for plotting winprobs/sigmoids)
	char_h2h_dict = {char_idx: {bin_id: char_h2h[char_idx,bin_id][0] for bin_id in range(n_bins+1) if char_h2h[char_idx,bin_id] != None} for char_idx in range(char_n)}

	char_skills = []
	for char_idx in range(char_n):
		xs = []
		ys = []
		ss = []
		for opp_bin in range(n_bins+1):
			ratio = char_h2h[char_idx,opp_bin][0]
			if ratio >= 0.:
				xs.append(float(opp_bin)/float(n_bins))
				ys.append(ratio)
				ss.append(char_h2h[char_idx,opp_bin][1])
			# remove sigmas from winprobs array so that it can be passed to plot_winprobs
			char_h2h[char_idx,opp_bin] = float(opp_bin)/float(n_bins)

		# fit sigmoid for each character across their histogram
		# must have more than 3 bins
		if len(xs) > 3:
			x = np.array(xs)
			y = np.array(ys)
			s = np.array(ss)

			#print(char_idx,char_labels[char_idx])
			#print(len(x),len(y),len(s))
			#print(x)
			#print(y)
			#print(s)

			v_b = get_fitsig_bounds(g=True)
			p0 = get_fitsig_guesses(g=True)
			try:
				p,cov = sp.optimize.curve_fit(alt_sigmoid,x,y,p0=p0,sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf',tr_solver='lsmr')

				char_skills.append(1.-integrate_alt_sigmoid([p],n_bins)[0])
			except RuntimeError:
				plot_winprobs(char_h2h[char_idx],char_h2h_dict,None,range(n_bins+1),char_idx,plot_rank=False,plot_sigmoid=False,mode='array',sig_mode='alt')
				char_skills.append('N/A')
		else:
			#print(char_idx,char_labels[char_idx])
			#print(len(xs))
			char_skills.append('N/A')

	return sorted([[char_labels[char_id],char_skills[char_id]] for char_id in range(char_n)],key=lambda t: (9999. if type(t[1]) is str else t[1],t[1]))

def disp_all(dicts,dispnum=20,key='elo',trans_cjk=True,avg_perf=False,scale_vals=False,min_activity=3,tier_tol=-1,plot_skills=False):
	tourneys,ids,p_info,records,skills,meta = dicts
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
	if key == 'srank':
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