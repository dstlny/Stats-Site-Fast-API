import sys
import os

## my files
import application.pubg.settings as api_settings
from application.pubg.models import *
from application.cache_utils import *

## external libs
import json as old_json
import orjson as json
import requests
import urllib

## py libs
import time
from datetime import datetime, timedelta, time as datetime_time, timezone
from dateutil.parser import parse
from dateutil.tz import UTC
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
import logging
from typing import *

from application.exceptions import *
import application.launch_args as launch_arguments

session = requests.Session()

formatter = logging.Formatter(
	fmt='[%(asctime)s](%(levelname)s) %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)

LOG_SQL = launch_arguments.SHOULD_LOG_SQL

if LOG_SQL:
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	file_handler = logging.FileHandler(filename='sql.log', mode='a+')
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
else:
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(logging.INFO)
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	
def build_url(
	platform: str,
) -> str:

	return "{}{}".format(
		api_settings.BASE_API_URL,
		api_settings.PLATFORM_SHARD.format(platform.strip().lower())
	)

def get_platform(
	url: str,
) -> str:

	url = url.strip().lower()
	
	if 'steam' in url or 'pc' in url:
		return 'steam'
	elif 'xbox' in url:
		return 'xbox'
	elif "psn" in url:
		return 'psn'
	elif "kakao" in url:
		return 'kakao'
	elif 'stadia' in url:
		return 'stadia'
	elif "tour" in url:
		return 'tour'

def build_player_url(
	base_url: str,
	player_name: str,
) -> str:
	return "{}{}{}".format(
		base_url,
		api_settings.PLAYER_FILTER,
		player_name
	)

def build_player_account_id_url(
	base_url: str,
	player_id: str,
) -> str:
	return "{}{}".format(
		base_url,
		api_settings.PLAYER_ACCOUNT_FILTER.format(player_id)
	)

def build_season_url(
	base_url: str,
	season_id: str,
	player_id: str,
	is_ranked: bool,
) -> str:

	return "{}{}{}".format(
		base_url,
		api_settings.SEASON_FILTER.format(player_id, season_id),
		'/ranked' if is_ranked else ''
	)

def build_lifetime_url(
	base_url: str,
	player_id: str,
) -> str:
	return "{}{}".format(
		base_url,
		api_settings.LIFETIME_FILTER.format(player_id)
	)

def build_tournament_url(
	tournament_id: str,
) -> str:
	return "{}{}".format(
		api_settings.BASE_API_URL,
		api_settings.TOURNAMENTS_FILTER.format(tournament_id)
	)

def build_match_url(
	base_url: str,
	platform: str,
) -> str:
	return "{}{}".format(
		base_url,
		api_settings.MATCH_FILTER.format(platform)
	)

def build_leaderboard_url(
	base_url: str,
	season_id: str,
	game_mode: str,
) -> str:
	return "{}{}".format(
		base_url,
		api_settings.LEADERBOADS_FILTER.format(season_id, game_mode)
	)

def build_list_all_seasons_url(
	base_url: str,
):
	return "{}{}".format(
		base_url,
		api_settings.SEASON_LIST_URL
	)

def correct_perspective(perspective) -> str:
	return perspective.lower() if perspective and 'all' not in perspective.lower() else None

def correct_mode(
	mode: str
) -> str:
	return mode.lower() if mode and 'all' not in mode.lower() else None

def get_map_name(
	map_codename: str
) -> str:
	return api_settings.MAP_BINDING.get(map_codename)

def make_request(
	url: str
) -> dict:

	with FuturesSession() as session:
		session.headers.update(api_settings.API_HEADER)
		future = session.get(url)
		response = future.result()

		try:
			json_response = json.loads(response.content)
			return json_response
		except:
			rate_limit_remaining = int(response.headers.get('X-Ratelimit-Remaining'))
			rate_limit_reset = int(response.headers.get('X-Ratelimit-Reset'))

			if rate_limit_remaining == 0:
				time_to_sleep = (datetime.fromtimestamp(rate_limit_reset) - datetime.now()).total_seconds()
				raise ExtendedHTTPException(
					status_code=503,
					detail=f"Sorry, looks like we are being rate-limited by the PUBG API. Please try searching for this player again in {time_to_sleep} seconds.",
					plain=False
				)
			else:
				raise ExtendedHTTPException(
					status_code=503,
					detail=f"Sorry, looks like something has gone wrong with the PUBG API. This (should) resolve itself within a minute or two.",
					plain=False
				)

async def parse_player_object(
	player_id: str,
	platform_url: str, 
	matches: list
) -> list:

	player = await Player.filter(api_id__iexact=player_id).first()
	
	if not player:
		player = Player(
			api_id=player_id,
			platform_url=platform_url,
			api_url=build_player_account_id_url(platform_url, player_id),
			alternative_names=[]
		)
		await player.save()

	return_matches = []
	
	with FuturesSession() as session:
		session.headers.update(api_settings.API_HEADER)
		return_matches_append = return_matches.append
		_build_match_url = build_match_url
		for future in as_completed((session.get(_build_match_url(platform_url, match['id'])) for match in matches)):
			future_result = future.result()
			return_matches_append(json.loads(future_result.content))

	return return_matches, player

def get_player_match_id(
	player_id: str, 
	match_id: str
) -> str:
	return "{}".format(match_id)  

async def get_match_data(
	player_api_id: str
) -> List[Roster]:

	## get two weeks ago, to the ealiest datetime on the first day
	two_weeeks_ago = datetime.combine(datetime.now() - timedelta(days=15), datetime_time.min)

	roster_data = Roster.filter(
		participants__player__api_id=player_api_id,
		match__created__gte=two_weeeks_ago
	)\
	.exclude(
		match__map__name='Camp Jackal'
	)\
	.prefetch_related(
		'match',
		'match__map',
		'participants',
		'participants__player'
	)

	return roster_data

def player_placement_format(
	total_teams: int,
	placement: int
) -> str:

	if total_teams and placement:
		if placement == 1:
			return f'<span class="badge badge-success">{placement}/{total_teams}</span>'
		else:
			return f'<span class="badge badge-danger">{placement}/{total_teams}</span>'
	elif not total_teams and placement:
		if placement == 1:
			return f'<span class="badge badge-success">{placement}/100</span>'
		else:
			return f'<span class="badge badge-danger">{placement}/100</span>'

async def parse_player_matches(
	match_json_list: list, 
	player_id: str, 
	platform_url: str
) -> None:

	json_length = len(match_json_list)
	message = f'{json_length} matches to parse for {player_id}'

	match_count = 0

	total_time_taken = 0

	save = True

	maps = Map.all()
	players = Player.all()

	## 'local variable' optimisation
	_get_map_name = get_map_name
	_correct_mode = correct_mode
	_build_player_account_id_url = build_player_account_id_url

	_player_create = Player.create
	_players_filter = players.filter

	_participant_create = Participant.create
	_roster_create = Roster.create

	_match_create = Match.create
	_match_get = Match.get
	
	_map_create = Map.create
	_maps_filter = maps.filter

	_maps = {
		x.name: x.id
		for x in await maps
	}
	_players = {}

	for match in match_json_list:

		start_time = time.time()

		match_count += 1

		match_id = match['data']['id']

		# try:
		match['data']['attributes']['createdAt'] = match['data']['attributes']['createdAt'].replace('T', ' ').replace('Z', '')
		match_date = datetime.strptime(match['data']['attributes']['createdAt'], "%Y-%m-%d %H:%M:%S")
		match_map =  _get_map_name(match['data']['attributes']['mapName'])
		match_mode = _correct_mode(match['data']['attributes']['gameMode'])
		match_custom = match['data']['attributes']['isCustomMatch']
		match_type = match['data']['attributes']['matchType']

		match_url = match['data']['links']['self']
		match_url = match_url.replace('playbattlegrounds', 'pubg')

		match_participants =  [
			x for x in match['included']
			if x['type'] == 'participant'
		]

		## naive caching to reduce database queries
		map_id = _maps[match_map]

		try:
			this_match = await _match_get(
				api_id=match_id
			)
		except:
			this_match = await _match_create(
				api_id=match_id,
				created=match_date,
				map_id=map_id,
				mode=match_mode,
				api_url=match_url,
				is_custom_match=match_custom,
				match_type=match_type,
				total_teams=len(match_participants)
			)

		current_player_parsed = [
			x for x in match_participants
			if 'attributes' in x
			and 'stats' in x['attributes']
			and x['attributes']['stats']['playerId'] == player_id
		]
		this_participant_api_id = current_player_parsed[0]['id']

		team_roster = [
			x for x in match['included']
			if x['type'] == 'roster'
			and 'relationships' in x
			and 'participants' in x['relationships']
			and any(
				z['id'] == this_participant_api_id for z in x['relationships']['participants']['data']
			)
		]
		
		roster_id = team_roster[0]['id']
		roster_placement = team_roster[0]['attributes']['stats']['rank']

		roster = await _roster_create(
			placement=roster_placement,
			match_id=this_match.id,
			api_id=roster_id
		)

		roster_id = roster.id

		roster_participant_ids = [
			x['id'] for x in team_roster[0]['relationships']['participants']['data']
		]

		roster_participants_list = []
		roster_participants_list_append = roster_participants_list.append

		for participant in (x for x in match_participants if x['id'] in roster_participant_ids):

			participant_api_id = participant['id']
			participant_kills = participant['attributes']['stats'].get('kills', None)
			participant_damage = participant['attributes']['stats'].get('damageDealt', None)
			participant_placement = participant['attributes']['stats'].get('winPlace', None)
			participant_name = participant['attributes']['stats'].get('name', None)
			participant_player_api_id =  participant['attributes']['stats'].get('playerId', None)
			knocks = participant['attributes']['stats'].get('DBNOs', None)
			ride_distance = participant['attributes']['stats'].get('rideDistance', None)
			swim_distance = participant['attributes']['stats'].get('swimDistance', None)
			walk_distance = participant['attributes']['stats'].get('walkDistance', None)

			if 'ai' in participant_player_api_id:
				participant_is_ai = True
			else:
				participant_is_ai = False

			## naive caching to reduce database queries
			try:
				participant_player_object = _players[participant_player_api_id]
			except:
				player_queryset = _players_filter(api_id=participant_player_api_id)
				player_exists = await player_queryset.exists()

				if player_exists is False:
					participant_player_object = await _player_create(
						api_id=participant_player_api_id,
						platform_url=platform_url,
						api_url=_build_player_account_id_url(platform_url, player_id),
						alternative_names=[]
					)
				else:
					participant_player_object = await player_queryset.first()

				_players[participant_player_api_id] = participant_player_object

			if player_id == participant_player_api_id:
				if participant_name not in participant_player_object.alternative_names:
					participant_player_object.alternative_names.append(participant_name)
					await participant_player_object.save()

			participant_player_object_id = participant_player_object.id

			participant_object = await _participant_create(
				api_id=participant_api_id,
				kills=participant_kills,
				player_name=participant_name,
				placement=participant_placement,
				damage=participant_damage,
				player_id=participant_player_object_id,
				is_ai=participant_is_ai,
				knocks=knocks,
				ride_distance=ride_distance,
				swim_distance=swim_distance,
				walk_distance=walk_distance
			)

			roster_participants_list_append(participant_object)

		await roster.participants.add(*roster_participants_list)

		taken = time.time() - start_time
		seconds_taken = "{:0.4f}".format(taken)
		total_time_taken += taken
		message =  f"[{match_count}/{json_length}] ({match_id}) took {seconds_taken}(s)"

		if not LOG_SQL:
			logger.info(message)

		# except:
		# 	message = f'Threw the following error when trying to parse a match ({match_id}). {sys.exc_info()[1]}'
			
		# 	if not LOG_SQL:
		# 		logger.info(message)

	total_time_taken = "{:0.4f}".format(total_time_taken)
	message =  f"Took a total of {total_time_taken}(s)"
	
	if not LOG_SQL:
		logger.info(message)

async def get_player_matches(
	player_id: str,
	platform_url: str,
	matches: list
) -> None:
	player_matches, player = await parse_player_object(
		player_id=player_id,
		platform_url=platform_url,
		matches=matches
	)

	if len(player_matches) > 0:
		await parse_player_matches(
			match_json_list=player_matches,
			player_id=player_id,
			platform_url=platform_url
		)
		match_data = await get_match_data(
			player_api_id=player_id
		)
		await create_cached_match_data(
			current_player=player,
			match_data=match_data,
			api_id=player_id
		)
	
async def create_cached_match_data(
	current_player: Player,
	match_data: List[Roster],
	api_id: str
) -> Union[list, None]:

	match_data_cache_key = api_settings.PLAYER_MATCH_DATA_CACHE_KEY.format(api_id)
	match_data = await match_data
	player_aliases = await Participant.filter(
		player__api_id=api_id
	).distinct().prefetch_related(
		'player'
	).values_list(
		'player__alternative_names',
		flat=True
	)
	all_participants = Participant.all().prefetch_related('player')

	ajax_data = {
		'data':[],
		'player_aliases': [x for x in player_aliases[0]]
	}

	_ajax_data_append = ajax_data['data'].append
	_ajax_data_player_alises_append = ajax_data['player_aliases'].append
	_player_placement_format = player_placement_format
	_human = human
	
	for roster in match_data:

		roster_participants = await roster.participants.all().prefetch_related('player')

		_latest_names = {
			x.player.id: x.player.alternative_names[0] if x.player.alternative_names else x.player_name
			for x in roster_participants
		}

		roster_match = roster.match

		match_dict = {}
		match_dict['id'] = roster_match.id
		match_dict['raw_mode'] = roster_match.mode.upper()

		if roster_match.match_type and 'comp' in roster_match.match_type:
			mode = f'{match_dict["raw_mode"]}<br><span class="badge badge-success">Ranked</span>'
		else:
			mode = f'{match_dict["raw_mode"]}<br><span class="badge badge-secondary">Not Ranked</span>'
		
		match_dict['mode'] = mode

		if roster_match.map:
			match_map = roster_match.map.name
		else:
			match_map = None

		created = roster_match.created

		match_dict['map'] = match_map
		match_dict['date_created'] = {
			'display': datetime.strftime(created, '%d/%m/%Y %H:%M:%S'), ## this is what will display in the datatable.
			'timestamp': datetime.timestamp(created) ## this is what the datatable will sort by
		}
		match_dict['time_since'] = _human(roster_match.created)
		match_dict['team_details_object'] = []
		team_details_object_append = match_dict['team_details_object'].append

		temp_list = []
		for x in roster_participants:

			kills = x.kills
			damage = x.damage
			latest_name = _latest_names[x.player.id]

			temp_list.append(f"{latest_name}: {kills} kill(s) | {damage} damage<br>")

			participant_dict = {
				'kills': kills,
				'player_name': latest_name,
				'damage': damage,
				'api_id': x.player.api_id
			}
			team_details_object_append(participant_dict)

		match_detail_url = f"/pubg/match_detail/{roster_match.api_id}/{api_id}/"

		match_dict['team_details'] = ''.join(temp_list)
		match_dict['team_placement'] = _player_placement_format(roster_match.total_teams, roster.placement)
		match_dict['actions'] = f'<a href="{match_detail_url}" class="btn btn-link btn-sm active" role="button">View Match</a>',
		match_dict['btn_link'] = match_detail_url

		_ajax_data_append(match_dict)

	now = datetime.now()

	ajax_data['last_refreshed'] = now.timestamp()
	ajax_data['next_refreshes'] = (now + timedelta(minutes=35)).timestamp()

	await create_cache(
		cache_key=match_data_cache_key,
		content=ajax_data,
		minutes=30
	)

	return ajax_data

async def retrieve_player_season_stats(
	api_id: str,
	platform: str
) -> None:

	platform_url = build_url(platform)

	current_season = await Season.get(is_current=True, platform=platform.lower())
	current_player = await Player.filter(api_id=api_id, platform_url=platform_url).first()

	if current_season:
		for is_ranked in [True, False]:
			season_url = build_season_url(
				base_url=platform_url,
				season_id=current_season.api_id,
				player_id=api_id,
				is_ranked=is_ranked
			)
			season_request = make_request(season_url)

			player_id = current_player.id
			season_id = current_season.id

			if season_request:

				attributes = season_request.get('data').get('attributes')
				game_mode_stats = attributes.get('gameModeStats') or attributes.get('rankedGameModeStats')

				## we should really only save the details that we do not have
				game_modes = [
					game_mode for game_mode in game_mode_stats
				]

				for game_mode in game_modes:
					stats =  game_mode_stats.get(game_mode)

					assists = stats.get('assists', None)
					boosts = stats.get('boosts', None)
					dBNOs = stats.get('dBNOs', None)
					dailyKills = stats.get('dailyKills', None)
					dailyWins = stats.get('dailyWins', None)
					damageDealt = stats.get('damageDealt', None)
					days = stats.get('days', None)
					headshotKills = stats.get('headshotKills', None)
					heals = stats.get('heals', None)
					killPoints = stats.get('killPoints', None)
					kills = stats.get('kills', None)
					longestKill = stats.get('longestKill', None)
					longestTimeSurvived = stats.get('longestTimeSurvived', None)
					losses = stats.get('losses', None)
					maxKillStreaks = stats.get('maxKillStreaks', None)
					mostSurvivalTime = stats.get('mostSurvivalTime', None)
					rankPoints = stats.get('rankPoints', None)
					rankPointsTitle = stats.get('rankPointsTitle', None)
					revives = stats.get('revives', None)
					rideDistance = stats.get('rideDistance', None)
					roadKills = stats.get('roadKills', None)
					roundMostKills = stats.get('roundMostKills', None)
					roundsPlayed = stats.get('roundsPlayed', None)
					suicides = stats.get('suicides', None)
					swimDistance = stats.get('swimDistance', None)
					teamKills = stats.get('teamKills', None)
					timeSurvived = stats.get('timeSurvived', None)
					top10s = stats.get('top10s', None)
					vehicleDestroys = stats.get('vehicleDestroys', None)
					walkDistance = stats.get('walkDistance', None)
					weaponsAcquired = stats.get('weaponsAcquired', None)
					weeklyKills = stats.get('weeklyKills', None)
					weeklyWins = stats.get('weeklyWins', None)
					winPoints = stats.get('winPoints', None)
					wins = stats.get('wins', None)

					kwargs = {
						'mode':game_mode,
						'assists':assists,
						'boosts':boosts,
						'knocks':dBNOs,
						'daily_kills':dailyKills,
						'damage_dealt':damageDealt,
						'days':days,
						'daily_wins':dailyWins,
						'headshot_kills':headshotKills,
						'heals':heals,
						'kill_points':killPoints,
						'kills':kills,
						'longest_kill':longestKill,
						'longest_time_survived':longestTimeSurvived,
						'losses':losses,
						'max_kill_streaks':maxKillStreaks,
						'most_survival_time':mostSurvivalTime,
						'rank_points':rankPoints,
						'rank_points_title':rankPointsTitle,
						'revives':revives,
						'ride_distance':rideDistance,
						'road_kills':roadKills,
						'round_most_kills':roundMostKills,
						'rounds_played':roundsPlayed,
						'suicides':suicides,
						'swim_distance':swimDistance,
						'team_kills':teamKills,
						'time_survived':timeSurvived,
						'top_10s':top10s,
						'vehicle_destroys':vehicleDestroys,
						'walk_distance':walkDistance,
						'weapons_acquired':weaponsAcquired,
						'weekly_kills':weeklyKills,
						'weekly_wins':weeklyWins,
						'win_points':winPoints,
						'wins':wins,
						'player_id':player_id,
						'season_id':season_id,
						'is_ranked':is_ranked
					}

					player_season_stats = PlayerSeasonStats.filter(
						mode=game_mode,
						player_id=player_id,
						season_id=season_id,
						is_ranked=is_ranked
					)
					player_season_stats_exists = await player_season_stats.exists()
					
					if player_season_stats_exists:
						player_season_stats = await player_season_stats.update(
							**kwargs
						)
					else:
						player_season_stats = PlayerSeasonStats(
							**kwargs
						)
						await player_season_stats.save()


async def get_match_telemetry_from_match(
	match_json: list,
	match: Match,
	account_id: Optional[str] = None,
	return_early: bool = False
) -> Optional[dict]:

	assets = [
		x for x in match_json['included']
		if x['type'] == 'asset'
	]

	for asset in assets:
		asset_id = asset.get('id', None)
		asset_attributes = asset.get('attributes', None)
		if asset_attributes:
			url = asset_attributes.get('URL', None)
			date_created = asset_attributes.get('createdAt', None)
			date_created = datetime.strptime(date_created.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
			if url:
				telemetry_data = make_request(url)

				if return_early:
					return telemetry_data
				else:
					await parse_match_telemetry(
						url=url,
						asset_id=asset_id,
						telemetry_data=telemetry_data,
						match=match,
						date_created=date_created,
						account_id=account_id
					)

async def create_leaderboard_for_match(
	match_json: list,
	telemetry: Telemetry,
	save: bool = True,
	platform: Optional[str] = None
) -> Optional[list]:

	game_results_on_finished = [
		x for x in match_json
		if x['_T'] == 'LogMatchEnd'
	]

	telemetry_events = []

	game_results_on_finished_results = [
		x['gameResultOnFinished']['results'] for x in game_results_on_finished	
	][0]

	characters = [
		x['characters'] for x in game_results_on_finished	
	][0]

	victim_game_results = [
		x['victimGameResult'] for x in match_json
		if x['_T'] == 'LogPlayerKill'
	]

	log_player_take_damage_events = [
		x for x in match_json
		if x['_T'] == 'LogPlayerTakeDamage'
	]

	for x in game_results_on_finished_results:
		victim_game_results.append(x)
	
	teams = {}
	players = {}

	team_ids = []

	## build a list of rosters and their team members
	ais = 0
	non_ais = 0

	for character_entry in characters:

		character = character_entry.get('character')

		if character:

			team_id = character.get('teamId')
			team_ranking = character.get('ranking')
			player_name = character.get('name')
			player_acount_id = character.get('accountId')

			if 'ai' in player_acount_id:
				ais += 1
				is_ai = True
			else:
				non_ais += 1
				is_ai = False

			if team_id not in teams:

				team_ids.append(team_id)

				teams[team_id] = {
					'team_id': team_id,
					'roster_rank': team_ranking,
					'participant_objects':[
						{
							'player_name': player_name,
							'player_account_id': player_acount_id,
							'player_kills': 0,
							'damage_dealt': 0,
							'is_ai': is_ai
						}
					]
				}

			else:

				participant_details = {
					'player_name': player_name,
					'player_account_id': player_acount_id,
					'player_kills': 0,
					'damage_dealt': 0,
					'is_ai': is_ai
				}

				teams[team_id]['participant_objects'].append(participant_details)

	## this has kills for the team who are first place 
	for victim_game_result in victim_game_results:
		team_id = victim_game_result['teamId']
		kills = victim_game_result['stats']['killCount']
		account_id = victim_game_result['accountId']

		for participant in teams[team_id]['participant_objects']:

			if participant['player_account_id'] == account_id:
				participant['is_ai'] = 'ai' in account_id
				participant['player_kills'] = kills

	for log_player_take_damage_event in log_player_take_damage_events:
		attacker = log_player_take_damage_event['attacker']

		if attacker:
			team_id = attacker['teamId']
			account_id = attacker['accountId']
			damage_dealt = log_player_take_damage_event['damage']

			for participant in teams[team_id]['participant_objects']:
				if participant['player_account_id'] == account_id:
					participant['damage_dealt'] += damage_dealt

	rosters = []

	for team_id in team_ids:
		team = teams[team_id]
		participant_objects = ''

		for x in team['participant_objects']:
			if not x['is_ai']:
				participant_objects += f"<a class='fas fa-user' href='/pubg/user/{urllib.parse.quote(x['player_name'])}/?platform={urllib.parse.quote(platform)}'></a> {x['player_name']}: {x['player_kills']} kill(s) | {round(x['damage_dealt'], 2)} damage<br>"
			else:
				participant_objects += f"<i class=\"fas fa-robot\"></i> {x['player_name']}: {x['player_kills']} kill(s) | {round(x['damage_dealt'], 2)} damage<br>"

		team['participant_objects'] = participant_objects
		rosters.append(team)

	if save:

		telemet_roster = TelemetryRoster(
			json=rosters,
			telemetry=telemetry
		)

		await telemet_roster.save()
		
		telemetry_events.append(
			TelemetryEvent(
				event_type='AICount',
				telemetry=telemetry,
				description=ais
			)
		)

		telemetry_events.append(
			TelemetryEvent(
				event_type='PlayerCount',
				telemetry=telemetry,
				description=non_ais
			)
		)
		await TelemetryEvent.bulk_create(telemetry_events)

	else:
		return rosters

async def parse_match_telemetry(
	url: str,
	asset_id: str,
	telemetry_data: list,
	date_created: datetime,
	match: Match,
	account_id: str
) -> None:

	match_id = match.id

	telemetry_check = Telemetry.filter(
		match_id=match_id,
		player__api_id=account_id,
		api_id=asset_id
	)
	this_player = await Player.filter(api_id=account_id).first()
	current_participant = await Participant.filter(player=this_player).order_by('-id').first()
	player_name = current_participant.player_name
	kill_causes = ItemTypeLookup.all()

	telemetry_events = []

	save = True

	player_id = this_player.id

	append = telemetry_events.append

	if not await telemetry_check.exists():

		match_kills = 0
		dead = False
		won_match = False

		match_telemet = Telemetry(
			api_id=asset_id,
			api_url=url,
			created_at=date_created,
			match_id=match_id,
			player_id=this_player.id
		)

		if save:
	 		await match_telemet.save()
		
		await create_leaderboard_for_match(
			match_json=telemetry_data,
			telemetry=match_telemet,
			platform=get_platform(url)
		)

		telem_id = match_telemet.id

		heal_item_ids = [
			'Item_Boost_PainKiller_C',
			'Item_Heal_FirstAid_C',
			'Item_Boost_EnergyDrink_C',
			'Item_Heal_Bandage_C',
			'Item_Heal_MedKit_C'
		]

		telem_to_capture = [
			'LogItemUse',
			'LogPlayerKill',
			'LogMatchEnd',
			'LogMatchStart',
			'LogPlayerTakeDamage'
		]
		
		log_player_events = [
			x for x in telemetry_data
			if x['_T'] in telem_to_capture
			and (
					( 
						'attacker' in x
						and x['attacker']
						and 'accountId' in x['attacker']
						and x['attacker']['accountId'] == account_id
					)
				or
					( 
						'killer' in x
						and x['killer']
						and 'accountId' in x['killer']
						and x['killer']['accountId'] == account_id
					)
				or
					(
						'victim' in x
						and x['victim']
						and 'accountId' in x['victim']
						and x['victim']['accountId'] == account_id
					)
				or
					(
						'item' in x
						and x['item']['itemId'] in heal_item_ids
						and 'character' in x
						and x['character']['accountId'] == account_id
					)
				or not (
						( 
							'attacker' in x
						)
					or
						( 
							'killer' in x
						)
					or
						(
							'victim' in x
						)
					or
						(
							'item' in x
						)
				)
			)
		]

		del telemetry_data

		if 'ai' in account_id:
			player_name = f'<i class="fas fa-robot"></i> <b>{player_name}</b>'
		else:
			player_name = f'<i class="fas fa-user"></i> <b>{player_name}</b>'

		ais = 0
		last_victim_health = 0
		last_attacker_health = 0

		_player_demises = {}
		_player_downs = {}

		for log_event in log_player_events:
			
			event_type = log_event['_T']
			event_timestamp = log_event['_D']

			if event_timestamp:
				event_timestamp = parse(event_timestamp)
				event_timestamp.astimezone(UTC)

			if event_type == 'LogPlayerKill':

				victim_name = log_event['victim']['name']
				victim_id = log_event['victim']['accountId']

				if victim_id == account_id:
					dead = True

				if 'ai' in victim_id:
					victim_name = f'<i class="fas fa-robot"></i> <b>{victim_name}</b>'
				else:
					victim_name = f'<i class="fas fa-user"></i> <b>{victim_name}</b>'

				killer = log_event.get('killer')

				if killer:

					killer_name = log_event['killer']['name']
					killer_id = log_event['killer']['accountId']
					killer_x = log_event['killer']['location']['x']
					killer_y = log_event['killer']['location']['y']

					if 'victim' in log_event:
						victim_x = log_event['victim']['location']['x']
						victim_y = log_event['victim']['location']['y']
					else:
						victim_x = killer_x
						victim_y = killer_y
					
					if killer_id == account_id:
						match_kills += 1
						dead = False

					if 'ai' in killer_id:
						killer_name = f'<i class="fas fa-robot"></i> <b>{killer_name}</b>'
					else:
						killer_name = f'<i class="fas fa-user"></i> <b>{killer_name}</b>'

				else:

					victim_x = log_event['victim']['location']['x']
					victim_y = log_event['victim']['location']['y']

					killer = log_event.get('killer')

					if killer:
						killer_x = log_event['killer']['location']['x']
						killer_y = log_event['killer']['location']['y']
					else:
						killer_x = victim_x
						killer_y = victim_y

					damage_type = log_event.get('damageTypeCategory')

					if damage_type:
						killer_name = log_event['damageTypeCategory']

				kill_location = log_event['damageReason']
				
				if kill_location not in ['None', 'NonSpecific']:
					kill_location = kill_location.title()
				else:
					kill_location = None

				kill_cause = log_event['damageCauserName']
				kill_cause = await kill_causes.filter(reference=kill_cause).first()

				if kill_cause:
					kill_cause = kill_cause.name
				else:
					kill_cause = log_event['damageCauserName']

				_player_demises[victim_id] = True

				if kill_cause in ['Redzone', 'Bluezone']:
					event_description = f'{victim_name} died inside the <b>{kill_cause}</b>'
				else:
					if killer_name == 'Damage_Drown':
						event_description = f'{victim_name} died by drowning'
					else:
						event_description = f'{killer_name} killed {victim_name} with a <b>{kill_cause}</b>'

				append(TelemetryEvent(
					event_type=event_type,
					timestamp=event_timestamp,
					description=event_description,
					telemetry_id=telem_id,
					player_id=player_id,
					killer_x_cord=killer_x,
					killer_y_cord=killer_y,
					victim_x_cord=victim_x,
					victim_y_cord=victim_y
				))
				
				if match_kills:
					
					if dead:
						event_description = f'{player_name} died with <b>{match_kills} kill(s)</b>'
					else:
						event_description = f'{player_name} now has <b>{match_kills} kill(s)</b>'

					append(TelemetryEvent(
						event_type=event_type,
						timestamp=event_timestamp,
						description=event_description,
						telemetry_id=telem_id,
						player_id=player_id
					))

			if event_type == 'LogItemUse':

				item_id = log_event['item']['itemId']
				item_used = await kill_causes.filter(reference=item_id).first()
				item_used = item_used.name

				event_description = f'{player_name} used a <b>{item_used}</b>'

				if item_id in ['Item_Boost_PainKiller_C', 'Item_Boost_EnergyDrink_C']:
					event_type = 'LogItemUseBoost'
				else:
					event_type = 'LogItemUseMed'

				append(TelemetryEvent(
					event_type=event_type,
					timestamp=event_timestamp,
					description=event_description,
					telemetry_id=telem_id,
					player_id=player_id
				))

			if event_type == 'LogMatchEnd':

				game_results = log_event['gameResultOnFinished']

				if game_results:

					won_match = any(
						x['accountId'] == account_id
						for x in game_results['results']
					)

				if won_match:
					event_description = f'<b>Winner Winner Chicken Dinner!</b>'
				else:
					event_description = f'{player_name} did not win this match. Better luck next time!'
				
				append(TelemetryEvent(
					event_type=event_type,
					timestamp=event_timestamp,
					description=event_description,
					telemetry_id=telem_id,
					player_id=player_id
				))

			if event_type == 'LogMatchStart':

				event_description = 'Match started'

				append(TelemetryEvent(
					event_type=event_type,
					timestamp=event_timestamp,
					description=event_description,
					telemetry_id=telem_id,
					player_id=player_id
				))

			if event_type == 'LogPlayerTakeDamage':

				attacker = log_event.get('attacker')
				victim = log_event.get('victim')
				damage_causer = log_event.get('damageCauserName')
				damage_causer = await kill_causes.filter(reference=damage_causer).first()

				if attacker and victim:
					attacker_name = attacker.get('name', None)
					victim_name = victim.get('name', None)

					if attacker_name == victim_name:
						continue
				
					attacker_id = attacker.get('accountId', None)
					victim_id = victim.get('accountId')

					victim_is_ai = 'ai' in victim_id
					attacker_is_ai = 'ai' in attacker_id

					if attacker_is_ai:
						attacker_name = f'<i class="fas fa-robot"></i> <b>{attacker_name}</b>'
					else:
						attacker_name = f'<i class="fas fa-user"></i> <b>{attacker_name}</b>'

					if victim_is_ai:
						victim_name =  f'<i class="fas fa-robot"></i> <b>{victim_name}</b>'
					else:
						victim_name = f'<i class="fas fa-user"></i> <b>{victim_name}</b>'

					if victim_id in _player_demises and _player_demises[victim_id] == True:
						continue

					if victim_id in _player_downs and _player_downs.get(victim_id, {}).get('down', False) is True:
						if _player_downs.get(victim_id, {}).get('count', 0) > 2:
							continue

					victim_health = victim.get('health', None)
					attacker_health = attacker.get('health', None)

					if victim_health < 100:
						normalised_victim_damage = round(100 - (100-victim_health))

						if normalised_victim_damage == 0:
							if victim_id in _player_downs:
								_player_downs[victim_id]['count'] += 1
							else:
								_player_downs[victim_id] = {
									'down': True,
									'count': 1
								}
								
							normalised_victim_damage = victim_health

						if victim_id in _player_downs:
							_player_downs[victim_id]['count'] += 1

							if _player_downs[victim_id]['count'] > 2:
								event_description = f'{victim_name} continued taking damage from {attacker_name} with a {damage_causer} whilst in a downed state.'
							else:
								event_description = f'{victim_name} began taking damage from {attacker_name} with a {damage_causer} whilst in a downed state.'
						else:
							event_description = f'{victim_name} took {normalised_victim_damage} damage from {attacker_name} with a {damage_causer} and now has {100 - normalised_victim_damage} HP left.'
					else:
						event_description = f'{attacker_name} started atacking {victim_name} with a {damage_causer} who was at {victim_health} HP.'

					append(TelemetryEvent(
						event_type='DamageEvent',
						timestamp=event_timestamp,
						description=event_description,
						telemetry_id=telem_id,
						player_id=player_id
					))

		event_description = match_kills
		event_type = 'LogTotalMatchKills'

		append(TelemetryEvent(
			event_type=event_type,
			timestamp=event_timestamp,
			description=event_description,
			telemetry_id=telem_id,
			player_id=player_id
		))

		await TelemetryEvent.bulk_create(telemetry_events)