import os
import discord
import psycopg2
from discord.ext import commands
from dotenv import load_dotenv








#leer el token
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






@bot.command()
async def TABLA(ctx):
    # Establecer la conexión a la base de datos
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="TRY_NOT_TO_DELTA",
        user="postgres",
        password="admin"
    )

    # Crear una consulta SQL para seleccionar toda la tabla
    cursor = conn.cursor()
    query = "SELECT * FROM public.tntd"
    cursor.execute(query)
    results = cursor.fetchall()

    # Cerrar el cursor y la conexión
    cursor.close()
    conn.close()

    # Dividir los resultados en dos partes
    half = len(results) // 2
    first_half = results[:half]
    second_half = results[half:]

    # Crear la descripción del primer mensaje
    first_half_table = "\n".join([f"{row}" for row in first_half])

    # Crear el primer mensaje
    first_response = discord.Embed(
        title="Tabla (Parte 1)",
        description=first_half_table
    )

    # Crear la descripción del segundo mensaje
    second_half_table = "\n".join([f"{row}" for row in second_half])

    # Crear el segundo mensaje
    second_response = discord.Embed(
        title="Tabla (Parte 2)",
        description=second_half_table
    )

    # Enviar los mensajes en Discord
    await ctx.send(embed=first_response)
    await ctx.send(embed=second_response)













bot.run(TOKEN)