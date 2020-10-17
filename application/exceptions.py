from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
from typing import Optional
from starlette.responses import RedirectResponse

class ExtendedHTTPException(HTTPException):
	def __init__(self, plain: bool, redirect: Optional[str] = None, as_json: Optional[bool] = False, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.plain = plain
		self.redirect = redirect
		self.as_json = as_json
