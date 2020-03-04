import os,sys,time

def write_blank_config_file():
	config_text = """# System Config
----------------
[Runtime configs]
save = True 			# Toggle saving data and results (default True)
load = True 			# Toggle loading data and results (default True)
verbosity = 0 			# Set verbosity, from [0-9] (default 0)

teamsize = 1 			# Toggle singles/doubles/crews (default 1)
static_teams = False 	# Toggle tracking individual players or static teams (default False)
use_arcadians = False 	# Toggle inclusion of Arcadian events (events excluding ranked/top players) (default False)

force_first = True		# Only return the first matching result for query calls (default True) 
print = False 			# Toggle printing of tournament readin results to console (default False)
display_size = 64 		# Number of players to print out for tournament readin results (default 64)

----------------
[Storage configs]
offline_mode = False 			# [WIP] Toggle whether to search online for information. Automatically enables all caching. (default False)
cache_results = True 			# Toggle saving tournament phases and events locally. Recommended only if frequently rebuilding database. (default True)
cache_slugs = True 				# Toggle saving slugs from ssbwiki's List of National Tournaments. (default True)
cache_mainranks = True 			# Toggle saving mainrank results from ssbwiki. (default True)
use_cached_ranks = False 		# Use saved mapping between matched player_ids and cached mainranks. (default False)
cache_social_media = True 		# Toggle saving social media accounts // smash.gg player api direct calls. Recommended if frequently rebuilding database. (default True)
cache_region_mappings = True 	# Toggle saving region lookups/data for players. (default True)
pregenerate_website_searchbar = False # Toggle pregeneration of player searchbar content files for smashranks site (default False)

----------------
[Analysis configs]
min_activity = 3 				# Minimum event attendance to be considered an "active" player (default 3)

# Elo configs
elo_init_value = 1500 			# Initial rating for players in Elo algorithm (default 1500)
use_fide_k = True 				# Toggle using FIDE K-factor vs. USCF method (default True)
use_fide_perf = True 			# Toggle using FIDE performance calculations vs "algorithm of 400" (default True)

# Glicko-2 configs
glicko_tau = 0.5 				# Tau value used by Glicko-2 algorithm, between 0.3 and 1.2 is recommended (default 0.5)
glicko_tol = 0.000001 			# Tolerance threshold to be used by Glicko-2 algorithm, a very small value is recommended (default 0.000001)
glicko_init_value = 1500 		# Initial rating for players in Glicko-2 algorithm (default 1500)
glicko_init_rd = 350 			# Initial rating deviation for players in Glicko-2 algorithm (default 350)
glicko_init_sigma = 0.06 		# Initial sigma for players in Glicko-2 algorithm (default 0.06)

# TrueSkill configs
trueskill_init_mu = 25 			# Initial skill rating for TrueSkill algorithm (default 25)
trueskill_init_sigma = 8.33333 	# Initial skill rating variance for TrueSkill algorithm (default 25/3 == 8.3333...)

# S-Rank configs
srank_alpha = 0.5 				# S-Rank learnrate (default 0.5)
srank_beta = 0.9 				# S-Rank learning momentum coefficient; currently deprecated (default 0.9)
srank_tol = 0.0001 				# S-Rank convergence tolerance. Recommended <= 0.0001 (default 0.0001)
srank_learn_decay = True 		# Toggle learnrate decaying over time (default True)
srank_pad_zeros = False 		# Toggle padding of zeros to LHS of winprobs limit before fitting sigmoids (default False)
srank_running_avg_sigma = 0.1 	# Sigma of Gaussian window, to capture and weight win probabilities (default 0.1)
srank_running_avg_step = 0.05 	# Step size for sliding windows (default 0.05)
srank_fit_corners = False 		# Toggle inclusion of expected boundary points in sigfit to help encourage normal sigmoid behavior (default False)
srank_combine_unranked = False 	# Toggle consolidation of unranked player winprobs for sigmoid fitting (default False)
srank_print_res = False 		# Print results of sigmoid fitting to console (default False)
srank_ranking_period = 12		# Duration of S-Rank "current" ranking period, in months (default 12)

srank_sig_mode = alt 			# Change which sigmoid type is fit to data, from ['sigmoid','simple','alt']. sigmoid is fastest, alt is most accurate. (default alt)
srank_fit_mode = winprobs 		# Change how the data is presented to the sigmoid fitting subroutine, from [winprobs,histogram,running_avg,mixed]. (default winprobs)
srank_calc_mode = array			# Choose calculation mode, from ['array','dict']. Array is strongly recommended. (default array)
srank_score_mode = intsig 		# Choose scoring method, from ['intsig','intercept','average']. Intsig required if sig_mode = alt. (default intsig)
srank_seed_mode = last 			# Choose seeding method, from ['last','winrate','placing','random','blank','normalized_skills']. Last or blank recommended. (default last)

srank_max_iter = 1000 			# Max iterations per update_sigmoids call. Recommended ~500-1000 for standard config, ~100 if running_bins are enabled. (default 1000)
srank_max_size = None 			# Max number of players to consider in ranking calculations. If None, all "active" players are considered.
srank_simbrack = False 			# Toggle scoring by simulated brackets rather than sigmoid fitting; deprecated (default False)

character_matchups = False 		# Toggle for generating character matchup charts (default False)
matchup_mode = default 			# Set character matchup chart calculation mode
make_tier_list = False 			# Toggle for generating character tier lists (default False)
tier_list_mode = default 		# Set character tier list calculation mode

web_upload = False 				# Toggle for pushing the db to the online Firebase instance (default False)
fb_key_path = ../lib/Firebase_API_Key.json 		# Path to Firebase API Key json file"""

	try:
		config_file = open('./configs/defaults.conf','w')
	except FileNotFoundError:
		if not os.path.isdir('./configs/'):
			os.mkdir('./configs/')
		config_file = open('./configs/defaults.conf','x')
	config_file.write(config_text)
	config_file.close()

# generates files necessary for a clean install // establishes necessary directories
# write blank smash.gg/firebase api key files
# WIP
def setup_dirs():
	return None


if __name__ == '__main__':
	print('I should set up something!')
	setup_dirs()
	write_blank_config_file()