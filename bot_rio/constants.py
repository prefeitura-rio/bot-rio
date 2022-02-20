from enum import Enum
from os import getenv


def nonull_getenv(env_name):
    env_value = getenv(env_name)
    if env_value is None:
        raise ValueError(f'{env_name} is not set')
    return env_value


class constants (Enum):

    # Envs
    DISCORD_TOKEN = nonull_getenv('DISCORD_TOKEN')
    IDEA_CHANNEL = nonull_getenv('IDEA_CHANNEL')
    IDEA_SPREADSHEET_ID = nonull_getenv('IDEA_SPREADSHEET_ID')
    GERAL_CHANNEL = nonull_getenv('GERAL_CHANNEL')
    LANGUAGES_CHANNELS = nonull_getenv('LANGUAGES_CHANNELS').split(";")
    GCLOUD_CREDENTIALS = nonull_getenv('GCLOUD_CREDENTIALS')

    # Bot
    COMMAND_PREFIX = '!'
    DEFAULT_ISSUE_BODY = '''Issue criada automaticamente pelo Bot.rio!

    Favor preencher detalhes!'''

    # Credentials
    GSPREAD_SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
