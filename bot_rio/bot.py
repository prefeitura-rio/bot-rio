__all__ = ["bot"]

import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from loguru import logger

from bot_rio.constants import constants
from bot_rio.utils import add_line_to_spreadsheet

bot = commands.Bot(command_prefix=constants.COMMAND_PREFIX.value)


@bot.event
async def on_ready():
    logger.info(f'{bot.user} tá on!!!')


@bot.command(name='ideia', help='Cataloga uma ideia na planilha!')
async def ideia(ctx: Context):

    # Check if the idea is in the correct channel
    if str(ctx.channel.id) != constants.IDEA_CHANNEL.value:
        await ctx.send("🙃 Esse comando não deve ser usado nesse canal!")
        return

    # Get the idea
    idea = ctx.message.content[len(
        constants.COMMAND_PREFIX.value) + 1 + len('ideia'):]
    logger.info(f"Ideia: {idea}")

    # Create the issue
    try:
        add_line_to_spreadsheet(
            constants.IDEA_SPREADSHEET_ID.value,
            [idea],
            worksheet_name="Lista de ideias",
        )
        await ctx.send(f"🚀 Ideia registrada com sucesso!")
    except Exception as e:
        logger.error(e)
        await ctx.send(f"🥲 Não foi possível criar a issue! Erro: {e}")
        return
