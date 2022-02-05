import base64
import json
from os import getenv

from google.oauth2 import service_account
import gspread
import requests

from bot_rio.constants import constants


def parse_idea(idea: str, mode: str) -> str:
    """Parses an idea for Github or Google Sheets.
    Args:
        idea: The idea to be parsed.
        mode: The mode to parse the idea in.
    Returns:
        The parsed idea.

    Input format: [name/desc.]; [author]; [org.]; [tags]
    If the idea doesn't follow the format, raise an error.
    Output formats:
        Github:
            TODO.
        Google Sheets:
            [name/desc., org., tags]
    """
    if mode == 'github':
        raise NotImplementedError("Github is still not supported!")
    elif mode == 'gspread':
        if ';' not in idea:
            raise ValueError(
                "A ideia deve seguir o formato: [nome/desc.]; [responsável]; [org.]; [tags]")
        split = idea.split(';')
        if len(split) != 4:
            raise ValueError(
                "A ideia deve seguir o formato: [nome/desc.]; [responsável]; [org.]; [tags]")
        name, author, org, tags = split
        if not name:
            raise ValueError("A ideia deve ter um nome!")
        if not author:
            raise ValueError("A ideia deve ter um responsável!")
        if not org:
            org = 'Rio'
        if not tags:
            tags = 'rio'
        return [name, author, org, tags]


def create_github_issue(title, body, repo_name):
    """Creates an issue on Github"""
    url = f'https://api.github.com/repos/{repo_name}/issues'
    headers = {'Authorization': f'token {constants.GITHUB_TOKEN.value}'}
    data = {'title': title, 'body': body}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()


def get_credentials_from_env(scopes: list = None) -> service_account.Credentials:
    """Gets credentials from env vars"""
    env: str = constants.GCLOUD_CREDENTIALS.value
    info: dict = json.loads(base64.b64decode(env))
    cred = service_account.Credentials.from_service_account_info(info)
    if scopes:
        cred = cred.with_scopes(scopes)
    return cred


def get_gspread_client() -> gspread.Client:
    """Gets gspread client"""
    cred = get_credentials_from_env(scopes=constants.GSPREAD_SCOPE.value)
    return gspread.authorize(cred)


def add_line_to_spreadsheet(
    spreadsheet_id: str,
    line: str,
    worksheet_name: str = None,
    client: gspread.Client = None,
):
    """Adds a line to a spreadsheet"""
    if not client:
        client = get_gspread_client()
    sheet = client.open_by_key(spreadsheet_id)
    if worksheet_name:
        sheet = sheet.worksheet(worksheet_name)
    sheet.append_row(line, value_input_option='USER_ENTERED')
