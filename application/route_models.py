from pydantic import BaseModel
from typing import Optional
from fastapi import Form

class Player(BaseModel):
	player_name: Optional[str] = None
	platform: Optional[str] = None
	ranked: Optional[bool] = None
	api_id: Optional[str] = None
	title: Optional[str] = None
	game_mode: Optional[list] = None

class Match(BaseModel):
	match_id: int
	account_id: Optional[str] = None

class Leaderboard(BaseModel):
	season_id: Optional[str] = None
	platform: str
	game_mode: Optional[str] = None
	title: Optional[str] = None
	game_type: Optional[str] = None

class RouteUser(BaseModel):
	username: str
	email: Optional[str] = None
	is_active: bool

class RouteUserWithPassword(BaseModel):
	username: str
	email: Optional[str] = None
	is_active: bool
	password: Optional[str] = None

class TokenActive(BaseModel):
	is_authed: Optional[bool] = False

class Token(BaseModel):
	access_token: str
	token_type: str

class TokenData(BaseModel):
	username: Optional[str] = None