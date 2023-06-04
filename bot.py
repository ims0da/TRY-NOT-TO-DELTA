import discord
from discord.ext import commands
from commands import Commands
from dotenv import load_dotenv
import os
from commands7k import Commands7k
from commandset import Commandset
# Leer el token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

commands = Commands(bot)
commands7k_instance = Commands7k(bot)
commandset_instance = Commandset(bot)

bot.run(TOKEN)
