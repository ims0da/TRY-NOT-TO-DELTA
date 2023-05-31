import discord
from discord.ext import commands
from commands import Commands
# from dotenv import load_dotenv
import os
# Leer el token
# load_dotenv()
# TOKEN = os.getenv("DISCORD_TOKEN")

# Cargar los comandos de la clase Commands
# Si es necesario añadir comandos, añadirlos a la clase Commands
# si tienes alguna duda con mi codigo hablame al md y te lo
# explico
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
commands = Commands(bot)

bot.run("MTA1MzA4Nzc3MDg5OTM5NDU2MA.GKDSo8.fTHsIpKreRU1O2C7ptb1weslPMTgwSk9mEr5tk")
