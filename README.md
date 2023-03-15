# Project homework_bot
Telegram bot for tracking the status of checking homework on Yandex.The workshop.
Sends messages when the status is changed - taken for verification, there are comments, counted.
## Technologies:
* Python 3.9
* python-dotenv 0.19.0
* python-telegram-bot 13.7
## How to launch a project:
Clone the repository and go to it on the command line:
```
    git clone git@github.com:Chameleon812/homework_bot.git
```
```
    cd homework_bot
```
Create and activate a virtual environment:
```
    python -m venv env
```
```
    source env/bin/activate
```
Install dependencies from a file requirements.txt:
```
    python -m pip install --upgrade pip
```
```
    pip install -r requirements.txt
```
Write to environment variables (file .env) required keys:

* Yandex profile token.Practicum
* Telegram bot token
* Your telegram ID

Launch a project:
```
    python homework.py
```
