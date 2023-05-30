import os
import discord
from discord.ext import commands
from commands import Commands

# Leer el token
TOKEN = "MTExMzE0NDMzNzU0MzQ3MTE5Ng.Gwo5Uz.LNIOu1JjPCxhyXja8f0cppZ6Wz6-K7y8dJ0GqU"

# Cargar los comandos de la clase Commands
# Si es necesario añadir comandos, añadirlos a la clase Commands
# si tienes alguna duda con mi codigo hablame al md y te lo
# explico
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
commands = Commands(bot)  

bot.run(TOKEN)
