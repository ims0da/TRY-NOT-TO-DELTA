import discord
from bot import TNTDBot
import logging
from logging.handlers import RotatingFileHandler
import colorlog
import os

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: %(message)s")

console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(name)s: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    reset=True,
    style="%",
)
try:
    file_handler = RotatingFileHandler(filename="logs/tntdlogs.log", encoding="utf-8", mode="w",
                                       maxBytes=20 * 1024 * 1024, backupCount=5)
except FileNotFoundError:
    os.mkdir("logs")
    file_handler = RotatingFileHandler(filename="logs/tntdlogs.log", encoding="utf-8", mode="w",
                                       maxBytes=20 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Token Ados
# TOKEN = "MTExMjc0NDk0MTk0NTM2MDQ3NQ.GCMv80.q9wMnJd1w0ov1oVsGOA06yq1kUHBDTpB3WJAco"

# Token Shiro
# TOKEN = "MTA1MzA4Nzc3MDg5OTM5NDU2MA.GGCLZD.0UYjdfI9-7DsYH-vQWJUjQZMGb99RCOvZYgFIY"

# Token Nupi
TOKEN = "MTExMjkzMjgxNDQ2MDA0NzM2MA.GOSzVA.o_spK1IiNOkp--B4a1HSASMlyaSvOwHyTxwJaY"

intents = discord.Intents.default()
intents.message_content = True

client = TNTDBot(logger, intents=intents)
client.run(TOKEN, log_handler=None)
