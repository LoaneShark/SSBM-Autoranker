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
parser.add('-cf','--config_file',help='path to config file',default='./defaults.conf',is_config_file=True)

# instance/db type args
parser.add('-g','--game',help='game id to be used: Melee=1, P:M=2, Wii U=3, 64=4, Ultimate=1386 (default melee)',default=1, required=True)
parser.add('-y','--year',help='The year you want to analyze (for ssbwiki List of Majors scraper)(default 2016)',default=2016, required=True)
parser.add('-yc','--year_count',help='How many years to analyze from starting year',default=0)
parser.add('-fg','--force_game',help='game id to be used, force use (cannot scrape non-smash slugs)',default=False)

parser.add('-c','--current_db',help='keep the database "current" i.e. delete tourney records over 1 year old (default False)',action='store_true')
parser.add('-sd','--season_db',help='keep the database as the "current season" i.e. delete tourney records not in current (realtime) year (default False)',action='store_true')

parser.add('-sl','--slug',help='tournament URL slug',default=None)
parser.add('-ss','--short_slug',help='shorthand tournament URL slug',default=None)

# basic/general config args
parser.add('-s','--save',help='save db/cache toggle (default True)',action='store_false')
parser.add('-l','--load',help='load db/cache toggle (default True)',action='store_false')
parser.add('-v','--verbosity',help='verbosity [0-9]',default=0)

parser.add('-t','--teamsize',help='1 for singles bracket, 2 for doubles, 4+ for crews (default 1)',default=1)
parser.add('-st','--static_teams',help='store teams as static units, rather than strack skill of its members individually [WIP]',action='store_true')
parser.add('-ar','--use_arcadians',help='count arcadian events (default False)',action='store_true')

parser.add('-ff','--force_first',help='force the first criteria-matching event to be the only event (default True)',action='store_false')
parser.add('-d','--display_size',help='lowest placing shown on pretty printer output, or -1 to show all entrants (default 64)',default=64)
parser.add('-p','--print',help='print tournament final results to console as they are read in (default False)',action='store_true')

# storage args
parser.add('-o','--offline',help='[WIP] Toggle whether to search online for information. Automatically enables all caching. (default False)',action='store_true')
parser.add('-cs','--cache_slugs',help='load slugs toggle (default True)',action='store_false')
parser.add('-cr','--cache_results',help='save phase data after tournament is done being read in (default False)',action='store_true')
parser.add('-cm','--cache_mainranks',help='load slugs toggle (default True)',action='store_false')
parser.add('-cu','--use_cached_ranks',help='use saved rank -> p_id mapping (default False)',action='store_true')
parser.add('-cw','--cache_social_media',help='cache social media accounts/player info query (default False)',action='store_true')
parser.add('-cg','--cache_region_mappings',help='cache player city/state/country to citydict (default True)',action='store_false')

# analysis parameter args
parser.add('-ma','--min_activity',help='minimum number of tournament appearances in order to be ranked. ELO etc still calculated.',default=3)

parser.add('-ei','--elo_init_value',help='Initial value for new players in Elo algorithm (default 1500)',default=1500)
parser.add('-ek','--use_fide_k',help='toggle whether to use FIDE vs. USCF method to calculate K-factor (default True)',action='store_false')
parser.add('-ep','--use_fide_perf',help='toggle whether to use FIDE vs. alg of 400 for performance values (default True)',action='store_false')

parser.add('-gt','--glicko_tau',help='tau value to be used by Glicko-2 algorithm (default 0.5)',default=0.5)
parser.add('-ge','--glicko_tol',help='convergence tolerance value to be used by Glicko-2 algorithm (default 0.000001)',default=0.000001)
parser.add('-gv','--glicko_init_value',help='initial rating value to be used by Glicko-2 algorithm (default 1500)',default=1500.)
parser.add('-gr','--glicko_init_rd',help='initial rating deviation value to be used by Glicko-2 algorithm (default 350)',default=350.)
parser.add('-gs','--glicko_init_sigma',help='initial sigma value to be used by Glicko-2 algorithm (default 0.06)',default=0.06)

parser.add('-ra','--srank_alpha',default = 0.5, help= 'S-Rank learnrate (default 0.5)')
parser.add('-rb','--srank_beta',default = 0.9, help= ' S-Rank learning momentum coefficient; currently deprecated (default 0.9)')
parser.add('-rt','--srank_tol',default = 0.0001, help= ' S-Rank convergence tolerance. Recommended <= 0.0001 (default 0.0001)')
parser.add('-rl','--srank_learn_decay',action = 'store_false', help= ' Toggle learnrate decaying over time (default True)')
parser.add('-rh','--srank_use_bins',action = 'store_true', help= ' Toggle if sigmoids are fit to histogram records vs. individual h2h records (default False)')
parser.add('-rv','--srank_use_running_avg',action = 'store_true', help= ' Toggle if sigmoids are fit to local avg winrate vs. individual h2h records, overwrites use_bins (default False)')
parser.add('-rp','--srank_print_res',action = 'store_true', help= ' Print results of sigmoid fitting to console (default False)')

parser.add('-rs','--srank_sig_mode',default = 'alt', help= ' Change which sigmoid type is fit to data, from [sigmoid,simple,alt]. sigmoid is fastest, alt is most accurate. (default alt)')
parser.add('-rc','--srank_calc_mode',default = 'array', help= ' Choose calculation mode, from [array,dict]. Array is strongly recommended. (default array)')
parser.add('-rr','--srank_score_mode',default = 'intsig', help= ' Choose scoring method, from [intsig,intercept,average]. Intsig required if sig_mode = alt. (default intsig)')
parser.add('-rm','--srank_seed_mode',default = 'last', help= ' Choose seeding method, from [last,winrate,placing,random,blank,normalized_skills]. Last or blank recommended. (default last)')

parser.add('-ri','--srank_max_iter',default = 1000, help= ' Max iterations per update_sigmoids call. Recommended ~500-1000 for standard config, ~100 if running_bins are enabled. (default 1000)')
parser.add('-rn','--srank_max_size',default = None, help= ' Max number of players to consider in ranking calculations. If None, all "active" players are considered.')
parser.add('-rx','--srank_simbrack',default = False, help= ' Toggle scoring by simulated brackets rather than sigmoid fitting; deprecated (default False)')

options,args = parser.parse_known_args()

def get_args():
	return options


if __name__ == "__main__":
	#args = parser.parse_known_args()
	print(options)
	#write_blank_config_file()