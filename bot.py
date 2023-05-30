import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from commands import Commands

# Leer el token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
commands = Commands(bot)  # Cargar los comandos de la clase Commands
# Si es necesario añadir comandos, añadirlos a la clase Commands
# si tienes alguna duda con mi codigo hablame al md y te lo
# explico

bot.run(TOKEN)
