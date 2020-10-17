import sys
sys.path.append("..")

from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import urllib.parse

import application.common.settings as common_application_settings 
from application.route_models import Player

router = APIRouter()

from app import templates

@router.get('/', response_class=HTMLResponse)
async def index(
	request: Request
):

	return templates.TemplateResponse("base/index.html", {
		"request": request,
		"modules": common_application_settings.MODULE_DICTIONARY 
	})

@router.get('/woops/', response_class=HTMLResponse)
async def error(
	request: Request
):

	return templates.TemplateResponse("error.html", {
		"request": request,
		"error": 'Something seems to have happened'
	})

@router.get('/{module_reference}/', response_class=HTMLResponse)
async def moodule_index(
	request: Request,
	module_reference: str
):

	if module_reference in common_application_settings.MODULE_LIST:

		this_module = common_application_settings.MODULE_MAPPING.get(module_reference)

		return templates.TemplateResponse("module_search.html", {
			"request": request,
			"module": this_module
		})
	else:
		raise HTTPException(
			status_code=404,
			detail="Module not found"
		)

@router.get('/{module_reference}/user/{player_name}/', response_class=HTMLResponse)
async def module_user(
	request: Request,
	module_reference: str,
	player_name: str,
	platform: Optional[str] = None
):

	if module_reference in common_application_settings.MODULE_LIST:

		this_module = common_application_settings.MODULE_MAPPING.get(module_reference)
		
		player = await this_module['player_function'](
			parameters=Player(
				player_name=player_name
			)
		)

		in_database = player.get('in_database', None)

		## if no player by this name in the database - lets search them, and then try again
		if in_database == False:
		
			player_search  = await this_module['endpoint_functions']['search'](
				parameters=Player(
					player_name=player_name,
					platform=platform
				)
			)
			player = await this_module['player_function'](
				parameters=Player(
					player_name=player_name
				)
			)

		return templates.TemplateResponse(this_module['module_index'], {
			"request": request,
			"module": this_module,
			"perspective_selections": this_module.get('perspectives'),
			"platform_selections": this_module.get('platforms'),
			"gamemode_selections": this_module.get('game_modes_no_perspective') or this_module.get('game_modes'),
			"player_name": player_name,
			"platform": platform,
			"account_id": player.get('api_id'),
			"titles": player.get('titles'),
			'api_endpoints': this_module.get('endpoints'),
			'labels': common_application_settings.LABELS,
			'not_display': common_application_settings.NOT_DISPLAY,
			'all_modes': player.get('all_modes'),
			'mode_types': player.get('mode_types')
		})

	else:
		raise HTTPException(
			status_code=404,
			detail="Module not found"
		)


@router.get('/{module_reference}/leaderboards/{platform}/', response_class=HTMLResponse)
async def module_leaderboard(
	request: Request,
	module_reference: str,
	platform: str
):

	if module_reference in common_application_settings.MODULE_LIST:

		this_module = common_application_settings.MODULE_MAPPING.get(module_reference)
		endpoint_functions = this_module.get('endpoint_functions')
		endpoints = this_module.get('endpoints')

		if endpoint_functions and 'seasons_for_platform' in endpoint_functions:
			seasons = await endpoint_functions['seasons_for_platform'](
				parameters=Player(
					platform=platform
				)
			)

			regions = []
			for region in this_module['regions']:
				region_value = region['value'] 
				if platform == 'steam':
					if 'pc' in region_value or len(region_value) == 0:
						regions.append(region)
				else:
					if platform in region_value or len(region_value) == 0:
						regions.append(region)

		else:
			seasons = None
			regions = None

		return templates.TemplateResponse(f'{module_reference}/leaderboards.html', {
			"request": request,
			"module": this_module,
			"season_selections": seasons,
			"game_mode_selection": this_module.get('game_modes', None) or this_module.get('game_modes_no_perspective', None),
			"title_selection": this_module.get('titles'),
			"region_selection": regions,
			"platform": platform,
			"api_endpoints": endpoints
		})

	else:
		raise HTTPException(
			status_code=404,
			detail="Module not found"
		)

@router.get('/pubg/match_detail/{match_api_id}/{account_api_id}/', response_class=HTMLResponse)
async def pubg_match_detail(
	request: Request,
	match_api_id: str,
	account_api_id: str
):

	module_reference = 'pubg'
	
	if module_reference in common_application_settings.MODULE_LIST:

		this_module = common_application_settings.MODULE_MAPPING.get(module_reference)
		endpoint_functions = this_module.get('endpoint_functions')
		endpoints = this_module.get('endpoints')

		if endpoint_functions and 'match_detail' in endpoint_functions:
			match_details = await endpoint_functions['match_detail'](
				match_api_id=match_api_id,
				account_api_id=account_api_id
			)
		else:
			match_details = None

		return templates.TemplateResponse(f'{module_reference}/match_detail.html', {
			"request": request,
			"module": this_module,
			'telemetry_data': match_details.get('telemetry_data'),
			"api_endpoints": endpoints
		})

	else:
		raise HTTPException(
			status_code=404,
			detail="Module not found"
		)