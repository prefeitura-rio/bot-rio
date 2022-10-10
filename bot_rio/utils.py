import base64
from datetime import datetime, timedelta
import json
from typing import Dict, List

from google.oauth2 import service_account
import gspread
import pendulum
import requests
from trello import Board, List as TrelloList, TrelloClient

from bot_rio.constants import constants


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


def build_status_from_board(board: Board) -> str:
    """
    Builds a status string from a Trello board

    Format:
    <Board name> (semana de <last_monday> a <last_friday>) - snapshot <timestamp>

    ✅ Entregas da semana anterior:
    - <Card in list "Entregas da última semana>
    - <Card in list "Entregas da última semana>

    ▶️ Prioridades da semana atual:
    - <Card in list "Prioridades da semana>
    - <Card in list "Prioridades da semana>

    ⏭️ Tarefas planejadas para o futuro:
    - <Card in list "Backlog">
    - <Card in list "Backlog">

    ⏸️ Bloqueios:
    - <Card in list "Bloqueios">
    - <Card in list "Bloqueios">

    🎯 Metas:
    - <Card in list "Metas">
    - <Card in list "Metas">
    """
    # Assert that all mentioned lists exist and get them
    lists: Dict[str, TrelloList] = {}
    all_lists = board.list_lists()
    for list_name in constants.TRELLO_LISTS.value:
        for trello_list in all_lists:
            if trello_list.name == list_name:
                lists[list_name] = trello_list
                break
        else:
            raise ValueError(
                f"Lista {list_name} não encontrada no quadro {board.name}")
    # Get last monday and friday
    last_monday = get_last_monday().strftime('%d/%m/%Y')
    last_friday = get_last_friday().strftime('%d/%m/%Y')
    # Get snapshot timestamp
    timestamp = pendulum.now(
        tz="America/Sao_Paulo").strftime('%d/%m/%Y %H:%M:%S')
    status = f"**{board.name}** (semana de {last_monday} a {last_friday}) - snapshot {timestamp}\n\n"
    for list_name in constants.TRELLO_LISTS.value:
        status += f"{constants.TRELLO_LISTS_EMOJIS.value[list_name]} {list_name}:\n"
        for card in lists[list_name].list_cards():
            status += f"- {card.name}\n"
        status += "\n"
    return status


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


def get_last_friday() -> datetime:
    """Gets the last friday"""
    last_monday = get_last_monday()
    friday = last_monday + timedelta(days=4)
    return friday


def get_last_monday() -> datetime:
    """Gets the last monday"""
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    if monday == today:
        monday -= timedelta(days=7)
    return monday


def get_trello_board(board_id: str, client: TrelloClient = None) -> Board:
    """Gets a Trello board"""
    if not client:
        client = get_trello_client()
    return client.get_board(board_id)


def get_trello_client() -> TrelloClient:
    """Gets Trello client"""
    return TrelloClient(
        api_key=constants.TRELLO_KEY.value,
        token=constants.TRELLO_TOKEN.value,
    )


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


def parse_reference(reference: str) -> str:
    """Parses a reference for Google Sheets.
    Args:
        reference: The reference to be parsed.
    Returns:
        The parsed reference.

    Input format: [tema]; [subtema]; [link]
    If the reference doesn't follow the format, raise an error.
    Output formats:
        Github:
            TODO.
        Google Sheets:
            [tema, subtema, link]
    """
    if ';' not in reference:
        raise ValueError(
            "A referência deve seguir o formato: [tema]; [subtema]; [link]")
    split = reference.split(';')
    if len(split) != 3:
        raise ValueError(
            "A referência deve seguir o formato: [tema]; [subtema]; [link]")
    theme, subtheme, link = split
    if not theme:
        raise ValueError("A referência deve ter um tema!")
    if not subtheme:
        raise ValueError("A referência deve ter um subtema!")
    if not link:
        raise ValueError("A referência deve ter um link!")
    return [theme, subtheme, link]


def smart_split(
    text: str,
    max_length: int,
    separator: str = " ",
) -> List[str]:
    """
    Splits a string into a list of strings.
    """
    if len(text) <= max_length:
        return [text]

    separator_index = text.rfind(separator, 0, max_length)
    if (separator_index >= max_length) or (separator_index == -1):
        raise ValueError(
            f'Cannot split text "{text}" into {max_length}'
            f'characters using separator "{separator}"'
        )

    return [
        text[:separator_index],
        *smart_split(
            text[separator_index + len(separator):],
            max_length,
            separator,
        ),
    ]
