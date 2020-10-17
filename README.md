# FastAPI (python) and MySQL based Stats Site
- Consists of a front-end (FastAPI with Jinja2) and a API - FastAPI + MySQL
- Uses: [Tortoise ORM](https://github.com/tortoise/tortoise-orm "Tortoise ORM")
- This is essentialy the following project: [https://github.com/dstlny/PUBG-API-Stats-Site](https://github.com/dstlny/PUBG-API-Stats-Site), just written in a different framework using different tools.

# Getting started - things that probably need to be done
- Any version of Python3 that supports `Typing` should work.
- Install the python dependencies using `pip install -r requirements.txt`.
- Setup MySQL and change the settings within `api/initialiser.py` to reflect your local database.
    - This will automatically migrate the models over to your database once the application is ran.
    
 - ### If you want to use the PUBG Module:
    - Change `API_TOKEN` within `application/pubg//settings.py` to your PUBG API Token

 - ### If you want to use the Call of Duty module:
    - Change `CALL_OF_DUTY_API_EMAIL` within `application/cod/settings.py` to your 'My Call of Duty' email [from here](https://my.callofduty.com/login)
    - Change `CALL_OF_DUTY_API_PASSWORD` within `application/cod/settings.py` to your 'My Call of Duty' password
    
 - ### Authentication is turned on by default.
    - If you want to removed this, you'll need to dig and find where it's used.
    - If you however want to use authentication then change `AUTH_SECRET_KEY` within `application/auth/settings.py`

- Start FastAPI using `python app.py`
- Navigate to localhost, and search away.
