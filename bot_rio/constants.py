from enum import Enum
from os import getenv


def nonull_getenv(env_name):
    env_value = getenv(env_name)
    if env_value is None:
        raise ValueError(f'{env_name} is not set')
    return env_value


class constants (Enum):

    # Envs
    BASES_SHEET_NAME = nonull_getenv('BASES_SHEET_NAME')
    BASES_SPREADSHEET_ID = nonull_getenv('BASES_SPREADSHEET_ID')
    BOT_RIO_API_URL = nonull_getenv('BOT_RIO_API_URL')
    BOT_RIO_API_TOKEN = nonull_getenv('BOT_RIO_API_TOKEN')
    DISCORD_TOKEN = nonull_getenv('DISCORD_TOKEN')
    GCLOUD_CREDENTIALS = nonull_getenv('GCLOUD_CREDENTIALS')
    GERAL_CHANNEL = nonull_getenv('GERAL_CHANNEL')
    IDEA_CHANNEL = nonull_getenv('IDEA_CHANNEL')
    IDEA_SPREADSHEET_ID = nonull_getenv('IDEA_SPREADSHEET_ID')
    LANGUAGES_CHANNELS = nonull_getenv('LANGUAGES_CHANNELS').split(";")
    OPENAI_API_KEY = nonull_getenv('OPENAI_API_KEY')
    REDIS_CONNECTION_URL = nonull_getenv('REDIS_CONNECTION_URL')
    REFERENCES_CHANNEL = nonull_getenv('REFERENCES_CHANNEL')
    REFERENCES_SPREADSHEET_ID = nonull_getenv('REFERENCES_SPREADSHEET_ID')
    STATUS_CHANNEL = nonull_getenv('STATUS_CHANNEL')
    TRELLO_KEY = nonull_getenv('TRELLO_KEY')
    TRELLO_STATUS_BOARD_INFRA = nonull_getenv('TRELLO_STATUS_BOARD_INFRA')
    TRELLO_TOKEN = nonull_getenv('TRELLO_TOKEN')

    # Trello
    TRELLO_LISTS = ["Entregas da semana anterior", "Prioridades da semana atual",
                    "Tarefas planejadas para o futuro", "Bloqueios", "Metas"]
    TRELLO_LISTS_EMOJIS = {
        "Metas": "🎯",
        "Bloqueios": "⏸️",
        "Tarefas planejadas para o futuro": "⏭️",
        "Prioridades da semana atual": "▶️",
        "Entregas da semana anterior": "✅"
    }

    # Bot
    COMMAND_PREFIX = '!'
    DEFAULT_ISSUE_BODY = '''Issue criada automaticamente pelo Bot.rio!

    Favor preencher detalhes!'''

    # OpenAI
    COMPLETIONS_MODEL = "text-davinci-003"

    # Credentials
    GSPREAD_SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
