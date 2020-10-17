from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from typing import Optional
import importlib

from fastapi import Depends, FastAPI, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

import application.auth.settings as auth_settings
from application.auth.functions import *
import logging
import re
import sys

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
	fmt='[%(asctime)s](%(levelname)s) %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

password_regex = re.compile('^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$')

@router.post("/token/", response_model=Token)
async def login_for_access_token(
	request: Request,
	form_data: OAuth2PasswordRequestForm = Depends()
):
	access_token_expires = timedelta(
		minutes=auth_settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
	)

	user = await authenticate_user(form_data.username, form_data.password)

	if user is None:
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=f"User with username '{form_data.username}' does not exist.",
			headers={"WWW-Authenticate": "Bearer"},
			plain=True
		)
	elif user is False:
		logger.info(f'{form_data.username} is current user.')
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Incorrect username or password.",
			headers={"WWW-Authenticate": "Bearer"},
			plain=True
		)

	access_token = create_access_token(
		data={"sub": user.username}, expires_delta=access_token_expires
	)
	return {"access_token": access_token, "token_type": "bearer"}

@router.get("/is_authed/")
async def is_authed(
	request: Request,
	token_active: TokenActive = Depends(token_is_good)
):
	return token_active

@router.get("/login/")
async def login(
	request: Request,
	current_user: RouteUser = Depends(get_current_active_user)
):
	if current_user:
		logger.info(f'{current_user.username} is logged in.')

	return current_user

@router.post("/add_email/")
async def add_email(
	request: Request,
	current_user: RouteUserWithPassword = Depends(get_current_active_user_with_password),
	current_password: str = Form(...),
	password_confirm: str = Form(...),
	email: str = Form(...)
):

	if current_password == password_confirm:

		if verify_password(current_password, current_user.password):
			
			user_exists = await check_if_user_exists(email)

			if user_exists:
				raise ExtendedHTTPException(
					status_code=status.HTTP_401_UNAUTHORIZED ,
					detail={
						'fields': {
							'email': "Email already taken.",
						}
					},
					plain=True,
					as_json=True
				)
			else:
				current_user.email = email
				await current_user.save()
				logger.info(f'{current_user.username} changed email.')
				return { 'text': 'Email sucessfully changed!' }

		else:
			raise ExtendedHTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED ,
				detail={
					'should_expire_token': False,
					'detail': 'Entered passwords do not match password on-file for account.'
				},
				plain=True,
				as_json=True
			)

	else:
			
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED ,
			detail={
				'fields': {
					'current_password': 'This does not match "Confirm Password"',
					'password_confirm': 'This does not match "Current Password"'
				}
			},
			plain=True,
			as_json=True
		)

@router.post("/change_password/")
async def change_password(
	request: Request,
	current_user: RouteUserWithPassword = Depends(get_current_active_user_with_password),
	current_password_: str = Form(...),
	new_password_: str = Form(...)
):

	if re.search(password_regex, new_password_):

		if verify_password(current_password_, current_user.password):
			new_password_ = get_password_hash(new_password_)
			current_user.password = new_password_
			await current_user.save()
			logger.info(f'{current_user.username} changed password.')
			return { 'text': 'Password sucessfully changed!' }
		else:
			raise ExtendedHTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED ,
				detail={
					'should_expire_token': False,
					'fields': {
						'current_password_': 'Password does not match current password for account.'
					}
				},
				plain=True,
				as_json=True
			)
	else:
		raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED ,
			detail={
				'should_expire_token': False,
				'fields': {
					'new_password_': 'New password should match the following criteria: <ol><li>At least one uppercase and lowercase letter.</li><li>Minimum eight characters in length.</li><li>At least one digit.</li><li>At least one special character (#?!@$%^&*-).</li></ol>'
				}
			},
			plain=True,
			as_json=True
		)
		
@router.post("/register/")
async def register(
	request: Request,
	form_data: OAuth2PasswordRequestForm = Depends()
):

	access_token_expires = timedelta(
		minutes=auth_settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
	)

	user_exists = await check_if_user_exists(form_data.username)

	if user_exists:
		raise ExtendedHTTPException(
			status_code=status.HTTP_409_CONFLICT ,
			detail="User with this username already exists.",
			plain=True
		)
	else:
		if re.search(password_regex, form_data.password):
			user = await create_user(
				username=form_data.username,
				password=form_data.password
			)
			access_token = create_access_token(
				data={"sub": user.username}, expires_delta=access_token_expires
			)
			logger.info(f'{user.username} registered.')
			return {
				"access_token": access_token,
				"token_type": "bearer",
				"username": user.username,
				"is_active": user.is_active
			}
		else:
			raise ExtendedHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED ,
			detail={
				'should_expire_token': False,
				'detail': 'Password should match the following criteria: <ol><li>At least one uppercase and lowercase letter.</li><li>Minimum eight characters in length.</li><li>At least one digit.</li><li>At least one special character (#?!@$%^&*-).</li></ol>'
			},
			plain=True,
			as_json=True
		)
	
