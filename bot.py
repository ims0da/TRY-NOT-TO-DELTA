import os
import discord
from discord.ext import commands
from commands import Commands
from dotenv import load_dotenv
# Leer el token
TOKEN = "DISCORD_TOKEN"

# Cargar los comandos de la clase Commands
# Si es necesario añadir comandos, añadirlos a la clase Commands
# si tienes alguna duda con mi codigo hablame al md y te lo
# explico
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
commands = Commands(bot)  

bot.run(TOKEN)
