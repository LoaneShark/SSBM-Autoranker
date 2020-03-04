#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen,Request
from six.moves.urllib.error import HTTPError
import matplotlib.image as mpimg
#from six.moves.urllib.parse import urlencode
import requests
import re,os,pickle,time,json
from emoji import UNICODE_EMOJI
#from json.decoder import JSONDecodeError
#from google.cloud import translate as g_translate
#from googletrans import Translator
#import romkan
from pykakasi import kakasi,wakati
import regex
import shutil
import subprocess
#from translation import baidu
from arg_utils import *

## OVERHEAD FUNCTIONS

## AUXILIARY FUNCTIONS
# returns the full slug (needed to pull tourney data) given the short slug
def get_slug(ss):
	url = 'https://smash.gg/%s'%ss
	full_url = unshorten_url(url)

	idx = (full_url.split('/')).index('tournament')
	return full_url.split('/')[idx+1]

# returns true if the description contains explicit mention of a given game (default melee/SSBM)
#SSB = 4 	SSBM = 1	SSBB = 5 	P:M = 2		SSB4 = 3 	SSBU = 1386 	RoA = 24
def has_game(descr,game=1, gamemap={1: ['melee','ssbm','ssbmelee'], 2: ['P:M','project: m','project melee','project m','PM'], \
				3: ['ssb4','smash 4','ssb wii u','smash wii u','for wii u','wii u','wiiu','sm4sh','smash4'], 4: ['smash 64','ssb64','64','n64'], \
				5: ['brawl','ssbb'], 1386: ['ssbu','ultimate','sp','special','ssbs','smush','smultimate','5mash','5ma5h','sma5h','smash 5','smash5'],\
				24: ['rivals','aether','roa','rivahls']}):
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
	link = 'https://api.smash.gg/phase_group/%d?expand[]=sets&expand[]=seeds'%num
	#link = 'https://api.smash.gg/phase_group/%d?expand[]=sets&expand[]=seeds&expand[]=player'%num
	tempdata = urlopen(link).read()
	return tempdata.decode('UTF-8')

# used to save datasets/hashtables
def save_obj(t_id,phase,obj, name):
	if not os.path.isdir('obj'):
		os.mkdir('obj')
	if not os.path.isdir('obj/%d'%t_id):
		os.mkdir(str('obj/%d'%t_id))
	if not os.path.isdir('obj/%d/%d'%(t_id,phase)):
		os.mkdir(str('obj/%d/%d'%(t_id,phase)))
	with open('obj/'+str(t_id)+'/'+str(phase)+'/'+name +'.pkl','wb') as f:
		pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
	return True

# used to load datasets/hashtables
def load_obj(t_id,phase,name):
	with open('obj/'+str(t_id)+'/'+str(phase)+'/'+name+'.pkl','rb') as f:
		return pickle.load(f)

# saves all params for the load_sets function
def save_all(t_id,phase,params):
	names = ['entrants','wins','losses','results','names','meta','sets']
	return all([save_obj(t_id,phase,param,name) for param,name in zip(params,names)])

# load all params for the load_sets function
def load_all(t_id,phase):
	names = ['entrants','wins','losses','results','names','meta','sets']
	return [load_obj(t_id,phase,name) for name in names]

# prints smash.gg query pulls as pretty JSON .txt files (for human readability)
def clean_data(infile, outfile):
	with open(infile) as i_f:
		data = json.loads(i_f.read())
	o_f = open(outfile,'w')
	o_f.write(json.dumps(data,indent=4))
	o_f.close()
	return True

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
	if s in UNICODE_EMOJI:
		return True
	data = regex.findall(r'\X', s)
	flags = regex.findall(u'[\U0001F1E6-\U0001F1FF]', s)
	if print_e:
		print('data: ',data)
		print('flags: ',flags)
		print(s)
	for word in data:
		if any(char[0] in UNICODE_EMOJI for char in data):
			if print_e:
				print('data loop ',char)
			return True
	for word in flags:
		if any(char in UNICODE_EMOJI for char in word):
			if print_e:
				print('flag loop ',char)
			return True
	if len(flags) > 0:
		return True
	return False

# detects if a character is chinese, japanese, or korean
def is_cjk(char):
	ranges = [
	  {'from': ord(u'\u3300'), 'to': ord(u'\u33ff')},         # compatibility ideographs
	  {'from': ord(u'\ufe30'), 'to': ord(u'\ufe4f')},         # compatibility ideographs
	  {'from': ord(u'\uf900'), 'to': ord(u'\ufaff')},         # compatibility ideographs
	  {'from': ord(u'\U0002F800'), 'to': ord(u'\U0002fa1f')}, # compatibility ideographs
	  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
	  {'from': ord(u'\u30a0'), 'to': ord(u'\u30ff')},         # Japanese Katakana
	  {'from': ord(u'\u2e80'), 'to': ord(u'\u2eff')},         # cjk radicals supplement
	  {'from': ord(u'\u4e00'), 'to': ord(u'\u9fff')},
	  {'from': ord(u'\u3400'), 'to': ord(u'\u4dbf')},
	  {'from': ord(u'\U00020000'), 'to': ord(u'\U0002a6df')},
	  {'from': ord(u'\U0002a700'), 'to': ord(u'\U0002b73f')},
	  {'from': ord(u'\U0002b740'), 'to': ord(u'\U0002b81f')},
	  {'from': ord(u'\U0002b820'), 'to': ord(u'\U0002ceaf')}  # included as of Unicode 8.0
	]
	return any([range['from'] <= ord(char) <= range['to'] for range in ranges])

# detects if a string contains cjk characters
def has_cjk(text):
	return any([is_cjk(text_char) for text_char in str(text)])

# transliterates japanese text to english characters
def transliterate(text):

	translator = kakasi()
	translator.setMode('H','a')
	translator.setMode('K','a')
	translator.setMode('J','a')
	translator.setMode('r','Hepburn')
	#translator.setMode('s',True)
	translator.setMode('C',True)
	conv = translator.getConverter()
	return conv.do(text)

	## DEPRECATED
	#trans_text = romkan.to_hepburn(text)
	#if trans_text == text:
	#	trans_text2 = kanji_to_romaji(text)
	#	if trans_text2 == text:
	#		return trans_text
	#	else:
	#		return trans_text2
	#else:
	#	return trans_text

# transliterates text with mixed cjk and roman characters
# (DEPRECATED)
def transliterate_split_cjk(text):
	#char_bools = [is_cjk(text_char) for text_char in text]
	cjk_char = False
	first_idx = 0
	tempstr = ''
	for i in range(len(text)):
		# if character is in cjk block::
		if is_cjk(text[i]) or text[i] in [' ','-']:
			# if it's the first one, start recording indices
			if cjk_char == False:
				first_idx = i
				cjk_char = True
			# if we are in the middle of one, continue
			else:
				# unless it's the end of the word
				if i == len(text)-1:
					#print(text[first_idx:i])
					tempstr += transliterate(text[first_idx:i+1])
				else:
					continue
		else:
			# if we are not in one, transfer characters over
			if cjk_char == False:
				tempstr += text[i]
			# if we are at the end of one, transliterate whole preceding block and add it
			else:
				cjk_char = False
				tempstr += transliterate(text[first_idx:i])
				tempstr += text[i]
	return tempstr

# saves a single dict
def save_dict(data,name,ver,loc='db'):
	if not os.path.isdir('%s'%loc):
		os.mkdir(str('%s'%loc))
	if ver != None:
		if len(ver.split('/')) > 1:
			pathstr = '%s'%loc
			for sub_ver in ver.split('/'):
				pathstr += '/%s'%sub_ver
				if not os.path.isdir(pathstr):
					os.mkdir(pathstr)
		else:
			if not os.path.isdir('%s/%s'%(loc,ver)):
				os.mkdir(str('%s/%s'%(loc,ver)))
	#if not os.path.isdir('%s/%s/%s'%(loc,ver,name)):
	#	os.mkdir(str('%s/%s/%s'%(loc,ver,name)))
		with open(str(loc)+'/'+str(ver)+'/'+name +'.pkl','wb') as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
	else:
		with open(str(loc)+'/'+name +'.pkl','wb') as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
	return True

# loads a single dict
def load_dict(name,ver,loc='db',count=0):
	try:
		if ver != None:
			with open(str(loc)+'/'+str(ver)+'/'+name+'.pkl','rb') as f:
				return pickle.load(f)
		else:
			with open(str(loc)+'/'+name+'.pkl','rb') as f:
				return pickle.load(f)
	except FileNotFoundError:
		if name == 'socials':
			return None
		elif name == 'tourneys':
			t = {}
			#t['slugs'] = {}
			#t['groups'] = {}
			save_dict(t,name,ver,loc)
			return t
		elif name == 'meta':
			m = {}
			m['slugs'] = {}
			save_dict(m,name,ver,loc)
			return m
		elif name == 'skills':
			s = {}
			s['mainrank'] = {}
			s['mainrank_readin'] = {}
			s['elo'] = {}
			s['elo-rnk'] = {}
			s['elo-pct'] = {}
			s['elo_del'] = {}
			s['glicko'] = {}
			s['glicko-rnk'] = {}
			s['glicko-pct'] = {}
			s['glicko_del'] = {}
			s['srank'] = {}
			s['srank-rnk'] = {}
			s['srank-pct'] = {}
			s['srank_del'] = {}
			s['srank_sig'] = {}
			s['perf'] = {}
			s['trueskill'] = {}
			s['trueskill-rnk'] = {}
			s['trueskill-pct'] = {}
			s['trueskill_del'] = {}
			s['glixare'] = {}
			s['glixare-rnk'] = {}
			s['glixare-pct'] = {}
			s['glixare_del'] = {}
			save_dict(s,name,ver,loc)
			return s
		else:
			save_dict({},name,ver,loc)
			return {}
	except (EOFError,pickle.UnpicklingError) as e:
		print(e)
		print('Sleeping...')
		time.sleep(100)
		if count <= 1000:
			load_dict(name,ver,loc,count=count+1)
		else:
			raise e

def write_blank_dict(name,loc='db'):
	try:
		os.remove('%s/blank/%s.pkl'%(loc,name))
	except FileNotFoundError:
		print('invalid blank dict location')
		return False
	else:
		return load_dict(name,'blank',loc)

# deletes a single dict
def delete_dict(name,ver,loc='db'):
	if os.path.isdir('%s'%loc):
		if ver != None and ver != '':
			if os.path.isdir('%s/%s'%(loc,ver)):
				verstr = str(ver)+'/'+str(name)+'.pkl'
			else:
				return False
		else:
			verstr = str(name)+'.pkl'
		try:
			os.remove('%s/%s'%(loc,verstr))
			return True
		except FileNotFoundError:
			return False
	else:
		return False

# saves the slugs pulled by scraper to avoid having to rescrape every time
def save_slugs(slugs,game,year,loc='db',to_save_db=True):
	if to_save_db:
		#if v >= 4:
		#	print('Saving scraped slugs...')
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
			return True
		except OSError:
			return False

# pulls the list of characters/ids from the old API and saves them locally as a dict
def save_character_dicts(games='smash',chars=None,to_load=True,force_new_icons=False):
	if to_load:
		characters = load_dict('characters',None,'../lib')
		icons = load_dict('character_icons',None,'../lib')
	else:
		characters = {}
		icons = {}

	c_file = urlopen('https://api.smash.gg/characters').read()
	c_data = json.loads(c_file.decode('UTF-8'))

	if games == 'smash':
		games = [1,2,3,4,5,1386,24]
	elif games == 'all':
		games = (load_dict('videogames',None,'../lib')).keys()
	if type(games) is int:
		games = [games]

	for character in c_data['entities']['character']:
		game_id = character['videogameId']
		if game_id in games:
			if game_id not in characters:
				characters[game_id] = {}
			if game_id not in icons:
				icons[game_id] = {}
			stock_icon_url = sorted([[img['url'],img['width']] for img in character['images']],key=lambda l: l[1])[0][0]
			if stock_icon_url not in icons[game_id] or force_new_icons:
				stock_icon_header = {'User-Agent' : 'Magic Browser'}
				stock_icon_req = Request(stock_icon_url,headers=stock_icon_header)
				icons[game_id][character['id']] = mpimg.imread(urlopen(stock_icon_req))
			characters[game_id][character['id']] = character['name']

	if save_dict(characters,'characters',None,loc='../lib') and save_dict(icons,'character_icons',None,loc='../lib'):
		return characters
	else:
		return False

# given the image data saved in a dict, converts them to folders of image files
def save_stock_icons(games='smash'):
	if games == 'smash':
		games = [1,2,3,4,5,1386,24]
	elif games == 'all':
		games = (load_dict('videogames',None,'../lib')).keys()
	if type(games) is int:
		games = [games]
	
	icons = load_dict('character_icons',None,'../lib')

	if not os.path.isdir('../lib/icons'):
		os.mkdir('../lib/icons')

	for game_id in games:
		if game_id in icons:
			if not os.path.isdir('../lib/icons/%d'%game_id):
				os.mkdir('../lib/icons/%d'%game_id)
			for char_id in icons[game_id]:
				mpimg.imsave('../lib/icons/%d/%d.png'%(game_id,char_id),icons[game_id][char_id])

	return True

# pulls the list of videogames/ids from the old API and saves them locally as a dict
def save_videogame_dicts(games='all',chars=None,to_load=True):
	if to_load:
		videogames = load_dict('videogames',None,'../lib')
	else:
		videogames = {}

	c_file = urlopen('https://api.smash.gg/videogames').read()
	c_data = json.loads(c_file.decode('UTF-8'))

	if games == 'smash':
		games = [1,2,3,4,5,1386,24]
	elif games == 'all':
		games = c_data['result']
	if type(games) is int:
		games = [games]

	for videogame in c_data['entities']['videogame']:
		if videogame['id'] in games:
			videogames[videogame['id']] = {}
			videogames[videogame['id']]['name'] = videogame['name']
			videogames[videogame['id']]['displayName'] = videogame['displayName']
			videogames[videogame['id']]['slug'] = videogame['slug']

	#return save_dict(characters,'characters',None,loc='../lib')
	if save_dict(videogames,'videogames',None,loc='../lib'):
		return videogames
	else:
		return False

# pulls just the tournament start date from the slug, without reading in the full event
def get_tournament_date(slug):
	tourneylink ='https://api.smash.gg/tournament/%s'%slug

	try:
		tfile = urlopen(tourneylink).read()
		tdata = json.loads(tfile.decode('UTF-8'))

		# date tuple in (year, month, day) format
		t_date = time.localtime(tdata['entities']['tournament']['startAt'])[:3]

		return t_date

	except HTTPError:
		print('Error 404: tourney [%s] not found'%slug)
		return False

# prints tournament results by player's final placing
def print_results(res,names,entrants,losses,characters,game=1,max_place=64,translate_cjk=True):
	maxlen = 0

	res_l = [item for item in res.items()]
	res_s = sorted(res_l, key=lambda l: (0-l[1]['placing'],len(l[1]['path'])), reverse=True)

	if game != 5:
		chardict = load_dict('characters',None,loc='../lib')
		chardict = chardict[game]

	# Error catching
	if res == [] or len(res) <= 0:
		print('Error: no bracket found')
		return False

	team_mult = max([len(names[plyr[0]][1]) for plyr in res_s])
	#print(team_mult,names[res_s[0][0]])

	num_rounds = len(res_s[0][1]['path'])
	#lsbuff = '\t'*(num_rounds-len(res_s[-1][1][1])+1)
	roundnames = [names['groups'][group] for group in res_s[0][1]['path']]
	roundslen = sum([len(str(name)) for name in roundnames]) + 2*num_rounds
	sp_slot = 13*team_mult
	tag_slot = 24*team_mult
	tag_title = 'Tag'
	if team_mult >= 4:
		sp_slot = 0
		tag_slot = 24
		tag_title = 'Crew'
	id_slot = 8*team_mult
	print(team_mult)
	print(('\n{:>%d.%d}'%(sp_slot,sp_slot)).format('Sponsor |'),('{:<%d.%d}'%(tag_slot,tag_slot)).format(tag_title),('{:<%d.%d}'%(id_slot,id_slot)).format('ID #'), \
		'Place\t',('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('Bracket'),'{:<16.16}'.format('Main'),'Losses\n')
	for player in res_s:
		#if type(team_s[0]) is int:
		#	team = [team_s]
		#else:
		#	team = team_s
		#for player in team:
		if player[1]['placing'] > max_place and max_place > 0:
			break
		else:
			playerstrings = []
			entr_mult = len(names[player[0]][1])
			# assemble player/team tags and sponsors, make readable
			for idx in range(entr_mult):
				if names[player[0]][0][idx] == '' or names[player[0]][0][idx] == None:
					sp = '  '
				else:
					sp = names[player[0]][0][idx]
					if translate_cjk:
						if any([is_cjk(sp_char) for sp_char in sp]):
							#sp = '『'+''.join(translate(sp_char) for sp_char in sp)+'』'
							#sp = '<'+(translate(sp,to='ja')).pronunciation+'>'
							sp = '<'+transliterate(sp)+'>'
					if len(sp) > 12:
						sp = sp[:8] + '... |'
					else:
						if sp[-2:] != ' |':
							#sp = '/'.join(str(n) for n in names[player[0]][0]) + ' |'
							sp = names[player[0]][0][idx] + ' |'
				sp_slot = 13#*team_mult
				for ch in sp:
					if is_emoji(ch):
						sp_slot -= 1
				#tag = '/'.join(str(n) for n in names[player[0]][1])
				tag = names[player[0]][1][idx]
				if translate_cjk:
					if any([is_cjk(tag_char) for tag_char in tag]):
						#tag = '『'+''.join(translate(tag_char) for tag_char in tag)+'』'
						#tag = '<'+(translate(tag,to='ja')).pronunciation+'>'
						tag = '<'+transliterate(tag)+'>'
						#tag = '<'+''.join([(translate(tag_char)).text for tag_char in tag])+'>'
				tag_slot = 24#*team_mult
				if len(tag) > tag_slot:
					tag = tag[:tag_slot-3]+'...'
				for ch in tag:
					if is_emoji(ch):
						tag_slot -= 1

				playerstrings.extend([(sp,tag)])

			# select the character with the highest pickrate as the player's 'main'
			if player[0] in characters and game != 5:
				char_idx = sorted([char_id for char_id in characters[player[0]]],key=lambda c_id: sum(characters[player[0]][c_id]),reverse=True)[0]
				main_str = chardict[char_idx]
				#main_str = str(char_idx)
			else:
				main_str = ''

			# tabulate their losses in bracket
			if player[0] in losses:
				#print(losses)
				if len(playerstrings) >= 4:
					ls_list = [entrants[loss[0]][0][2] for loss in losses[player[0]]]
				else:
					ls_list = [' / '.join(str(j) for j in l) for l in [names[loss[0]][1] for loss in losses[player[0]]]]

				if translate_cjk:
					ls_list = ['<'+transliterate(l_tag)+'>' if any([is_cjk(l_tag_char) for l_tag_char in l_tag]) else l_tag for l_tag in ls_list]
					#for l_tag in ls_list:
					#	if any([is_cjk(l_tag_char) for l_tag_char in l_tag]):
					#		print('ohno')
					#		ls_list.replace(l_tag,'<'+(translate(l_tag,to='ja')).pronunciation+'>')
					#		print(l_tag,ls_list)

				ls = '['+', '.join(ls_list)+']'
			else:
				ls = None

			#if len(player[1][1]) > maxlen:
			#	maxlen = len(player[1][1])
			#lsbuff = '\t'*(maxlen-len(player[1][1])+1)
			#if len(player[1][1]) > 2:
			#	lsbuff = '\t'
			#else:
			#	lsbuff = '\t\t\t'
			if len(playerstrings) == 1: #or len(playerstrings) >= 4:
				print(('{:>%d.%d}'%(sp_slot,sp_slot)).format(sp),('{:<%d.%d}'%(tag_slot,tag_slot)).format(tag),('{:>%d.%d}'%(8*team_mult,8*team_mult)).format(' / '.join(str(n) for n in entrants[player[0]][1])), \
				'  {:<5.5}'.format(str(player[1]['placing'])),('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('['+', '.join(str(i) for i in [names['groups'][group] for group in player[1]['path']])+']'),'{:<16.16}'.format(main_str),ls)
			elif len(playerstrings) >= 4: #or len(playerstrings) >= 4:
				team_name = entrants[player[0]][0][2]
				print(('{:<%d.%d}'%(tag_slot,tag_slot)).format(team_name),('{:>%d.%d}'%(8*team_mult,8*team_mult)).format(' / '.join(str(n) for n in entrants[player[0]][1])), \
				'  {:<5.5}'.format(str(player[1]['placing'])),('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('['+', '.join(str(i) for i in [names['groups'][group] for group in player[1]['path']])+']'),ls)
			else:
				print(('{:<%d.%d}'%(team_mult*(sp_slot+tag_slot),team_mult*(sp_slot+tag_slot))).format(' & '.join(('{:<%d.%d}'%(sp_slot+tag_slot,sp_slot+tag_slot)).format(('{:>%d.%d}'%(sp_slot,sp_slot)).format(sp)+' '+('{:<%d.%d}'%(tag_slot,tag_slot)).format(tag)) for sp,tag in playerstrings)), \
					('{:>%d.%d}'%(8*team_mult,8*team_mult)).format('/'.join(str(n) for n in entrants[player[0]][1])), \
				'  {:<5.5}'.format(str(player[1]['placing'])),('{:<%d.%d}'%(roundslen+5,roundslen+5)).format('['+', '.join(str(i) for i in [names['groups'][group] for group in player[1]['path']])+']'),ls)

	return res_s

if __name__ == '__main__':
	#print(save_character_dicts(1386))
	#print(save_stock_icons(1386))
	#write_blank_dict('meta')

	#clean_data('./old/sns5setsraw.txt','./old/sns5setsclean.txt')

	#save_videogame_dicts()
	save_character_dicts()
	save_stock_icons()