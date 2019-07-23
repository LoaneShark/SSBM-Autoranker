import os,sys,pickle,time,csv
import argparse
import configargparse
from setup import write_blank_config_file

def add_bool_arg(parser, name, default=False):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--' + name, dest=name, action='store_true')
    group.add_argument('--no-' + name, dest=name, action='store_false')
    parser.set_defaults(**{name:default})

parser = configargparse.get_argument_parser()
# config file path
parser.add('-cf','--config_file',help='path to config file',default='./configs/defaults.conf',is_config_file=True,type=str)

# instance/db type args
parser.add('-g','--game',help='game id to be used: Melee=1, P:M=2, Wii U=3, 64=4, Ultimate=1386 (default melee)',default=1, required=True, type=int)
parser.add('-y','--year',help='The year you want to analyze (for ssbwiki List of Majors scraper)(default 2016)',default=2016, required=True, type=int)
parser.add('-yc','--year_count',help='How many years to analyze from starting year',default=0, type=int)
parser.add('-fg','--force_game',help='game id to be used, force use (cannot scrape non-smash slugs)',default=False)
parser.add('-d','--debug',help='debug id toggle, will save separately (default False)',action='store_true')
parser.add('-ds','--debug_str',help='optional str to append to db key name (alphanumeric chars only)',default=False)

parser.add('-c','--current_db',help='keep the database "current" i.e. delete tourney records over 1 year old (default False)',action='store_true')
parser.add('-sd','--season_db',help='keep the database as the "current season" i.e. delete tourney records not in current (realtime) year (default False)',action='store_true')

parser.add('-sl','--slug',help='tournament URL slug',default=None)
parser.add('-ss','--short_slug',help='shorthand tournament URL slug',default=None)

# basic/general config args
parser.add('-s','--save',help='save db/cache toggle (default True)',action='store_false')
parser.add('-l','--load',help='load db/cache toggle (default True)',action='store_false')
parser.add('-v','--verbosity',help='verbosity [0-9]',default=0, type=int)

parser.add('-t','--teamsize',help='1 for singles bracket, 2 for doubles, 4+ for crews (default 1)',default=1, type=int)
parser.add('-st','--static_teams',help='store teams as static units, rather than strack skill of its members individually [WIP]',action='store_true')
parser.add('-ar','--use_arcadians',help='count arcadian events (default False)',action='store_true')

parser.add('-ff','--force_first',help='force the first criteria-matching event to be the only event (default True)',action='store_false')
parser.add('-dn','--display_size',help='lowest placing shown on pretty printer output, or -1 to show all entrants (default 64)',default=64, type=int)
parser.add('-p','--print',help='print tournament final results to console as they are read in (default False)',action='store_true')

# storage args
parser.add('-o','--offline',help='[WIP] Toggle whether to search online for information. Automatically enables all caching. (default False)',action='store_true')
parser.add('-cs','--cache_slugs',help='load slugs toggle (default True)',action='store_false')
parser.add('-cr','--cache_results',help='save phase data after tournament is done being read in (default False)',action='store_true')
parser.add('-cm','--cache_mainranks',help='toggle caching the "official" rankings (default True)',action='store_false')
parser.add('-cu','--use_cached_ranks',help='use saved rank -> p_id mapping (default False)',action='store_false')
parser.add('-cw','--cache_social_media',help='cache social media accounts/player info query (default True)',action='store_false')
parser.add('-cg','--cache_region_mappings',help='cache player city/state/country to citydict (default True)',action='store_false')
parser.add('-sb','--pregenerate_website_searchbar',help='toggle whether to pregenerate necessary ajax files for website searchbar (default False)',action='store_true')

# analysis parameter args
parser.add('-ma','--min_activity',help='minimum number of tournament appearances in order to be ranked. ELO etc still calculated.',default=3, type=int)

parser.add('-ei','--elo_init_value',help='Initial value for new players in Elo algorithm (default 1500)',default=1500., type=float)
parser.add('-ek','--use_fide_k',help='toggle whether to use FIDE vs. USCF method to calculate K-factor (default True)',action='store_false')
parser.add('-ep','--use_fide_perf',help='toggle whether to use FIDE vs. alg of 400 for performance values (default True)',action='store_false')

parser.add('-gt','--glicko_tau',help='tau value to be used by Glicko-2 algorithm (default 0.5)',default=0.5, type=float)
parser.add('-ge','--glicko_tol',help='convergence tolerance value to be used by Glicko-2 algorithm (default 0.000001)',default=0.000001, type=float)
parser.add('-gv','--glicko_init_value',help='initial rating value to be used by Glicko-2 algorithm (default 1500)',default=1500., type=float)
parser.add('-gr','--glicko_init_rd',help='initial rating deviation value to be used by Glicko-2 algorithm (default 350)',default=350., type=float)
parser.add('-gs','--glicko_init_sigma',help='initial sigma value to be used by Glicko-2 algorithm (default 0.06)',default=0.06, type=float)

parser.add('-ra','--srank_alpha',default = 0.5, help='S-Rank learnrate (default 0.5)', type=float)
parser.add('-rb','--srank_beta',default = 0.9, help='S-Rank learning momentum coefficient; currently deprecated (default 0.9)', type=float)
parser.add('-rv','--srank_tol',default = 0.0001, help='S-Rank convergence tolerance. Recommended <= 0.0001 (default 0.0001)', type=float)
parser.add('-rd','--srank_learn_decay',action = 'store_false', help='Toggle learnrate decaying over time (default True)')
parser.add('-rz','--srank_pad_zeros',action = 'store_true', help='Toggle padding of zeros to LHS of top win (default False)')
parser.add('-rw','--srank_running_avg_sigma', default = 0.1, help='Gaussian window sigma for running average weighting (default 0.1)', type=float)
parser.add('-rl','--srank_running_avg_step', default = 0.05, help='Step size for gaussian windows in running average calculation (default 0.05)', type=float)
parser.add('-ro','--srank_fit_corners',action='store_true',help='Toggle inclusion of data points (0,0) and (1,1) to help fit expected sigmoid shape (default False)')
parser.add('-ru','--srank_combine_unranked',action='store_true',help='Toggle consolidation of unranked player winprobs // "the field" (default False)')
parser.add('-rp','--srank_print_res',action = 'store_true', help='Print results of sigmoid fitting to console (default False)')
parser.add('-rt','--srank_ranking_period',default = 12,help='Duration of S-Rank "current" ranking period, in months (default 12)',type=int)

parser.add('-rs','--srank_sig_mode',default = 'alt', help='Change which sigmoid type is fit to data, from [sigmoid,simple,alt]. sigmoid is fastest, alt is most accurate. (default alt)')
parser.add('-rf','--srank_fit_mode',default = 'winprobs', help='Change how the data is presented to the sigmoid fitting subroutine, from [winprobs,histogram,running_avg,mixed]. (default winprobs)')
parser.add('-rc','--srank_calc_mode',default = 'array', help='Choose calculation mode, from [array,dict]. Array is strongly recommended. (default array)')
parser.add('-rr','--srank_score_mode',default = 'intsig', help='Choose scoring method, from [intsig,intercept,average]. Intsig required if sig_mode = alt. (default intsig)')
parser.add('-rm','--srank_seed_mode',default = 'last', help='Choose seeding method, from [last,winrate,placing,random,blank,normalized_skills]. Last or blank recommended. (default last)')

parser.add('-ri','--srank_max_iter',default = 1000, help='Max iterations per update_sigmoids call. Recommended ~500-1000 for standard config, ~100 if running_bins are enabled. (default 1000)', type=int)
parser.add('-rn','--srank_max_size',default = None, help='Max number of players to consider in ranking calculations. If None, all "active" players are considered. (default None)')
parser.add('-rx','--srank_simbrack',default = False, help='Toggle scoring by simulated brackets rather than sigmoid fitting; deprecated (default False)')
## < show key sigmoids >

# character matchups // tier lists
parser.add('-mu','--character_matchups',action='store_true',help='toggle for generating character matchup charts (default False)')
parser.add('-mm','--matchup_mode',default='default',help='set character matchup chart calculation mode')
parser.add('-tl','--make_tier_list',action='store_true',help='toggle for generating character tier lists (default False)')
parser.add('-tm','--tier_list_mode',default='default',help='set character tier list calculation mode')

# web db args
parser.add('-wu','--web_upload',action='store_true',help='toggle for pushing the game db to the online database (default False)')
parser.add('-wk','--fb_key_path',default='../lib/Firebase_API_Key.json',help='path to the firebase api key json file for the web db')

args,arglist = parser.parse_known_args()

if args.verbosity >= 7:
	print(args)

def get_args():
	return args

def generate_db_str():
	db_list = [str(args.game),str(args.year),str(args.year_count)]
	if args.current_db:
		if args.season_db:
			db_list.append('s')
		else:
			db_list.append('c')

	if args.use_arcadians:
		db_list.append('a')

	if args.teamsize > 1:
		db_list.append('t'+str(args.teamsize))

	if args.debug:
		db_list.append('d')
	if args.debug_str:
		#db_list.append('KEY')
		db_list.append(str(args.debug_str))

	db_str = '_'.join(db_list)
	return db_str

def get_db_verstr():

	verstr = str(args.game)+'/'+str(args.year)
	if args.year_count > 0:
		verstr +='-'+str(args.year+args.year_count)
	if args.current_db:
		verstr += '_c'
	if args.debug_str:
		verstr += '_'+str(args.debug_str)

	return verstr

if __name__ == '__main__':
	#args = parser.parse_known_args()
	print(args)
	#write_blank_config_file()