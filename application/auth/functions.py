from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

import application.auth.settings as auth_settings
from application.auth.functions import *
from application.auth.models import *
from application.route_models import *
from application.exceptions import *
import logging
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

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

def verify_password(
	plain_password: str,
	hashed_password: str
) -> bool:
	return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(
	password: str
) -> str:
	return pwd_context.hash(password)

async def get_user_by_username(
	username: str
) -> Union[User, None]:
	try:
		return await User.get(username=username)
	except:
		return None

async def get_user_by_email(
	email: str
) -> Union[User, None]:
	try:
		return await User.get(email=username)
	except:
		return None

async def authenticate_user(
	username: str,
	password: str
) -> Union[None, bool, User]:
	user = await get_user_by_username(username)

	if user is None:
		return None

	if not verify_password(password, user.password):
		return False

	return user

async def check_if_user_exists(
	username: str,
	email: str = None
) -> Union[None, bool, User]:

	if email:
		user = await get_user_by_email(email)
	else:
		user = await get_user_by_username(username)

	if user is None:
		return False

	return True

async def create_user(
	username: str,
	password: str
) -> User:
	hashed_password = get_password_hash(password)
	
	user = await User.create(
		username=username,
		password=hashed_password,
		is_active=True
	)

	return user

def create_access_token(
	data: dict,
	expires_delta: Optional[timedelta] = None
) -> str:
	to_encode = data.copy()

	now = datetime.now(timezone.utc)

	if expires_delta:
		expire = now + expires_delta
	else:
		expire = now + timedelta(minutes=15)

	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, auth_settings.AUTH_SECRET_KEY, algorithm=auth_settings.AUTH_ALGORITHM)

	return encoded_jwt

async def token_is_good(
	token: str = Depends(oauth2_scheme)
) -> Union[TokenActive, ExtendedHTTPException]:
	try:
		payload = jwt.decode(token, auth_settings.AUTH_SECRET_KEY, algorithms=[auth_settings.AUTH_ALGORITHM])
		username = payload.get("sub")

		if username is None:
			raise ExtendedHTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Could not validate credentials.",
				plain=True
			)

		token_active = TokenActive(
			is_authed=True
		)
		return token_active
	except JWTError as e:
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="You are not authorized to access this page.",
			plain=False
		)

async def get_current_user(
	token: str = Depends(oauth2_scheme)
) -> Union[ExtendedHTTPException, User]:
	try:
		payload = jwt.decode(token, auth_settings.AUTH_SECRET_KEY, algorithms=[auth_settings.AUTH_ALGORITHM])
		username = payload.get("sub")

		if username is None:
			raise ExtendedHTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Could not validate credentials.",
				plain=True
			)

		token_data = TokenData(username=username)
	except JWTError as e:
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="You are not authorized to access this page.",
			plain=False,
			redirect='/'
		)

	user = await get_user_by_username(username=token_data.username)

	if user is None:
		raise ExtendedHTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="User does not exist.",
			plain=True
		)

	return user

async def get_current_active_user(
	current_user: RouteUser = Depends(get_current_user)
) -> RouteUser:

	if not current_user.is_active:
		raise HTTPException(status_code=400, detail="Inactive user")

	return current_user

async def get_current_active_user_with_password(
	current_user: RouteUserWithPassword = Depends(get_current_user)
) -> RouteUserWithPassword:

	if not current_user.is_active:
		raise HTTPException(status_code=400, detail="Inactive user")

	return current_user
