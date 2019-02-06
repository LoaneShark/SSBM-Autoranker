## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
from datetime import date, timedelta
#import json
#import argparse
#import shutil
#from timeit import default_timer as timer
from copy import deepcopy as dcopy
## CALCULATION IMPORTS
import numpy as np
import scipy as sp 
from scipy.special import expit, logit
import sklearn
from math import *
import scipy.optimize
from random import *
from sklearn.cluster import KMeans as km
## UTIL IMPORTS
from dict_utils import get_abs_id_from_tag,get_en_tag
from readin_utils import save_dict,load_dict

activity_min = 3

def set_default_activity_min(val):
	activity_min = val
	return activity_min

# returns true if given player meets specified minimum activity requirements (default 3)
def is_active(dicts,p_id,tag=None,min_req=activity_min,min_wins=0):
	tourneys,ids,p_info,records,skills = dicts
	if tag != None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if p_id not in records:
		return False
	if min_wins > 0:
		if len([opp_id for opp_id in records[p_id]['wins']]) < min_wins:
			return False
	attendance = [t_id for t_id in records[p_id]['placings'] if type(records[p_id]['placings'][t_id]) is int if p_info[p_id]['sets_played'] > 6]
	#print(len(attendance))
	return (len(attendance) >= min_req)

# returns a list of booleans for each given player, if they meet activity requirements
def are_active(dicts,p_ids,tags=[],min_req=activity_min):
	tourneys,ids,p_info,records,skills = dicts
	if type(tags) is list and len(tags) > 0:
		p_ids = [get_abs_id_from_tag(dicts,tag) for tag in tags]
	return [is_active(dicts,p_id,min_req=min_req) for p_id in p_ids]

def score(dicts,placing,t_id,t_size=None):
	tourneys,ids,p_info,records,skills = dicts

	if t_size == None:
		num_entrants = tourneys[t_id]['numEntrants']
	else:
		num_entrants = t_size
	percent = (log(num_entrants,2)-log(placing,2))/log(num_entrants,2)
	return percent

## ELO CALCULATION UTILS
# Calculates the event performance rating for a single event
# using the FIDE "rule of 400" PR estimator
# (not a very meaningful metric; unused in other calculations)
def calc_performance(dicts,abs_id,t_info,use_FIDE=True):
	tourneys,ids,p_info,records,skills = dicts
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	#print("Calculating performance: %d :: %s"%(abs_id,t_name))
	w_count,l_count = 0.,0.
	opp_skills = 0.

	wins = records[abs_id]['wins']
	losses = records[abs_id]['losses']

	#if t_id not in records[abs_id]['placings']:
		#return 0.

	if use_FIDE:
		dp_table = load_dict('FIDE_dp',None,loc='../lib')
		pct = score(dicts,records[abs_id]['placings'][t_id],t_id,t_size)
		hi_val = max(ceil(pct*100.)/100.,0.)
		lo_val = max(floor(pct*100.)/100.,0.)
		dp = (dp_table[hi_val]+dp_table[lo_val])/2.

	for l_id in wins:
		#l_abs_id = ids[t_id][wins[e_id][0]]

		w_count += wins[l_id].count(t_id)
		opp_skills += p_info[l_id]['elo']*float(w_count)
	for w_id in losses:
		#w_abs_id = ids[t_id][losses[e_id][0]]

		l_count += losses[w_id].count(t_id)
		opp_skills += p_info[w_id]['elo']*float(l_count)

	if (w_count + l_count) == 0.:
		return 0.
	if use_FIDE:
		 res = (opp_skills / float(l_count+w_count))+dp
	else:
		res = (opp_skills + 400.*float(w_count-l_count))/float(w_count+l_count)
	#print(res)
	return res

def update_performances(dicts,t_info,use_FIDE=True):
	tourneys,ids,p_info,records,skills = dicts
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info

	for abs_id in records:
		if t_id in records[abs_id]['placings']:
			skills['perf'][abs_id][t_id] = calc_performance(dicts,abs_id,t_info,use_FIDE)
		#else:
		#	skills['perf'][abs_id][t_id] = 0.
		#print(skills['perf'][abs_id][t_id])

# returns the player's K-factor
# (used in Elo calculations)
def calc_k_factor(elo,n_played):

	# FIDE K-factor method of calculation
	if n_played < 30:
		if elo < 2400:
			return 40
		else:
			return 20
	else:
		if elo < 2400:
			return 20
		else:
			return 10

	# not used (old)
	if elo >= 2400:
		return 16.
	elif elo >= 2100:
		return 24.
	else:
		return 32.

# returns the player's expected score for a match
# (used in Elo calculations)
def exp_score(elo_a,elo_b):
	return 1.0/(1. + 10.**((float(elo_b)-float(elo_a))/400.))

# updates the player's elo score given their expected and actual results of the event
def update_elo(elo,expected,actual,N):
	K = calc_k_factor(elo,N)

	# days of wonder K-scaling (not used because of FIDE system)
	#if N < 20:
	#	K *= (float(N)/20.)

	return elo + K*(actual-expected)

## GLICKO CALCULATION UTILS
# (from glicko.net's algorithm)
# returns mu,phi given r,RD (and vice versa)
def glicko_scale(rating,RD):
	return (rating-1500.)/173.7178,RD/173.7178
def glicko_unscale(mu_p,phi_p):
	return 173.7178*mu_p+1500.,phi_p*173.7178

# returns the estimated variance of the player's rating
# mu = target player's glicko-2 rating
# mus, phis = opponent players' glicko-2 ratings and rating deviations
def glicko_variance(mu,p_matches):
	#mus = [match[1] for match in p_matches]
	#phis = [match[2] for match in p_matches]
	return sum([(glicko_g(phi_j)**2.) * glicko_E(mu,mu_j,phi_j) * (1-glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in p_matches])**-1.

# returns the estimated improvement in rating
def glicko_delta(mu,p_matches):
	#scores = [match[0] for match in p_matches]
	#mus = [match[1] for match in p_matches]
	#phis = [match[2] for match in p_matches]
	return glicko_variance(mu,p_matches)*sum([glicko_g(phi_j)*(s_j-glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in p_matches])
	
# helper function for glicko
def glicko_g(phi):
	return 1./(sqrt(1.+(3.*(phi**2.))/(pi**2.)))

# helper function for glicko
def glicko_E(mu,mu_j,phi_j):
	return 1./(1.+exp(-1.*glicko_g(phi_j)*(mu-mu_j)))

# iterative algorithm to update the glicko-2 volatility
# mu = glicko-2 rating
# phi = glicko-2 rating deviation
# sigma = glicko-2 rating volatility
def glicko_update_vol(mu,phi,sigma,p_matches,delta,v_g,tau):
	mus = [match[1] for match in p_matches]
	phis = [match[2] for match in p_matches]
	# step 1 (definitions)
	a = log(sigma**2.)
	tol = 0.000001
	#tau = glicko_tau
	f = lambda x: ((exp(x)*((delta**2.)-(phi**2.)-v_g-exp(x)))/(2.*(((phi**2.)+v_g+exp(x))**2.)))-((x-a)/(tau**2.))

	# step 2 (initial values)
	A = log(sigma**2.)
	if delta**2. > (phi**2.+v_g):
		B = log((delta**2.)-(phi**2.)-v_g)
	else:
		k = 1.
		while f(a-(k*tau)) < 0.:
			k += 1.
		B = a-(k*tau)

	# step 3 (iteration)
	f_A = f(A)
	f_B = f(B)
	while abs(f_B-f_A) > tol:
		#3a
		C = A + ((A-B)*f_A)/(f_B-f_A)
		f_C = f(C)

		#3b
		if f_C*f_B < 0.:
			A = B
			f_A = f_B
		else:
			f_A = f_A/2.

		#3c
		B = C 
		f_B = f_C

		#3d: stop if |f_B-f_A| > tol

	# step 4 (completion)
	sigma_prime = exp(A/2.)

	return sigma_prime

# updates the glicko ratings for all players that entered,
# after a given tournament
old_glicko_tau = 0.5
def update_glicko(dicts,matches,t_info,tau=0.5,ranking_period=60):
	tourneys,ids,p_info,records,skills = dicts
	t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	# converts match information to (s_j,mu_j,phi_j) format
	p_info_old = dcopy(p_info)

	for abs_id in p_info:
		# step 1 (instantiate starting values)
		# glicko stores a tuple with (rating,RD,volatility)
		if 'glicko' not in p_info[abs_id]:
			p_info[abs_id]['glicko'] = (1500.,350.,0.06)
			p_info_old[abs_id]['glicko'] = (1500.,350.,0.06)

		# step 2 (scale values)
		r,RD,sigma = p_info[abs_id]['glicko']
		mu,phi = glicko_scale(r,RD)
		
		#if abs_id in matches
		if t_id in ids[abs_id] and abs_id in matches and len(matches[abs_id]) > 0:
			p_matches = [(match[0],p_info_old[match[1]]['glicko']) for match in matches[abs_id]]
			p_matches = [(match[0],glicko_scale(match[1][0],match[1][1])) for match in p_matches]
			p_matches = [(match[0],match[1][0],match[1][1]) for match in p_matches]

			# step 3 (compute v)
			v_g = glicko_variance(mu,p_matches)
			# step 4 (compute delta)
			delta = glicko_delta(mu,p_matches)

			# step 5 (compute sigma')
			sigma_prime = glicko_update_vol(mu,phi,sigma,p_matches,delta,v_g,tau)

			# step 6 (update phi to new pre-rating value)
			phi_star = sqrt(phi**2. + sigma_prime**2.)

			# step 7 (update mu and phi)
			phi_prime = 1./sqrt(1./(phi_star**2) + 1./v_g)
			mu_prime = mu + (phi_prime**2)*sum([glicko_g(phi_j)*(s_j - glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in p_matches])

		else:
			#print(t_date)
			if t_id == p_info[abs_id]['last_event']:
				last_date = t_date
			else:
				last_date = tourneys[p_info[abs_id]['last_event']]['date']
			if date(last_date[0],last_date[1],last_date[2]) < (date(t_date[0],t_date[1],t_date[2])-timedelta(days=ranking_period)):
				phi_prime = phi
			else:
				phi_prime = sqrt(phi**2 + sigma**2)
			mu_prime = mu
			sigma_prime = sigma

		# step 8 (unscale values)
		r_prime,RD_prime = glicko_unscale(mu_prime,phi_prime)
		p_info[abs_id]['glicko'] = (r_prime,RD_prime,sigma_prime)

		# store new values & changes
		skills['glicko'][abs_id][t_id] = (r_prime,RD_prime,sigma_prime)
		r_del,RD_del,sigma_del = r_prime-r,RD_prime-RD,sigma_prime-sigma
		#if not(r_del == 0 and RD_del == 0 and sigma_del == 0):
		skills['glicko_del'][abs_id][t_id] = (r_del,RD_del,sigma_del)


## SIMBRACK MAIN CALCULATIONS

# simulates a bracket
## WIP
def calc_simbrack(dicts,t_info,max_iter=1000,min_req=3,rank_size=None,disp_size=100,mode='array',print_res=False,plot_ranks=True,alpha=0.5):
	tourneys,ids,p_info,records,skills = dicts
	#larry_id,T_id,jtails_id = get_abs_id_from_tag(dicts,'Tweek'),get_abs_id_from_tag(dicts,'Ally'),get_abs_id_from_tag(dicts,'Jtails')
	#print(void_id,dabuz_id,larry_id)
	#t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info
	if mode != 'array':
		mode == 'dict'
	## get the players that meet activity requirements to start with.
	## sort them by elo initially
	id_list = [abs_id for abs_id in records if is_active(dicts,abs_id,min_req=min_req,min_wins=1)]
	id_list = sorted(id_list,key=lambda abs_id: p_info[abs_id]['elo'],reverse=True)
	if rank_size != None and rank_size <= len(id_list):
		disp_size = min(disp_size,rank_size)
		id_list = id_list[:rank_size]
	## get the win probs for the whole db
	#winps,chis = winprobs(dicts,id_list=id_list)
	winps,chis = winprobs(dicts,id_list=None,mode='dict')

	## initialize data with [id, tag, elo, glicko] structure
	#data = np.array([[p_id,get_en_tag(dicts,tag=p_info[p_id]['tag']),float(p_info[p_id]['elo']),float(p_info[p_id]['glicko'][0])] for p_id in id_list],dtype='object')
	data = np.array([[p_id,get_en_tag(dicts,tag=p_info[p_id]['tag']),float(p_info[p_id]['elo']),float(p_info[p_id]['glicko'][0])] for p_id in winps],dtype='object')

	## get initial skillranks by rescaling all ranks (elo and glicko) to be between 0 and 1 (for sigmoid fitting)
	## normalize elo/glicko by all db entrants (N)
	N = float(len(winps.keys()))
	n = float(len(id_list))
	#N = float(len(id_list))
	elo_min = np.min(data[:,2])
	elo_max = np.max(data[:,2])
	data[:,2] = ((data[:,2]-elo_min)/(elo_max-elo_min))*(1./N-1.)+1.
	glicko_min = np.min(data[:,3])
	glicko_max = np.max(data[:,3])
	data[:,3] = ((data[:,3]-glicko_min)/(glicko_max-glicko_min))*(1./N-1.)+1.
	## average normalized elo and glicko for initial skillranks
	data[:,2] = (data[:,2]+data[:,3])/2.
	data = data[:,:3]
	## convert data to a dict and pass to simbrack
	data_dict = {p_id: [tag,skill_rank] for p_id,tag,skill_rank in data}

	print('Simulating Bracket... (%d entrants)'%n)
	#new_data_dict,sigs = simbrack(data_dict,winps,id_list,max_iter=max_iter)
	#new_data_dict,sigs,data_hist = simbrack(data_dict,winps,chis,id_list,max_iter=max_iter,simulate_bracket=False,score_intsigs=True,learn_rate=0.5,learn_decay=False,simple_sigmoid=False)
	new_data,sigs,data_hist = simbrack(data_dict,winps,chis,id_list,max_iter=max_iter,simulate_bracket=False,score_intsigs=True,learn_rate=alpha,learn_decay=True,simple_sigmoid=False,mode=mode,tol=0.008)
	if mode == 'dict':
		new_data_dict = dcopy(new_data)

	if print_res:
		print('=======================')
		#p_list = [sigs[p_id] for p_id in id_list]
		if mode == 'dict':
			p_list = [sigs[p_id] for p_id in sigs]
		else:
			p_list = list(sigs)
		mins = [min(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
		maxs = [max(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
		means = [np.mean(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
		#else:
		#	mins = [min(attr) for attr in [[p_val[i] for p_val in sigs] for i in range(len(sigs[0]))]]
		#	maxs = [max(attr) for attr in [[p_val[i] for p_val in sigs] for i in range(len(sigs[0]))]]
		#	means = [np.mean(attr) for attr in [[p_val[i] for p_val in sigs] for i in range(len(sigs[0]))]]
		print(mins)
		print(maxs)
		print([maxp-minp for maxp,minp in zip(maxs,mins)])
		print(means)
		print('=======================')
		print('Integrating sigmoids...')
		#intsigs = {p_id: 1.-integrate_sigmoid(sigs[p_id],N) for p_id in sigs}
		#intsig_res = [[new_data_dict[p_id][0],1.-integrate_sigmoid(sigs[p_id],N),new_data_dict[p_id][1],p_id] for p_id in sigs]
		#intsig_res = [[new_data_dict[p_id][0],new_data_dict[p_id][1],inv_sigmoid(0.5,sigs[p_id][0],sigs[p_id][1],sigs[p_id][2],sigs[p_id][3]),p_id] for p_id in id_list]
		if mode == 'dict':
			intsig_res = [[new_data_dict[p_id][0],new_data_dict[p_id][1],inv_sigmoid(0.5,(sigs[p_id][0],sigs[p_id][1],sigs[p_id][2],sigs[p_id][3])),p_id] for p_id in id_list]
		else:
			intsig_res = [[data_dict[p_id][0],skill,inv_sigmoid(0.5,(sig[0],sig[1],sig[2],sig[3])),p_id] for skill,sig,p_id in zip(new_data,sigs,id_list)]
		intsig_res = sorted(intsig_res,key=lambda l: l[1])
		intsigs = {intsig[-1]: intsig[:-1] for intsig in intsig_res}
		if disp_size <= len(intsig_res):
			intsig_res = intsig_res[:disp_size]
		print('---------------------------------------------')
		print('{:<21.21}'.format('Tag'),'{:<7.7}'.format('Intsig'),'{:<7.7}'.format('Y-int'),'Player ID')
		print('---------------------------------------------')
		for intsig_line in intsig_res:
			print('{:<21.21}'.format(str(intsig_line[0])),'{:<7.7}'.format(str(round(intsig_line[1],4))),'{:<7.7}'.format(str(round(intsig_line[2],4))),intsig_line[3])
		#print(sigs[int(intsig_line[3])])
		#print(len([opp_id for opp_id in winps[int(intsig_line[3])]]))
	#plot_skills(data_dict,id_list)
	#plot_skills(new_data_dict,id_list)
	#plot_skills(intsigs,id_list,plot_tags=True)

	if mode == 'array':
		# convert everything to dicts for returns
		new_data_dict = {p_id: [data_dict[p_id][0],skill_rank] for p_id,skill_rank in zip(id_list,new_data)}
		# add non-adjusted skill-ranks for plotting purposes (players that didn't meet activity reqs)
		for p_id in data_dict:
			if p_id not in new_data_dict:
				new_data_dict[p_id] = data_dict[p_id]
		sigdict = {p_id: p for p_id,p in zip(id_list,sigs)}
		data_hist_dict = {p_id: skill_hist for p_id,skill_hist in zip(id_list,[data_hist[:,p_idx] for p_idx in range(int(n))])}
	else:
		data_hist_dict = data_hist
		sigdict = sigs
	if plot_ranks:
		plot_skills(new_data_dict,id_list,mode='dict')
	return new_data_dict,winps,sigdict,data_hist_dict,id_list
	#return new_data,winps,sigs,data_hist,id_list

	#plot_winprobs(dicts,new_data_dict,winps,sigs,larry_id,plot_tags=True)
	#plot_winprobs(dicts,new_data_dict,winps,sigs,T_id,plot_tags=True)
	#plot_winprobs(dicts,new_data_dict,winps,sigs,jtails_id,plot_tags=True)

# NEEDS TO BE TWEAKED: Just getting it functional for now
def simbrack(data,winps,chis,id_list,max_iter=100,learn_rate=0.5,beta=0.9,tol=0.0001,simulate_bracket=True,score_intsigs=True,learn_decay=True,simple_sigmoid=False,mode='array'):
	N = float(len(data.keys()))
	n = float(len(id_list))
	print("N:",N," n:",n)
	if learn_rate == None:
		learn_decay = False
	elif learn_rate < 0:
		learn_rate = 0
		learn_decay = False
	#void_id,dabuz_id,larry_id = 23277,4702,1035

	count = 0
	#new_data = dcopy(data)
	if mode == 'dict':
		skill_ranks = dcopy(data)
		new_skills = dcopy(data)
		old_skills = dcopy(data)
	else:
		skill_ranks = [data[p_id][1] for p_id in id_list]
		new_skills = np.array(skill_ranks,copy=True)
		old_skills = np.array(skill_ranks,copy=True)

	#print(len(skill_ranks))
	#print(new_skills)
	#print(new_skills.shape)
	#print(old_skills.shape)

	p_guess = lambda p_id:[np.float64(data[p_id][1]),np.float(0.1),np.float(1.0),np.float(4.0)]
	if mode == 'dict':
		sigs = {p_id: p_guess(p_id) for p_id in id_list}
		covs = {}
		data_history = {p_id: [data[p_id][1]] for p_id in data}
	else:
		sigs = np.array([p_guess(p_id) for p_id in id_list],dtype=np.float64)
		covs = []
		data_history = np.array([skill_ranks],dtype=np.float64)

	all_converged = False
	while count < max_iter and not all_converged:
		print('iter:',count)
		#for s4_id,tag in zip([void_id,dabuz_id,larry_id],['VoiD','Dabuz','Larry Lurr']):
			#print(tag)
			#print(s4_id)
			#if count == 0:
			#	print(data[s4_id])
			#else:
			#	print(old_data[s4_id])
			#print(new_data[s4_id])
		count += 1
		#skill_rank = old_data
		p_count = 0

		#vfitsig = np.vectorize(fitsig,excluded=['data','winps','chis'])

		#sigres = vfitsig(data=new_data,winps=winps,chis=chis,p_id=id_list,old_guess=[sigs[p_id] for p_id in id_list],signature='(%d,%d),(%d)->(%d)'%(n,n,n,n))
		#sigs = {p_id: res[0] for p_id,res in zip(id_list,sigres)}
		#covs = {p_id: res[1] for p_id,res in zip(id_list,sigres)}
		if mode == 'dict':
			wins = {p_id: 0 for p_id in id_list}
			old_skills = dcopy(new_skills)

			for p_id in id_list:
				p_count += 1
				#print("count:",count)
				#print("player num:",p_count)
				#print("p_id:",p_id)
				#print(old_data[p_id])
				#print(new_data[p_id])
				#print(len(winps[p_id]))
				sigres = fitsig(new_skills,data,winps,chis,p_id,old_guess=sigs[p_id],simple_sigmoid=simple_sigmoid,mode=mode)
				
				sigs[p_id] = sigres[0]
				covs[p_id] = sigres[1]
				if type(sigs[p_id]) is type(None):
					return None

		else:
			wins = np.zeros((int(n),int(n)))
			old_skills = np.array(new_skills,copy=True)

			sigs,covs = fitsig(new_skills,data,winps,chis,np.array(id_list,dtype=int),old_guess=sigs,simple_sigmoid=simple_sigmoid,mode=mode,three_pass=True)
			if any([type(sig) == type(None) for sig in sigs]):
				return None


		# iterate through simulated RR bracket and tabulate wins
		if simulate_bracket:
			if mode == 'array':
				wins = np.zeroes((n,n))
			else:
				wins = {p_id: 0 for p_id in id_list}
			for pl_id in id_list:
				for opp_id in id_list:
					if pl_id != opp_id:
						xj = new_data[pl_id][1]
						x0j, y0j, cj, kj = sigs[pl_id]
						#x0j, cj, kj = sigs[pl_id]

						xk = new_data[opp_id][1]
						x0k, y0k, ck, kk = sigs[opp_id]
						#x0k, ck, kk = sigs[opp_id]

						pj = cfsigmoid(xk,x0j,y0j,cj,kj)
						#pj = cfsigmoid(xk,x0j,cj,kj)
						pk = cfsigmoid(xj,x0k,y0k,ck,kk)
						#pk = cfsigmoid(xj,x0k,ck,kk)

						# remove impossible values // always introduce a chance of upset (1/10,000)
						pj = max(pj,0.0001)
						pj = min(pj,0.9999)
						pk = max(pk,0.0001)
						pk = min(pk,0.9999)
						if random() < pj:
							wins[pl_id] += 1.
						elif random() < pk:
							wins[opp_id] += 1.
						else:
							wins[pl_id] += 1.

			winlist = [wins[key] for key in wins]
			#print(winlist)
			#lmin = min(winlist)
			lmin = 0.
			#lmax = max(winlist)
			lmax = 2.*n - 2.

			res = {}
			## TODO: FIX THIS PROBABLY
			for abs_id in id_list:
				# calculate each player's win percentage, normalized
				#print(n)
				res[abs_id] = ((wins[abs_id]-lmin)/(lmax-lmin))*(1./n - 1.) + 1.
				# update step
				# data[t] = data[t-1] + delta*(simulated-data[t-1])
				new_data[abs_id][1] = old_data[abs_id][1] + (learn_rate/sqrt(10.*float(count)))*(res[abs_id]-old_data[abs_id][1])

		else:
			# update step for array mode
			if mode == 'array':
				# update step for all ids [empirical]
				all_converged = True

				if score_intsigs:
					s_new = 1.-integrate_sigmoid(sigs,n)
				else:
					s_new = inv_sigmoid(0.5,sigs)
				
				update_diff = abs(s_new-old_skills)
				if any([diff > tol for diff in update_diff]):
					all_converged = False

				if learn_decay:
					new_skills = old_skills + (learn_rate/sqrt(float(count)))*(s_new-old_skills)
					#new_data[abs_id][1] = s_old + (learn_rate/sqrt(float(count)))*(s_new-s_old)
				else:
					new_skills = old_skills + learn_rate*(s_new-old_skills)
					#new_data[abs_id][1] = s_old + learn_rate*(s_new-s_old)

				data_history = np.append(data_history,[new_skills],axis=0)
			# update step for dict mode
			else:
				all_converged = True
				for abs_id in id_list:
					#if simple_sigmoid:
					#	x0,k = sigs[abs_id]
					#	if score_intsigs:
					#		s_new = 1.-integrate_sigmoid((x0,0.,1.,k),n)
					#	else:
					#		s_new = inv_sigmoid(0.5,x0,0.,1.,k)
					#else:
					x0,y0,c,k = sigs[abs_id]
					if score_intsigs:
						s_new = 1.-integrate_sigmoid((x0,y0,c,k),n)
					else:
						s_new = inv_sigmoid(0.5,(x0,y0,c,k))
					#if np.isnan(s_new):
					#	print(new_data[abs_id][0])
					s_old = old_skills[abs_id][1]
					update_diff = abs(s_new-s_old)
					if update_diff > tol:
						all_converged = False
					# cut the learnrate in half every 20 iterations
					if learn_decay:
						learn_rate *= 1./float(2**(int(count)/int(20)))

					#new_skills[abs_id][1] = beta*s_old + (1.-beta)*learn_rate*(s_new-s_old)
					new_skills[abs_id][1] = s_old + learn_rate*(s_new-s_old)

					# append score to history dict
					if abs_id not in data_history:
						data_history[abs_id] = []
					data_history[abs_id].extend([new_skills[abs_id][1]])

		# data(t) -> data(t-1)
		#old_data = dcopy(new_data)
	return new_skills,sigs,data_history

## SIMBRACK HELPER UTILS
# returns the h2h record for two given players (from p1's perspective)
def h2h(dicts,p1_id,p2_id):
	tourneys,ids,p_info,records,skills = dicts
	w,l = 0,0

	if p2_id in records[p1_id]['wins']:
		w = len(records[p1_id]['wins'][p2_id])
	else:
		w = 0.
	if p2_id in records[p1_id]['losses']:
		l = len(records[p1_id]['losses'][p2_id])
	else:
		l = 0.
	return (w,l) 

# returns a dict with the probability that player A beats player B, based on h2h records
# (stores -1 if no records exist)
def winprobs(dicts,id_list=None,mode='array'):
	tourneys,ids,p_info,records,skills = dicts
	if id_list == None:
		id_list = [p_id for p_id in records]
	if mode != 'array':
		mode = 'dict'

	if mode == 'dict':
		winps = {abs_id: {} for abs_id in id_list}
		chis = {abs_id: {} for abs_id in id_list}
	else:
		winps = np.ones((len(id_list),len(id_list)))
		winps.fill(-1.)
		chis = np.ones((len(id_list),len(id_list)))
	for abs_id in id_list:
		if mode == 'array':
			abs_idx = np.where(id_list == abs_id)
		'''if 'wins' not in records[abs_id] or 'losses' not in records[abs_id]:
			print(abs_id)
			print(p_info[abs_id]['tag'])
			print(records[abs_id])
			print(records[abs_id]['wins'])
			print(records[abs_id]['losses'])'''
		opps = [w_id for w_id in records[abs_id]['wins']]
		opps.extend([l_id for l_id in records[abs_id]['losses']])
		for opp_id in opps:
			if mode == 'array':
				opp_idx = np.where(id_list == opp_id)
			nw,nl = h2h(dicts,abs_id,opp_id)
			if abs_id == opp_id or (nw+nl <= 0):
				prob = -1.
				if mode == 'dict':
					chis[abs_id][opp_id] = 0.
				else:
					chis[abs_idx,opp_idx] = 0.
			else:
				prob = nw/(nw+nl)
				# calculate standard error/uncertainty
				h2h_scores = [1 for win in range(int(nw))]
				h2h_scores.extend([0 for loss in range(int(nl))])
				if nw+nl <= 1:
					if mode == 'dict':
						chis[abs_id][opp_id] = 0.5
					else:
						chis[abs_idx,opp_idx] = 0.5
				else:
					p_sigma = np.sqrt(sum([(gamescore-prob)**2. for gamescore in h2h_scores])/(nw+nl-1.))
					if p_sigma == 0:
						p_sigma = 0.5/np.sqrt(nw+nl-1.)
					if mode == 'dict':
						chis[abs_id][opp_id] = p_sigma
					else:
						chis[abs_idx,opp_idx] = p_sigma
			if mode == 'dict':
				winps[abs_id][opp_id] = prob
			else:
				winps[abs_idx,opp_idx] = prob
	return winps,chis

## SIMBRACK PRINTING UTILS
# plots the win probabilities for a player given their rank, and 
# calculates and plots the logistic function regression
def plot_winprobs(data,winps,sigs,id_list,p_id,plot_sigmoid=True,plot_tags=False,simple_sigmoid=False,mode='dict'):
	#tourneys,ids,p_info,records,skills = dicts
	#dats = winps[p_id]
	if mode == 'dict':
		skill_rank = data[p_id][1]
	else:
		id_list = np.array(id_list,dtype=int)
		p_idx = np.where(id_list == p_id)[0][0]
		skill_rank = data[p_idx]
		plot_tags = False

	N = float(len(winps.keys()))
	if plot_sigmoid:
		if mode == 'dict':
			n = float(len(sigs.keys()))
		else:
			n = float(len(sigs))
	else:
		n = 1.
	#print data
	#print dats
	xs = []
	ys = []
	ts = []
	for opp_id in winps[p_id]:
		ratio = float(winps[p_id][opp_id])
		if ratio >= 0:
			if mode == 'dict':
				xs.append(data[opp_id][1]*n)
				ts.append(data[opp_id][0])
				ys.append(ratio)
			else:
				# can only plot non-active skills in dict mode
				if opp_id in id_list:
					xs.append(data[np.where(id_list == opp_id)])
					ys.append(ratio)
	#x = np.array(xs)/N
	x = np.array(xs)
	y = np.array(ys)
	if plot_sigmoid:
		# get plotting data for sigmoid
		if mode == 'dict':
			p = sigs[p_id]
		else:
			p = sigs[p_idx]
		xp = np.linspace(0, 1, 15000)
		#print(p)
		#x0,c,k = p
		#if simple_sigmoid:
		#	x0,k = p 
		#	pxp = simple_cfsigmoid(xp,x0,k)
		#else:

		x0,y0,c,k = p
		#pxp = sigmoid(p,xp)
		pxp = sigmoid(xp,x0,y0,c,k)
			#pxp = cfsigmoid(xp,x0,c,k)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	if plot_sigmoid:
		plt.plot(x,y,'b.',n*xp,pxp,'g-')
		#plt.plot(N*x,y,'b.',N*xp,pxp,'g-')
	else:
		plt.plot(x,y,'b.')
		#plt.plot(N*x,y,'b.')
	if mode == 'dict':
		name = data[p_id][0]
	else:
		name = str(p_id)
	if plot_tags:
		for x,y,t in zip(xs,ys,ts):
			ax.annotate(t,xy=(x,y),textcoords='data',fontsize='small',rotation=-45)
	plt.title('%s\'s chance of winning vs the field\nN=%d n=%d (skill-rank %.3f)'%(name, N, n, skill_rank*n))
	plt.ylabel('Probability of winning a set')
	plt.xlabel('Opponent skill-rank')
	plt.ylim(-0.1,1.1)
	plt.show()

# plots the skills of players against their ordered rank
def plot_skills(data,id_list,plot_tags=False,mode='dict'):
	#tourneys,ids,p_info,records,skills = dicts
	n = len(id_list)
	if mode == 'dict':
		N = float(len(data.keys()))
		ps = [[data[p_id][1]*n,data[p_id][0]] for p_id in id_list]
		ps = sorted(ps,key=lambda l: l[0])
		ys = [p[0] for p in ps]
		tags = [p[1] for p in ps]
	else:
		plot_tags = False
		N = len(data)
		ps = data*float(n)
		ps = sorted(ps)
		ys = ps
	#if byrank:
	#	plt.plot(range(1,1+len(skillset)), skillset, "b.")
	#else:
	#	plt.plot(skillset, len(skillset)*skillset, "b.")
	xs = range(1,len(ys)+1)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	plt.plot(xs,ys,'b.')
	if plot_tags:
		for x,y,t in zip(xs,ys,tags):
			ax.annotate(t,xy=(x,y),textcoords='data',fontsize='small',rotation=-45)
	plt.grid()
	plt.title("Player Rank vs. Perceived Skill")
	plt.xlabel("Player Rank")
	plt.ylabel("(Normalized) Skill-Rank")
	plt.ylim(-0.1,len(ys)+2)
	plt.xlim(-0.1,len(ys)+2)
	plt.show()

def plot_hist(skill_hist,start_idx=0,p_idx=0,p_id=None,id_list=None,plot_delta=False,mode='dict'):

	if p_id != None:
		if mode == 'dict':
			skill_hist = skill_hist[p_id]
		elif id_list != None:
			p_idx = np.where(np.array(id_list) == p_id)
			skill_hist = skill_hist[:,p_idx]
	else:
		if mode == 'dict':
			if id_list != None:
				p_id = id_list[p_idx]
			else:
				p_id = None
			skill_hist = skill_hist[p_id]
		else:
			skill_hist = skill_hist[:,p_idx]

	fig,ax1 = plt.subplots()

	# plot skill history
	xs = range(start_idx,len(skill_hist))
	ys = skill_hist[start_idx:]
	ax1.plot(xs,ys,'r-',label='skill_history')

	# plot slope
	if plot_delta:
		x_dels = xs[1:]
		y_dels = ys[1:]-ys[:-1]

		ax2 = ax1.twinx()
		ax2.plot(x_dels,y_dels,'b--',label='dy/dx')
		ax2.set_ylabel('Change in Skill',color='tab:blue')
		ax2.tick_params(axis='y')

	plt.grid()
	#plt.legend()
	plt.title('Skill History for %d'%p_id)
	ax1.set_ylabel('Skill-Rank',color='tab:red')
	ax1.tick_params(axis='y')
	ax1.set_xlabel('Iteration')
	fig.tight_layout()
	plt.show()

## SIGMOID FITTING UTILS (for simbrack)
# sigmoid function, used to extrapolate probability distributions
def sigmoid(x,x0,y0,c,k):
	#x0,y0,c,k=p
	#print x0,y0,c,k
	#y = c / (1. + np.exp(-k*(x-x0))) + y0
	y = c*expit(k*10.*(x-x0)) + y0
	return y
def inner_sigmoid(x,x0,k):
	y = expit(k*10.*(x-x0))
	return y
def deep_sigmoid(x,x0,y0,c,k,y,s):
	inner_p,inner_cov = sp.optimize.curve_fit(inner_sigmoid,x,y,p0=(x0,k),sigma=s,bounds=([-1.,0.],[1.,10.]),method='trf',tr_solver='lsmr')
	x0,k = inner_p
	return sigmoid(x,x0,y0,c,k)
def inv_sigmoid(y,p):
	x0,y0,c,k=p
	#print x0,y0,c,k
	#y = c / (1. + np.exp(-k*(x-x0))) + y0
	#y = c*expit(-k*10*(x-x0)) + y0
	x = logit((y-y0)/c)/(10.*k)+x0
	return x
def cfsigmoid(x,x0,y0,c,k):
	#x0,y0,c,k=p
	#print x0,y0,c,k
	y = c / (1. + np.exp(-k*10*(x-x0))) + y0
	return y
def inv_cfsigmoid(y,x0,y0,c,k):
	x = np.log(c/(y-y0) - 1.)/(-k) + x0
	if np.isinf(x) or np.isnan(x):
		print(x)
		print(y,x0,y0,c,k)
		#return 0.
	return x
# strictly binds cfsigmoid to y in [0,1]
def bounded_cfsigmoid(x,p):
	x0,y0,c,k = p
	#x0 = p[:,0]
	#y0 = p[:,1]
	#c = p[:,2]
	#k = p[:,3]
	#print x0,y0,c,k
	y = c / (1. + np.exp(-k*10*(x-x0))) + y0
	#y = min(y,1.)
	#y = max(y,0.)
	# bound results to be in [0,1]
	y = np.clip(y,0.,1.)
	return y
def simple_cfsigmoid(x,x0,c,k):
	return c / (1.+np.exp(-k*10*(x-x0)))
def integrate_sigmoid(p,n):
	#x0,y0,c,k = p
	#print(len(p))
	#area = sp.integrate.quad(cfsigmoid,0.,1.,args=p)
	vint = np.vectorize(sp.integrate.quad,excluded=['func','a','b'],signature='(k)->(),()')
	area = vint(func=bounded_cfsigmoid,a=0.,b=1.,args=p)
	#area = sp.integrate.quad(bounded_cfsigmoid,0.,1.,args=p)
	#print(area)
	return area[0]
#def logcfsig(x,x0,c,k):
#	logy = np.log(1/(1+c))
def logsig(p,x):
	x0,y0,c,k=p
	#print p
	logy = k*(x-x0)
	return logy
# arctan function as alternative to sigmoid
def cfarctan(x,x0,y0,c,k):
	y = c * np.arctan(k*10*(x+x0)) + y0
	return y
# calculates difference between observed y values and given sigmoid
def logresiduals(p,x,y):
	return np.log(float(y)) - logsig(p,x)
def cfresiduals(p,x,y):
	x0,y0,c,k = p
	return cfsigmoid(x,x0,y0,c,k) - y
# jacobian matrix for sigmoid fitting
def cfjac(p,x,y):
	x0,y0,c,k = p
	J = np.empty((x.size,p.size))
	expval = np.exp(-k*10*(x-x0))
	den = 1. + expval

	# d/dx0
	J[:,0] = -k*expval*(den**-2.)
	# d/dy0
	J[:,1] = 1.
	# d/dc
	J[:,2] = 1./den
	# d/dk
	J[:,3] = -expval*(x-x0)*(den**-2.)
	return J

# normalize distribution range to [0,1]
def resize(arr,lower=0.0,upper=1.0):
	arr = arr.copy()
	if lower>upper: 
		lower,upper=upper,lower
	arr -= arr.min()
	arr *= (upper-lower)/arr.max()
	arr += lower
	return arr

# fits a sigmoid function to the provided data, and then returns the parameters
def fitsig(skill_ranks,data,winps,chis,id_list,old_guess=None,method='curve_fit',simple_sigmoid=False,scipy_sigmoid=False,three_pass=False,mode='array'):
	N = float(len(data.keys()))
	if mode == 'dict':
		n = 1.
	else:
		n = float(len(id_list))
	xlist = []
	ylist = []
	slist = []
	nlist = []

	for p_idx in range(int(n)):
		# instantiate data points at the bounds to help fit realistic curves (between 0 and 1)
		#xs = [0.000001,0.999999]
		#ys = [0.000001,0.999999]
		#ss = [0.000001,0.000001]
		#xs = [0.000001,0.000001,0.000001,0.000001,0.999999,0.999999,0.999999,0.999999]
		#ys = [0.000001,0.000001,0.000001,0.000001,0.999999,0.999999,0.999999,0.999999]
		#ss = [0.000001,0.000001,0.000001,0.000001,0.000001,0.000001,0.000001,0.000001]
		xs = [1.,0.]
		ys = [1.,0.]
		ss = [0.1,0.1]

		if mode == 'dict':
			p_id = id_list
			for opp_id in winps[p_id]:
				ratio = float(winps[p_id][opp_id])
				opp_skill = skill_ranks[opp_id][1]
				if ratio > 0:
					xs.append(opp_skill)
					ys.append(ratio)
					ss.append(chis[p_id][opp_id])
				if ratio == 0:
					xs.append(opp_skill)
					ys.append(0.001)
					ss.append(chis[p_id][opp_id])

		if mode == 'array':
			p_id = id_list[p_idx]
			for opp_id in winps[p_id]:
				ratio = float(winps[p_id][opp_id])
				if opp_id in id_list:
					opp_skill = skill_ranks[np.where(id_list == opp_id)][0]
				else:
					opp_skill = data[opp_id][1]
				if ratio > 0:
					xs.append(opp_skill)
					ys.append(ratio)
					ss.append(chis[p_id][opp_id])
				if ratio == 0:
					xs.append(opp_skill)
					ys.append(0.001)
					ss.append(chis[p_id][opp_id])

		if xs != [] and len(xs) >= 1:
			xlist.append(xs)
			ylist.append(ys)
			slist.append(ss)
			nlist.append(len(xs))

	## pad empty values to enable numpy array
	nmax = max(nlist)
	#print(nmax,min(nlist))
	for i in range(len(xlist)):
		n_i = len(xlist[i])
		if n_i < nmax:
			#print(n_i)
			buff = [-1.]*(nmax-n_i)
			xlist[i].extend(buff)
			ylist[i].extend(buff)
			slist[i].extend(buff)

	x = np.array(xlist)#/N
	y = np.array(ylist)
	s = np.array(slist)
	n_i = np.array(nlist, dtype=int)

	# fit sigmoid function to data
	if type(old_guess) == type(None):
		if simple_sigmoid:
			p_cfguess = np.fill(len(id_list),[np.float64(skill_ranks),np.float(1.0),np.float(4.0)])
		else:
			p_cfguess = np.ones((int(n),4))
			p_cfguess[:] = [np.float64(skill_ranks),np.float64(0.1),np.float64(1.0),np.float64(4.0)]
	else:
		p_cfguess = old_guess

	## define bounds:
	# f(x) in [0,1] :: 
	# 		x_0 in [-1,1]		y_0 in (-1,1) 		c in (0,inf) 		k in (0,inf)
	#
	# 		x-x_0 must be in [0,1]	
	#		y <= c+y_0   so c+y_0 must be in (0,inf)

	if simple_sigmoid:
		v_b = [[-1.,1.],[0.,10.]]
		#v_b_2 = [[-1.,1.],[0.,1.],[0.,10.]]
	else:
		v_b = [[-1.,1.],[-1.,1.],[0.,1.],[0.,20.]]
	# v_b = [[-1.,1.],[-1.,1.],[0.,3.],[0.,10.]]

	if mode == 'array':
		vsf = np.vectorize(sub_fitsig,excluded=['v_b','dats','params'],signature='(),(n),(n),(n),(),(k)->(k),(k)')

		#return sub_fitsig(id_list,x,y,s,p_cfguess,v_b,(data,winps)):
		return vsf(p_id=id_list,x=x,y=y,s=s,n_i=n_i,p0=p_cfguess,v_b=v_b,dats=(data,winps),params=(method,simple_sigmoid,scipy_sigmoid,three_pass,mode))
	elif mode == 'dict':
		return sub_fitsig(id_list,x,y,s,n_i,p_cfguess,v_b,(data,winps),(method,simple_sigmoid,scipy_sigmoid,three_pass,mode))

# subroutine of fitsig, so that many can be fit in parallel
def sub_fitsig(p_id,x,y,s,n_i,p0,v_b,dats,params):
	data,winps = dats
	p_cfguess = p0
	method,simple_sigmoid,scipy_sigmoid,three_pass,mode = params

	if mode == 'array':
		x = x[:n_i]
		y = y[:n_i]
		s = s[:n_i]
	else:
		x = x[0]
		y = y[0]
		s = s[0]

	if scipy_sigmoid:
		print(p_id)
		try:
			return sp.optimize.curve_fit(sigmoid,x,y,p0=p_cfguess,sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf')
			#return sp.optimize.curve_fit(lambda x,x0,y0,c,k: deep_sigmoid(x,x0,y0,c,k,y,s),x,y,p0=p_cfguess,sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf')
		except RuntimeError:
			print('scipy sigmoid error')
			plot_winprobs(data,winps,None,None,p_id,plot_sigmoid=False,plot_tags=True)
			return None

	# fit first params (x_0,k)
	try:
		if simple_sigmoid:
			p,cov = sp.optimize.curve_fit(lambda x,x0,k:simple_cfsigmoid(x,x0,1.,k),x,y,p0=(p_cfguess[0],p_cfguess[2]),sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf')
			#p,cov = sp.optimize.curve_fit(simple_cfsigmoid,x,y,p0=(p[0],p_cfguess[1],p[1]),sigma=ss,bounds=([b[0] for b in v_b_2],[b[1] for b in v_b_2]),method='trf')
			return [p[0],0.,1.,p[1]],np.diag(cov)
		# first fit x_0 and k
		if method == 'curve_fit':
			first_guess,cov_guess = sp.optimize.curve_fit(lambda x,x0,k:sigmoid(x,x0,p_cfguess[1],p_cfguess[2],k),x,y,p0=(p_cfguess[0],p_cfguess[3]),sigma=s,bounds=([v_b[0][0],v_b[3][0]],[v_b[0][1],v_b[3][1]]),method='trf')
			#first_guess,cov_guess = sp.optimize.curve_fit(lambda x,x0,k:sigmoid(x,x0,p_cfguess[1],p_cfguess[2],k),x,y,p0=(p_cfguess[0],p_cfguess[3]),sigma=s,bounds=([v_b[0][0],v_b[3][0]],[v_b[0][1],v_b[3][1]]),method='trf',tr_solver='lsmr',x_scale='jac')
			x0_guess,k_guess = first_guess
			cov_guess = np.diag(cov_guess)
		else:
			first_res = sp.optimize.least_squares(cfresiduals,p_cfguess,jac=cfjac,args=(x,y),bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf')
			p = first_res.x
			cov = first_res.jac
			return p,cov

	except RuntimeError:
		print('x_0, k: %s'%data[p_id][0])
		#plot_winprobs(data,winps,None,None,p_id,plot_sigmoid=False,plot_tags=True)
		x0_guess,k_guess = (p_cfguess[0],p_cfguess[3])
		cov_guess = np.full_like((1,2),-1.)

	# fit second params (y_0,c)
	try:
		second_guess,second_cov_guess = sp.optimize.curve_fit(lambda x,y0,c:sigmoid(x,x0_guess,y0,c,k_guess),x,y,p0=(p_cfguess[1],p_cfguess[2]),sigma=s,bounds=([v_b[1][0],v_b[2][0]],[v_b[1][1],v_b[2][1]]),method='trf')
		y0_guess,c_guess = second_guess
		second_cov_guess = np.diag(second_cov_guess)
	except RuntimeError:
		#print(x0_guess,k_guess)
		print('y_0, c: %s'%data[p_id][0])
		#plot_winprobs(data,winps,None,None,p_id,plot_sigmoid=False,plot_tags=True)
		y0_guess,c_guess = (p_cfguess[1],p_cfguess[2])
		second_cov_guess = np.full_like((1,2),-1.)
	fit_guess = (x0_guess,y0_guess,c_guess,k_guess)

	# fit first params again with new guesses (optional)
	if three_pass:
		try:
			#final_guess,final_cov_guess = sp.optimize.curve_fit(lambda x,x0,k:cfsigmoid(x,x0,p_cfguess[1],p_cfguess[2],k),x,y,p0=(p_cfguess[0],p_cfguess[3]),sigma=s,bounds=([v_b[0][0],v_b[3][0]],[v_b[0][1],v_b[3][1]]),method='trf',tr_solver='lsmr',x_scale='jac')
			#soft_bounds = [[max(val-.25*abs(val),bound[0]),min(val+.25*abs(val),bound[1])] for val,bound in zip(fit_guess,v_b)]
			#x0_guess,k_guess = final_guess
			final_guess,final_cov_guess = sp.optimize.curve_fit(sigmoid,x,y,p0=p_cfguess,sigma=s,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf')
			final_cov = np.diag(final_cov_guess)
			#p,cov = sp.optimize.curve_fit(cfsigmoid,x,y,p0=fit_guess,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf',tr_solver='lsmr')
			#try:
			#	final_p,final_cov = sp.optimize.curve_fit(cfsigmoid,x,y,p0=fit_guess,bounds=([b[0] for b in v_b],[b[1] for b in v_b]),method='trf',tr_solver='lsmr',x_scale='jac')
				#final_p,final_cov = sp.optimize.curve_fit(cfsigmoid,x,y,p0=fit_guess,bounds=([b[0] for b in soft_bounds],[b[1] for b in soft_bounds]),method='trf',tr_solver='lsmr',x_scale='jac')
			#except ValueError:
			#	print ([var > b[0] and var < b[1] for b in v_b])
			#	return None
			#return final_p,final_cov
		except RuntimeError:
			print('final pass: %s | %d'%(data[p_id][0],p_id))
			#plot_winprobs(data,winps,None,None,p_id,plot_sigmoid=False,plot_tags=True)
			final_guess = np.array([x0_guess,y0_guess,c_guess,k_guess])
			final_cov = np.array([cov_guess[0],second_cov_guess[0],second_cov_guess[1],cov_guess[1]])
	else:
		final_guess = np.array([x0_guess,y0_guess,c_guess,k_guess])
		final_cov = np.array([cov_guess[0],second_cov_guess[0],second_cov_guess[1],cov_guess[1]])
	return final_guess,final_cov

# fit multiple sigmoids (DEPRECATED)
def old_fitsigs(skill_ranks,data,winps,chis,p_ids,old_guess=None,method='curve_fit',simple_sigmoid=False,scipy_sigmoid=False,three_pass=False):
	return np.array([fitsig(skill_ranks,data,winps,chis,p_id,p0,method,simple_sigmoid,scipy_sigmoid,three_pass) for p_id,p0 in zip(p_ids,old_guess)],dtype=np.float64)

if __name__ == "__main__":

	dp_table = {}
	with open('../lib/FIDE_dp.csv') as dp_f:
		#dp_dats = dp_f.read_csv()
		for line in dp_f:
			splitline = line.split(',')
			dp_table[float(splitline[0])] = float(splitline[1])

	save_dict(dp_table,'FIDE_dp',None,loc='../lib')
	#print(dp_table)