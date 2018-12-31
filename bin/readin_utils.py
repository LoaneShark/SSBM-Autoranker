#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen
import requests
import re,os,pickle,time,json
from emoji import UNICODE_EMOJI
import regex
import shutil

## AUXILIARY FUNCTIONS
# returns the full slug (needed to pull tourney data) given the short slug
def get_slug(ss):
	url = "https://smash.gg/%s"%ss
	full_url = unshorten_url(url)

	idx = (full_url.split('/')).index("tournament")
	return full_url.split('/')[idx+1]

# returns true if the description contains explicit mention of a given game (default melee/SSBM)
#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386
def has_game(descr,game=1, gamemap={1: ['melee','ssbm','ssbmelee'], 2: ['P:M','project: m','project melee','project m'], \
				3: ['ssb4','smash 4','ssb wii u','smash wii u','for wii u'], 4: ['smash 64','ssb64'], 5: ['brawl','ssbb'], 1386: ['ssbu','ultimate']}):
	if descr == None:
		return False
	else:
		return any([re.search(keyword,descr,re.IGNORECASE) for keyword in gamemap[game]])

# returns true if the description contains explicit mention of being the right team size
def is_teams(descr,teamsize):
	teammap = {1: ['singles','solo','1v1','1 v 1','1 vs 1','1vs1'],2:['doubles','teams','2v2','2 v 2','2 vs 2','pairs','duos'],3:['3v3','3 v 3','3 vs 3','triples']}
	if descr == None:
		return False
	else:
		return re.search('arcadian',descr,re.IGNORECASE) or re.search('unranked',descr,re.IGNORECASE)

# returns true if the description contains explicit mention of being an amateur/side bracket
def is_amateur(descr):
	if descr == None:
		return False
	else:
		return re.search('amateur',descr,re.IGNORECASE) or re.search('novice',descr,re.IGNORECASE) or re.search('newbie',descr,re.IGNORECASE)\
		or re.search('beginner',descr,re.IGNORECASE) or re.search('newcomer',descr,re.IGNORECASE)#or re.search('redemption',descr,re.IGNORECASE)

# returns true if the description contains explicit mention of being an arcadian
def is_arcadian(descr):
	if descr == None:
		return False
	else:
		return re.search('arcadian',descr,re.IGNORECASE) or re.search('unranked',descr,re.IGNORECASE)

# returns true if the description contains explicit mention of being a ladder
def is_ladder(descr):
	if descr == None:
		return False
	else:
		return re.search('ladder',descr,re.IGNORECASE) or re.search('staircase',descr,re.IGNORECASE) or re.search('stairway',descr,re.IGNORECASE)

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

# returns True if a given string is only ascii characters
def is_ascii(s):
	if has_emojis(s):
		return False
	else:
		return len(s) == len(s.encode())

# returns True if a given string contains emoji characters
# NOTE: currently ONLY works for FLAG EMOJIS (\U0001F1E6-\U0001F1FF)
def is_emoji(s,print_e=False):
	#s = s.encode('utf8').decode('utf8')
	data = regex.findall(r'\X', s)
	flags = regex.findall(u'[\U0001F1E6-\U0001F1FF]', s)
	if print_e:
		print("data: ",data)
		print("flags: ",flags)
		print(s)
	for word in data:
		if any(char[0] in UNICODE_EMOJI for char in data):
			if print_e:
				print("data loop ",char)
			return True
	for word in flags:
		if any(char in UNICODE_EMOJI for char in word):
			if print_e:
				print("flag loop ",char)
			return True
	if len(flags) > 0:
		return True
	return False

# saves a single dict
def save_dict(data,name,ver,loc='db'):
	if not os.path.isdir('%s'%loc):
		os.mkdir(str('%s'%loc))
	if not os.path.isdir('%s/%s'%(loc,ver)):
		os.mkdir(str('%s/%s'%(loc,ver)))
	#if not os.path.isdir('%s/%s/%s'%(loc,ver,name)):
	#	os.mkdir(str('%s/%s/%s'%(loc,ver,name)))
	with open(str(loc)+'/'+str(ver)+'/'+name +'.pkl','wb') as f:
		pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

# loads a single dict
def load_dict(name,ver,loc='db'):
	try:
		with open(str(loc)+'/'+str(ver)+'/'+name+'.pkl','rb') as f:
			return pickle.load(f) 
	except FileNotFoundError:
		if name == 'tourneys':
			t = {}
			t['slugs'] = {}
			#t['groups'] = {}
			save_dict(t,name,ver,loc)
			return t
		else:
			save_dict({},name,ver,loc)
			return {}

# saves the slugs pulled by scraper to avoid having to rescrape every time
def save_slugs(slugs,game,year,loc='db',to_save_db=True):
	if to_save_db:
		#if v >= 4:
		#	print("Saving scraped slugs...")
		if not os.path.isdir('%s/%s'%(loc,game)):
			os.mkdir(str('%s/%s'%(loc,game)))
		if not os.path.isdir('%s/%s/slugs'%(loc,game)):
			os.mkdir(str('%s/%s/slugs'%(loc,game)))
		with open(str(loc)+'/'+str(game)+'/slugs/'+str(year) +'.pkl','wb') as f:
			pickle.dump(slugs, f, pickle.HIGHEST_PROTOCOL)
		return True
	else:
		return False

# loads the slugs pulled by scraper to avoid having to rescrape every time
def load_slugs(game,year,loc='db'):
	try:
		with open(str(loc)+'/'+str(game)+'/slugs/'+str(year)+'.pkl','rb') as f:
			return pickle.load(f) 
	except FileNotFoundError:
		return False

# deletes the json pulls and phase data stored by readin
# (for use once a tourney has been imported fully, to remove garbage files from accumulating)
def delete_tourney_cache(t_id):
	if os.path.isdir('obj/%d'%t_id):
		shutil.rmtree('obj/%d'%t_id)

# prints tournament results by player's final placing
def print_results(res,names,entrants,losses,max_place=64):
	maxlen = 0

	res_l = [item for item in res.items()]
	res_s = sorted(res_l, key=lambda l: (0-l[1][0],len(l[1][1])), reverse=True)

	num_rounds = len(res_s[0][1][1])
	#lsbuff = "\t"*(num_rounds-len(res_s[-1][1][1])+1)
	roundnames = [names['groups'][group] for group in res_s[0][1][1]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 2*num_rounds
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
					if sp[-2:] != " |":
						sp = names[player[0]][0] + " |"
			sp_slot = 13
			for ch in sp:
				if is_emoji(ch):
					sp_slot -= 1
			tag = names[player[0]][1]
			tag_slot = 24
			if len(tag) > tag_slot:
				tag = tag[:21]+"..."
			for ch in tag:
				if is_emoji(ch):
					tag_slot -= 1
			if player[0] in losses:
				#print(losses)
				ls = "["+", ".join(str(l) for l in [names[loss[0]][1] for loss in losses[player[0]]])+"]"
			else:
				ls = None

			if len(player[1][1]) > maxlen:
				maxlen = len(player[1][1])
			lsbuff = "\t"*(maxlen-len(player[1][1])+1)
			#if len(player[1][1]) > 2:
			#	lsbuff = "\t"
			#else:
			#	lsbuff = "\t\t\t"
			print(("{:>%d.%d}"%(sp_slot,sp_slot)).format(sp),("{:<%d.%d}"%(tag_slot,tag_slot)).format(names[player[0]][1]),"{:>7.7}".format(str(entrants[player[0]][1])), \
				"  {:<5.5}".format(str(player[1][0])),"\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("["+", ".join(str(i) for i in [names['groups'][group] for group in player[1][1]])+"]"),ls)
	return(res_s)