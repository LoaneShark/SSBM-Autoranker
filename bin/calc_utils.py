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
	attendance = [t_id for t_id in records[p_id]['placings'] if type(records[p_id]['placings'][t_id]) is int]
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
	w_count,l_count = 0.,0.
	opp_skills = 0.

	wins = records[abs_id]['wins']
	losses = records[abs_id]['losses']

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
		return (opp_skills / float(l_count+w_count))+dp
	return (opp_skills + 400.*float(w_count-l_count))/float(w_count+l_count)

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
def update_glicko(dicts,matches,t_info,tau=0.5):
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
			if date(last_date[0],last_date[1],last_date[2]) < (date(t_date[0],t_date[1],t_date[2])-timedelta(days=30)):
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

## SIGMOID FITTING // SIMBRACK CALCULATION UTILS
# sigmoid function, used to extrapolate probability distributions
def sigmoid(p,x):
	x0,y0,c,k=p
	#print x0,y0,c,k
	y = c / (1 + np.exp(-k*(x-x0))) + y0
	return y
def cfsigmoid(x,x0,c,k):
	#x0,y0,c,k=p
	#print x0,y0,c,k
	y = c / (1. + np.exp(-k*(x-x0)))
	return y
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
	arr=arr.copy()
	if lower>upper: 
		lower,upper=upper,lower
	arr -= arr.min()
	arr *= (upper-lower)/arr.max()
	arr += lower
	return arr

# fits a sigmoid function to the provided data, and then returns the parameters
def fitsig(winps, rank, data):
	dats = winps[rank-1]
	N = len(data)
	#print data[rank-1,2]
	#print data
	#print dats
	xs = []
	ys = []
	for i in range(N):
		ratio = float(dats[i])
		if ratio > 0:
			xs.append(float(i+1))
			ys.append(ratio)
		if ratio == 0:
			xs.append(float(i+1))
			ys.append(0.001)
	x = np.array(xs, dtype=np.float64)/N
	y = np.array(ys, dtype=np.float64)
	#x = np.array(xs, dtype='float')
	#y = np.array(ys, dtype='float')
	#print len(xs)
	#print x
	#print y
	# fit sigmoid function to data
	p_guess=(np.float64(rank/N),np.float64(np.median(y)),np.float64(1.0),np.float64(1.0))
	p_cfguess=(np.float64(rank/N),np.float(1.0),np.float(1.0))
	#p_cfguess=(np.float64(rank/N),np.float(1.0))
	#results = scipy.optimize.differential_evolution(residuals,[(0.,1.),(-1.,2.),(-10.,10.),(-5.,5.)],args=(x,y))  
	#results = scipy.optimize.leastsq(residuals,p_guess,args=(x,y),full_output=1)  
	#results = scipy.optimize.curve_fit(cfsigmoid,x,y,p0=p_cfguess,bounds=([-0.1,-1.1],[1.1,20.]))
	results = scipy.optimize.curve_fit(cfsigmoid,x,y,p0=p_cfguess,bounds=([0.,0.,0.],[1.1,1.1,13.5]))
	p, cov = results
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