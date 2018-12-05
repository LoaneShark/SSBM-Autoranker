import matplotlib.pyplot as plt 
from six.moves.urllib.request import urlopen
import numpy as np 
import scipy as sp 
import json

## TODO: - Finish set data readin
## 		 - Figure out what to do with the data // what data do we want

def readin():
	print("Henlo")

# reads the match data for a given phase
def read_sets(phases):
	entrants = {}
	wins = {}
	losses = {}
	results = {}
	pools = {}
	bracket = {}

	for phase in phases:
		data = pull_phase(phase)
		seedata = data['entities']['seeds']

		for x in seedata:
			e_id = x['entrantId']
			res = x['placement']
			if x['isDisqualified']:
				res = -1

			flatten = lambda l: [item for sublist in l for item in sublist]
			if e_id in bracket:
				
			else:
				bracket[e_id] = (,[phase,x['progressingPhaseGroupId']])

			entrants[e_id] = (x['mutations']['entrants'][str(e_id)]['name'],x['mutations']['entrants'][str(e_id)]['playerIds'][str(x['mutations']['entrants'][str(e_id)]['participantIds'][0])])

	print(entrants)
	return entrants,wins,losses,results

# reads the phase data for a given tournament
def read_phases(tourney,getBracket=False):
	waves = {}
	#with open(filepath) as f:
	#	data = json.loads(f.read())

	phaselink ="https://api.smash.gg/tournament/%s?expand[]=event&expand[]=groups&expand[]=phase"%tourney
	tfile = urlopen(phaselink).read()
	tdata = json.loads(tfile.decode("UTF-8"))

	t_id = tdata['entities']['tournament']['id']

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
	if getBracket:
		return (t_id,group_ids,waves)
	else:
		return (t_id,group_ids)

# returns the full JSON data for a phase given its ID number
def pull_phase(num):
	link = "https://api.smash.gg/phase_group/%d?expand[]=sets&expand[]=seeds"%num
	tempdata = urlopen(link).read()
	return tempdata.decode("UTF-8")


def clean_data(infile, outfile):
	with open(infile) as i_f:
		data = json.loads(i_f.read())
	o_f = open(outfile,"w")
	o_f.write(json.dumps(data,indent=4))
	o_f.close()

if __name__ == "__main__":
	#read_sets("sets.txt")

	#pull_phase(764818)
	print(read_phases("the-big-house-8"))

	#clean_data("phases.txt","phasesclean.txt")
	#clean_data("sets.txt","setsclean.txt")