from application.pubg.models import *
from application.pubg.functions import build_list_all_seasons_url, make_request
from datetime import datetime, timedelta, timezone
import logging
from fastapi_utils.tasks import repeat_every
import importlib
import os
import sys

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

def init_commands(app):
	''' 
		app: FastAPI instance
		Will run a few background commands every X seconds
	'''

	application = app

	@application.on_event("startup")
	@repeat_every(seconds=86400)
	async def clear_down_old_matches():
		'''
			This function will run every 24 hours.
			Will clear out old matches from the Database that we can no-longer query
			Due to data-retention of the PUBG API
		'''
		now = datetime.now()

		logger.debug(f'Command: clear_down_old_matches started at {now}')

		two_weeeks_ago = datetime.combine(now-timedelta(days=14), datetime_time.min)

		roster_data = await Roster.filter(
			match__created__lte=two_weeeks_ago
		)\
		.prefetch_related(
			'match',
			'match__map',
			'participants',
			'participants__player'
		)

		for roster in roster_data:
			message = f'Deleting all data related to match {roster.match.api_id.split("_")[1]}'
			logger.debug(message)
			await roster.delete()

		else:
			logger.debug(f'Command: clear_down_old_matches ended at {now}')

	@application.on_event("startup")
	@repeat_every(seconds=86400)
	async def make_sure_seasons_upto_date():
		'''
			This function will run every 48 hours.
			Will make sure4 that all seasons are correct
		'''
		now = datetime.now()

		logger.debug(f'Command: make_sure_seasons_upto_date started at {now}')
		current_seasons = Season.all()

		for platform in ['xbox', 'psn', 'stadia', 'steam']:
			platform_url = build_url(platform)
			all_seasons_url = build_list_all_seasons_url(
				base_url=platform_url
			)
			data = make_request(all_seasons_url)

			if data:
				actual_data = data.get('data', {})
				if actual_data:
					for season_data in actual_data:
						api_id = season_data.get('id', None)

						try:
							season_in_db = await current_seasons.get(
								api_id=api_id,
								platform=platform
							)
						except:
							season_in_db = None

						kwargs = {
							'api_id': api_id,
							'is_current': season_data.get('attributes', {}).get('isCurrentSeason', None),
							'is_off_season': season_data.get('attributes', {}).get('isOffseason', None),
							'api_url': all_seasons_url,
							'platform': platform
						}

						if season_in_db is not None:
							season_in_db.is_current = season_data.get('attributes', {}).get('isCurrentSeason', False)
							season_in_db.is_off_season = season_data.get('attributes', {}).get('isOffseason', False)
							season_in_db.api_url = all_seasons_url
							season_in_db.platform = platform
							await season_in_db.save()
							logger.debug(f'Command make_sure_seasons_upto_date: Created season "{api_id}" for "{platform}"')
						else:
							await Season.create(
								**kwargs
							)
							logger.debug(f'Command make_sure_seasons_upto_date: Updated season "{api_id}" for "{platform}"')

		else:
			logger.debug(f'Command: make_sure_seasons_upto_date ended at {now}')

	@application.on_event("startup")
	@repeat_every(seconds=86400)
	async def replace_references_to_old_users():
		'''
			This function will run every 24 hours.
			Will get the latest player_name for every user
			and will replace any reference to a players old usernames (if changed),
			to their new usernames.
		'''
		now = datetime.now()

		logger.debug(f'Command: replace_references_to_old_users started at {now}')

		all_players = await Player.all()
		all_participants = Participant.all()
		all_rosters = Roster.all()

		for player in all_players:
			latest_participant = await all_participants.filter(
				player_id=player.id
			).order_by('-id').first()
			
			all_telemetry = await Telemetry.filter(
				player_id=player.id
			)

			if latest_participant:
				
				new_participant_name = latest_participant.player_name

				all_participat_objects = await all_participants.filter(
					player_id=player.id
				).exclude(
					id=latest_participant.id,
					player_name=new_participant_name
				)
				all_old_names = await all_participants.filter(
					player_id=player.id
				).exclude(
					id=latest_participant.id,
					player_name=new_participant_name
				).distinct().values_list('player_name', flat=True)

				for old_participant in all_participat_objects:
					old_participant_name = old_participant.player_name
					old_participant.player_name = new_participant_name
					await old_participant.save()
				else:
					message = f'Renamed all references of "{old_participant_name}" to "{new_participant_name}" in Participants'
					logger.debug(message)

				for telemetry in all_telemetry:
					all_telemetry_events = await TelemetryEvent.filter(
						telemetry_id=telemetry.id,
						player_id=player.id
					)
					all_telemetry_rosters = await TelemetryRoster.filter(
						telemetry_id=telemetry.id
					)
					if all_telemetry_events:
						for old_name in all_old_names:
							for event in all_telemetry_events:
								event_description = event.description
								if old_name in event_description:
									new_event_description = event_description.replace(old_name, new_participant_name)
									event.description = new_event_description
									await event.save()
							else:
								message = f'Renamed all references of "{old_name}" to "{new_participant_name}" in TelemtryEvents'
								logger.debug(message)

							for roster in all_telemetry_rosters:
								roster_json = roster.json

		else:
			logger.debug(f'Command: replace_references_to_old_users ended at {now}')