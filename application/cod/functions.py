import callofduty
from callofduty import Mode, Platform, Title, GameType
from callofduty.client import Client
from callofduty.player import Player
import json
import re
	
from application.cod.models import *
import application.cod.settings as cod_settings
from application.cache_utils import *
from tortoise.queryset import QuerySet


async def get_call_of_duty_client() -> Client:
	return await callofduty.Login(cod_settings.CALL_OF_DUTY_API_EMAIL, cod_settings.CALL_OF_DUTY_API_PASSWORD)

async def get_call_of_duty_search_results(
	client: Client,
	platform: Platform,
	player_name: str,
 	limit: int = 1
) -> List[Player]:
	return await client.SearchPlayers(platform, player_name, limit=limit)

def get_platform(
	platform: str
) -> Platform:

	platform = platform.lower()
	
	if 'steam' in platform:
		return Platform.Steam
	elif 'uno' in platform:
		return Platform.Activision
	elif ('xbl' in platform) or ('xbox' in platform):
		return Platform.Xbox
	elif 'psn' in platform:
		return Platform.PlayStation
	else:
		return Platform.BattleNet

def get_title(
	title: str = None
) -> Union[List[Title], Title]:

	if title:
	
		title = title.lower()

		if 'mw' in title:
			return Title.ModernWarfare
		elif 'bo4' in title:
			return Title.BlackOps4
		elif 'wwii' in title:
			return Title.WWII
		elif 'iw' in title:
			return Title.InfiniteWarfare 
		else:
			return Title.BlackOps3

	return [
		Title.ModernWarfare,
		Title.BlackOps4,
		Title.WWII,
		Title.InfiniteWarfare,
		Title.BlackOps3
	]


def get_title_as_str(
	title: str
) -> str:

	title = title.lower()

	if 'mw' in title:
		return 'Modern Warfare'
	elif 'bo4' in title:
		return 'Black Ops 4'
	elif 'wwii' in title:
		return 'World War II'
	elif 'iw' in title:
		return 'Infinite Warfare'
	else:
		return 'Black Ops 3'

def get_game_type_as_str(
	game_type: str
) -> str:

	game_type = game_type.lower()

	if 'core' in game_type:
		return 'Core'
	elif 'hc' in game_type:
		return 'Hardcore'
	elif 'arena' in game_type:
		return 'Arena'

def get_mode(
	mode: str = None,
	title: Title = None,
) -> Mode:

	if not mode:
		return Mode.Multiplayer

	mode = mode.lower()

	if 'mp' in mode:
		return Mode.Multiplayer
	elif 'zm' in mode:
		return Mode.Zombies
	elif 'wz' in mode:
		if title is Title.ModernWarfare:
			return Mode.Warzone
		elif title is Title.BlackOps4:
			return Mode.Blackout
		else:
			return Mode.Multiplayer

def get_game_type(
	game_type: str = None,
) -> GameType:

	if not game_type:
		return GameType.Core

	game_type = game_type.lower()

	if 'core' in game_type:
		return GameType.Core
	elif 'hc' in game_type:
		return GameType.Hardcore
	elif 'arena' in game_type:
		return GameType.WorldLeague

def is_unified_leaderboard(
	title: Title
) -> bool:

	is_unified_leaderboard = True

	if title is not Title.ModernWarfare:
		is_unified_leaderboard = False

	return is_unified_leaderboard

def is_valid_leaderboard_combination(
	title: Title,
	game_type: GameType,
	platform: Platform
) -> bool:

	is_valid = True

	if title in [Title.ModernWarfare, Title.BlackOps4]:

		if game_type.value not in ['core', 'hc']:
			is_valid = False
		
		if platform is Platform.Steam and game_type.value in ['core', 'hc']:
			is_valid = False
	
	elif title is Title.WWII:

		if game_type.value not in ['core']:
			is_valid = False
		
		if platform in [Platform.Steam, Platform.BattleNet] and game_type.value in ['core', 'hc']:
			is_valid = False
		
	elif title is Title.BlackOps3:

		if game_type.value not in ['core', 'hc', 'arena']:
			is_valid = False

		if platform in [Platform.BattleNet]:
			is_valid = False

	elif title is Title.InfiniteWarfare:

		if platform in [Platform.BattleNet, Platform.Xbox] and game_type.value in ['core', 'hc', 'arena']:
			is_valid = False

	return is_valid

def get_correct_leaderboard_combinations_for_title(
	title: Title,
	platform: Platform
) -> list:

	if title in [Title.ModernWarfare, Title.BlackOps4]:
		if platform is Platform.Steam:
			return []
		else:
			return [
				{
					'text': 'Core',
					'value': 'core'
				},
				{
					'text': 'Hardcore',
					'value': 'hc'
				}
			]

	elif title is Title.WWII:
		return [
			{
				'text': 'Core',
				'value': 'core'
			}
		]
	elif title is Title.BlackOps3:
		if platform in [Platform.BattleNet]:
			return []
		else:
			return [
				{
					'text': 'Core',
					'value': 'core'
				},
				{
					'text': 'Hardcore',
					'value': 'hc'
				},
				{
					'text': 'Arena',
					'value': 'arena'
				}
			]
	elif title is Title.InfiniteWarfare:
		if platform in [Platform.BattleNet]:
			return []
		else:
			return []
	else:
		return []

def return_field_mapping(
	field_mapping: dict, 
	item: dict, 
	data_fields: dict, 
) -> dict:
	
	items = {}

	for key, value in field_mapping.items():
		if value in data_fields:
			items[value] = item.get(key, None)

	return items

async def create_or_update_object_from_mapping(
	queryset_object: QuerySet,
	queryset_base_fields: dict,
	object_to_map: dict, 
	data_fields: dict
) -> None:	

	item_type_model_fields = queryset_base_fields['item_type'].model_fields

	items = return_field_mapping(
		item_type_model_fields,
		object_to_map,
		data_fields
	)
	
	queryset = queryset_object.filter(
		**queryset_base_fields
	)
	queryset_exists = await queryset.exists()

	fields = {}
	fields.update(queryset_base_fields)

	create_or_update = False

	## the Call of Duty API in all of it's infinite wisdom returns 'None' and 0 respectively
	## for all fields for any given object, even if the player hasn't played that object.
	## thuis, if this is the case we're wasting space int he DB. Just don't continue if this is the case.
	if not(
		all(
			value == 0 
			or 
			value == None 
			for value in items.values()
		)
	):
		fields.update(items)

		if not queryset_exists:
			
			thisobject = await queryset_object.create(
				**fields
			)

		else:

			await queryset.update(
				**fields
			)
			thisobject = await queryset.first()

		return thisobject

async def get_player_stats(
	player_id: int,
	current_player: Player, 
	platform: Platform,
	username: str,
	title: Title
) -> None:

	cod_player_stats = []
	item_types = CODItemType.all()

	matches_to_process = []

	mode_types = CODModeType.all()
	game_modes = await item_types.filter(
		is_game_mode=True
	)
	weapons = item_types.filter(
		is_weapon=True
	)
	killstreaks = item_types.filter(
		is_kill_streak=True
	)
	general_item_type = await item_types.filter(
		reference__iexact='general_stats'
	).first()
	current_platform = await CODPlatform.filter(
		reference=platform.value
	).first()

	cod_player_platforms = CODPlayerPlatforms.filter(
		codplayer_id=player_id,
		codplatform_id=current_platform.id
	)
	cod_player_platforms_exists = await cod_player_platforms.exists()

	if not cod_player_platforms_exists:
		await CODPlayerPlatforms.create(
			codplayer_id=player_id,
			codplatform=current_platform
		)

	## gets stats for all titles
	modes_to_capture = [
		(Mode.Multiplayer, 'mp')
	]

	if title is Title.ModernWarfare:
		modes_to_capture.append((Mode.Warzone, 'mwwz'))

	if title is Title.BlackOps4:
		modes_to_capture.append((Mode.Blackout, 'wz'))

	title_from_db = await CODTitle.filter(
		reference__iexact=title.value
	).first()

	cod_player_titles = CODPlayerTitles.filter(
		codplayer_id=player_id,
		codtitle_id=title_from_db.id
	)
	cod_player_titles_exists = await cod_player_titles.exists()

	if not cod_player_titles_exists:
		await CODPlayerTitles.create(
			codplayer_id=player_id,
			codtitle_id=title_from_db.id
		)

	for mode in modes_to_capture:

		mode_0 = mode[0]
		mode_type_reference = mode[1]

		mode_type = await mode_types.filter(
			reference__iexact=mode_type_reference
		).first()
		
		await CODTitleModeTypes.get_or_create(
			codtitle_id=title_from_db.id,
			codmodetype_id=mode_type.id
		)

		profile_cache_key = cod_settings.CALL_OF_DUTY_TITLE_PROFILE_CACHE_KEY.format(player_id, title.value, mode_0.value)
		cached_title_profile = await get_from_cache(
			cache_key=profile_cache_key
		)

		# see if we have this cached already... 
		# if we do, good, else fetch
		if cached_title_profile:
			title_profile = cached_title_profile
		else:
			try:
				title_profile = await current_player.profile(title, mode_0)
			except:
				continue

		await create_cache(
			cache_key=profile_cache_key,
			content=title_profile,
			minutes=10
		)
		
		data_fields = [x['name'] for x in CODPlayerTitleStats.describe()['data_fields']]

		queryset_base_fields = {}
		queryset_base_fields['player_id'] = player_id
		queryset_base_fields['title'] = title_from_db
		queryset_base_fields['item_type'] = general_item_type
		queryset_base_fields['mode_type'] = mode_type

		await create_or_update_object_from_mapping(
			queryset_object=CODPlayerTitleStats,
			queryset_base_fields=queryset_base_fields,
			object_to_map=title_profile,
			data_fields=data_fields
		)

		lifetime_stats = title_profile.get('lifetime', None)

		if lifetime_stats:

			all_lifetime_stats = lifetime_stats.get('all', {}).get('properties', None)

			## generate lifetime stats
			if all_lifetime_stats:

				all_lifetime_item_type = await item_types.filter(reference__iexact='all').first()

				queryset_base_fields = {}
				queryset_base_fields['player_id'] = player_id
				queryset_base_fields['title'] = title_from_db
				queryset_base_fields['item_type'] = all_lifetime_item_type

				await create_or_update_object_from_mapping(
					queryset_object=CODPlayerTitleStats,
					queryset_base_fields=queryset_base_fields,
					object_to_map=all_lifetime_stats,
					data_fields=data_fields
				)

			gamemode_stats = lifetime_stats.get('mode', None)

			## generate per gamemode stats
			if gamemode_stats:

				for game_mode in game_modes:

					game_mode_stats_properties =  gamemode_stats.get(game_mode.reference, {}).get('properties', None)

					if game_mode_stats_properties:

						queryset_base_fields = {}
						queryset_base_fields['player_id'] = player_id
						queryset_base_fields['title'] = title_from_db
						queryset_base_fields['item_type'] = game_mode

						await create_or_update_object_from_mapping(
							queryset_object=CODPlayerTitleStats,
							queryset_base_fields=queryset_base_fields,
							object_to_map=game_mode_stats_properties,
							data_fields=data_fields
						)

			item_stats = lifetime_stats.get('itemData', None)

			## generate weapon stats
			if item_stats:
			
				weapoon_keys = [
					'weapon_sniper',
					'tacticals',
					'lethals',
					'weapon_lmg',
					'weapon_launcher',
					'weapon_pistol',
					'weapon_assault_rifle',
					'weapon_other',
					'weapon_shotgun',
					'weapon_smg',
					'weapon_marksman',
					'weapon_melee'
				]

				for weapoon_key in weapoon_keys:

					weapon_category_stats = item_stats.get(weapoon_key, None)

					if weapon_category_stats:

						reference_of_weapons_in_category = weapon_category_stats.keys()
						weapons_in_category = await weapons.filter(reference__in=reference_of_weapons_in_category)

						for weapon_in_category in weapons_in_category:
							weapon_stats_properties =  weapon_category_stats.get(weapon_in_category.reference, {}).get('properties', None)

							if weapon_stats_properties:

								queryset_base_fields = {}
								queryset_base_fields['player_id'] = player_id
								queryset_base_fields['title'] = title_from_db
								queryset_base_fields['item_type'] = weapon_in_category
								queryset_base_fields['mode_type'] = mode_type

								await create_or_update_object_from_mapping(
									queryset_object=CODPlayerTitleStats,
									queryset_base_fields=queryset_base_fields,
									object_to_map=weapon_stats_properties,
									data_fields=data_fields
								)

			## generate killstreak stats
			killstreak_stats = lifetime_stats.get('scorestreakData', None)

			if killstreak_stats:

				killstreak_keys = [
					'lethalScorestreakData',
					'supportScorestreakData'
				]

				for killstreak_key in killstreak_keys:

					killstreak_category_stats = killstreak_stats.get(killstreak_key, None)

					if killstreak_category_stats:

						reference_of_killstreaks_in_category = killstreak_category_stats.keys()
						killstreaks_in_category = await killstreaks.filter(reference__in=reference_of_killstreaks_in_category)

						for killstreak_in_category in killstreaks_in_category:

							killstreak_stats_properties =  killstreak_category_stats.get(killstreak_in_category.reference, {}).get('properties', None)

							if killstreak_stats_properties:

								queryset_base_fields = {}
								queryset_base_fields['player_id'] = player_id
								queryset_base_fields['title'] = title_from_db
								queryset_base_fields['item_type'] = killstreak_in_category

								await create_or_update_object_from_mapping(
									queryset_object=CODPlayerTitleStats,
									queryset_base_fields=queryset_base_fields,
									object_to_map=killstreak_stats_properties,
									data_fields=data_fields
								)

		mode_matches = await current_player._client.http.GetPlayerMatchesDetailed(
			title=title.value,
			platform=platform.value,
			username=username,
			mode=mode_0.value,
			limit=20,
			startTimestamp=0,
			endTimeStamp=0
		)

		mode_matches_summary = mode_matches['data'].get('summary', None)

		## store the BR match summary
		if mode_matches_summary:
			mode_matches_summary_keys = mode_matches_summary.keys()
			mode_matches_summary_keys = [key for key in mode_matches_summary_keys if key != 'all']
			mode_matches_summary_keys.append('br_all')
			mode_matches_keys_to_exclude = ['br', 'br_dmz']

			modes_in_category = await item_types.filter(
				is_game_mode=True,
				reference__in=mode_matches_summary_keys
			).exclude(
				reference__in=mode_matches_keys_to_exclude
			)

			for mode_in_category in modes_in_category:

				mode_in_category_stats =  mode_matches_summary.get(mode_in_category.reference, None)

				if mode_in_category_stats:

					queryset_base_fields = {}
					queryset_base_fields['player_id'] = player_id
					queryset_base_fields['title'] = title_from_db
					queryset_base_fields['item_type'] = mode_in_category
					queryset_base_fields['mode_type'] = mode_type

					await create_or_update_object_from_mapping(
						queryset_object=CODPlayerTitleStats,
						queryset_base_fields=queryset_base_fields,
						object_to_map=mode_in_category_stats,
						data_fields=data_fields
					)

		matches = mode_matches['data'].get('matches', None)

		if matches:
			
			data_fields = [x['name'] for x in CODPlayerMatch.describe()['data_fields']]

			for match in matches:

				items = {}
				items.update(match)
				items.update(match['playerStats'])

				match_mode = await item_types.filter(is_game_mode=True, reference=match['mode']).first()

				if match_mode:

					queryset_base_fields = {}
					queryset_base_fields['player_id'] = player_id
					queryset_base_fields['title'] = title_from_db
					queryset_base_fields['item_type'] = match_mode
					queryset_base_fields['mode_type'] = mode_type
					queryset_base_fields['match_id'] = str(match['matchID'])

					actual_match = await create_or_update_object_from_mapping(
						queryset_object=CODPlayerMatch,
						queryset_base_fields=queryset_base_fields,
						object_to_map=items,
						data_fields=data_fields
					)

					if queryset_base_fields['match_id'] != 'None':
						try:
							match = await current_player._client.http.GetMatch(
								title=title.value,
								platform=platform.value, 
								matchId=int(queryset_base_fields['match_id'])
							)
							match_teams = match['data']['teams']

							for team_no, team in enumerate(match_teams):
								cod_player_match_team = CODPlayerMatchTeam.filter(
									team_no=team_no,
									codplayermatch_id=actual_match.id
								)
								cod_player_match_exists = await cod_player_match_team.exists()
								team_participants = []

								if cod_player_match_exists:
									cod_player_match_team = await cod_player_match_team.first()
								else:
									cod_player_match_team = await CODPlayerMatchTeam.create(
										team_no=team_no,
										codplayermatch_id=actual_match.id
									)

								team_members = []

								for member in team:
									member_provider = member['provider']

									cod_platform = await CODPlatform.filter(reference__iexact=member_provider).first()

									member_username = member['username']

									cod_player = CODPlayer.filter(
										player_name__iexact=member_username
									)
									cod_player_exists = await cod_player.exists()

									if cod_player_exists:
										cod_player = await cod_player.first()
									else:
										cod_player = await CODPlayer.create(
											player_name=member_username
										)

									await cod_player.titles.add(*[title_from_db])
									await cod_player.platforms.add(*[cod_platform])
									team_members.append(cod_player)

								await cod_player_match_team.codplayerteamplayer.add(*team_members)

						except Exception as e:
							continue