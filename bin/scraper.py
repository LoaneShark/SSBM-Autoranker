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
		#print(old_c_year,c_year)
		#print(i,c_year[0],game_ids[int(c_year[1])])

		old_c_year = int(c_year[0])

		if game_ids[int(c_year[1])] == name:
			if int(c_year[0]) == year:
				return i+3
				break
			if int(c_year[0]) > year:
				return None

# scrapes PGR/SSBMRank/etc. from ssbwiki for given game/year
# ABANDONED
def scrape_ranks(game,year):
	if game == 1:
		if year >= 2018:
			rank_name = 'MPGR'
		else:
			rank_name = 'SSBMRank'
	elif game == 2:
		rank_name = 'PMRank'
	elif game == 3 or game == 1386:
		rank_name = 'PGR'
	elif game == 4:
		rank_name = '64_League_Rankings'
	elif game == 5:
		rank_name = 'SSBBRank'
	else:
		return False

	rank_url = 'https://www.ssbwiki.com/' + rank_name


if __name__ == '__main__':
	print(scrape(1386,2019,verb=9))
	#scrape_slugs(['https://www.ssbwiki.com/Tournament:Valhalla'])
	
	#url = 'https://www.ssbwiki.com/List_of_national_tournaments'
	#page = urlopen(url).read()
	#page = page.decode('UTF-8')
	#table_index(BeautifulSoup(page,features='lxml'),1,2017)
	#print(BeautifulSoup(page,features='lxml').table)