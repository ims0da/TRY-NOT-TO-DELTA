import discord
from discord.ext import commands
from commands import Commands
from dotenv import load_dotenv
import os
from commands7k import Commands7k
# Leer el token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Cargar los comandos de la clase Commands
# Si es necesario añadir comandos, añadirlos a la clase Commands
# si tienes alguna duda con mi codigo hablame al md y te lo
# explico
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
commands = Commands(bot)
commands7k_instance = Commands7k(bot)

bot.run(TOKEN)