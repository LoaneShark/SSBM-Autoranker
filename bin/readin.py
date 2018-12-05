import matplotlib.pyplot as plt 
from six.moves.urllib.request import urlopen
import numpy as np 
import scipy as sp 
import json
import argparse
from timeit import default_timer as timer
import os,pickle

parser = argparse.ArgumentParser()
parser.add_argument('-v','--verbosity',help='verbosity',default=0)
parser.add_argument('-s','--save',help='save results toggle (default on)[WIP]',default=True)
parser.add_argument('-l','--load',help='load results toggle (default off)[WIP]',default=False)
args = parser.parse_args()
v = int(args.verbosity)
# verbosity for save/load statements
lv = 3
save_res = args.save
load_res = args.load

## TODO: - Finish readin
## 		 - Read set data and results (W/L, game count, etc.)
## 		 - Figure out what to do with the data // what data do we want
## 		 - Save and load results

def readin():
	print("Henlo")

# reads the match data for a given phase
def read_sets(phases):
	entrants = {}
	wins = {}
	losses = {}
	results = {}
	bracket = {}
	names = {}
	end_buff = False

	for phase in phases:
		pstart = timer()
		load_succ = False
		if load_res and not end_buff:
			try:
				if v >= lv:
					print("Loading %d..."%phase)
				entrants,wins,losses,results,bracket,names = load_all(phase)
				load_succ = True
			except FileNotFoundError:
				if v >= lv:
					print("Phase group %d not found locally"%phase)
				end_buff = True
				load_succ = False
		if not load_succ:
			data = json.loads(pull_phase(phase))
			if v >= 3:
				print("Reading group: %s | %d"%(data['entities']['groups']['displayIdentifier'],phase)) 
			seedata = data['entities']['seeds']

			#i = 0
			for x in seedata:
				#if i < 10:
					#print(x.items())
					#print("\n")
				e_id = x['entrantId']
				tag = x['mutations']['entrants'][str(e_id)]['name']
				names[e_id] = tag
				res = x['placement']
				if x['isDisqualified']:
					res = -1

				if v >= 4:
					print(e_id,tag,res)
				if v >= 5 and e_id in results:
					print(results[e_id])

				flatten = lambda l: [item for sublist in l for item in sublist]
				if x['progressionSeedId'] == 'null' or x['progressionSeedId'] == None:
					if e_id in results:
						results[e_id] = [res,[results[e_id][1]].extend(phase)]
					else:
						results[e_id] = [res,phase]
				else:
					if e_id in results:
						results[e_id] = [res,[results[e_id][1].extend(x['progressingPhaseGroupId'])]]
					else:
						results[e_id] = [res,[phase,x['progressingPhaseGroupId']]]
				#i = i+1
				entrants[e_id] = (x['mutations']['entrants'][str(e_id)]['name'],x['mutations']['entrants'][str(e_id)]['playerIds'][str(x['mutations']['entrants'][str(e_id)]['participantIds'][0])])
			
			if save_res:
				if v >= lv:
					print("Saving %d..."%phase)
				save_all(phase,[entrants,wins,losses,results,bracket,names])

		if v >= 3:
			print("{:.0f}".format(1000*(timer()-pstart)) + " ms")
	return entrants,wins,losses,results,bracket,names

# reads the phase data for a given tournament
def read_phases(tourney,getBracket=False):
	if v == 2:
		start = timer()
	waves = {}
	#with open(filepath) as f:
	#	data = json.loads(f.read())

	phaselink ="https://api.smash.gg/tournament/%s?expand[]=event&expand[]=groups&expand[]=phase"%tourney
	tfile = urlopen(phaselink).read()
	tdata = json.loads(tfile.decode("UTF-8"))

	t_id = tdata['entities']['tournament']['id']

	if v >= 1:
		print("Reading tournament: %s | %d"%(tdata['entities']['tournament']['name'],t_id))

	event_ids = [event['id'] for event in tdata['entities']['event'] if event['videogameId'] == 1 and event['entrantSizeMin'] == 1]
	phase_ids = [phase['id'] for phase in tdata['entities']['phase'] if phase['eventId'] in event_ids]
	group_ids = [group['id'] for group in tdata['entities']['groups'] if group['phaseId'] in phase_ids]

	for w in tdata['entities']['groups']:
		if w['id'] not in waves:
			waves[w['id']] = [w['phaseId'],w['winnersTargetPhaseId'],w['losersTargetPhaseId']]
	#print(t_id)
	#print(event_ids)
	#print(phase_ids)
	#print(group_ids)
	if v == 2:
		print("{:.3f}".format(timer()-start) + " s")

	if getBracket:
		return (t_id,group_ids,waves)
	else:
		return (t_id,group_ids)

# returns the full JSON data for a phase given its ID number
def pull_phase(num):
	link = "https://api.smash.gg/phase_group/%d?expand[]=sets&expand[]=seeds"%num
	tempdata = urlopen(link).read()
	return tempdata.decode("UTF-8")

# used to save datasets/hashtables
def save_obj(phase,obj, name):
	if not os.path.exists('obj/%d'%phase):
		os.mkdir(str('obj/%d'%phase))
	with open('obj/'+ str(phase) + '/' + name + '.pkl', 'wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

# used to load datasets/hashtables
def load_obj(phase,name):
	with open('obj/' + str(phase) + '/' + name + '.pkl', 'rb') as f:
		return pickle.load(f)

# saves all params for the load_sets function
def save_all(phase,params):
	names = ["entrants","wins","losses","results","bracket","names"]
	for param,name in zip(params,names):
		save_obj(phase,param,name)

# load all params for the load_sets function
def load_all(phase):
	names = ["entrants","wins","losses","results","bracket","names"]
	return [load_obj(phase,name) for name in names]

# prints smash.gg query pulls as pretty JSON .txt files
def clean_data(infile, outfile):
	with open(infile) as i_f:
		data = json.loads(i_f.read())
	o_f = open(outfile,"w")
	o_f.write(json.dumps(data,indent=4))
	o_f.close()

# prints tournament results by player's final placing
def print_results(res,tags):
	res_l = [item for item in res.items()]

	res_s = sorted(res_l, key=lambda l: l[0])

	for player in res_s:
		print(tags[player[0]],player)
	return(res_s)

if __name__ == "__main__":
	#read_sets("sets.txt")

	#pull_phase(764818)
	tid,ps = read_phases("the-big-house-8")
	es,ws,ls,rs,br,ns = read_sets(ps)

	print_results(rs,ns)

	#clean_data("phases.txt","phasesclean.txt")
	#clean_data("sets.txt","setsclean.txt")