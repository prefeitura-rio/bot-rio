__all__ = ["bot"]

from typing import List

import discord
from discord import Member, TextChannel
from discord.ext import commands
from discord.ext.commands.context import Context
from googlesearch import search
from loguru import logger
from trello import Board

from bot_rio.constants import constants
from bot_rio.utils import (
    add_line_to_spreadsheet,
    build_status_from_board,
    build_status_from_sheet,
    get_trello_client,
    parse_idea,
    parse_reference,
    smart_split,
)

bot = commands.Bot(command_prefix=constants.COMMAND_PREFIX.value)

#########################
#
# Event Handlers
#
#########################


@bot.event
async def on_ready():
    logger.info(f'{bot.user} tá on!!!')


@bot.event
async def on_member_join(member: Member):
    channel: TextChannel = bot.get_channel(constants.GERAL_CHANNEL.value)
    embed = discord.Embed(
        title="Alô, alô, alô!",
        description=(f"Olá {member.display_name}, seja bem-vindo(a)! :smile:\n"
                     "Sinta-se livre para se apresentar em #apresente-se-aqui! Nos vemos por aí! :emd:"
                     ),
    )
    await channel.send(embed=embed)

#########################
#
# Commands
#
#########################


@bot.command(
    name='ideia',
    help='💡 Cataloga uma ideia na planilha. O formato deve ser [nome/desc.]; [responsável]; [org.]; [tags]'
)
async def ideia(ctx: Context):

    # Check if the idea is in the correct channel
    if str(ctx.channel.id) != constants.IDEA_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    try:
        # Get the idea
        idea = parse_idea(
            ctx.message.content[len(
                constants.COMMAND_PREFIX.value) + 1 + len('ideia'):],
            mode="gspread",
        )
        logger.info(f"Ideia: {idea}")

        # Add it to the spreadsheet
        add_line_to_spreadsheet(
            constants.IDEA_SPREADSHEET_ID.value,
            idea,
            worksheet_name="Lista de ideias",
        )
        await ctx.send(
            f"🚀 Ideia registrada com sucesso!\n\n* Nome: {idea[0]}\n* Responsável: {idea[1]}\n* Órgão: {idea[2]}\n* Temas: {idea[3]}"
        )
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível catalogar a ideia! Erro: {e}")
        return

# https://discord.com/channels/891689044889698404/1006603086883721327


@bot.command(
    name='ref',
    help='📋 Cataloga uma referência na planilha. O formato deve ser [tema]; [subtema]; [link]'
)
async def ref(ctx: Context):

    # Check if the idea is in the correct channel
    if str(ctx.channel.id) != constants.REFERENCES_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    try:
        # Get the idea
        reference = parse_reference(
            ctx.message.content[len(
                constants.COMMAND_PREFIX.value) + 1 + len('ref'):],
        )
        logger.info(f"Referência: {reference}")

        # Add it to the spreadsheet
        add_line_to_spreadsheet(
            constants.REFERENCES_SPREADSHEET_ID.value,
            reference,
            worksheet_name="Referencias",
        )
        await ctx.send(
            f"🚀 Referência registrada com sucesso!\n\n* Tema: {reference[0]}\n* Subtema: {reference[1]}\n* Link: {reference[2]}"
        )
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível catalogar a ideia! Erro: {e}")
        return


@bot.command(
    name='ajuda',
    help='🤓 Procura por ajuda de programação no StackOverflow'
)
async def ajuda(ctx: Context):

    # Check if the command has been executed in one of the allowed channels
    if str(ctx.channel.id) not in constants.LANGUAGES_CHANNELS.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    try:
        # Get the query from the message
        query: str = ctx.message.content[len(
            constants.COMMAND_PREFIX.value) + 1 + len('ajuda'):].strip()
        if query == "":
            await ctx.send("🙃 Você deve fornecer uma consulta!")
            return
        logger.info(f"Query: {query}")

        # Search for the query on Google, including StackOverflow
        await ctx.send("🔍 Buscando...")
        for url in search(f"{query} site:stackoverflow.com", tld="com", num=5, stop=5, pause=2):
            if "stackoverflow.com" in url:
                await ctx.send(f"🔗 {url}\n\nEspero que ajude!", mention_author=True)
                return
        await ctx.send("🙃 Não encontrei nada com o que me passou! "
                       "Tente reduzir o número de palavras ou usar outros termos!",
                       mention_author=True)

    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível encontrar ajuda! Erro: {e}")
        return


@bot.command(
    name='status',
    help='🎯 Lista os status dos projetos do Escritório de Dados'
)
async def ajuda(ctx: Context):

    # Check if the command is in the correct channel
    if str(ctx.channel.id) != constants.STATUS_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    # React with a loading emoji
    await ctx.message.add_reaction("🔍")

    try:
        # Get Trello client
        client = get_trello_client()
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível conectar ao Trello! Erro: {e}")
        return

    # Get the boards we want
    boards: List[Board] = []
    for board_id in constants.TRELLO_STATUS_BOARD_IDS.value:
        try:
            boards.append(client.get_board(board_id))
        except Exception as e:
            logger.error(e)
            await ctx.send(f"🥲 Não foi possível acessar o board com ID {board_id}! Erro: {e}")
            return

    # For each board, build the status text
    status_text = []
    for board in boards:
        try:
            status_text.append(build_status_from_board(board))
        except Exception as e:
            logger.error(e)
            await ctx.send(f"🥲 Não foi possível gerar o status do board {board.name}! Erro: {e}")
            return

    try:
        # Send the status texts
        for text in status_text:
            for split in smart_split(text, max_length=2000, separator="\n"):
                await ctx.send(split)
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível enviar o texto de status! Erro: {e}")
        return


@bot.command(
    name='status_bases',
    help='🎯 Lista os status das bases de dados'
)
async def status_bases(ctx: Context):
    # Check if the command is in the correct channel
    if str(ctx.channel.id) != constants.STATUS_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    # React with a loading emoji
    await ctx.message.add_reaction("🔍")

    try:
        status_text = build_status_from_sheet(
            constants.BASES_SPREADSHEET_ID.value, constants.BASES_SHEET_NAME.value)
        for split in smart_split(status_text, max_length=2000, separator="\n\n"):
            await ctx.send(split)
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível enviar o texto de status! Erro: {e}")
        return
