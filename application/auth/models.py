from tortoise import models, fields

######################################################
# Tortoise Models
######################################################
class User(models.Model):
	''' 
		This defines a Map from the PUBG API 
	'''

	id = fields.IntField(pk=True)
	username = fields.CharField(max_length=225)
	email = fields.CharField(max_length=225, null=True)
	password = fields.CharField(max_length=225)
	is_active = fields.BooleanField(default=False)

	def __str__(self) -> str:
		return "{} ({})".format(self.id, self.username)
