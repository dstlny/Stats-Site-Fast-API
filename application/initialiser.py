from tortoise.contrib.fastapi import register_tortoise
import sys
import os

from application.commands import init_commands
import application.launch_args as launch_arguments

def init(app):
	"""
	Init routers and etc.
	:return:
	"""
	init_db(app)

def init_db(app):
	"""
	Init database models.
	:param app:
	:return:
	"""
	if launch_arguments.IS_LOCAL:
		config = {
			'connections':{
				'default': {
					'engine': 'tortoise.backends.asyncpg',
					"credentials":{
						"database": 'local',
						"host": "127.0.0.1",
						"password": 'Maya1972!!',
						"port": 5432,
						"user": "postgres",
					}
				}
			},
			"apps": {
				'api': {
					"models": [
						"application.pubg.models",
						"application.cod.models",
						"application.auth.models"
					]
				}
			}
		}
	else:
		config = {
			'connections':{
				'default': os.environ['DATABASE_URL']
			},
			"apps": {
				'api': {
					"models": [
						"application.pubg.models",
						"application.cod.models",
						"application.auth.models"
					]
				}
			}
		}
	
	register_tortoise(
		app,
		config=config,
		generate_schemas=True
	)
	
	init_commands(app)
