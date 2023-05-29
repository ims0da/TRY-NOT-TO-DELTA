import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')



@bot.command()
async def clear(ctx):
    response = 'Espero que no estés usando basura, enseguida se te asignarán los puntos.'
    await ctx.send(response)

bot.run(TOKEN)