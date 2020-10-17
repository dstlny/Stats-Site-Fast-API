from application.pubg.models import Cache
from datetime import datetime, timedelta, timezone
import base64
import pickle
from typing import *

async def get_from_cache(
	cache_key: str,
	ignore_expires: bool = False
) -> Optional[Cache]:

	cache = await Cache.filter(cache_key=cache_key).first()

	if cache:

		if ignore_expires:

			return cache.actual_content()

		else:

			if cache.has_expired():
				await cache.delete()
			else:
				return cache.actual_content()

	return None

async def delete_from_cache(
	cache_key: str
) -> bool:

	await Cache.filter(cache_key=cache_key).delete()

	return True

async def cache_touch(
	cache_key: str,
	minutes: int
) -> bool:

	cache = await Cache.filter(cache_key=cache_key).first()

	if cache:

		expires = cache.expires + timedelta(minutes=minutes)
		cache.expires = expires
		
		await cache.save()
		return True

	return False

async def create_cache(
	cache_key: str,
	content: Any,
	minutes: int = 30
) -> bool:

	pickle_protocol = pickle.HIGHEST_PROTOCOL

	cache = Cache.filter(cache_key=cache_key)
	cache_exists = await cache.exists()

	expires = datetime.now() + timedelta(minutes=minutes)
	pickled = pickle.dumps(content, pickle_protocol)
	b64encoded = base64.b64encode(pickled).decode('latin1')

	## if exists, update it.
	## - if we're updating, content in the cache has
	## -- Diverged from the DB
	## -- Somehow become corrupt.
	## Thus, refersh it
	if not cache_exists:

		try:
			cache = Cache(
				cache_key=cache_key,
				content=b64encoded,
				expires=expires
			)

			await cache.save()

			return True
		except Exception as e:
			return False

	else:
		await cache.update(
			cache_key=cache_key,
			content=b64encoded,
			expires=expires
		)

	return False