import numpy as np
import pandas as pd
#import seaborn as sns
#import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.utils import shuffle

from calc_utils import winprobs, is_active
from arg_utils import get_args
from dict_utils import get_en_tag

args = get_args()

def dicts_to_nn(dicts,seed='last',min_req=args.min_activity):
	tourneys,ids,p_info,records,skills,meta = dicts
	# get the players that meet activity requirements to start with.
	# sort them by elo initially
	id_list = [abs_id for abs_id in records if is_active(dicts,abs_id,min_req=min_req,min_wins=1)]
	id_list = sorted(id_list,key=lambda abs_id: p_info[abs_id]['elo'],reverse=True)

	# get the win probs for the whole db
	winps,chis = winprobs(dicts,id_list=None,mode='dict')
	N = float(len(winps.keys()))
	n = float(len(id_list))
	print('N: ',N,'   n:',n)

	# initialize data with [id, tag, elo, glicko] structure
	data = np.array([[p_id,get_en_tag(dicts,p_id=p_id),float(p_info[p_id]['elo']),float(p_info[p_id]['glicko'][0])] for p_id in winps],dtype='object')

	if seed == 'last':
		print('[seeding by previous/initial skill values]')
		data_dict = {p_id: ([tag,p_info[p_id]['srank_last']] if type(p_info[p_id]['srank_last']) is float else [tag,0.5] if p_id in id_list else [tag,1.0]) for p_id,tag,_,_ in data}
	else:
		print('[blanked seeding]')
		data_dict = {p_id: ([tag,0.5] if p_id in id_list else [tag,1.0]) for p_id,tag,_,_ in data}

	xlist = []
	ylist = []
	slist = []
	nlist = []
	players = []

	for p_idx in range(int(n)):
		xs = []
		ys = []
		ss = []
		p_id = id_list[p_idx]

		for opp_id in winps[p_id]:
			ratio = float(winps[p_id][opp_id])
			opp_skill = data_dict[opp_id][1]
			if not np.isnan(opp_skill):
				if ratio > 0:
					xs.append(opp_skill)
					ys.append(min(ratio,0.999))
					ss.append(chis[p_id][opp_id])
				if ratio == 0:
					xs.append(opp_skill)
					ys.append(0.001)
					ss.append(chis[p_id][opp_id])

		players.append([xs,ys,ss])
	return players


def main_nn(player_list):
	top_player = player_list[0]
	print(top_player)
	xs,ys,ss = top_player

	sigma_0 = 0.1
	#x_vals = np.arange(1,5.2,0.2)
	#x_arr = np.array([])
	#y_arr = np.array([])
	#samples = 50
	#for x in x_vals:
	#    x_arr = np.append(x_arr, np.full(samples,x))
	#    y_arr = np.append(y_arr, data_generator(x,sigma_0,samples))
	x_arr = xs; y_arr = ys
	x_arr, y_arr = shuffle(x_arr, y_arr)
	x_test = np.arange(0,1,0.01)

	fig, ax = plt.subplots(figsize=(10,10))
	plt.grid(True)
	plt.xlabel('Skill Value')
	plt.ylabel('Winprob')
	ax.scatter(x_arr,y_arr,label='sampled data')
	ax.legend(loc='upper center',fontsize='large',shadow=True)
	plt.show()

	NN(top_player,x_test)

def NN(player,x_test):
	x_arr,y_arr,s_arr = player
	epochs = 500
	learning_rate = 0.0003
	display_step = 50
	if True:
		#batch_size = 50
		batch_size = 1
		batch_num = int(len(x_arr) / batch_size)
	else:
		batch_num = 1

	tf.reset_default_graph()
	x = tf.placeholder(name='x',shape=(None,1),dtype=tf.float32)
	y = tf.placeholder(name='y',shape=(None,1),dtype=tf.float32)

	layer = x
	for _ in range(3):
	    layer = tf.layers.dense(inputs=layer, units=12, activation=tf.nn.tanh)
	output = tf.layers.dense(inputs=layer, units=1)

	cost = tf.reduce_mean(tf.losses.mean_squared_error(labels=y,predictions=output))

	optimizer = tf.train.AdamOptimizer(learning_rate).minimize(cost)
	x_batches = np.array_split(x_arr, batch_num)
	y_batches = np.array_split(y_arr, batch_num)
	with tf.Session() as sess:
	    sess.run(tf.global_variables_initializer())
	    for epoch in range(epochs):
	        avg_cost = 0.0
	        x_batches, y_batches = shuffle(x_batches, y_batches)
	        for i in range(batch_num):
	            x_batch = np.expand_dims(x_batches[i],axis=1)
	            y_batch = np.expand_dims(y_batches[i],axis=1)
	            _, c = sess.run([optimizer,cost], feed_dict={x:x_batch, y:y_batch})
	            avg_cost += c/batch_num
	        if epoch % display_step == 0:
	            print('Epoch {0} | cost = {1:.4f}'.format(epoch,avg_cost))
	    y_pred = sess.run(output,feed_dict={x:np.expand_dims(x_test,axis=1)})
	    print('Final cost: {0:.4f}'.format(avg_cost))

	fig, ax = plt.subplots(figsize=(10,10))
	plt.grid(True)
	plt.xlabel('x')
	plt.ylabel('y')
	ax.scatter(x_arr,y_arr,c='b',label='sampled data')
	ax.scatter(x_test,y_pred,c='r',label='predicted values')
	ax.legend(loc='upper center',fontsize='large',shadow=True)
	plt.show()

def mdn_cost(mu, sigma, y):
    dist = tf.distributions.Normal(loc=mu, scale=sigma)
    return tf.reduce_mean(-dist.log_prob(y))

if __name__ == '__main__':
	main_nn()