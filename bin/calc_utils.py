## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
#import json
#import argparse
#import shutil
#from timeit import default_timer as timer
from copy import deepcopy as dcopy
#import country_converter as coco
#from geopy.geocoders import Nominatim
from math import *


## ELO CALCULATION UTILS
# Calculates the event performance rating for a single event
# using the FIDE "rule of 400" PR estimator
def calc_performance(records,p_info,abs_id,t_id):
	w_count,l_count = 0.,0.
	skills = 0.

	wins = records[abs_id]['wins']
	losses = records[abs_id]['losses']

	for l_id in wins:
		#l_abs_id = ids[t_id][wins[e_id][0]]

		skills += p_info[l_id]['elo']
		w_count += wins[l_id].count(t_id)
	for w_id in losses:
		#w_abs_id = ids[t_id][losses[e_id][0]]

		skills += p_info[w_id]['elo']
		l_count += losses[w_id].count(t_id)

	if (w_count + l_count) == 0:
		return 0
	return (skills + 400.*(w_count-l_count))/(w_count+l_count)

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
	return 1.0/(1. + 10.**((float(elo_a)-float(elo_b))/400.))

# updates the player's elo score given their expected and actual results of the event
def update_elo(elo,expected,actual,N):
	K = calc_k_factor(elo,N)

	return elo + K*(actual-expected)

## GLICKO CALCULATION UTILS
# (from glicko.net's algorithm)
#glicko_tau = 0.5
glicko_tau = 1.
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
def glicko_update_vol(mu,phi,sigma,p_matches,delta,v_g):
	mus = [match[1] for match in p_matches]
	phis = [match[2] for match in p_matches]
	# step 1 (definitions)
	a = log(sigma**2.)
	tol = 0.000001
	tau = glicko_tau
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
def update_glicko(p_info,ids,matches,t_id):
	# converts match information to (s_j,mu_j,phi_j) format
	#p_info_old = dcopy(p_info)

	for abs_id in p_info:
		# step 1 (instantiate starting values)
		# glicko stores a tuple with (rating,RD,volatility)
		if 'glicko' not in p_info[abs_id]:
			p_info[abs_id]['glicko'] = (1500.,350.,0.06)
		p_matches = [(match[0],p_info[match[1]]['glicko']) for match in matches[abs_id]]
		p_matches = [(match[0],glicko_scale(match[1][0],match[1][1])) for match in p_matches]
		p_matches = [(match[0],match[1][0],match[1][1]) for match in p_matches]

		# step 2 (scale values)
		r,RD,sigma = p_info[abs_id]['glicko']
		mu,phi = glicko_scale(r,RD)
		
		if t_id in ids[abs_id]:
			# step 3 (compute v)
			v_g = glicko_variance(mu,p_matches)
			# step 4 (compute delta)
			delta = glicko_delta(mu,p_matches)

			# step 5 (compute sigma')
			sigma_prime = glicko_update_vol(mu,phi,sigma,p_matches,delta,v_g)

			# step 6 (update phi to new pre-rating value)
			phi_star = sqrt(phi**2. + sigma_prime**2.)

			# step 7 (update mu and phi)
			phi_prime = 1./sqrt(1./(phi_star**2) + 1./v_g)
			mu_prime = mu + (phi_prime**2)*sum([glicko_g(phi_j)*(s_j - glicko_E(mu,mu_j,phi_j)) for s_j,mu_j,phi_j in p_matches])

		else:
			phi_prime = sqrt(phi**2 + sigma**2)
			mu_prime = mu
			sigma_prime = sigma

		# step 8 (unscale values)
		r_prime,RD_prime = glicko_unscale(mu_prime,phi_prime)
		p_info[abs_id]['glicko'] = (r_prime,RD_prime,sigma_prime)