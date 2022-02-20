__all__ = ["bot"]

from discord.ext import commands
from discord.ext.commands.context import Context
from googlesearch import search
from loguru import logger

from bot_rio.constants import constants
from bot_rio.utils import (
    add_line_to_spreadsheet,
    parse_idea
)

bot = commands.Bot(command_prefix=constants.COMMAND_PREFIX.value)


@bot.event
async def on_ready():
    logger.info(f'{bot.user} tá on!!!')


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
