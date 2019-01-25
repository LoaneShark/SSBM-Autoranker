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
import sklearn
from math import *
import scipy.optimize
from random import *
from sklearn.cluster import KMeans as km
## UTIL IMPORTS
from dict_utils import get_abs_id_from_tag
from readin_utils import save_dict,load_dict

activity_min = 3

def set_default_activity_min(val):
	activity_min = val
	return activity_min

# returns true if given player meets specified minimum activity requirements (default 3)
def is_active(dicts,p_id,tag=None,min_req=activity_min):
	tourneys,ids,p_info,records,skills = dicts
	if tag != None:
		p_id = get_abs_id_from_tag(dicts,tag)
	if p_id not in records:
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
def calc_simbrack(dicts,t_info,max_iter=100,min_req=3):
	tourneys,ids,p_info,records,skills = dicts
	#larry_id,T_id,jtails_id = get_abs_id_from_tag(dicts,'Tweek'),get_abs_id_from_tag(dicts,'Ally'),get_abs_id_from_tag(dicts,'Jtails')
	#print(void_id,dabuz_id,larry_id)
	#t_id,t_name,t_slug,t_ss,t_type,t_date,t_region,t_size = t_info

	# get the players that meet activity requirements to start with.
	# sort them by elo initially
	id_list = [abs_id for abs_id in records if is_active(dicts,abs_id,min_req=min_req)]
	id_list = sorted(id_list,key=lambda abs_id: p_info[abs_id]['elo'])
	# get the win probs
	winps = winprobs(dicts,id_list=None)
	# initialize data with [id, tag, elo, glicko] structure
	data = np.array([[p_id,p_info[p_id]['tag'],float(p_info[p_id]['elo']),float(p_info[p_id]['glicko'][0])] for p_id in winps],dtype='object')
	# get initial skillranks by rescaling all ranks (elo and glicko) to be between 0 and 1 (for sigmoid fitting)
	N = float(len(winps.keys()))
	elo_min = np.min(data[:,2])
	elo_max = np.max(data[:,2])
	data[:,2] = ((data[:,2]-elo_min)/(elo_max-elo_min))*(1./N-1.)+1.
	glicko_min = np.min(data[:,3])
	glicko_max = np.max(data[:,3])
	data[:,3] = ((data[:,3]-glicko_min)/(glicko_max-glicko_min))*(1./N-1.)+1.
	# average normalized elo and glicko for initial skillranks
	data[:,2] = (data[:,2]+data[:,3])/2.
	data = data[:,:3]
	# convert data to a dict and pass to simbrack
	data_dict = {p_id: [tag,skill_rank] for p_id,tag,skill_rank in data}

	print('Simulating Bracket... (%d entrants)'%len(id_list))
	new_data_dict,sigs = simbrack(data_dict,winps,id_list,max_iter=max_iter)

	print('===================')
	p_list = [sigs[p_id] for p_id in sigs]
	mins = [min(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
	maxs = [max(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
	means = [np.mean(attr) for attr in [[p_val[i] for p_val in p_list] for i in range(len(p_list[0]))]]
	print(mins)
	print(maxs)
	print([maxp-minp for maxp,minp in zip(maxs,mins)])
	print(means)
	print('===================')
	plot_skills(data_dict,id_list)
	plot_skills(new_data_dict,id_list,plot_tags=True)
	plot_winprobs(new_data_dict,winps,sigs,23277,plot_tags=True)
	plot_winprobs(new_data_dict,winps,sigs,432879,plot_tags=True)
	#plot_winprobs(new_data_dict,winps,sigs,1000,plot_tags=True)
	#plot_winprobs(new_data_dict,winps,sigs,1004,plot_tags=True)

	#plot_winprobs(dicts,new_data_dict,winps,sigs,larry_id,plot_tags=True)
	#plot_winprobs(dicts,new_data_dict,winps,sigs,T_id,plot_tags=True)
	#plot_winprobs(dicts,new_data_dict,winps,sigs,jtails_id,plot_tags=True)

# NEEDS TO BE TWEAKED: Just getting it functional for now
def simbrack(data,winps,id_list,max_iter=100,learn_rate=0.5):
	N = float(len(data.keys()))
	n = float(len(id_list))
	print("N:",N," n:",n)
	#void_id,dabuz_id,larry_id = 23277,4702,1035

	count = 0
	new_data = dcopy(data)
	old_data = dcopy(data)
	while count <= max_iter:
		print(count)
		#for s4_id,tag in zip([void_id,dabuz_id,larry_id],['VoiD','Dabuz','Larry Lurr']):
			#print(tag)
			#print(s4_id)
			#if count == 0:
			#	print(data[s4_id])
			#else:
			#	print(old_data[s4_id])
			#print(new_data[s4_id])
		old_data = dcopy(new_data)
		count += 1
		sigs = {}
		wins = {}
		p_count = 0
		for p_id in id_list:
			p_count += 1
			print("count:",count)
			print("player num:",p_count)
			print("p_id:",p_id)
			#print(old_data[p_id])
			print(new_data[p_id])
			print(len(winps[p_id]))
			sigs[p_id] = fitsig(new_data,winps,p_id)
			if type(sigs[p_id]) is type(None):
				return None
			wins[p_id] = 0.

		# iterate through simulated RR bracket and tabulate wins
		#wins = {p_id: 0 for p_id in id_list}
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
		print(winlist)
		#lmin = min(winlist)
		lmin = 0.
		lmax = max(winlist)

		res = {}
		for abs_id in id_list:
			# calculate each player's win percentage, normalized
			#print(n)
			res[abs_id] = ((float(wins[abs_id])-float(lmin))/(float(lmax)-float(lmin)))*(1./n -1.) + 1.
			# update step
			# data(t) = data(t-1) + (delta)*(predicted-observed)
			new_data[abs_id][1] = old_data[abs_id][1] + (learn_rate/sqrt(10.*float(count)))*(res[abs_id]-old_data[abs_id][1])
		# data(t) -> data(t-1)
		#old_data = dcopy(new_data)
	return new_data,sigs

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
def winprobs(dicts,id_list=None):
	tourneys,ids,p_info,records,skills = dicts
	
	winps = {}
	if id_list == None:
		id_list = [p_id for p_id in records]
	for abs_id in id_list:
		winps[abs_id] = {}
		'''if 'wins' not in records[abs_id] or 'losses' not in records[abs_id]:
			print(abs_id)
			print(p_info[abs_id]['tag'])
			print(records[abs_id])
			print(records[abs_id]['wins'])
			print(records[abs_id]['losses'])'''
		opps = [w_id for w_id in records[abs_id]['wins']]
		opps.extend([l_id for l_id in records[abs_id]['losses']])
		for opp_id in opps:
			nw,nl = h2h(dicts,abs_id,opp_id)
			if abs_id == opp_id or (nw+nl <= 0):
				prob = -1.
			else:
				prob = nw/(nw+nl)
			winps[abs_id][opp_id] = prob
	return winps

## SIMBRACK PRINTING UTILS
# plots the win probabilities for a player given their rank, and 
# calculates and plots the logistic function regression
## WIP CONVERSION
def plot_winprobs(data,winps,sigs,p_id,plot_sigmoid=True,plot_tags=False):
	#tourneys,ids,p_info,records,skills = dicts
	#dats = winps[p_id]
	skill_rank = data[p_id][1]
	N = float(len(data.keys()))
	#n = float(len(data.keys()))
	#print data
	#print dats
	xs = []
	ys = []
	ts = []
	for opp_id in winps[p_id]:
		ratio = float(winps[p_id][opp_id])
		if ratio >= 0:
			xs.append(data[opp_id][1]*N)
			ys.append(ratio)
			ts.append(data[opp_id][0])
	#x = np.array(xs)/N
	x = np.array(xs)
	y = np.array(ys)
	if plot_sigmoid:
		# get plotting data for sigmoid
		p = sigs[p_id]
		print(p)
		#x0,c,k = p
		x0,y0,c,k = p
		xp = np.linspace(0, 1, 15000)
		#pxp = sigmoid(p,xp)
		pxp = cfsigmoid(xp,x0,y0,c,k)
		#pxp = cfsigmoid(xp,x0,c,k)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	if plot_sigmoid:
		plt.plot(x,y,'b.',N*xp,pxp,'g-')
		#plt.plot(N*x,y,'b.',N*xp,pxp,'g-')
	else:
		plt.plot(x,y,'b.')
		#plt.plot(N*x,y,'b.')
	name = data[p_id][0]
	if plot_tags:
		for x,y,t in zip(xs,ys,ts):
			ax.annotate(t,xy=(x,y),textcoords='data',fontsize='small',rotation=-45)
	plt.title('%s\'s chance of winning vs the field N=%d (skill-rank %.3f)'%(name, N, data[p_id][1]*N))
	plt.ylabel('Probability of winning a set')
	plt.xlabel('Opponent skill-rank')
	plt.show()

# plots the skills of players against their ordered rank
def plot_skills(data, id_list,plot_tags=False):
	#tourneys,ids,p_info,records,skills = dicts
	N = float(len(data.keys()))
	n = float(len(id_list))
	#if byrank:
	#	plt.plot(range(1,1+len(skillset)), skillset, "b.")
	#else:
	#	plt.plot(skillset, len(skillset)*skillset, "b.")
	ps = [[data[p_id][1]*n,data[p_id][0]] for p_id in id_list]
	ps = sorted(ps,key=lambda l: l[0])
	ys = [p[0] for p in ps]
	tags = [p[1] for p in ps]
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
	plt.show()

## SIGMOID FITTING UTILS (for simbrack)
# sigmoid function, used to extrapolate probability distributions
def sigmoid(p,x):
	x0,y0,c,k=p
	#print x0,y0,c,k
	y = c / (1. + np.exp(-k*(x-x0))) + y0
	return y
def cfsigmoid(x,x0,y0,c,k):
	#x0,y0,c,k=p
	#print x0,y0,c,k
	y = c / (1. + np.exp(-k*10*(x-x0))) + y0
	return y
def cfarctan(x,x0,y0,c,k):
	y = c * np.arctan(k*10*(x+x0)) + y0
	return y
#def logcfsig(x,x0,c,k):
#	logy = np.log(1/(1+c))
def logsig(p,x):
	x0,y0,c,k=p
	#print p
	logy = k*(x-x0)
	return logy
# calculates difference between observed y values and given sigmoid
def logresiduals(p,x,y):
	return np.log(float(y)) - logsig(p,x)
def residuals(p,x,y):
	return y - sigmoid(p,x)
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
def fitsig(data,winps,p_id):
	skill_rank = data[p_id][1]
	#dats = [winps[p_id][opp_id] for opp_id in winps[p_id]]
	N = float(len(data.keys()))
	print("fitsig N: ",N)
	#rank
	#print data[rank-1,2]
	#print data
	#print dats
	xs = []
	ys = []
	for opp_id in winps[p_id]:
		ratio = float(winps[p_id][opp_id])
		#print(p_id,opp_id)
		#print(winps[p_id][opp_id])
		#print(len(winps[opp_id]))
		#print(data[opp_id])
		if opp_id == 5643:
			print(winps[opp_id])
		opp_skill = data[opp_id][1]
		if ratio > 0:
			xs.append(opp_skill)
			ys.append(ratio)
		if ratio == 0:
			xs.append(opp_skill)
			ys.append(0.001)

	print('xlen:',len(xs),' xmax:',max(xs),' xmin:',min(xs))
	print('ylen:',len(ys),' ymax:',max(ys),' ymin:',min(ys))
	x = np.array(xs, dtype=float)#/N
	y = np.array(ys, dtype=float)
	# fit sigmoid function to data
	#p_guess=(np.float64(rank/N),np.float64(np.median(y)),np.float64(1.0),np.float64(1.0))
	#p_cfguess=(np.float64(skill_rank/N),np.float(1.0),np.float(1.0))
	#p_cfguess=(np.float64(skill_rank),np.float(0.0),np.float(1.0),np.float(10.0))
	p_cfguess=(np.float64(skill_rank),np.float(0.0),np.float(1.0),np.float(4.0))
	#p_cfguess=(np.float64(skill_rank),np.float(1.0),np.float(1.0),np.float(4.0))
	#p_cfguess=(np.float64(0.5),np.float(0.0),np.float(1.0),np.float(4.0))
	#p_cfguess=(np.float64(rank/N),np.float(1.0))
	#results = scipy.optimize.differential_evolution(residuals,[(0.,1.),(-1.,2.),(-10.,10.),(-5.,5.)],args=(x,y))  
	#results = scipy.optimize.leastsq(residuals,p_guess,args=(x,y),full_output=1)  
	#results = scipy.optimize.curve_fit(cfsigmoid,x,y,p0=p_cfguess,bounds=([-0.1,-1.1],[1.1,20.]))

	try:
		results = sp.optimize.curve_fit(cfsigmoid,x,y,p0=p_cfguess,bounds=([-1.,-2.,-1.,0.],[2.,1.,3.,5.]),method='trf',tr_solver='lsmr',x_scale='jac')
		#results = sp.optimize.curve_fit(cfarctan,x,y,p0=p_cfguess,bounds=([-0.1,-2.5,0.,0.],[1.1,1.,3.,5.]),method='trf',tr_solver='lsmr',x_scale='jac')
	except RuntimeError:
		plot_winprobs(data,winps,None,p_id,plot_sigmoid=False,plot_tags=True)
		return None
	#except ValueError:
	#	print("oh NO")
	#	print(p_cfguess.shape())
	#	print(x.shape())
	#	print(y.shape())
	#	print(p_cfguess)

	p,cov = results
	#p,_,_,_,_ = results
	return p

if __name__ == "__main__":

	dp_table = {}
	with open('../lib/FIDE_dp.csv') as dp_f:
		#dp_dats = dp_f.read_csv()
		for line in dp_f:
			splitline = line.split(',')
			dp_table[float(splitline[0])] = float(splitline[1])

	save_dict(dp_table,'FIDE_dp',None,loc='../lib')
	#print(dp_table)