import discord
from discord.ext import commands
from commandset import Commandset as Commands
from dotenv import load_dotenv
import os
# Leer el token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Cargar los comandos de la clase Commands
commands = Commands(bot=bot)

bot.run(TOKEN)
