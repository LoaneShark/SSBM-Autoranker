import numpy as np 
import scipy as sp 
import os,sys,pickle,time,datetime
import firebase_admin
from firebase_admin import db as fdb
from firebase_admin.db import ApiCallError
from firebase_admin import auth

def main():
	return 0

# update firebase db by setting all values to local db, for a given game/year/count
def update_db(dicts,db_key,force_update=False):
	print('----------------------')
	tourneys,ids,p_info,records,skills = dicts
	db = get_db_reference()
	game_db = db.child(db_key)
	# if db doesn't exist, create it
	if db.get() is None or force_update:
		#game_db.set('')
		#db.push(db_key)
		print(db_key)
		print('pushed')
	# if game not in db or game is blank, add it
	if game_db.get() is None or (type(game_db.get()) is str and game_db.get() == '') or force_update:
		#game_db.set('')
		# add directories for all the major information dicts
		for dictname,dictdata in zip(['tourneys','ids','p_info','records','skills','sets'],dicts):
			#print(dictname)
			#print(is_clean_dict(dictdata))
			sub_db = game_db.child(dictname)
			# import dict data to firebase db
			if sub_db.get() is None:
				sub_db.set(dictdata)

# update all games for the given year/count [WIP]
def update_all(dicts,year,year_count):
	return False

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
		if type(e_dict) in [str,int,float,list,tuple,None,type(None),datetime.date]:
			return True
		else:
			print('e_key:',e_key,'||','value:',type(e_dict))
			print(e_dict)
			return False

if __name__ == '__main__':

	for user in auth.list_users().iterate_all():
		print('User: ' + user.uid)