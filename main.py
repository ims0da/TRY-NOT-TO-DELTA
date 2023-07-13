import discord
from bot import TNTDBot

# Token Ados
# TOKEN = "MTExMjc0NDk0MTk0NTM2MDQ3NQ.GCMv80.q9wMnJd1w0ov1oVsGOA06yq1kUHBDTpB3WJAco"

# Token Shiro
# TOKEN = "MTA1MzA4Nzc3MDg5OTM5NDU2MA.GGCLZD.0UYjdfI9-7DsYH-vQWJUjQZMGb99RCOvZYgFIY"

# Token Nupi
TOKEN = "MTExMjkzMjgxNDQ2MDA0NzM2MA.GOSzVA.o_spK1IiNOkp--B4a1HSASMlyaSvOwHyTxwJaY"

intents = discord.Intents.default()
intents.message_content = True

client = TNTDBot(intents=intents)
client.run(TOKEN)
