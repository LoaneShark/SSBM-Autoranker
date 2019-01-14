#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen
from six.moves.urllib.parse import urlencode
import requests
import re,os,pickle,time,json
from emoji import UNICODE_EMOJI
#from google.cloud import translate as g_translate
from googletrans import Translator
import regex
import shutil
import subprocess
#from translation import baidu

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
				3: ['ssb4','smash 4','ssb wii u','smash wii u','for wii u'], 4: ['smash 64','ssb64'], 5: ['brawl','ssbb'], 1386: ['ssbu','ultimate','sp','special','ssbs']}):
	if descr == None:
		return False
	else:
		return any([re.search(keyword,descr,re.IGNORECASE) for keyword in gamemap[game]])

# returns true if the description contains explicit mention of being the right team size
def is_teams(descr,teamsize):
	ts = min(teamsize,4)
	teammap = {1: ['singles','solo','1v1','1 v 1','1 vs 1','1vs1','ones'],2:['doubles','dubs','teams','2v2','2 v 2','2vs2','2 vs 2','pairs','duos','twos'],3:['3v3','3 v 3','3vs3','3 vs 3','triples'], \
				4: ['4v4','4 v 4','4vs4','4 vs 4','4 on 4','quads','crews','squads','fours','quartets','groups','crew']}
	if descr == None:
		return False
	else:
		return any([re.search(keyword,descr,re.IGNORECASE) for keyword in teammap[ts]])

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

# detects if a character is chinese, japanese, or korean
def is_cjk(char):
	ranges = [
	  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
	  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
	  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
	  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
	  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
	  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
	  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
	  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
	  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
	  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
	  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
	  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
	  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
	]
	return any([range["from"] <= ord(char) <= range["to"] for range in ranges])

# uses google's API to return translated names
def translate(text, src = '', to = 'en'):
	#parameters = ({'langpair': '{0}|{1}'.format(src, to), 'v': '1.0' })
	translated = '@@@'
	#dir_path = os.path.dirname(os.path.abspath(__file__))
	#parent_dir = '\\'.join(dir_path.split('\\')[:-1])
	#keyfile_path = parent_dir + '\\lib\\gcloud_keyfile.json'
	#print(keyfile_path)
	#print(os.path.isfile(keyfile_path))
	#subprocess.check_call(['set GOOGLE_APPLICATION_CREDENTIALS=%s'%keyfile_path])
	#print(os.system('set GOOGLE_APPLICATION_CREDENTIALS=%s'%keyfile_path))
	translator = Translator()
	#translate_client = g_translate.Client()
	#for text in (text[index:index + 4500] for index in range(0, len(text), 4500)):
		#parameters['q'] = text
		#response = json.loads(urlopen('http://ajax.googleapis.com/ajax/services/language/translate', data = urlencode(parameters).encode('utf-8')).read().decode('utf-8'))
		#response = translate_client.translate(text,target_language=to)
	translated = translator.translate(text,dest=to)
		#print(text)
		#print(response)

	#try:
	#	translated += response['translatedText']
	#except:
	#	pass

	#print(translated.text)
	return translated

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
		if name == 'skills':
			s = {}
			s['elo'] = {}
			s['elo_del'] = {}
			s['glicko'] = {}
			s['glicko_del'] = {}
			s['sim'] = {}
			s['sim_del'] = {}
			s['perf'] = {}
			save_dict(s,name,ver,loc)
			return s
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
		try:
			shutil.rmtree('obj/%d'%t_id)
		except OSError:
			return

# prints tournament results by player's final placing
def print_results(res,names,entrants,losses,max_place=64,translate_cjk=True):
	maxlen = 0

	res_l = [item for item in res.items()]
	res_s = sorted(res_l, key=lambda l: (0-l[1][0],len(l[1][1])), reverse=True)

	# Error catching
	if res == [] or len(res) <= 0:
		print("Error: no bracket found")
		return False

	team_mult = max([len(names[plyr[0]][1]) for plyr in res_s])
	#print(team_mult,names[res_s[0][0]])

	num_rounds = len(res_s[0][1][1])
	#lsbuff = "\t"*(num_rounds-len(res_s[-1][1][1])+1)
	roundnames = [names['groups'][group] for group in res_s[0][1][1]]
	roundslen = sum([len(str(name)) for name in roundnames]) + 2*num_rounds
	sp_slot = 13*team_mult
	tag_slot = 24*team_mult
	tag_title = "Tag"
	if team_mult >= 4:
		sp_slot = 0
		tag_slot = 24
		tag_title = "Crew"
	id_slot = 8*team_mult
	print(team_mult)
	print(("\n{:>%d.%d}"%(sp_slot,sp_slot)).format("Sponsor |"),("{:<%d.%d}"%(tag_slot,tag_slot)).format(tag_title),("{:<%d.%d}"%(id_slot,id_slot)).format("ID #"), \
		"Place\t",("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("Bracket"),"Losses\n")
	for player in res_s:
		#if type(team_s[0]) is int:
		#	team = [team_s]
		#else:
		#	team = team_s
		#for player in team:
		if player[1][0] > max_place and max_place > 0:
			break
		else:
			playerstrings = []
			entr_mult = len(names[player[0]][1])
			for idx in range(entr_mult):
				if names[player[0]][0][idx] == "" or names[player[0]][0][idx] == None:
					sp = "  "
				else:
					sp = names[player[0]][0][idx]
					if translate_cjk:
						if any([is_cjk(tsp_char) for sp_char in sp]):
							#tag = '『'+''.join(translate(tag_char) for tag_char in tag)+'』'
							sp = '<'+(translate(sp,to='ja')).pronunciation+'>'
					if len(sp) > 12:
						sp = sp[:8] + "... |"
					else:
						if sp[-2:] != " |":
							#sp = "/".join(str(n) for n in names[player[0]][0]) + " |"
							sp = names[player[0]][0][idx] + " |"
				sp_slot = 13#*team_mult
				for ch in sp:
					if is_emoji(ch):
						sp_slot -= 1
				#tag = "/".join(str(n) for n in names[player[0]][1])
				tag = names[player[0]][1][idx]
				if translate_cjk:
					if any([is_cjk(tag_char) for tag_char in tag]):
						#tag = '『'+''.join(translate(tag_char) for tag_char in tag)+'』'
						tag = '<'+(translate(tag,to='ja')).pronunciation+'>'
						#tag = '<'+''.join([(translate(tag_char)).text for tag_char in tag])+'>'
				tag_slot = 24#*team_mult
				if len(tag) > tag_slot:
					tag = tag[:tag_slot-3]+"..."
				for ch in tag:
					if is_emoji(ch):
						tag_slot -= 1

				playerstrings.extend([(sp,tag)])

			if player[0] in losses:
				#print(losses)
				if len(playerstrings) >= 4:
					ls_list = [entrants[loss[0]][0][2] for loss in losses[player[0]]]
				else:
					ls_list = [" / ".join(str(j) for j in l) for l in [names[loss[0]][1] for loss in losses[player[0]]]]

				if translate_cjk:
					ls_list = ['<'+(translate(l_tag,to='ja')).pronunciation+'>' if any([is_cjk(l_tag_char) for l_tag_char in l_tag]) else l_tag for l_tag in ls_list]
					#for l_tag in ls_list:
					#	if any([is_cjk(l_tag_char) for l_tag_char in l_tag]):
					#		print("ohno")
					#		ls_list.replace(l_tag,'<'+(translate(l_tag,to='ja')).pronunciation+'>')
					#		print(l_tag,ls_list)

				ls = "["+", ".join(ls_list)+"]"
			else:
				ls = None

			#if len(player[1][1]) > maxlen:
			#	maxlen = len(player[1][1])
			#lsbuff = "\t"*(maxlen-len(player[1][1])+1)
			#if len(player[1][1]) > 2:
			#	lsbuff = "\t"
			#else:
			#	lsbuff = "\t\t\t"
			if len(playerstrings) == 1: #or len(playerstrings) >= 4:
				print(("{:>%d.%d}"%(sp_slot,sp_slot)).format(sp),("{:<%d.%d}"%(tag_slot,tag_slot)).format(tag),("{:>%d.%d}"%(8*team_mult,8*team_mult)).format(" / ".join(str(n) for n in entrants[player[0]][1])), \
				"  {:<5.5}".format(str(player[1][0])),("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("["+", ".join(str(i) for i in [names['groups'][group] for group in player[1][1]])+"]"),ls)
			elif len(playerstrings) >= 4: #or len(playerstrings) >= 4:
				team_name = entrants[player[0]][0][2]
				print(("{:<%d.%d}"%(tag_slot,tag_slot)).format(team_name),("{:>%d.%d}"%(8*team_mult,8*team_mult)).format(" / ".join(str(n) for n in entrants[player[0]][1])), \
				"  {:<5.5}".format(str(player[1][0])),("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("["+", ".join(str(i) for i in [names['groups'][group] for group in player[1][1]])+"]"),ls)
			else:
				print(("{:<%d.%d}"%(team_mult*(sp_slot+tag_slot),team_mult*(sp_slot+tag_slot))).format(" & ".join(("{:<%d.%d}"%(sp_slot+tag_slot,sp_slot+tag_slot)).format(("{:>%d.%d}"%(sp_slot,sp_slot)).format(sp)+" "+("{:<%d.%d}"%(tag_slot,tag_slot)).format(tag)) for sp,tag in playerstrings)), \
					("{:>%d.%d}"%(8*team_mult,8*team_mult)).format("/".join(str(n) for n in entrants[player[0]][1])), \
				"  {:<5.5}".format(str(player[1][0])),("{:<%d.%d}"%(roundslen+5,roundslen+5)).format("["+", ".join(str(i) for i in [names['groups'][group] for group in player[1][1]])+"]"),ls)

	return(res_s)