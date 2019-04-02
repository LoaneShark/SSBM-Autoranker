#import numpy as np 
#import scipy as sp 
from six.moves.urllib.request import urlopen
from urllib.error import HTTPError
#import lxml.html as lh
#import pandas as pd
from bs4 import BeautifulSoup

v = 0

# scrapes the ssbwiki url links for each major tournament, and returns their smash.gg slug
# requires a game and year
def scrape(game,year,verb=0):
	if game not in [1,2,3,4,5,1386]:
		print('Error: Cannot scrape majors/slugs for this game ID (%d)'%game)
		return False
	v = verb
	url = 'https://www.ssbwiki.com/List_of_national_tournaments'

	if year < 2015:
		print('Error: The earliest smash.gg tournament data is 2015. For best results, use 2017 and on')
		return False
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
		pgr_map = {2016:{0:'v1',1:'v2'},2017:{0:'v3',1:'v4'},2018:{0:'v5',1:'100'}}
		if year > 2018 or year < 2016:
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
def scrape_ranks(game,year,yr_half=-1):
	rank_name,yearstr = get_rank_name(game,year,yr_half)

	if game == 3 or game == 2:
		rank_url = 'https://www.ssbwiki.com/'+rank_name+yearstr
	else:
		rank_url = 'https://www.ssbwiki.com/'+yearstr+rank_name

	# load page for ranks
	try:
		page = urlopen(rank_url).read()
		page = page.decode('UTF-8')
		doc = BeautifulSoup(page,features='lxml')
	except HTTPError:
		if year <= 2015:
			return False
		else:
			print('No ranks found for: %s, %d'%(rank_name,year))
			return scrape_ranks(game,year-1)

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
			tags.append(player_content[1].find_all('a')[1].text.strip())
			if len(player_content) >= 6:
				ratings.append(float(player_content[5].text))

	if ratings == []:
		ratings = None
	# take this out once the articles get split up
	if game == 4:
		yearstr = '2017'
	return tags,ratings,yearstr.strip('_')

def check_ssbwiki(dicts,p_id,tag):
	tourneys,ids,p_info,records,skills = dicts
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

if __name__ == '__main__':
	#print(scrape(1386,2019,verb=9))
	#print(scrape_ranks(4,2018))
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