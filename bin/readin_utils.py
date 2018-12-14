#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen
import requests
import re,os,pickle,time,json

## AUXILIARY FUNCTIONS
# returns the full slug (needed to pull tourney data) given the short slug
def get_slug(ss):
	url = "https://smash.gg/%s"%ss
	full_url = unshorten_url(url)

	idx = (full_url.split('/')).index("tournament")
	return full_url.split('/')[idx+1]

# returns true if the description contains explicit mention of melee/SSBM
def has_melee(descr):
	if descr == None:
		return False
	else:
		return re.search('melee',descr,re.IGNORECASE) or re.search('SSBM',descr,re.IGNORECASE) or re.search('SSBMelee',descr,re.IGNORECASE)

def is_amateur(descr):
	if descr == None:
		return False
	else:
		return re.search('amateur',descr,re.IGNORECASE) or re.search('redemption',descr,re.IGNORECASE) or re.search('novice',descr,re.IGNORECASE) \
		or re.search('beginner',descr,re.IGNORECASE)

def is_arcadian(descr):
	if descr == None:
		return False
	else:
		return re.search('arcadian',descr,re.IGNORECASE) or re.search('unranked',descr,re.IGNORECASE)

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
	names = ["entrants","wins","losses","results","names"]
	for param,name in zip(params,names):
		save_obj(t_id,phase,param,name)

# load all params for the load_sets function
def load_all(t_id,phase):
	names = ["entrants","wins","losses","results","names"]
	return [load_obj(t_id,phase,name) for name in names]

# prints smash.gg query pulls as pretty JSON .txt files
def clean_data(infile, outfile):
	with open(infile) as i_f:
		data = json.loads(i_f.read())
	o_f = open(outfile,"w")
	o_f.write(json.dumps(data,indent=4))
	o_f.close()

# unshortens a shortened url, if shortened
# (used to get slugs from short slugs)
def unshorten_url(url):
	session = requests.Session()
	resp = session.head(url, allow_redirects=True)
	return resp.url

# prints tournament results by player's final placing
def print_results(res,names,entrants,losses,max_place=64):
	maxlen = 0

	res_l = [item for item in res.items()]
	res_s = sorted(res_l, key=lambda l: (len(l[1][1]),0-l[1][0]), reverse=True)

	lsbuff = "\t"*(len(res_s[0][1][1])-len(res_s[-1][1][1])+1)
	num_rounds = len(res_s[0][1][1])
	roundnames = [names['g_%d'%group] for group in res_s[0][1][1]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 4*num_rounds
	print("\n{:>13.13}".format("Sponsor |"),"{:<24.24}".format("Tag"),"ID #\t","Place\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("Bracket"),"Losses\n")
	for player in res_s:
		if player[1][0] > max_place and max_place > 0:
			break
		else:
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

			if player[0] in losses:
				#print(losses)
				ls = [names[loss[0]][1] for loss in losses[player[0]]]
			else:
				ls = None

			if len(player[1][1]) > maxlen:
				maxlen = len(player[1][1])
			lsbuff = "\t"*(maxlen-len(player[1][1])+1)
			#if len(player[1][1]) > 2:
			#	lsbuff = "\t"
			#else:
			#	lsbuff = "\t\t\t"

			print("{:>13.13}".format(sp),"{:<24.24}".format(names[player[0]][1]),"{:>7.7}".format(str(entrants[player[0]][1])),"  {:<5.5}".format(str(player[1][0])),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format(str([names['g_%d'%group] for group in player[1][1]])),ls)
	return(res_s)