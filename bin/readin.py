import matplotlib.pyplot as plt 
from six.moves.urllib.request import urlopen
#import six.moves.urllib.parse as urlparse
#import httplib
import requests
import numpy as np 
import scipy as sp 
import json
import argparse
from timeit import default_timer as timer
import os,pickle,time

parser = argparse.ArgumentParser()
parser.add_argument('-v','--verbosity',help='verbosity',default=0)
parser.add_argument('-s','--save',help='save results toggle (default on)[WIP]',default=True)
parser.add_argument('-l','--load',help='load results toggle (default off)[WIP]',default=False)
args = parser.parse_args()
v = int(args.verbosity)
# verbosity for save/load statements
lv = 6
save_res = args.save
load_res = args.load

## TODO: - Finish readin
## 		 - Read set data and results (W/L, game count, etc.)
## 		 - Figure out what to do with the data // what data do we want
## 		 - Pretty printer
## 			- Print relevant IDs
## 			- see below about final placing
## 		 - Calculate absolute final placing (not just within pool)
## 		 - Convert data to absolute player id terms for better main file processing; pass on relevant info
## 		 - garbage collection // reduce filesize of stored files

def readin(tourney,type="slug"):
	if type == "slug":
		slug = tourney
	elif type == "ss":
		slug = get_slug(tourney)
	else:
		print("Error: invalid tourney identifier type")
		return None

	t,ps,pdata = read_phases(slug)

	#t,ps = read_phases("the-big-house-8")
	tid = t[0]
	es,ws,ls,rs,br,ns = read_sets(tid,ps,pdata)

	print_results(rs,ns)
	return es,ns,rs,ws,ls,br

# reads the match data for a given phase
def read_sets(t_id,phases,phase_data):
	entrants = {}
	wins = {}
	losses = {}
	results = {}
	bracket = {}
	names = {}
	end_buff = False

	if load_res and v >= 3:
		print("Loading cached files...")

	for phase in phases:
		pstart = timer()
		load_succ = False
		if load_res and not end_buff:
			try:
				if v >= lv:
					print("Loading %d..."%phase)
				entrants,wins,losses,results,bracket,names = load_all(t_id,phase)
				load_succ = True
			except FileNotFoundError:
				if v >= lv:
					print("Phase group %d not found locally"%phase)
				end_buff = True
				load_succ = False
		if not load_succ:
			data = json.loads(pull_phase(phase))

			wave_id = data['entities']['groups']['phaseId']
			if phase_data[wave_id][1] == 1:
				groupname = phase_data[wave_id][0]
			else:
				groupname = data['entities']['groups']['displayIdentifier']
			names['g_%d'%phase] = groupname
			if v >= 3:
				print("Reading group: %s | %d"%(groupname,phase)) 
			seedata = data['entities']['seeds']

			#i = 0
			for x in seedata:
				#if i < 10:
					#print(x.items())
					#print("\n")
				e_id = x['entrantId']
				part_id = x['mutations']['entrants'][str(e_id)]['participantIds'][0]
				abs_id = x['mutations']['entrants'][str(e_id)]['playerIds'][str(part_id)]
				tag = x['mutations']['participants'][str(part_id)]['gamerTag']
				prefix = x['mutations']['participants'][str(part_id)]['prefix']
				names[e_id] = (prefix,tag)

				continfo = x['mutations']['participants'][str(part_id)]['contactInfo']
				if 'nameFirst' in continfo:
					f_name = continfo['nameFirst']
				else:
					f_name = "N/A"
				if 'nameLast' in continfo:
					l_name = continfo['nameLast']
				else:
					l_name = "N/A"
				if 'state' in continfo:
					state = continfo['state']
				else:
					state = "N/A"
				if 'country' in continfo:
					country = continfo['country']
				else:
					country = 'N/A'
				metainfo = (f_name,l_name,state,country)

				res = x['placement']
				if x['isDisqualified']:
					res = -1

				if v >= 6:
					print(e_id,tag,res)
				if v >= 7 and e_id in results:
					print(results[e_id])

				#flatten = lambda l: [item for sublist in l for item in sublist]
				#if x['progressionSeedId'] == 'null' or x['progressionSeedId'] == None:
				if e_id in results:
					if v >= 8:
						print(results[e_id][1])
					results[e_id][0] = res
					results[e_id][1].extend([phase])
				else:
					results[e_id] = [res,[phase]]
				#else:
				#	if e_id in results:
				#		p = results[e_id][1]
				#		results[e_id][0] = res
				#		results[e_id][1].extend([x['progressingPhaseGroupId']])
				#	else:
				#		results[e_id] = [res,[phase,x['progressingPhaseGroupId']]]
				
				#entrants[i] = (names[i], player_id[i])
				entrants[e_id] = (names[e_id],abs_id,metainfo)
			
			if save_res:
				if v >= lv:
					print("Saving %d..."%phase)
				save_all(t_id,phase,[entrants,wins,losses,results,bracket,names])

		if v >= 3:
			print("{:.0f}".format(1000*(timer()-pstart)) + " ms")
	return entrants,wins,losses,results,bracket,names

# reads the phase data for a given tournament
def read_phases(tourney):
	if v == 2:
		start = timer()
	waves = {}
	#with open(filepath) as f:
	#	data = json.loads(f.read())

	phaselink ="https://api.smash.gg/tournament/%s?expand[]=event&expand[]=groups&expand[]=phase"%tourney
	tfile = urlopen(phaselink).read()
	tdata = json.loads(tfile.decode("UTF-8"))

	t_id = tdata['entities']['tournament']['id']
	t_name = tdata['entities']['tournament']['name']
	t_ss = tdata['entities']['tournament']['shortSlug']
	t_type = tdata['entities']['tournament']['tournamentType']
	# date tuple in (year, month, day) format
	t_date = time.localtime(tdata['entities']['tournament']['startAt'])[:3]
	t_region = (tdata['entities']['tournament']['addrState'],tdata['entities']['tournament']['countryCode'])
	t_info = (t_id,t_name,t_ss,t_type,t_date,t_region)

	if v >= 1:
		print("Reading tournament: %s | %d"%(tdata['entities']['tournament']['name'],t_id))

	event_ids = [event['id'] for event in tdata['entities']['event'] if event['videogameId'] == 1 and event['entrantSizeMin'] == 1]
	phase_ids = [phase['id'] for phase in tdata['entities']['phase'] if phase['eventId'] in event_ids]
	group_ids = [group['id'] for group in tdata['entities']['groups'] if group['phaseId'] in phase_ids]

	for w in tdata['entities']['phase']:
		if w['id'] not in waves:
			waves[w['id']] = [w['name'],w['groupCount'],w['phaseOrder'],w['eventId'],w['typeId'],w['isExhibition']]
	#print(t_id)
	#print(event_ids)
	#print(phase_ids)
	#print(group_ids)
	if v == 2:
		print("{:.3f}".format(timer()-start) + " s")
	
	return (t_info,group_ids,waves)

# returns the full JSON data for a phase given its ID number
def pull_phase(num):
	link = "https://api.smash.gg/phase_group/%d?expand[]=sets&expand[]=seeds"%num
	tempdata = urlopen(link).read()
	return tempdata.decode("UTF-8")

# used to save datasets/hashtables
def save_obj(t_id,phase,obj, name):
	if not os.path.isdir('obj/%d'%t_id):
		os.mkdir(str('obj/%d'%t_id))
	if not os.path.isdir('obj/%d/%d'%(t_id,phase)):
		os.mkdir(str('obj/%d/%d'%(t_id,phase)))
	with open('obj/'+str(t_id)+'/'+str(phase)+'/'+name +'.pkl','wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

# used to load datasets/hashtables
def load_obj(t_id,phase,name):
	with open('obj/'+str(t_id)+'/'+str(phase)+'/'+name+'.pkl','rb') as f:
		return pickle.load(f)

# saves all params for the load_sets function
def save_all(t_id,phase,params):
	names = ["entrants","wins","losses","results","bracket","names"]
	for param,name in zip(params,names):
		save_obj(t_id,phase,param,name)

# load all params for the load_sets function
def load_all(t_id,phase):
	names = ["entrants","wins","losses","results","bracket","names"]
	return [load_obj(t_id,phase,name) for name in names]

# prints smash.gg query pulls as pretty JSON .txt files
def clean_data(infile, outfile):
	with open(infile) as i_f:
		data = json.loads(i_f.read())
	o_f = open(outfile,"w")
	o_f.write(json.dumps(data,indent=4))
	o_f.close()

# returns the full slug (needed to pull tourney data) given the short slug
def get_slug(ss):
	url = "https://smash.gg/%s"%ss
	full_url = unshorten_url(url)

	idx = (full_url.split('/')).index("tournament")
	return full_url.split('/')[idx+1]

# unshortens a shortened url, if shortened
# (used to get slugs from short slugs)
def unshorten_url(url):
	session = requests.Session()
	resp = session.head(url, allow_redirects=True)
	return resp.url

# prints tournament results by player's final placing
def print_results(res,names):
	res_l = [item for item in res.items()]

	res_s = sorted(res_l, key=lambda l: (len(l[1][1]),0-l[1][0]), reverse=True)

	print("\nSponsor\t\t","Tag\t\t\t","Player ID\t","Placing\t","Bracket")
	for player in res_s:
		if names[player[0]][0] == "" or names[player[0]][0] == None:
			sp = "  "
		else:
			sp = names[player[0]][0]
			if len(sp) > 12:
				sp = sp[:8] + "... |"
			else:
				sp = names[player[0]][0] + " |"
		tag = names[player[0]][1]
		if len(tag) > 24:
			tag = tag[:21]+"..."
		print("{:>13.13}".format(sp),"{:<24.24}".format(names[player[0]][1]),"\t",player[0],"\t",player[1][0],"\t",[names['g_%d'%group] for group in player[1][1]])
	return(res_s)

if __name__ == "__main__":
	readin('summit7',type='ss')

	#print(get_slug('tbh8'))



	#read_sets("sets.txt")
	#pull_phase(764818)

	#clean_data("phases.txt","phasesclean.txt")
	#clean_data("sets.txt","setsclean.txt")