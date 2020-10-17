import asyncio
import callofduty
from callofduty import Mode, Platform, Title, GameType
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
import re
import urllib.parse
from operator import itemgetter

from datetime import datetime
from tortoise.query_utils import Q

import application.cod.settings as cod_settings
import application.route_models as route_models
from application.cod.functions import (
	get_platform,
	get_title,
	get_player_stats,
	get_call_of_duty_client,
	get_call_of_duty_search_results,
	get_mode,
	get_game_type,
	is_valid_leaderboard_combination,
	get_correct_leaderboard_combinations_for_title,
	get_game_type_as_str,
	get_title_as_str,
	is_unified_leaderboard
)
from application.cod.models import *
from application.cache_utils import *
from application.exceptions import *
import sys
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
	fmt='[%(asctime)s](%(levelname)s) %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

router = APIRouter()

player_name_regex = re.compile('#[0-9]+')

@router.post("/search/")
async def search(
	parameters: route_models.Player,
	background_tasks: BackgroundTasks
):
	
	player_name = parameters.player_name
	platform = get_platform(parameters.platform)
	title = get_title(parameters.title)

	player_search_cache_key = cod_settings.CALL_OF_DUTY_SEARCH_CACHE_KEY.format(player_name, title.value)
	ccached_player_search = await get_from_cache(
		cache_key=player_search_cache_key
	)
	
	if ccached_player_search:
		return ccached_player_search
	else:

		ajax_data = {}

		if platform is Platform.BattleNet:
			if '#' not in player_name:
				result = player_name_regex.search(player_name)
				if not(result):
					raise ExtendedHTTPException(
						status_code=404,
						detail='BattleNet requires you to enter the full username. e.g: {}#12345'.format(player_name),
						plain=True
					)

		try:
			client = await get_call_of_duty_client()
			player_results = await get_call_of_duty_search_results(
				client=client,
				platform=platform,
				player_name=player_name,
				limit=1
			)
		except Exception as e:
			logger.info(f'Call of duty API seems to be down. Searched: {player_name}, {platform}')
			raise ExtendedHTTPException(
				status_code=404,
				detail="Sorry, looks like the Call of Duty API is currently down.",
				plain=True
			)

		if len(player_results) > 0:

			current_player = player_results[0]

			player_account_id = current_player.accountId
			player_username = current_player.username
			player_platform = current_player.platform.name

			possible_cod_player = CODPlayer.filter(
				player_name__iexact=player_username
			)
			cod_player_exists = await possible_cod_player.exists()

			if cod_player_exists:
				cod_player = await possible_cod_player.first()
			else:
				cod_player = await CODPlayer.create(
					player_name=player_username,
					api_id=player_account_id
				)

			await get_player_stats(
				player_id=cod_player.id,
				current_player=current_player,
				platform=platform,
				username=player_name,
				title=title
			)
			
			player_results_cache_key = cod_settings.CALL_OF_DUTY_PROFILE_CACHE_KEY.format(player_name)
			await delete_from_cache(player_results_cache_key)

			ajax_data['redirect'] = f'/cod/user/{urllib.parse.quote(player_name)}/?platform={urllib.parse.quote(platform.value)}'

			await create_cache(
				cache_key=player_search_cache_key,
				content=ajax_data,
				minutes=30
			)

			return ajax_data

		else:
			raise ExtendedHTTPException(
				status_code=404,
				detail="Sorry, looks like this player does not exist.",
				plain=True
			)

@router.post("/player/")
async def player(
	parameters: route_models.Player
):

	player_name = parameters.player_name

	cod_player = await CODPlayer.filter(
		player_name__iexact=player_name
	).prefetch_related(
		'platforms',
		'titles',
		'titles__mode_types'
	).first()
	latest_cod_player = await cod_player
	latest_cod_player_platforms = await latest_cod_player.platforms
	latest_cod_player_titles = await latest_cod_player.titles

	player_results_cache_key = cod_settings.CALL_OF_DUTY_PROFILE_CACHE_KEY.format(player_name)

	cached_player_results = await get_from_cache(
		cache_key=player_results_cache_key
	)

	if cached_player_results:
		## only if no new content has since been added.
		## this means, all content must be the same - then we serve it.
		if (
			(
				'titles' in cached_player_results
			)
			and
			(
				len(cached_player_results['titles']) != 0
			)
			and
			(
				len(cached_player_results['titles']) == len(latest_cod_player_titles)
			)
			and
			(
				len(cached_player_results['platforms']) == len(latest_cod_player_platforms)
			)
		):
			return cached_player_results

	cod_player_stats = CODPlayerTitleStats.filter(
		player=latest_cod_player
	).prefetch_related('mode_type', 'item_type')

	item_types = CODItemType.all()
	lifetime_stats_item_type = await item_types.filter(
		reference__iexact='all'
	).first()
	all_item_types = await item_types.filter(
		Q(is_game_mode=True)|Q(is_kill_streak=True)
	)
	all_item_type_ids = {x.id for x in all_item_types}

	data_return = {}
	data_return['id'] = latest_cod_player.id
	data_return['platforms'] = [
		{
			'name': platform.name,
			'ref': platform.reference
		} for platform in latest_cod_player_platforms
	]
	data_return['titles'] = []
	data_return['mode_types'] = []
	data_return['all_modes'] = [x.reference for x in all_item_types]

	for title in latest_cod_player_titles:
		title_mode_types = await title.mode_types
		data_return['mode_types'].extend([x.reference for x in title_mode_types])
		mode_type_stats = await cod_player_stats.filter(
			item_type_id=lifetime_stats_item_type.id,
			title_id=title.id
		).first()

		## if any stats for this title..
		if mode_type_stats:

			model_fields = mode_type_stats.item_type.model_fields

			data_return_dict = {}
			data_return_dict['name'] = title.name
			data_return_dict['ref'] = title.reference
			data_return_dict['lifetime_stats'] = {}

			for key in model_fields.keys():
				model_field_key = model_fields[key]
				attr = getattr(mode_type_stats, model_field_key, None)
				if attr:
					data_return_dict['lifetime_stats'][model_field_key] = attr

			data_return_dict['gamemode_stats'] = []
			data_return_dict['killstreak_stats'] = []
			data_return_dict['mode'] = []
			
			mode_types = await title.mode_types
		
			for mode_type in mode_types:
				mode_type_dict = {}
				mode_type_dict['name'] = mode_type.name
				mode_type_dict['ref'] = mode_type.reference
				mode_type_dict['matches_in_mode'] = await CODPlayerMatch.filter(
					player_id=latest_cod_player.id,
					title_id=title.id,
					mode_type_id=mode_type.id,
					item_type_id__in=all_item_type_ids
				).exists()

				for item_type in all_item_types:
					item_type_stats = await cod_player_stats.filter(
						item_type_id=item_type.id,
						title_id=title.id
					).first()

					if item_type_stats:
						model_fields = item_type_stats.item_type.model_fields

						item_type_dict = {}
						item_type_dict['name'] = item_type_stats.item_type.name
						item_type_dict['ref'] = item_type_stats.item_type.reference

						if item_type.is_kill_streak:
							if item_type_dict not in data_return_dict['killstreak_stats']:
								data_return_dict['killstreak_stats'].append(item_type_dict)

						else:
							if item_type_dict not in data_return_dict['gamemode_stats']:
								data_return_dict['gamemode_stats'].append(item_type_dict)

				data_return_dict['mode'].append(mode_type_dict)

			data_return['titles'].append(data_return_dict)

	data_return['mode_types'] = list(set(data_return['mode_types']))

	await create_cache(
		cache_key=player_results_cache_key,
		content=data_return,
		minutes=30
	)

	return data_return

@router.post("/stats/")
async def stats(
	parameters: route_models.Player
):
	
	ajax_data = {}
	ajax_data['messages'] = None
	ajax_data['titles'] = {}

	player_name = parameters.player_name

	cod_player = await CODPlayer.filter(
		player_name__iexact=player_name
	).prefetch_related(
		'platforms',
		'titles',
		'titles__mode_types'
	).first()

	if cod_player:

		platform = parameters.platform

		if not platform or platform == 'None':
			platforms = await cod_player.platforms.all()
			cod_platform = platforms[0].reference
		else:
			cod_platform = await CODPlatform.filter(
				reference__iexact=platform
			).first()

		if cod_platform:

			game_modes = parameters.game_mode

			cod_item_types = await CODItemType.filter(
				reference__in=game_modes
			)

			if cod_item_types:

				titles = await cod_player.titles

				for title in titles:

					if title.reference not in ajax_data['titles']:
						ajax_data['titles'][title.reference] = {}
						ajax_data['titles'][title.reference]['stats'] = {}
						ajax_data['titles'][title.reference]['matches'] = {}

					for cod_item_type in cod_item_types:

						cod_player_stats_for_item_type = await CODPlayerTitleStats.filter(
							player_id=cod_player.id,
							title_id=title.id,
							item_type_id=cod_item_type.id
						).prefetch_related('item_type').first()

						if cod_player_stats_for_item_type:
							model_fields = cod_player_stats_for_item_type.item_type.model_fields

							ajax_data['titles'][title.reference]['stats'][cod_item_type.reference] = {
								'stats': []
							}

							for key in model_fields.keys():
								model_field_key = model_fields[key]
								attr = getattr(cod_player_stats_for_item_type, model_field_key, None)
								if attr:
									ajax_data['titles'][title.reference]['stats'][cod_item_type.reference]['stats'].append(
										{
											'ref': cod_item_type.reference,
											'value': attr,
											'text': cod_settings.CALL_OF_DUTY_MODULE_LABELS.get(model_field_key, None)
										}
									)

					title_mode_types = await title.mode_types

					cod_matches = CODPlayerMatch.filter(
						player_id=cod_player.id,
						title_id=title.id
					).prefetch_related('item_type')

					match_ignore = [

					]

					for mode_type in title_mode_types:

						matches_of_mode_type = await cod_matches.filter(
							mode_type_id=mode_type.id
						).order_by('-utc_start_seconds')

						if mode_type.reference not in ajax_data['titles'][title.reference]['matches']:
							ajax_data['titles'][title.reference]['matches'][mode_type.reference] = []

						for match in matches_of_mode_type:
							model_fields = match.item_type.model_fields

							match_dict = {
								'stats': [],
								'mode': match.item_type.name,
								'match_start': datetime.strftime(datetime.fromtimestamp(match.utc_start_seconds), '%d/%m/%Y %H:%M:%S') if match.utc_start_seconds else None,
								'match_end': datetime.strftime(datetime.fromtimestamp(match.utc_end_seconds), '%d/%m/%Y %H:%M:%S') if match.utc_end_seconds else None
							}
							match_teams = CODPlayerMatchTeam.filter(
								codplayermatch_id=match.id
							).prefetch_related(
								'codplayermatch',
								'codplayerteamplayer',
								'codplayerteamplayer__platforms'
							)
							match_teams_exists = await match_teams.exists()

							if match_teams_exists:

								if 'teams' not in match_dict:
									match_dict['teams'] = []

								match_teams = await match_teams

								for team in match_teams:
									team_members = await team.codplayerteamplayer.all()
									
									team_dict = {}
									team_dict['team_no'] = team.team_no
									team_dict['members'] = [
										{
											'player_name': team_member.player_name,
											'platform': await team_member.platforms.all().first()
										} for team_member in team_members
									]
									team_dict['order_number'] = 0 if any(x['player_name'].lower() == player_name for x in team_dict['members']) else 1
									match_dict['teams'].append(team_dict)

								match_dict['teams'] = sorted(match_dict['teams'], key=itemgetter('order_number')) 

							for key in model_fields.keys():
								model_field_key = model_fields[key]
								model_field_label = cod_settings.CALL_OF_DUTY_MODULE_LABELS.get(model_field_key, None)
								attr = getattr(match, model_field_key, None)
								if attr and model_field_key not in match_ignore and model_field_label:
									match_dict['stats'].append(
										{
											'value': attr,
											'text': model_field_label
										}
									)
									
							ajax_data['titles'][title.reference]['matches'][mode_type.reference].append(match_dict)

			else:
				ajax_data['messages'] = 'Game Mode with name (or reference) "{}" does not exist.'.format(game_mode)

		else:
			ajax_data['messages'] = 'Platform with name (or reference) "{}" does not exist.'.format(platform)

	else:
		ajax_data['messages'] = 'Player with name "{}" does not exist.'.format(player_name)

	return ajax_data

@router.post("/leaderboards/")
async def leaderboards(
	parameters: route_models.Leaderboard
):

	platform = get_platform(parameters.platform)
	title = get_title(parameters.title)
	game_type = get_game_type(parameters.game_type)

	if is_valid_leaderboard_combination(
		title=title,
		game_type=game_type,
		platform=platform
	):

		if is_unified_leaderboard(
			title=title
		):
			leaderboard_cache_key = cod_settings.CALL_OF_DUTY_TITLE_UNIFIED_LEADERBOARD_CACHE_KEY.format(
				title.value,
				game_type.value
			)
		else:
			leaderboard_cache_key = cod_settings.CALL_OF_DUTY_TITLE_LEADERBOARD_CACHE_KEY.format(
				title.value,
				platform.value,
				game_type.value
			)

		leaderboard_args = {}
		leaderboard_args['title'] = title
		leaderboard_args['platform'] = platform
			
		cached_data = await get_from_cache(
			cache_key=leaderboard_cache_key
		)
		if cached_data and 'data' in cached_data and len(cached_data['data']) > 0:
			return cached_data

		ajax_data = {}

		try:
			client = await get_call_of_duty_client()
		except:
			ajax_data['data'] = []
			return ajax_data

		base_entries = 20
		max_entries = 500
		needed_entries = range(1, (max_entries + base_entries) // base_entries)

		leaderboard_data = {}
		leaderboard_data['data'] = []
		
		## try it upwards of 2 times
		for y in range(0, 3):
			for x in needed_entries:
				leaderboard_args['page'] = x
				leaderboard_args['gameType'] = game_type

				try:
					leaderboard = await client.GetLeaderboard(
						**leaderboard_args
					)
					leaderboard_entries = leaderboard.entries
				except Exception as e:
					e_as_str = str(e)

					if 'no leaderboard' in e_as_str.lower():
						message = f'Sorry, no {get_game_type_as_str(game_type.value)} leaderboards for {get_title_as_str(title.value)}'
					elif 'service unavailable' in e_as_str.lower():
						break
					else:
						message = f'Sorry, the following error happened when trying to request the leaderboard (Exception: "{e_as_str}")". Please try again later...'

					ajax_data = {'message': message}
					await create_cache(
						cache_key=leaderboard_cache_key,
						content=ajax_data,
						minutes=30
					)
					return ajax_data

				entries = []

				for leaderboard_entry in leaderboard_entries:
					entry = leaderboard_entry.values

					data_entry = {}
					data_entry['rank'] = leaderboard_entry.rank
					data_entry['wins'] = entry.get('wins', 'N/A')
					data_entry['kills'] = entry.get('kills', 'N/A')
					data_entry['kdRatio'] = entry.get('kdRatio', 'N/A')
					data_entry['level'] = entry.get('level', 'N/A')
					data_entry['losses'] = entry.get('losses', 'N/A')
					data_entry['gamesPlayed'] = entry.get('gamesPlayed', 'N/A')
					data_entry['scorePerMinute'] = entry.get('scorePerMinute', 'N/A')
					data_entry['assists'] = entry.get('assists', 'N/A')
					data_entry['headshots'] = entry.get('headshots', 'N/A')
					data_entry['shots'] = entry.get('shots', 'N/A')
					data_entry['username'] = leaderboard_entry.username

					entries.append(data_entry)
				
				leaderboard_data['data'].extend(entries)

			await create_cache(
				cache_key=leaderboard_cache_key,
				content=leaderboard_data,
				minutes=30
			)

			return leaderboard_data

	else:

		correct_combinations = get_correct_leaderboard_combinations_for_title(
			title=title,
			platform=platform
		)

		if len(correct_combinations) > 0:
			return {
				'message': 'Invalid combination for leaderboard',
				'allowed_combos_for_title': correct_combinations
			}
		else:
			return {
				"message": 'This title is not supported for this platform',
			}