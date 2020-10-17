from application.pubg.api_router import (
	get_player as get_pubg_player,
	seasons_for_platform as get_pubg_seasons_for_platform,
	match_detail as get_pubg_match_detail,
	search as pubg_player_search
)
from application.cod.api_router import (
	player as get_cod_player,
	search as cod_player_search
)

MODULE_LIST = [
    'cod',
    'pubg'
]

MODULE_DICTIONARY = [
	{
		'short_name': 'pubg',
		'name': 'PLAYERUNKNOWN\'S BATTLEGROUNDS STATS',
		'title_name': 'PLAYERUNKNOWN\'S BATTLEGROUNDS',
		'prefix': '/pubg/',
		'image': '/static/images/pubg.jpg',
		'desc': """<p>Q: What is this module?</p>
			<p>A: This module is simply an alternative to much bigger sites such as PUBGLookup, PUBG.OP.GG etc</p>
			<hr>
			<p>Q: What can we do with this module?</p>
			<p>A: Well, currently it is pretty simple. But, currently this module has the following features
				<ol>
					<li>View any PUBG Matches from a user played in the last 14 days (<a href=\'/pubg/user/DefinitelyNotDes/?platform=steam\'>Me, for example</a>)</li>
					<li>View the details of a given match, as well as what happend in a given match.</li>
					<li>View other people which participated in those matches.</li>
					<li>Filter the list of matches by Game Mode, Perspective, and view an entire leaderboard of those matches.</li>
				</ol>
			</p>
			<hr>
		""",
		'module_search_url': '/api/pubg/search/',
		'perspectives':[
			{
				'value': '',
				'text': 'Select a Perspective'
			},
			{
				'value': 'all',
				'text': 'ALL'
			},
			{
				'value': 'fpp',
				'text': 'FPP'
			},
			{
				'value': 'tpp',
				'text': 'TPP'
			}
		],
		'game_modes_no_perspective': [
			{
				'value': '',
				'text': 'Select a Game Mode'
			},
			{
				'value': 'all',
				'text': 'ALL'
			},
			{
				'value': 'solo',
				'text': 'SOLO'
			},
			{
				'value': 'duo',
				'text': 'DUO'
			},
			{
				'value': 'squad',
				'text': 'SQUAD'
			}
		],
		'game_modes': [
			{
				'value': '',
				'text': 'Select a Game Mode'
			},
			{
				'value': 'all',
				'text': 'ALL'
			},
			{
				'value': 'solo',
				'text': 'SOLO'
			},
			{
				'value': 'solo-fpp',
				'text': 'SOLO FPP'
			},
			{
				'value': 'duo',
				'text': 'DUO'
			},
			{
				'value': 'duo-fpp',
				'text': 'DUO FPP'
			},
			{
				'value': 'squad',
				'text': 'SQUAD'
			},
			{
				'value': 'squad-fpp',
				'text': 'SQUAD FPP'
			},
			{
				'value': 'tdm',
				'text': 'TDM'
			}
		],
		'regions': [
			{
				'value': '',
				'text': 'Select a region for this platform'
			},
			{
				'value': 'pc-eu',
				'text': 'PC EU'
			},
			{
				'value': 'pc-as',
				'text': 'PC AS'
			},
			{
				'value': 'pc-jp',
				'text': 'PC JP'
			},
			{
				'value': 'pc-krjp',
				'text': 'PC KRJP'
			},
			{
				'value': 'pc-kakao',
				'text': 'PC KAKAO'
			},
			{
				'value': 'pc-na',
				'text': 'PC NA'
			},
			{
				'value': 'pc-oc',
				'text': 'PC OC'
			},
			{
				'value': 'pc-ru',
				'text': 'PC RU'
			},
			{
				'value': 'pc-sa',
				'text': 'PC SA'
			},
			{
				'value': 'pc-sea',
				'text': 'PC SEA'
			},
		
			{
				'value': 'psn-as',
				'text': 'PSN AS'
			},
			{
				'value': 'psn-eu',
				'text': 'PSN EU'
			},
			{
				'value': 'psn-na',
				'text': 'PSN NA'
			},
			{
				'value': 'psn-oc',
				'text': 'PSN OC'
			},
		
			{
				'value': 'xbox-as',
				'text': 'XBOX AS'
			},
			{
				'value': 'xbox-eu',
				'text': 'XBOX EU'
			},
			{
				'value': 'xbox-na',
				'text': 'XBOX NA'
			},
			{
				'value': 'xbox-oc',
				'text': 'XBOX OC'
			},
			{
				'value': 'xbox-sa',
				'text': 'XBOX SA'
			}
		],
		'platforms': [
			{
				'value': '',
				'text': 'Select a Platform'
			},
			{
				'value': 'steam',
				'text': 'PC'
			},
			{
				'value': 'xbox',
				'text': 'Xbox'
			},
			{
				'value': 'psn',
				'text': 'PlayStation'
			},
		],
		'field_warnings': {},
		'module_index': 'pubg/pubg_index.html',
		'requires_platform': True,
		'player_function': get_pubg_player,
		'endpoints': {
			'player': '/api/pubg/player/',
			'player_search': '/api/pubg/search/',
			'retrieve_player_stats': '/api/pubg/retrieve_season_stats/',
			'retrieve_matches': '/api/pubg/retrieve_matches/',
			'match_rosters': '/api/pubg/match_rosters/',
			'seasons_for_platform':'/api/pubg/seasons_for_platform/',
			'leaderboards': '/api/pubg/leaderboards/',
			'status': '/api/common/status/'
		},
		'endpoint_functions': {
			'seasons_for_platform':get_pubg_seasons_for_platform,
			'match_detail': get_pubg_match_detail,
			'search': pubg_player_search
		}
	},
	{
		'short_name': 'cod',
		'name': 'CALL OF DUTY STATS',
		'title_name': 'CALL OF DUTY',
		'prefix': '/cod/',
		'image': '/static/images/cod.jpg',
		'desc': """<p>Q: What is this module?</p>
			<p>A: This module is simply an alternative to much bigger sites such as cod.tracker.gg, codstats.net etc.</p>
			<hr>
			<p>Q: What can we do with this module?</p>
			<p>A: Well, currently it is pretty simple. But, currently this module has the following features
				<ol></ol>
			</p>
			<hr>
		""",
		'module_search_url': '/api/cod/search/',
		'platforms': [
			{
				'value': '',
				'text': 'Select a Platform'
			},
			{
				'value': 'steam',
				'text': 'Steam'
			},
			{
				'value': 'uno',
				'text': 'Activision'
			},
			{
				'value': 'battle',
				'text': 'Battle.Net'
			},
			{
				'value': 'xbl',
				'text': 'Xbox'
			},
			{
				'value': 'psn',
				'text': 'PlayStation'
			},
		],
		'titles': [
			{
				'value': '',
				'text': 'Select a Title',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': False
					}
				]
			},
			{
				'value': 'mw',
				'text': 'Modern Warfare 2019',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': True
					}
				]
			},
			{
				'value': 'bo4',
				'text': 'Black Ops 4',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': False
					}
				]
			},
			{
				'value': 'wwii',
				'text': 'World War II',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': False
					}
				]
			},
			{
				'value': 'iw',
				'text': 'Infinite Warfare',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': False
					}
				]
			},
			{
				'value': 'bo3',
				'text': 'Black Ops 3',
				'data_attributes':[
					{
						'name': "is-unified",
						'value': False
					}
				]
			},
		],
		'field_warnings': {
			'platform': {
				"battle": {
					'message': 'Battle.Net platform has the following requirements that need to be met before submiting: ',
					'requires': [
						{
							'char': '#',
							'example': '{username}#12345',
							'field': 'Player Name'
						}
					]
				}
			}
		},
		'module_index': 'cod/cod_index.html',
		'game_modes': [
			{
				'value': '',
				'text': 'Select a Game Mode'
			},
			{
				'value': 'core',
				'text': 'Core'
			},
			{
				'value': 'hc',
				'text': 'Hardcore'
			},
			{
				'value': 'arena',
				'text': 'Arena'
			}
		],
		'requires_platform': True,
		'player_function': get_cod_player,
		'endpoints': {
			'player': '/api/cod/player/',
			'player_search': '/api/cod/search/',
			'stats': '/api/cod/stats/',
			'leaderboards': '/api/cod/leaderboards/'
		},
		'endpoint_functions':{
			'search': cod_player_search
		}
	}
]

MODULE_MAPPING = {
	'pubg': MODULE_DICTIONARY[0],
	'cod': MODULE_DICTIONARY[1]
}

LABELS = {
	"record_longest_win_streak": "Longest Recorded Win Streak",
	"record_xp_in_a_match": "Record XP earned in a Match",
	"accuracy": "Accuracy",
	"losses": "Total Losses",
	"total_games_played": "Total games played",
	"win_loss_ratio": "Win Loss Ratio",
	"total_shots": "Total shots fired",
	"best_score_xp": "Best Score XP",
	"games_played": "Games Played",
	"deaths": "Total deaths",
	"wins": "Total wins",
	"score": "Total score",
	"kd_ratio": "KD Ratio",
	"best_assists": "Most Assists in a mach",
	"best_score": 'Highest score',
	"record_deaths_in_a_match": 'Highest deaths',
	'score_per_game': 'Average score per game',
	'record_kills_in_a_match': 'Highest kills',
	'suicides': 'Total suicides',
	'current_win_streak': 'Current winstreak',
	'kills': 'Total kills',
	'time_played_total': 'Total time played',
	'headshots': 'Total headshots',
	'assists': 'Total assists',
	'misses': 'Total shots missed',
	'misses': 'Total misses',
	'score_per_minute': 'Average SPM',
	'hits': 'Total hits',
	'best_kill_streak': 'Highest killstreak',
	'time_played': 'Total time played',
	'defuses': 'Total defuses',
	'plants': 'Total plants',
	'defends': 'Total defends',
	'avg_life_time': 'Average time alive',
	'objective_teams_wiped': 'Total team wipes',
	'wall_bangs': 'Total wall bangs',
	'kills_per_game': 'Average kills per game',
	'distance_travelled': 'Total distance travelled',
	'objective_munitions_box_teammate_used': 'Total munition boxes used',
	'gulag_deaths': 'Total deaths in gulag',
	'time_played': 'Total time played',
	'headshot_percentage': 'Average headshot percentage',
	'matches_played': 'Total matches played',
	'gulag_kills': 'Total gulag kills',
	'damage_done': 'Total damage done',
	'damage_taken': 'Total damage taken',
	'objective_br_mission_pickup_tablet': 'Total missions',
	'infected': 'Total infected',
	'time': 'Time played',
	'match_id': 'Match API ID',
	'utc_start_seconds': 'Match started at',
	'utc_end_seconds': 'Match ended at',
	'team_survival_time': 'Team survival time',
	'player_count': 'Total player count',
	'rank': 'Placement',
	'mode': 'Game Mode',
}

NOT_DISPLAY = [
	'best_sguard_wave',
	'best_squard_crates',
	'best_sguard_weapon_level',
	'best_confirmed',
	'best_score_xp',
	'best_squad_kills',
	'best_field_goals',
	'best_kill_chains',
	'best_match_bonus_xp',
	'best_match_xp',
	'best_sguard_weapon_level',
	'best_stabs',
	'best_returns',
	'ties',
	'best_damage',
	'best_kills_as_infected',
	'best_kills_as_survivor',
	'best_destructions',
	'best_rescues',
	'best_plants',
	'best_damage',
	'best_setbacks',
	'best_touchdowns',
	'best_deaths',
	'best_medal_xp',
	'best_defends',
	'best_kills',
	'best_defuses',
	'best_captures',
	'best_denied',
	'objective_last_stand_kill',
	'objective_destroyed_vehicle_light',
	'objective_br_down_enemy_circle_1',
	'objective_br_down_enemy_circle_2',
	'objective_br_down_enemy_circle_3',
	'objective_br_down_enemy_circle_4',
	'objective_br_down_enemy_circle_5',
	'objective_br_down_enemy_circle_6',
	'objective_br_down_enemy_circle_7',
	'objective_reviver',
	'objective_br_kiosk_buy',
	'executions',
	'objective_br_cache_open',
	'obj_time'
]