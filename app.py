from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, status, Response
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import PlainTextResponse
import uvicorn
from typing import Any
import os
import sys
import random

from application import initialiser
from application.pubg import api_router as pubg_api_router
from application.cod import api_router as cod_api_router
from application.auth import api_router as auth_api_router
from application.exceptions import *
import application.launch_args as launch_arguments

app = FastAPI(
	title='FastAPI Application',
	description='Created by Luke Elam. Open Source PUBG Stats site for Console and PC. GitHub: https://github.com/dstlny/Stats-Site-Fast-API',
	version='1.0',
	debug=launch_arguments.IS_DEBUG,
	docs_url=None,
	redoc_url=None
)
dir_path = os.path.dirname(os.path.realpath(__file__))
templates_path =  os.path.join(os.path.join(dir_path, 'application'), 'templates')
os.makedirs(os.path.dirname(templates_path), exist_ok=True)

templates = Jinja2Templates(
	directory=templates_path
)

## this will make sure that if any JS changes between updates, browsers will automatically re-validate their cached content of the site.
templates.env.globals['VERSION_NUMBER'] = random.choice(range(0, 10000))

## exception handler for when an error occurs
@app.exception_handler(ExtendedHTTPException)
async def http_exception_handler(
	request: Request,
	exc: ExtendedHTTPException
) -> Any:

	if exc.redirect:
		return JSONResponse(
			status_code=exc.status_code,
			content=jsonable_encoder({'redirect': exc.redirect}),
		)

	if not exc.plain:
		return templates.TemplateResponse("error.html", {
			"request": request,
			"error": str(exc.detail)
		})

	if not exc.as_json:
		return JSONResponse(
			status_code=exc.status_code,
			content=jsonable_encoder({'detail':  str(exc.detail)}),
		)
	else:
		return JSONResponse(
			status_code=exc.status_code,
			content=jsonable_encoder({'detail': exc.detail}),
		)
		
## api routers
app.include_router(
	pubg_api_router.router,
	prefix="/api/pubg"
)
app.include_router(
	cod_api_router.router,
	prefix="/api/cod"
)
app.include_router(
	auth_api_router.router,
	prefix="/api/auth"
)

from application.common import api_router as common_api_router
from application.common import view_router as common_view_router
## view routers
app.include_router(
	common_view_router.router
)
app.include_router(
	common_api_router.router,
	prefix="/api/common"
)

## mount static
static_path =  os.path.join(os.path.join(dir_path, 'application'), 'static')
os.makedirs(os.path.dirname(static_path), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

initialiser.init(app)
host_ip = "127.0.0.1"

if launch_arguments.IS_WINDOWS:
	if __name__ == "__main__":
		uvicorn.run(
			app=app,
			host=host_ip,
			port=8000,
			loop='asyncio'
		)