#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen
from urllib.error import HTTPError
#import lxml.html as lh
#import pandas as pd
from bs4 import BeautifulSoup
from arg_utils import *

args = get_args()
v = args.verbosity

# scrapes the ssbwiki url links for each major tournament, and returns their smash.gg slug
# requires a game and year
def scrape(game,year,verb=v):
	if year < 2015:
		print('Error: The earliest smash.gg tournament data is 2015. For best results, use 2017 and on')
		return False

	if game not in [1,2,3,4,5,1386]:
		if game == 24:
			return rivals_events(year)
		else:
			print('Error: Cannot scrape majors/slugs for this game ID (%d)'%game)
			return False

	v = verb
	url = 'https://www.ssbwiki.com/List_of_national_tournaments'

	if v >= 3:
		temp = ""
		if v >=4:
			temp = url
		print('Scraping...\t%s'%temp)
	page = urlopen(url).read()
	page = page.decode('UTF-8')
	doc = BeautifulSoup(page,features='lxml')

	t_idx = table_index(doc,game,year)
	if t_idx == None:
		return []

	i = 0
	res = []
	for table in doc.find_all('table'):
		if i == t_idx:
			for row in table.find_all('tr'):
				#print(row)
				t = [element for element in row.find_all('td')]
				if len(t) > 0:
					head = [t[0].find_all('a')[0]['href']]
					head.extend([x.text for x in t])
					res.append(head[:-1])
				else:
					res.append(t)
		i = i+1
	doc.decompose()
	res = res[1:]
	#res = [item for item in res if 'redlink' not in item[0]]
	if v >= 5:
		print(res)

	links = ['https://www.ssbwiki.com%s'%event[0] for event in res]
	entrant_counts = [event[3] for event in res]
	return scrape_slugs(links,v=verb)

# given a set of tourney wiki page urls, returns all of their smash.gg slugs
def scrape_slugs(urls,v=0):
	return [scrape_slug(url,v=v) for url in urls]

# given a url for a tournament's ssbwiki page, returns the smash.gg bracket slug
def scrape_slug(url,v=0):
	#print(url)
	if 'redlink' in url:
		url = url.split('&')[0]
		#print (url)
		try:
			page = urlopen(url).read()
		except HTTPError:
			if v >= 5:
				print('HTTPError: Could not open %s'%url)
			return ((None,url.split('Tournament')[-1][1:]))


		#return((None,doc.h1.text[11:]))
	page = urlopen(url).read()
	page = page.decode('UTF-8')
	doc = BeautifulSoup(page,features='lxml')
	challonge_found = False

	for content in doc.find_all('a'):
		smashlink = content.get('href')
		if not smashlink == None and len(smashlink.split('/'))>2:
			if smashlink.split('/')[2] == 'smash.gg':
				#print(smashlink)
				slug = smashlink.split('/')[4]
				if v >= 5:
					print('scraping...',slug)
				return slug
			elif smashlink.split('/')[2] == 'challonge.com':
				if not challonge_found:
					if v >= 1:
						print('Tournament [%s] could not be read: Challonge support not available yet'%url.split('/')[3])
					challonge_found = True
	# return tuple of None with tournament title if smash.gg link could not be found
	return((None,doc.h1.text[11:]))

# needs a beautifulsoup doc of the ssbwiki national tournaments page,
# a given year, and a given game.
def table_index(doc,game,year):
	game_ids = {1: 'Super Smash Bros.', 2: 'Super Smash Bros. Melee', 3: 'Super Smash Bros. Brawl', 5: 'Super Smash Bros. for Wii U', 4: 'Super Smash Bros. for 3DS',7: 'Project: M', 6: 'Super Smash Bros. Ultimate'}
	game_keys = {1: 'Super Smash Bros. Melee', 2: 'Project: M', 3: 'Super Smash Bros. for Wii U', 4: 'Super Smash Bros.', 5: 'Super Smash Bros. Brawl', 1386: 'Super Smash Bros. Ultimate'}
	name = game_keys[game]
	#print(name)

	tables = doc.find_all('table')
	headers = doc.find_all('h3')
	#print(tables)
	c_game = 0
	old_c_year = 99999
	for i in range(0,min(len(tables),len(headers))):
		table = tables[i+3]
		header = headers[i]
		if header.span == None and header.text == 'Views':
			return None
		c_year = header.span['id'].split('_')
		if int(c_year[0]) <= old_c_year:
			c_game = c_game + 1
		if(len(c_year) == 1):
			c_year = [c_year[0],c_game]
		else:
			c_year[1] = c_game

		old_c_year = int(c_year[0])

		if game_ids[int(c_year[1])] == name:
			if int(c_year[0]) == year:
				return i+3
				break
			if int(c_year[0]) > year:
				return None

# gets the name of the ranking system and the necessary url slug for a given game and year
def get_rank_name(game,year,yr_half=-1):
	if game == 1:
		if year >= 2018:
			rank_name = 'MPGR'
			yearstr = str(year) + '_'
			if yr_half == 0:
				yearstr = 'Summer_'+yearstr
		else:
			rank_name = 'SSBMRank'
			yearstr = str(year) + '_'
			if yr_half == 0:
				yearstr = 'Summer_'+yearstr
	elif game == 2:
		rank_name = 'PMRank'
		yearstr = '_' + str(year)
	elif game == 3:
		rank_name = 'PGR'
		if yr_half < 0:
			yr_half = 1
		pgr_map = {2016:{1:'v1'},2017:{0:'v2',1:'v3'},2018:{0:'v5',1:'v5'},2019:{0:'100'}}
		if year > 2018 or year < 2016 or yr_half not in pgr_map[year]:
			yearstr = '_'+str(year)
		else:
			yearstr = '_'+pgr_map[year][yr_half]
	elif game == 1386:
		rank_name = 'PGRU'
		yearstr = str(year) + '_'
		if yr_half == 0:
			yearstr = 'Summer_'+yearstr
	elif game == 4:
		rank_name = '64_League_Rankings'
		#yearstr = str(year) + '_'
		if year <= 2016:
			yearstr = str(year)+'_'
		else:
			# only import 2017 until 2016 gets split out into its own article
			yearstr = ''
	elif game == 5:
		rank_name = 'SSBBRank'
		if year == 2016 or year == 2017:
			yearstr = '2016-2017_'
		elif year == 2014 or year == 2015:
			yearstr = '2014_'
		else:
			yearstr = str(year) + '_'
	else:
		return False
	return rank_name,yearstr

# scrapes PGR/SSBMRank/etc. from ssbwiki for given game/year
def scrape_ranks(game,year,rank_str,yearstr,yr_half=-1):

	if game not in [1,2,3,4,5,1386]:
		return False

	rank_url = 'https://www.ssbwiki.com/'+rank_str

	# load page for ranks
	try:
		page = urlopen(rank_url).read()
		page = page.decode('UTF-8')
		doc = BeautifulSoup(page,features='lxml')
	except HTTPError:
		if year < 2015 or (year < 2018 and game == 1386):
			return False
		else:
			print('No ranks found for: %s, %d'%(rank_str,year))
			if year <= args.year:
				return scrape_ranks(game,year-1,rank_str,yearstr,yr_half)
			else:
				return False

	tags = []
	ratings = []
	tables = doc.find_all('table')

	# find index on page of ranking table
	t_i = -1
	for i in range(1,len(tables)):
		curr_table = tables[i]
		first_row = curr_table.find_all('tr')[0]
		if len(first_row.find_all('th')) > 0:
			if 'rank' in first_row.find_all('th')[0].text.lower():
				t_i = i
				break

	if t_i < 0:
		return False
	rank_table = tables[t_i]

	# scrape rankings
	for player in rank_table.find_all('tr'):
		if len(player.find_all('th')) > 0.:
			continue # ignore header row
		else:
			player_content = player.find_all('td')
			player_links = player_content[1].find_all('a')
			if len(player_links) >= 2:
				tags.append(player_links[1].text.strip())
				if len(player_content) >= 6:
					ratings.append(float(player_content[5].text))

	if ratings == []:
		ratings = None
	# take this out once the articles get split up
	if game == 4:
		yearstr = '2017'
	return tags,ratings,yearstr.strip('_')

def check_ssbwiki(dicts,p_id,tag):
	tourneys,ids,p_info,records,skills,meta = dicts
	#print('Checking Wiki for: %s (%d)'%(tag,p_id))
	# modify tag to handle properly in urls
	if tag is None:
		return None
	tag = tag.strip()
	tag = tag.replace(' ','%20')
	urlattempt = 'https://www.ssbwiki.com/Smasher:'+tag

	try:
		page = urlopen(urlattempt).read()
		page = page.decode('UTF-8')
		doc = BeautifulSoup(page,features='lxml')

		head1 = doc.find('h1')
		if head1.get('id') == 'firstHeading':
			if 'disambiguation' in head1.text:
				print('attempting to match...')
				bulletlist = doc.find('ul')
				for line in bulletlist.find_all('li'):
					if ', a smasher from ' in line.text:
						state = line.text.split(', a smasher from ')
						state = state[1]

						if state in p_info[p_id]['region']:
							ssbwiki_stub = line.find('a').get('href')
							print('matched: %s'%ssbwiki_stub)
							return ssbwiki_stub[9:] # remove the '/Smasher:' that is prepended
				print('no match found')
				return None

		for div in doc.find_all('div'):
			if div.get('id') == 'mw-content-text':
				if div.find('div').get('class') == None:
					return urlattempt.split('/Smasher:')[1]
				else:
					#if div.find('div').get('class').split(' ')[0] == 'noarticletext':
					return None
		
	except HTTPError:
		#print('Page not found')
		return None
	except UnicodeEncodeError:
		#print('Unicode Error')
		return None

	return None

# hardcode these in for now/testing purposes
def rivals_events(year):
	if year < 2016:
		return False

	if year == 2016:
		return ['na-rcs-week-1','eu-rcs-week-1','na-rcs-week-2','eu-rcs-week-2','na-rcs-week-3','eu-rcs-week-3','na-rcs-week-4','garden-of-gods-a-rivals-of-aether-national',\
				'eu-rcs-week-4','na-rcs-week-5','eu-rcs-week-5','na-rcs-week-6','eu-rcs-week-6','guts-4-game-underground-tournament-spectacular-4','toast','na-rcs-week-7',\
				'eu-rcs-week-7','rewired-2016-1','na-rcs-week-8','eu-rcs-week-8','na-rcs-week-9','eu-rcs-week-9','na-rcs-week-10','eu-rcs-week-10','na-rcs-week-11',\
				'eu-rcs-week-11','na-rcs-week-12','eu-rcs-week-12']
	elif year == 2017:
		return ['genesis-4','battle-arena-melbourne-9','road-to-shine-rivals','au-rcs-may-monthly','the-bigger-balc','eu-rcs-may-monthly','road-to-shine-rivals','eu-rcs-june-monthly',\
				'au-rcs-june-monthly','na-rcs-july-monthly','au-rcs-july-monthly','eu-rcs-july-monthly','low-tier-city-5','rivals-super-smash-con','na-rcs-august-monthly',\
				'shine-2017','eu-rcs-august-monthly','au-rcs-august-monthly','au-rcs-ohn15','na-rcs-september-monthly','heat-wave','eu-rcs-september-monthly','au-rcs-september-monthly',\
				'gametyrant-expo-2017','na-rcs-october-monthly','au-rcs-october-monthly','eu-rcs-october-monthly','na-rcs-november-monthly','au-rcs-november-monthly','eu-rcs-november-monthly',\
				'au-rcs-december-monthly','na-rcs-december-monthly','eu-rcs-december-monthly']
	elif year == 2018:
		return ['genesis-5','battle-arena-melbourne-10','na-rcs-season-3-may-monthly-2','smash-n-splash-4','na-rcs-season-3-june-monthly','eu-rcs-season-3-june-monthly-1',\
				'andromeda-1','2gg-hyrule-saga','au-rcs-season-3-june-monthly','na-rcs-season-3-july-monthly','first-impact-2018','au-rcs-season-3-july-monthly',\
				'eu-rcs-season-3-july-monthly','rivals-at-super-smash-con-2018','au-rcs-season-3-august-monthly','shine-2018','eu-rcs-season-3-august-monthly',\
				'na-rcs-season-3-august-monthly','au-rcs-season-3-september-monthly','mega-metal-cavern','eu-rcs-season-3-september-monthly','na-rcs-season-3-september-monthly',\
				'na-rcs-season-3-october-monthly','heat-wave-2','au-rcs-season-3-october-monthly','eu-rcs-season-3-october-monthly','gametyrant-expo-2018',\
				'na-rcs-season-3-november-monthly','traction-4','eu-rcs-season-3-november-monthly','au-rcs-season-3-november-monthly','na-rcs-season-3-december-monthly',\
				'au-rcs-season-3-december-monthly','don-t-park-on-the-grass-2018-1','eu-rcs-season-3-december-monthly']
	elif year == 2019:
		return ['genesis-6','frostbite-2019','road-to-season-4-online-qualifier','gote-4thekids-2019-charity-pro-am-sponsored-by-mortv','smash-n-splash-5',\
				'au-rcs-june-online-monthly','eu-rcs-june-online-monthly','bigwinchampionship-2','albion-4','na-rcs-season-4-july-online-major','metal-cavern-20',\
				'couchwarriors-vic-july-ranking-battle-2019-smash-roa','rivals-of-aether-at-evo-2019','indie-showcase-super-smash-con-2019','awakening-5-1','biggie-ii',\
				'eu-rcs-september-online-monthly','au-rcs-september-online-monthly','glitch-7-minus-world','bifrost-iii-sessrumnir','heat-wave-3',\
				'au-rcs-october-online-monthly','syndicate-2019','eu-rcs-november-online-monthly','dreamhack-atlanta','au-rcs-november-online-monthly',\
				'traction-5','couchwarriors-crossup-2','na-rcs-season-4-december-online-major']
	elif year == 2020:
		return ['genesis-7']
	else:
		return False

if __name__ == '__main__':
	#print(scrape(1386,2019,verb=9))
	#print(scrape_ranks(4,2018))

	print(scrape_ranks(1386,2019,'Summer_2019_PGRU','Summer_2019_',0))

	if False:
		urlattempt = 'https://www.ssbwiki.com/Smasher:Light'
		try:
			page = urlopen(urlattempt).read()
			page = page.decode('UTF-8')
			doc = BeautifulSoup(page,features='lxml')

			head1 = doc.find('h1')
			if head1.get('id') == 'firstHeading':
				if 'disambiguation' in head1.text:
					bulletlist = doc.find('ul')
					for line in bulletlist.find_all('li'):
						if ', a smasher from ' in line.text:
							state = line.text.split(', a smasher from ')
							state = state[1]

							#if state in p_info[p_id]['region']:
							ssbwiki_stub = line.find('a').get('href')
							print(ssbwiki_stub[9:]) # remove the '/Smasher:' that is prepended
		except HTTPError:
			print('ass')
	#scrape_slugs(['https://www.ssbwiki.com/Tournament:Valhalla'])
	
	#url = 'https://www.ssbwiki.com/List_of_national_tournaments'
	#page = urlopen(url).read()
	#page = page.decode('UTF-8')
	#table_index(BeautifulSoup(page,features='lxml'),1,2017)
	#print(BeautifulSoup(page,features='lxml').table)