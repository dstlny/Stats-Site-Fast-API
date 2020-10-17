from tortoise import models, fields

######################################################
# Tortoise Models
######################################################
class CODTitle(models.Model):
	''' 
		This defines a Titles from the COD API
	'''

	id = fields.IntField(pk=True)
	name = fields.CharField(max_length=64)
	reference = fields.CharField(max_length=64)
	mode_types = fields.ManyToManyField('api.CODModeType', through='codtitlemodetypes')

	def __str__(self) -> str:
		return "{} ({})".format(self.name, self.reference)

class CODPlatform(models.Model):
	''' 
		This defines a Platforms from the COD API
	'''

	id = fields.IntField(pk=True)
	name = fields.CharField(max_length=64)
	reference = fields.CharField(max_length=64)

	def __str__(self) -> str:
		return "{} ({})".format(self.name, self.reference)

class CODTitleModeTypes(models.Model):

	id = fields.IntField(pk=True)
	codtitle = fields.ForeignKeyField('api.CODTitle', on_delete=fields.CASCADE)
	codmodetype = fields.ForeignKeyField('api.CODModeType', on_delete=fields.CASCADE)

	def __str__(self) -> str:
		return "{} ({})".format(self.name, self.reference)

class CODPlayerTitles(models.Model):
	''' 
		This defines a Players Titles from the COD API
	'''

	id = fields.IntField(pk=True)
	codplayer = fields.ForeignKeyField('api.CODPlayer', on_delete=fields.CASCADE)
	codtitle = fields.ForeignKeyField('api.CODTitle', on_delete=fields.CASCADE)

	def __str__(self) -> str:
		return f"{self.id}"

class CODPlayerPlatforms(models.Model):
	''' 
		This defines a Players Platform from the COD API
	'''

	id = fields.IntField(pk=True)
	codplayer = fields.ForeignKeyField('api.CODPlayer', on_delete=fields.CASCADE)
	codplatform = fields.ForeignKeyField('api.CODPlatform', on_delete=fields.CASCADE)

	def __str__(self) -> str:
		return f"{self.id}"

class CODItemType(models.Model):
	''' 
		This defines a Platforms from the COD API
	'''

	id = fields.IntField(pk=True)
	name = fields.CharField(max_length=64)
	reference = fields.CharField(max_length=64)
	model_fields = fields.JSONField()
	is_weapon = fields.BooleanField(default=False, null=True)
	is_kill_streak = fields.BooleanField(default=False, null=True)
	is_game_mode = fields.BooleanField(default=False, null=True)

	def __str__(self) -> str:
		return "{} ({})".format(self.name, self.reference)

class CODModeType(models.Model):
	''' 
		This defines a Platforms from the COD API
	'''

	id = fields.IntField(pk=True)
	name = fields.CharField(max_length=64)
	reference = fields.CharField(max_length=64)

	def __str__(self) -> str:
		return "{} ({})".format(self.name, self.reference)

class CODPlayerTitleStats(models.Model):

	id = fields.IntField(pk=True)
	player = fields.ForeignKeyField('api.CODPlayer', on_delete=fields.CASCADE)
	title = fields.ForeignKeyField('api.CODTitle', on_delete=fields.CASCADE)
	item_type = fields.ForeignKeyField('api.CODItemType', on_delete=fields.CASCADE)
	mode_type = fields.ForeignKeyField('api.CODModeType', on_delete=fields.CASCADE, null=True)

	level = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	level_xp_remainder = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	level_xp_gained = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	prestige = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	prestige_id = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	
	total_xp = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	paragon_rank = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	paragon_id = fields.DecimalField(max_digits=16, decimal_places=2, null=True)

	match_id = fields.CharField(max_length=255, null=True)
	gulag_kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_teams_wiped = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_last_stand_kill = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	wall_bangs = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	avg_life_time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_destroyed_vehicle_light = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	kills_per_game = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	distance_travelled = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_munitions_box_teammate_used = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_1 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_2 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_3 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_4 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_5= fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_6 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_mission_pickup_tablet = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_reviver = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_kiosk_buy = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	time_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	headshot_percentage = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	executions = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	matches_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	gulag_deaths = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	nearmisses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_cache_open = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	damage_done = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	damage_taken = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	team_placement = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	team_survival_time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	utc_start_seconds = fields.IntField(null=True)
	utc_end_seconds = fields.IntField(null=True)
	player_count = fields.IntField(null=True)
	rank = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	player_count = fields.DecimalField(max_digits=16, decimal_places=2, null=True)

	record_longest_win_streak = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	record_xp_in_a_match = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	accuracy = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	last_updated = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	losses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	total_games_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	win_loss_ratio = fields.DecimalField(max_digits=16, decimal_places=2, null=True) # winLossRatio or wlRatio
	total_shots = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_score_xp = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	games_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_sguard_wave = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_sguard_weapon_level = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_squad_kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_squad_wave = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_confirmed = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	deaths = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	wins = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_squard_crates = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	kd_ratio = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_assists = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_field_goals = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_score = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	record_deaths_in_a_match = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score_per_game = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_spm = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kill_chains = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	record_kills_in_a_match = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	suicides = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	current_win_streak = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_match_bonus_xp = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_match_xp = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_s_guard_weapon_level = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kd = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kills_as_infected = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_returns = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_stabs = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kills_as_survivor = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	time_played_total = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_destructions = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	headshots = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_rescues = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	assists = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	ties = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	record_killstreak = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_plants = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	misses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_damage = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_setbacks = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_touchdowns = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score_per_minute = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_deaths = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_medal_xp = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_defends = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_squad_revives = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_defuses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_captures = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	hits = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_kill_streak = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	best_denied = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	time_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	infected = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	defuses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	plants = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	defends = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	top_twenty_five = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	downs = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	top_ten = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	contracts = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	cash = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	revives = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	obj_time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	set_backs = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	shots = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	uses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	awarded_count = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	max_level = fields.DecimalField(max_digits=16, decimal_places=2, null=True)

	def __str__(self) -> str:
		return f"{self.__class__.__name__} {self.id}"

class CODPlayerMatch(models.Model):

	player = fields.ForeignKeyField('api.CODPlayer', on_delete=fields.CASCADE)
	title = fields.ForeignKeyField('api.CODTitle', on_delete=fields.CASCADE)
	item_type = fields.ForeignKeyField('api.CODItemType', on_delete=fields.CASCADE)
	mode_type = fields.ForeignKeyField('api.CODModeType', on_delete=fields.CASCADE)
	
	match_id = fields.CharField(max_length=255, null=True)
	kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	gulag_kills = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_teams_wiped = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_last_stand_kill = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	wall_bangs = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	avg_life_time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_destroyed_vehicle_light = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	kills_per_game = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	distance_travelled = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_munitions_box_teammate_used = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_1 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_2 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_3 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_4 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_5= fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_down_enemy_circle_6 = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_mission_pickup_tablet = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_reviver = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_kiosk_buy = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	time_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	headshot_percentage = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	executions = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	matches_played = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	gulag_deaths = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	nearmisses = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	objective_br_cache_open = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	damage_done = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	damage_taken = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	team_placement = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	team_survival_time = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	utc_start_seconds = fields.IntField(null=True)
	utc_end_seconds = fields.IntField(null=True)
	rank = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	player_count = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	headshots = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	assists = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	deaths = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	score_per_minute = fields.DecimalField(max_digits=16, decimal_places=2, null=True)
	kd_ratio = fields.DecimalField(max_digits=16, decimal_places=2, null=True)

	def __str__(self) -> str:
		return f"{self.__class__.__name__} {self.id}"

class CODPlayerMatchTeam(models.Model):
	''' 
		This defines a team in a Call of Duty matchh
	'''
	id = fields.IntField(pk=True)
	team_no = fields.IntField(null=True)
	codplayermatch = fields.ForeignKeyField('api.CODPlayerMatch', on_delete=fields.CASCADE)
	codplayerteamplayer = fields.ManyToManyField('api.CODPlayer', through='codplayermatchteamplayer')
	
	def __str__(self) -> str:
		return self.team_no

class CODPlayerMatchTeamPlayer(models.Model):
	''' 
		This defines a CODPlayerMatchTeam's members
	'''
	id = fields.IntField(pk=True)
	codplayermatchteam = fields.ForeignKeyField('api.CODPlayerMatchTeam', on_delete=fields.CASCADE)
	codplayer = fields.ForeignKeyField('api.CODPlayer', on_delete=fields.CASCADE)

	def __str__(self) -> str:
		return self.id

class CODPlayer(models.Model):
	''' 
		This defines a Player from the COD API
	'''

	id = fields.IntField(pk=True)
	api_id = fields.CharField(max_length=255, null=True)
	player_name = fields.CharField(max_length=255)
	platform_url = fields.CharField(max_length=255, null=True)
	titles = fields.ManyToManyField('api.CODTitle', through='codplayertitles')
	platforms = fields.ManyToManyField('api.CODPlatform', through='codplayerplatforms')
	api_url = fields.CharField(max_length=255, null=True)

	def __str__(self) -> str:
		return self.api_id

