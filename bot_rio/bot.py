__all__ = ["bot"]

from typing import List

import discord
from discord import Member, Message, TextChannel
from discord.ext import commands
from discord.ext.commands.context import Context
from googlesearch import search
from loguru import logger
import openai
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
openai.api_key = constants.OPENAI_API_KEY.value

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


@bot.event
async def on_message(message: Message):
    if bot.user.mentioned_in(message):
        # React to the message adding the waiting emoji
        await message.add_reaction("⏳")
        # Get prompt from the message
        prompt = message.content.replace(f"<@{bot.user.id}>", "")
        # Get the response from OpenAI
        response = openai.Completion.create(
            prompt=prompt,
            temperature=0,
            max_tokens=300,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            model=constants.COMPLETIONS_MODEL.value,
        )["choices"][0]["text"].strip(" \n")
        # Remove the waiting emoji and add the OK emoji
        await message.remove_reaction("⏳", bot.user)
        await message.add_reaction("✅")
        # Send the response
        await message.channel.send(response)

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
async def status(ctx: Context):

    # Check if the command is in the correct channel
    if str(ctx.channel.id) != constants.STATUS_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    # React with a loading emoji
    await ctx.message.add_reaction("🔍")

    try:
        # Get query from the message
        query: str = ctx.message.content[len(
            constants.COMMAND_PREFIX.value) + 1 + len('status'):].strip()
        logger.info(f"Query: {query}")
        # Assert that query is not empty, has only one word and is a valid input
        if query == "":
            # TODO: When implementing more projects, change this.
            query = "infra"
        elif len(query.split()) > 1:
            await ctx.send("🙃 Você só pode pedir status de uma área por vez!")
            return
        elif query not in ["infra", "estudio", "parcerias", "formação"]:
            message = "🙃 Você só pode pedir status de uma das seguintes áreas: \n\n"
            message += "• infra\n"
            message += "• estudio\n"
            message += "• parcerias\n"
            message += "• formação\n\n"
            message += "Basta digitar `!status [área]`"
            await ctx.send(message, mention_author=True)
            return
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível compreender seu pedido! Erro: {e}")
        return

    try:
        # Get Trello client
        client = get_trello_client()
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível conectar ao Trello! Erro: {e}")
        return

    try:
        # Get the board we want
        if query == "infra":
            board = client.get_board(constants.TRELLO_STATUS_BOARD_INFRA.value)
        else:
            await ctx.send("🙃 Ainda não temos status para essa área!")
            return
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível acessar o board com ID {constants.TRELLO_STATUS_BOARD_INFRA.value}! Erro: {e}")
        return

    # Build the status text
    try:
        status_text = build_status_from_board(board)
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível gerar o status do board {board.name}! Erro: {e}")
        return

    try:
        # Send the status texts
        for split in smart_split(status_text, max_length=2000, separator="\n"):
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


@bot.command(
    name='link_tabela',
    help='🔗 Cria um link para uma tabela do BigQuery'
)
async def link_tabela(ctx: Context):

    try:
        # Get information from the message.
        # Accepted formats:
        # - <project>.<dataset>.<table>
        # - <project> <dataset>.<table>
        # - <project> <dataset> <table>

        # Get the message content
        message_content: str = ctx.message.content[len(
            constants.COMMAND_PREFIX.value) + 1 + len('link_tabela'):].strip()

        if message_content == "":
            await ctx.send("🙃 Você deve fornecer o caminho da tabela!")
            return

        # Split the message content both by spaces and dots
        message_content = message_content.replace(".", " ")
        message_content = message_content.split(" ")

        # Check if the message content has the correct length
        if len(message_content) != 3:
            await ctx.send("🙃 O caminho da tabela deve ter 3 partes: <project> <dataset> <table>!")
            return

        # Get the project, dataset and table
        project: str = message_content[0]
        dataset: str = message_content[1]
        table: str = message_content[2]

        # Build the link
        link: str = "https://console.cloud.google.com/bigquery?" + \
            f"p={project}&d={dataset}&t={table}&page=table"

        # Send the link
        await ctx.send(f"🔗 {link}", mention_author=True)

    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível gerar o link! Erro: {e}")
        return
