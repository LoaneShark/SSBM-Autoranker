## DEPENDENCY IMPORTS
import matplotlib.pyplot as plt 
import os,sys,pickle,time
import re
from timeit import default_timer as timer
from copy import deepcopy as dcopy
# ANALYSIS IMPORTS
import numpy as np
import scipy as sp 
import sklearn
from math import *
import scipy.optimize
import warnings
from random import *
from operator import itemgetter
from sklearn.cluster import KMeans as km
## UTIL IMPORTS
from analysis_utils import *
#from db_utils import load_dict,save_dict

tourneys, ids, records, p_info = {},{},{},{}

def set_dicts(dicts):
	tourneys, ids, records, p_info = dicts

# perform the main calculations and data processing
# (DEPRECATED)
def old_main():
	print("Reading data files")
	(wins, metadata, tourneys, placings) = dataread()
	N = len(metadata) # number of players in dataset
	T = len(tourneys) # number of tourneys in placings dataset

	#print tourneys
	#print placings
	#print metadata

	# calculate percentage of rounds won in bracket for each player
	print("Guessing initial skill ranks")
	rounds = np.array(placings, copy=True, dtype='object')
	for player in rounds:
		for i in range(len(player)):
			player[i] = prounds(player[i],tourneys[i,0])

	# calculate the aggregate and average percentage of rounds won for each player
	aggrnds = [[n for n in player if type(n) is float or type(n) is int] for player in rounds]
	avgrnds = np.array([np.mean([n for n in player if type(n) is float or type(n) is int]) for player in rounds])
	
	# catcher to make sure no fraudulent placing data slips through
	for i in range(len(rounds)):
		#print rounds[i]
		if -9999. in rounds[i]:
			print(metadata[i,0])

	# reorder the data by the new round win probability
	tmprank = np.zeros(N, dtype=[('name', 'S20'), ('rank', int), ('percentage', float), ('PID', int)])
	for n in range(N):
		# store (player name, ssbmrank 2017, placing percentage, player ID])
		#print n
		tmprank[n][0] = metadata[n,0]
		if (n > 50):
			m = 51
		else:
			m = n+1
		#print tmp
		tmprank[n][1] = m
		tmprank[n][2] = avgrnds[n]
		tmprank[n][3] = n
	newrank = np.sort(tmprank,order=['percentage', 'rank'])
	newrank = np.flip(newrank,0)
	data = np.zeros((N,5), dtype = 'object')
	for i in range(N):
		data[i,0] = i+1
		data[i,1] = newrank[i][1]
		data[i,2] = newrank[i][0]
		data[i,3] = newrank[i][2]
		data[i,4] = newrank[i][3]
	# establish W/L matrices with new player order
	tmpwins = np.array(wins, copy=True)
	for i in range(N):
		for j in range(N):
			tmpwins[i,j] = wins[data[i,4],data[j,4]]
	wins = np.array(tmpwins, copy=True)
	losses = np.array(wins.T, copy=True)

	winps = winprobs(wins,losses)


	# clean data (remove players with insufficient match data)
	print("Cleaning data...")
	data,winps,N = prunedata(data,winps)

	# simulate the results of a bracket
	print("Simulating Brackets...")
	skills,probs = simbracket(data,winps,100)
	print(skills)
	
	score = np.inf
	optparams = (3,[])
	X = np.array([[i, s] for (i,s) in zip(skills[:,1],skills[:,1])])
	
	# cluster the quality groups
	for k in range(9,13):
		kmeans = km(n_clusters=k,max_iter=420,algorithm="full",tol=1e-6).fit(X)
		labels = kmeans.labels_
		if score > kmeans.inertia_:
			score = kmeans.inertia_
			optparams = (k,labels)

	# calculate the aggregate skill rank data for each character and region
	chars = {}
	regns = {}
	for i in range(N):
		main = metadata[i,2]
		region = metadata[i,1]
		skill = skills[i,1]
		if main in chars.keys():
			chars[main].append(skill)
		else: chars[main] = [skill]
		if region in regns.keys():
			regns[region].append(skill)
		else: regns[region] = [skill]

	#plotskill(skills[:,1])
	plotdats(chars,regns)
	plotclusters(skills,labels,k)

# calculates and returns the probabilities of winning 
def winprobs(wins,losses):
	nranks = len(wins)
	winps = np.zeros((nranks,nranks))
	winps.fill(-1.)
	for player in range(nranks):
		for opp in range(nranks):
			nw = wins[player,opp]
			nl = losses[player,opp]
			if (player==opp) or (nw+nl <= 0):
				prob = -1.
			else:
				prob = nw/(nw+nl)
				winps[player,opp] = prob
	return np.array(winps, dtype=np.float64)

# runs up to <maxiter> number of simulated brackets (with random seeding).
# the result of each bracket is then used to update percieved skills.
# terminates when max iterations is reached, or equilibrium in player
# ranking order is achieved.
def simbracket(data, winps, maxiter):
	
	N = len(data)
	ranks = data[:,0]
	names = data[:,2]
	skills = data[:,3]
	data[:,1] = names[:]
	data[:,2] = skills[:]
	data = data[:,1:3]
	
	h2h = {}
	for pl in range(N):
		for opp in range(N):
			if (pl != opp):
				h2h[(data[pl,0],data[opp,0])] = winps[pl,opp]
	
	count = 0
	learnrate = 0.5
	smin = np.min(data[:,1])
	smax = np.max(data[:,1])
	data[:,1] = ((data[:,1]-smin)/(smax-smin))*(1./N - 1.) + 1.
	newdata = np.array(data, copy=True)
	while count < maxiter:
		#if count % 10 == 0:
		#	print count
		count += 1

		# recalculate win distribution probabilities for new rankings
		winps.fill(-1.)
		for i in range(N):
			for j in range(N):
				if i != j:
					winps[i,j] = h2h[data[i,0],data[j,0]]
		sigs = np.array([fitsig(winps, i+1, data) for i in range(N)])
		
		# run sample RR bracket
		wins = np.zeros(N,dtype=np.float64)
		for j in range(N):
			for k in range(j,N):
				if j != k:
					xj = newdata[j,1]
					x0j = sigs[j,0]
					cj = sigs[j,1]
					kj = sigs[j,2]
					xk = newdata[k,1]
					x0k = sigs[k,0]
					ck = sigs[k,1]
					kk = sigs[k,2]
					pj = cfsigmoid(xk,x0j,cj,kj)
					pk = cfsigmoid(xj,x0k,ck,kk)
					if random() < pj:
						wins[j] += 1
					elif random() < pk:
						wins[k] += 1
					else:
						wins[j] += 1
		lmin = np.min(wins[:])
		lmax = np.max(wins[:])
		res = ((wins[:]-lmin)/(lmax-lmin))*(1./N - 1.) + 1.
		
		newdata[:,1] = data[:,1] + (learnrate/np.sqrt(10*count))*(res-data[:,1])
		# sort to new skillranks
		newdata = np.array(sorted(newdata,key=itemgetter(1)))
		
		# set (t-1) dataset equal to (t) dataset for next iteration
		data = np.array(newdata, copy=True)
	return newdata,winps
	
# prunes players with insufficient data	
def prunedata(data, winps):
	N = len(data)
	rank = 1
	while rank<=N:
		dats = winps[rank-1]
		xs = []
		for i in range(len(data)):
			ratio = float(dats[i])
			if ratio >= 0:
				xs.append(float(i+1))
		if len(xs) <= 6:
			print("Pruning",data[rank-1,2])
			tmpdata = np.zeros((len(data)-1,5), dtype='object')
			tmpdata[:rank-1] = data[:rank-1]
			tmpdata[rank-1:] = data[rank:]
			tmpdata[rank-1:,0] = data[rank:,0]-1
			data = tmpdata.copy()

			tmpwinps = np.zeros((len(winps)-1,len(winps)), dtype='float')
			tmpwinps[:rank-1] = winps[:rank-1]
			tmpwinps[rank-1:] = winps[rank:]
			tmpwinps2 = np.zeros((len(tmpwinps),len(tmpwinps)), dtype='float')
			tmpwinps2[:,:rank-1] = tmpwinps[:,:rank-1]
			tmpwinps2[:,rank-1:] = tmpwinps[:,rank:]
			winps = tmpwinps2.copy()
			N -= 1
		rank += 1
	return (data, winps, N)

# plots the skills of players against their ordered rank
def plotskill(skillset, byrank=True):
	if byrank:
		plt.plot(range(1,1+len(skillset)), skillset, "b.")
	else:
		plt.plot(skillset, len(skillset)*skillset, "b.")
	plt.title("Player Rank vs. Perceived Skill")
	plt.xlabel("Player Rank")
	plt.ylabel("(Normalized) Skill Value")
	plt.show()

# show boxplots of character and region skill data
def plotdats(chars, regions):

	chardata = [chars[key] for key in chars.keys()]
	charlabels = [key for key in chars.keys()]
	regdata = [regions[key] for key in regions.keys()]
	reglabels = [key for key in regions.keys()]


	fig = plt.figure()
	# character data boxplot
	axc = fig.add_subplot(211)
	bpc = axc.boxplot(chardata)
	axc.set_xlabel("Character")
	axc.set_ylabel("Perceived skill")
	axc.set_xticklabels(charlabels)
	for tick in axc.get_xticklabels():
		tick.set_rotation(45)
	# regional data boxplot
	axr = fig.add_subplot(212)
	bpr = axr.boxplot(regdata)
	axr.set_xlabel("Region")
	axr.set_ylabel("Perceived skill")
	axr.set_xticklabels(reglabels)
	for tick in axr.get_xticklabels():
		tick.set_rotation(45)
	
	plt.show()

# plots the wins and losses of a given player, from their rank
def plotrecord(wins, losses, rank):
	nump = len(wins)
	plt.plot(range(50), wins[rank-1,:50], "g.", label="wins")
	plt.plot(range(50), losses[rank-1,:50], "r.", label="losses")
	plt.title("Record vs the top 50*")
	plt.ylabel("Record")
	plt.xlabel("Rank")
	#plt.legend(loc="best")
	plt.show()

# plots the win probabilities for a player given their rank, and 
# calculates and plots the logistic function regression
def plotwinprobs(winps, rank, data):
	dats = winps[rank-1]
	N = len(data)
	#print data
	#print dats
	xs = []
	ys = []
	for i in range(len(data)):
		ratio = float(dats[i])
		if ratio >= 0:
			xs.append(float(i+1))
			ys.append(ratio)
	x = np.array(xs)/N
	y = np.array(ys)
	# get plotting data for sigmoid
	p = fitsig(winps,rank,data)
	print(p)
	#x0,y0,c,k = p
	x0,c,k = p
	xp = np.linspace(0, 1, 1500)
	#pxp = sigmoid(p,xp)
	pxp = cfsigmoid(xp,x0,c,k)

	plt.plot(N*x,y,"b.",N*xp,pxp,"g-")
	name = data[rank-1,0]
	plt.title("%s's chance of winning vs the field (rnk %d)" %(name, rank))
	plt.ylabel("Probability of winning a set")
	plt.xlabel("Player rank")
	plt.show()

# plots the clusters given data and labels
def plotclusters(skills, labels, k):
	N = len(skills)
	fig = plt.figure()
	ax = fig.add_subplot(111)
	scatter = ax.scatter(range(N),skills[:,1],c=labels)
	ax.set_xlabel("Player Ranking")
	ax.set_ylabel("Perceived Skill")
	plt.title("Clustering of Player Ranking vs. Perceived skill for %d clusters" %(k))
	plt.show()

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
	return np.log(np.float64(y)) - logsig(p,x)
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
	old_main()