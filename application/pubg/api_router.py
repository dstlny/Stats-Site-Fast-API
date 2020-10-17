from datetime import datetime, timedelta
from tortoise import Tortoise
from tortoise.query_utils import Q
from fastapi import HTTPException, APIRouter
from dateutil.parser import parse
from ago import human
import urllib.parse

import application.pubg.settings as api_settings
import application.route_models as route_models
from application.pubg.functions import (
	build_url, build_lifetime_url, make_request, correct_perspective, correct_mode,
	build_player_url, get_player_matches, retrieve_player_season_stats, build_player_account_id_url,
	make_request, build_match_url, get_match_telemetry_from_match, get_match_data, create_leaderboard_for_match, get_player_match_id,
	parse_player_matches,  player_placement_format, get_platform, build_leaderboard_url, create_cached_match_data
)

from application.cache_utils import *
from application.pubg.models import *
from application.exceptions import *

router = APIRouter()

@router.post("/search/")
async def search(
	parameters: route_models.Player
):

	platform = parameters.platform
	player_name = parameters.player_name

	player_response_cache_key = api_settings.PLAYER_RESPONSE_CACHE_KEY.format(player_name, platform)

	cached_player_response = await get_from_cache(player_response_cache_key)

	if cached_player_response:
		return cached_player_response

	player_request_cache_key = api_settings.PLAYER_REQUEST_CACHE_KEY.format(player_name, platform)

	platform_url = build_url(platform)
	player_url = build_player_url(base_url=platform_url, player_name=player_name)

	cached_player_request = await get_from_cache(player_request_cache_key)

	if not cached_player_request or 'data' not in cached_player_request:
		player_request = make_request(player_url)
		await create_cache(
			cache_key=player_request_cache_key,
			content=player_request,
			minutes=30
		)
	else:
		player_request = cached_player_request

	ajax_data = {}

	if 'data' in player_request:

		ajax_data['redirect'] = f'/pubg/user/{urllib.parse.quote(player_name)}/?platform={platform}'

		if isinstance(player_request['data'], list):
			player_id = player_request['data'][0]['id']
			
			api_ids = await Roster.filter(
				participants__player__api_id=player_id
			).only(
				'match__api_id'
			).prefetch_related(
				'match',
				'participants'
			).distinct().values_list(
				'match__api_id',
				flat=True
			)

			length_of_matches_in_request = len(player_request['data'][0]['relationships']['matches']['data'])
			matches = [match for match in player_request['data'][0]['relationships']['matches']['data'] if match['id'] not in api_ids]
		else:
			player_id = player_request['data']['id']

			api_ids = await Roster.filter(
				participants__player__api_id=player_id
			).only(
				'match__api_id'
			).prefetch_related(
				'match'
			).distinct().values_list(
				'match__api_id',
				flat=True
			)
			
			length_of_matches_in_request = len(player_request['data']['relationships']['matches']['data'])
			matches = [match for match in player_request['data']['relationships']['matches']['data'] if match['id'] not in api_ids]

		if length_of_matches_in_request > 0:

			if len(matches) > 0:

				await get_player_matches(
					player_id=player_id, 
					platform_url=platform_url, 
					matches=matches
				)
				
			await create_cache(
				cache_key=player_response_cache_key,
				content=ajax_data,
				minutes=30
			)

			return ajax_data

		else:

			raise ExtendedHTTPException(
				status_code=400,
				detail=f"Player hasn't played any matches in the last 14 days.",
				plain=True
			)

	else:
		raise ExtendedHTTPException(
			status_code=404,
			detail=f"Player with name '{player_name}' does not exist.",
			plain=True
		)

@router.post("/retrieve_matches/")
async def retrieve_matches(
	parameters: route_models.Player
):
	
	api_id = parameters.api_id
	current_player = await Player.filter(api_id=api_id).first()

	if not current_player:
		player_name = parameters.player_name
		all_players = await Player.all()
		for player in all_players:
			if player_name in player.alternative_names:
				current_player = player
				break

	if current_player:

		match_data_cache_key = api_settings.PLAYER_MATCH_DATA_CACHE_KEY.format(api_id)
		cached_ajax_data = await get_from_cache(match_data_cache_key)
		cached_player_request = None
		processing_in_background = False

		## if no cached data, we can assume that the player visited this page just via typing it in the URL and not searching the player.
		if cached_ajax_data:
			return cached_ajax_data
		else:
			match_data = await get_match_data(
				player_api_id=api_id
			)
			match_data_exists = await match_data.exists()

			## try build a url and get some data
			platform = get_platform(current_player.platform_url)
			platform_url = build_url(platform)
			player_name = parameters.player_name

			player_response_cache_key = api_settings.PLAYER_RESPONSE_CACHE_KEY.format(player_name, platform)
			cached_player_response = await get_from_cache(player_response_cache_key, ignore_expires=True)

			has_cached_search_response = False
			is_currently_processing = False

			if cached_player_response:
				has_cached_search_response = True
				is_currently_processing = cached_player_response.get('currently_processing', False)

			## only get past this, if the user isn't being processed already 
			if not has_cached_search_response and not is_currently_processing:
				await search(
					parameters=route_models.Player(
						player_name=player_name,
						platform=platform
					)
				)
				processing_in_background = True

			if match_data_exists:

				ajax_data = await create_cached_match_data(
					current_player=current_player,
					match_data=match_data,
					api_id=api_id
				)

				return ajax_data
			else:

				if not processing_in_background:
					message = "It would seem no TPP/FPP (SOLO, DUO, SQUAD) matches exist for this user for the last 14 days."
				else:
					message = "We are currently processing this players matches..."

				ajax_data = {
					'error': message,
					'api_id': api_id
				}

				return ajax_data

	else:

		raise HTTPException(status_code=404, detail="No player with id {} found".format(api_id))
 
@router.post("/retrieve_season_stats/")
async def retrieve_season_stats(
	parameters: route_models.Player
):

	api_id = parameters.api_id
	platform = parameters.platform

	season_stats_cache_key = api_settings.PLAYER_SEASON_STATS_CACHE_KEY.format(api_id)

	cached_ajax_data  = await get_from_cache(season_stats_cache_key)

	if cached_ajax_data:
		return cached_ajax_data

	current_player = await Player.filter(
		api_id=api_id
	).first()

	if not platform or platform == 'None':
		platform = get_platform(current_player.platform_url)

	await retrieve_player_season_stats(api_id,  platform)

	ajax_data = []

	season_stats_queryset = await PlayerSeasonStats.filter(
		player_id=current_player.id,
		season__is_current=True,
		season__platform=platform
	).prefetch_related(
		'season',
		'player'
	)

	ranked_count = 0

	for x in season_stats_queryset:

		x_mode = x.mode
		x_mode_lower = x_mode.lower().replace('-', '_')

		if x.is_ranked:

			season_stat_dict = {
				f"ranked_{x_mode_lower}_season_stats": correct_mode(x_mode_lower.replace('_', ' ')).upper(),
				f"ranked_{x_mode_lower}_season_matches": "{} {}".format(x.rounds_played, 'Matches Played'),
				f"ranked_{x_mode_lower}_season_kills__text": 'Overall Kills',
				f"ranked_{x_mode_lower}_season_kills__figure": x.kills,
				f"ranked_{x_mode_lower}_season_damage__text": 'Overal Damage Dealt',
				f"ranked_{x_mode_lower}_season_damage__figure": str(x.damage_dealt),
				f"ranked_{x_mode_lower}_season_longest_kill__text": 'Longest Kill',
				f"ranked_{x_mode_lower}_season_longest_kill__figure": str(x.longest_kill),
				f"ranked_{x_mode_lower}_season_headshots__text": 'Overall Headshot kills',
				f"ranked_{x_mode_lower}_season_headshots__figure": x.headshot_kills
			}

			ranked_count += 1

		else:
			season_stat_dict = {
				f"{x_mode_lower}_season_stats": correct_mode(x.mode.replace('_', ' ')).upper(),
				f"{x_mode_lower}_season_matches": "{} {}".format(x.rounds_played, 'Matches Played'),
				f"{x_mode_lower}_season_kills__text": 'Overall Kills',
				f"{x_mode_lower}_season_kills__figure": x.kills,
				f"{x_mode_lower}_season_damage__text": 'Overal Damage Dealt',
				f"{x_mode_lower}_season_damage__figure": str(x.damage_dealt),
				f"{x_mode_lower}_season_longest_kill__text": 'Longest Kill',
				f"{x_mode_lower}_season_longest_kill__figure": str(x.longest_kill),
				f"{x_mode_lower}_season_headshots__text": 'Overall Headshot kills',
				f"{x_mode_lower}_season_headshots__figure": x.headshot_kills
			}

		ajax_data.append(season_stat_dict)


	if ranked_count < 2:
		modes_not_added = set()
		all_game_modes = await PlayerSeasonStats.filter(mode__icontains='squad').values_list('mode', flat=True)
		for is_ranked in [True, False]:
			for x in all_game_modes:
				if is_ranked:
					dict_key = f"ranked_{x.lower().replace('-', '_')}_season_stats"
				else:
					dict_key = f"{x.lower().replace('-', '_')}_season_stats"

				if not any(dict_key in x for x in ajax_data):
					modes_not_added.add(x)

			if dict_key:
				ajax_data += [
					{
						'container' :f"ranked_{x.lower().replace('-', '_')}_season_stats_container",
						'text': f"No ranked data available for {correct_mode(x.replace('_', ' ')).upper()}"
					} for x in modes_not_added
				]
			else:
				ajax_data += [
					{
						'container' :f"{x.lower().replace('-', '_')}_season_stats_container",
						'text':  f"No data available for {correct_mode(x.replace('_', ' ')).upper()}"
					} for x in modes_not_added
				]
				
	await create_cache(
		cache_key=season_stats_cache_key,
		content=ajax_data,
		minutes=120
	)

	return ajax_data

@router.post("/match_rosters/")
async def match_rosters(
	parameters: route_models.Match
):

	match_id = parameters.match_id
	match = await Match.get(id=match_id)
	api_id = match.api_id
	
	match_roster_cache = api_settings.MATCH_ROSTER_CACHE_KEY.format(api_id)
	cached_ajax_data  = await get_from_cache(match_roster_cache)

	if cached_ajax_data:
		return cached_ajax_data

	account_id = api_id.split('_')[0]
	match_url = match.api_url

	if not match_url or api_id not in match_url:
		current_player = await Player.filter(
			api_id__iexact=account_id
		).first()
		match_id = api_id.split('_')[1]
		platform_url = current_player.platform_url
		match_url = build_match_url(platform_url, match_id)

	match_json = make_request(match_url)

	telemetry = await get_match_telemetry_from_match(
		match_json=match_json,
		match=match,
		return_early=True
	)

	rosters = await create_leaderboard_for_match(
		match_json=telemetry,
		telemetry=None,
		save=False,
		platform=get_platform(match_url)
	)

	await create_cache(
		cache_key=match_roster_cache,
		content=rosters,
		minutes=60
	)

	return rosters

@router.post("/match_detail/{match_api_id}/{account_api_id}")
async def match_detail(
	match_api_id,
	account_api_id
):

	match_detail_cache_key = api_settings.MATCH_DETAIL_CACHE_KEY.format(match_api_id, account_api_id)
	cached_ajax_data = await get_from_cache(match_detail_cache_key)

	if cached_ajax_data:
		return cached_ajax_data

	match = await Match.get(
		api_id=match_api_id
	).prefetch_related('map')
	telemetry_objects = Telemetry.filter(
		match_id=match.id,
		player__api_id=account_api_id
	)
	telemetry_objects_exists = await telemetry_objects.exists()

	current_player = await Player.filter(
		api_id=account_api_id
	).order_by(
		'id'
	).first()
	participant = await Participant.filter(
		player_id=current_player.id
	).order_by(
		'-id'
	).first()
	player_name = participant.player_name

	if not telemetry_objects_exists:
		
		cached_match_json = await get_from_cache(
			cache_key=api_settings.MATCH_API_CALL_CACHE_KEY.format(match_api_id)
		)

		## avoid calling this more and once
		if cached_match_json:
			match_json = cached_match_json
		else:
			match_url = match.api_url

			if not match_url or match_api_id not in match_url:
				platform_url = current_player.platform_url
				match_url = build_match_url(platform_url, match_api_id)

			match_json = make_request(match_url)

		await get_match_telemetry_from_match(
			match_json=match_json,
			match=match,
			return_early=False,
			account_id=account_api_id
		)

		telemetry = await Telemetry.filter(
			match_id=match.id,
			player__api_id=account_api_id
		).first()

	else:
		telemetry = await telemetry_objects.first()

	telemetry_events = TelemetryEvent.filter(
		telemetry_id=telemetry.id
	)

	try:

		log_match_start = await telemetry_events.get(
			event_type__iexact='LogMatchStart'
		)
		total_match_kills = await telemetry_events.get(
			event_type__iexact='LogTotalMatchKills'
		)
		log_match_end = await telemetry_events.get(
			event_type__iexact='LogMatchEnd'
		)
		roster_telem = await TelemetryRoster.get(
			telemetry_id=telemetry.id
		)
		roster_participant = await Participant.filter(
			player__api_id=account_api_id
		).prefetch_related(
			'player'
		).first()
		damage_events = await telemetry_events.filter(
			event_type__iexact='DamageEvent'
		)

		log_match_start_timestamp = parse(log_match_start.timestamp)
		log_match_start_timestamp = str(log_match_start_timestamp)

		if '+' in log_match_start_timestamp:
			log_match_start_timestamp = str(log_match_start_timestamp).split('+')[0]

		log_match_start_timestamp = str(log_match_start_timestamp).split('.')[0]
		log_match_end_timestamp = parse(log_match_end.timestamp)

		log_match_end_timestamp = str(log_match_end_timestamp)

		if '+' in log_match_end_timestamp:
			log_match_end_timestamp = str(log_match_end_timestamp).split('+')[0]

		log_match_end_timestamp = str(log_match_end_timestamp).split('.')[0]

		FMT = '%Y-%m-%d %H:%M:%S'
		
		elapased_time = datetime.strptime(log_match_end_timestamp, FMT) - datetime.strptime(log_match_start_timestamp, FMT)

		heals_items_used = await telemetry_events.filter(
			event_type__iexact='LogItemUseMed'
		).count()
		boost_items_used = await telemetry_events.filter(
			event_type__iexact='LogItemUseBoost'
		).count()

		ai_events = telemetry_events.filter(
			event_type__iexact='AICount'
		)
		ai_events_exists = await ai_events.exists()
		player_events = telemetry_events.filter(
			event_type__iexact='PlayerCount'
		)
		player_events_exists = await player_events.exists()

		ais = False
		ai_count = 0
		player_count = 0
		ai_percentage = 0.00
		
		if ai_events_exists:
			ai_count = await ai_events.first()
			ai_count = int(ai_count.description)
			ais = True

		if player_events_exists:
			player_count = await player_events.first()
			player_count = int(player_count.description)

		total_count = ai_count + player_count
		ai_percentage = round((ai_count / total_count) * 100)
		player_percentage =  round((player_count / total_count) * 100)

		exlude_types = [
			'LogTotalMatchKills',
			'Roster',
			'DamageEvent'
		]

		telemetry_excluding_some_events = await telemetry_events.exclude(
			Q(event_type__in=exlude_types) | Q(timestamp__isnull=True)
		)

		match_map_url = match.map.image_url
		map_name = match.map.name
		
		telemetry_data = {
			'telemetry_data':{
				'platform': get_platform(current_player.platform_url),
				'match_data':{
					'match_id': match_api_id,
					'match_elapsed_time': f'{elapased_time} minutes',
					'match_map_name': map_name,
					'map_image': match_map_url,
					'time_since': human(match.created),
					'damage_events':[
						{
							'timestamp': datetime.strftime(parse(x.timestamp), '%H:%M:%S'),
							'event': x.description,
							'event_type': x.event_type,
						} for x in damage_events
					],
					'events': [
						{
							'timestamp': datetime.strftime(parse(x.timestamp), '%H:%M:%S'),
							'event': x.description,
							'event_type': x.event_type,
							'killer_x_cord': x.killer_x_cord,
							'killer_y_cord': x.killer_y_cord,
							'victim_x_cord': x.victim_x_cord,
							'victim_y_cord': x.victim_y_cord
						} for x in telemetry_excluding_some_events
					],
					'player_breakdown':{
						'ais': ais,
						'ai_count': ai_count,
						'ai_percentage': ai_percentage,
						'player_count': player_count,
						'player_percentage': player_percentage,
						'total_count': total_count,
						'rosters': roster_telem.json,
					}
				},
				'player_data':{
					'player_kills': total_match_kills.description,
					'player_damage': roster_participant.damage,
					'knocks': roster_participant.knocks,
					'player_name': player_name,
					'boost_items_used': boost_items_used,
					'heals_items_used': heals_items_used
				}
			}
		}

		await create_cache(
			cache_key=match_detail_cache_key,
			content=telemetry_data,
			minutes=40
		)

		return telemetry_data
	except:
		await telemetry_events.delete()
		await telemetry.delete()
		await match_detail(
			match_api_id=match_api_id,
			account_api_id=account_api_id
		)

@router.post("/leaderboards/")
async def leaderboards(
	parameters: route_models.Leaderboard
):

	platform = parameters.platform
	season_id = parameters.season_id
	game_mode = parameters.game_mode

	leaderboard_cache_key = api_settings.LEADERBOARDS_CACHE_KEY.format(platform, season_id, game_mode)

	cached_ajax_data = await get_from_cache(leaderboard_cache_key)

	if cached_ajax_data:
		return cached_ajax_data

	platform_url = build_url(platform)
	leaderboard_url = build_leaderboard_url(
		base_url=platform_url,
		season_id=season_id,
		game_mode=game_mode
	)
	leaderboard_json = make_request(leaderboard_url)
	
	await create_cache(
		cache_key=leaderboard_cache_key,
		content=leaderboard_json,
		minutes=60
	)

	return leaderboard_json

_seasons_for_platform_cache = {}

@router.post("/seasons_for_platform/")
async def seasons_for_platform(
	parameters: route_models.Player
):

	platform = parameters.platform

	if platform not in _seasons_for_platform_cache:
		seasons = await Season.filter(platform=platform)

		response = [
			{
				'value': season.api_id,
				'text': season.api_id,
				'attr': {
					'name': 'data-requires-shard',
					'value': season.requires_region_shard,
				}
			} for season in seasons
		]

		_seasons_for_platform_cache[platform] = response

		return _seasons_for_platform_cache[platform]
	else:
		return _seasons_for_platform_cache[platform]

@router.post("/player/")
async def get_player(
	parameters: route_models.Player
):

	player_name = parameters.player_name

	participant = await Participant.filter(
		Q(player__alternative_names__icontains=player_name)|Q(player_name=player_name)
	).prefetch_related('player').order_by('-id').first()

	if participant is None:
		all_players = await Player.all()
		for player in all_players:
			if player_name in player.alternative_names:
				participant = await Participant.filter(player__id=player.id).prefetch_related('player').order_by('-id').first()
				break
	
	if participant:
		latest_participant = await participant
		return { 
			'platform': get_platform(latest_participant.player.platform_url),
			'api_id': latest_participant.player.api_id,
			'in_database': True
		}
	else:
		return  {
			'in_database': False
		}