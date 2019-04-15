import numpy as np 
import scipy as sp 
import os,sys,pickle,time,datetime,math
import firebase_admin
from firebase_admin import db as fdb
from firebase_admin.db import ApiCallError
from firebase_admin import auth
from six.moves.urllib.error import HTTPError
## UTIL IMPORTS
from db_utils import load_db_sets,easy_load_db_sets

def main():
	return True

# update firebase db by setting all values to local db, for a given game/year/count
def update_db(dicts,db_key,force_update=False,new_db=False):
	print('----------------------')
	tourneys,ids,p_info,records,skills,meta = dicts
	# load sets from db and add them to 'dicts'
	split_key = db_key.split('_')
	yc_str = ''
	if int(split_key[2]) > 0:
		yc_str += '-'+str(int(split_key[1])+int(split_key[2]))
	sets = easy_load_db_sets(ver=str(split_key[0])+'/'+str(split_key[1])+yc_str)
	dicts = (tourneys,ids,p_info,records,skills,meta,sets)

	# open db
	db = get_db_reference()
	game_db = db.child(db_key)
	# assume db exists -- this was using too much data and pulling the ENTIRE database
	if new_db:
		# if db doesn't exist, create it
		if db.get() is None:
			game_db.set('')
			#db.push(db_key)
			#print(db_key)
			#print('pushed')
			print('no db found')
		# if game not in db or game is blank, add it
		if game_db.get() is None or (type(game_db.get()) is str and game_db.get() == '') or force_update:
			game_db.set('')
	# add directories for all the major information dicts
	for dictname,dictdata in zip(['tourneys','ids','p_info','records','skills','meta','sets'],dicts):
		print('pushing...',dictname)
		sub_db = game_db.child(dictname)
		# import dict data to firebase db
		if sub_db.get() is None or force_update:
			try:
				sub_db.set(dictdata)
			# if dict is too big to upload at once
			except ApiCallError as e:
				print('ApiCallError pushing \'%s\': attempting batch upload...'%dictname)
				if dictname == 'skills':
					for skill_key in dictdata.keys():
						skill_db_ref = sub_db.child(skill_key)
						try:
							skill_db_ref.set(dictdata[skill_key])
						except ApiCallError as e2:
							batch_upload(dictdata[skill_key],skill_db_ref)
				else:
					batch_upload(dictdata,sub_db)
			except TypeError as te:
				print('Upload failed. Checking for dirtied dict...')
				is_clean_dict(dictdata)

	print('%s pushed'%db_key)

# update all games for the given year/count [WIP]
def update_all(dicts,year,year_count,is_current=False):
	for game_id in [1,2,3,4,5,1386]:
		gamestr = str(game_id)+'_'+str(year)+'_'+str(year_count)
		if is_current:
			gamestr += '_c'
		update_db(dicts,gamestr)

def delete_sub_db(db_ref,game,year,year_count,is_current=False):
	gamestr = str(game)+'_'+str(year)+'_'+str(year_count)
	if is_current:
		gamestr += '_c'
	print('deleting... ',gamestr)
	sub_ref = db_ref.child(gamestr)

	return sub_ref.delete()

# gets a reference to the firebase db object
def get_db_reference():
	FIREBASE_CONFIG = {
		'apiKey': 'AIzaSyAfoIXJXWGlxuMvOOJCBDYa-Jbw8FaiblY',\
		'authDomain': 'smashranks-db.firebaseapp.com',\
		'databaseURL': 'https://smashranks-db.firebaseio.com',\
		'projectId': 'smashranks-db',\
		'storageBucket': 'smashranks-db.appspot.com',\
		'messagingSenderId': '1057783802681'};

	cred = firebase_admin.credentials.Certificate('../lib/Firebase_API_Key.json')
	app = firebase_admin.initialize_app(cred)

	return fdb.reference(url='https://smashranks-db.firebaseio.com')

# scans a dict and returns true if no numpy objects are stored
def is_clean_dict(e_dict,e_key=None):
	if type(e_dict) is dict:
		return all([is_clean_dict(e_dict[key],key) if type(key) in [str,int,float,list,tuple,None,type(None),datetime.date] else False for key in e_dict])
	# base case
	else:
		if type(e_dict) in [str,int,float,list,tuple,None,type(None),bool,datetime.date]:
			return True
		else:
			print('e_key:',e_key,'||','value:',type(e_dict))
			print(e_dict)
			return False

# uploads a dict by chunks, in the event that it's too big to be pushed all at once
def batch_upload(big_dict,sub_db_ref,batch_size=500):
	dict_keys = sorted(big_dict.keys())
	num_batches = math.ceil(float(len(dict_keys))/float(batch_size))
	print('Separating into batches:... N:',len(dict_keys),'  N_batches:',num_batches)

	for nb in range(num_batches):
		print('uploading batch: %d'%nb)
		# if it's the last batch, go til the end of the remaining keys
		if nb >= num_batches-1:
			upload_batch = dict_keys[nb*batch_size:]
		else:
			upload_batch = dict_keys[nb*batch_size:(nb+1)*batch_size]

		upload_dict = {this_key:big_dict[this_key] for this_key in upload_batch}
		print(len(upload_batch),len(upload_dict))

		sub_db_ref.update(upload_dict)

if __name__ == '__main__':

	#for user in auth.list_users().iterate_all():
	#	print('User: ' + user.uid)
	curr_db = get_db_reference()
	for game in [1,2,3,4,5,1386]:
		print(delete_sub_db(curr_db,game,2018,0))
		print(delete_sub_db(curr_db,game,2018,1))
		print(delete_sub_db(curr_db,game,2018,1,True))