import discord
from dotenv import load_dotenv
from bot import TNTDBot
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = TNTDBot(intents=intents)
client.run(TOKEN)
