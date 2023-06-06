import discord
import psycopg2
import requests
from tabulate import tabulate
import math
import asyncio
from constants import *
from PIL import Image
from io import BytesIO
import json

ayuda_comandos = {
    "/players": "Muestra la leaderboard con los puntos actuales, también esta /playerset para etterna y /players7k para 7k. ENGLISH: Shows players, pretty self explanatory",
    "/tabla": "Muestra la base de datos de mapas con el link del mapa, el nombre, la diff name, el mod y el clear, también esta /tablaet para etterna y /tabla7k para 7k. ENGLISH: Shows current maps in the database.",
    "/clear": "Has hecho un clear a un mapa y requieres de tus puntos",
    "/ayuda": "Muestra este comando ENGLISH: Shows this command.",
    "/requestmap": "Requestea un mapa o pack el cual debe ser aprobado por playtesters. /requestmap para 4k, /requestmapet para etterna y /requestmap7k para 7k ENGLISH: Request a map."
}


def crear_jugador_mapas_jugados(player: str):
    with open("mapas_jugados_4k.json", "r") as raw_data:
        map_data = json.load(raw_data)

    with open("mapas_jugados_4k.json", "w") as raw_data:
        map_data[player] = []
        json.dump(map_data, raw_data, indent=4)


def escribir_mapas_jugados(player: str, map_id: int):
    with open("mapas_jugados_4k.json", "r") as raw_data:
        data = json.load(raw_data)
        data_list = data[player]
        data_list.append(map_id)

    with open("mapas_jugados_4k.json", "w") as raw_data:
        json.dump(data, raw_data, indent=4)


def leer_mapas_jugados(player):
    with open("mapas_jugados_4k.json", "r") as raw_data:
        data = json.load(raw_data)
        player_map_data = data[player]
        return player_map_data


class Commands:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.conn = None
        self.start_commands()

    def start_db_connection(self):
        """Inicializa la conexión a la base de datos"""
        self.conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="TRY_NOT_TO_DELTA",
            user="postgres",
            password="admin"
        )

    # Consulta a base de datos
    def query(self, string: str, *args):
        # Iniciar conexión a base de datos
        self.start_db_connection()

        # Crear una consulta SQL para seleccionar toda la tabla
        cursor = self.conn.cursor()
        cursor.execute(string, args)
        results = cursor.fetchall()

        # Cerrar el cursor y la conexión
        cursor.close()
        self.conn.close()

        # Devolver el resultado
        return results

    def insert(self, string: str, *args):  # <- este es lo mismo que el metodo query de arriba, solo que cuando quieres insertar, modificar o eliminar, no puedes hacer un fetch.
        self.start_db_connection()  # <- por eso no hay un return, porque no hay nada que devolver, solo se ejecuta la consulta y ya, es digamos "interno"

        cursor = self.conn.cursor()
        print(string, args)
        cursor.execute(string, args)

        # Si la consulta es una operación de modificación (como INSERT, UPDATE o DELETE),
        # puedes realizar un commit en la conexión
        self.conn.commit()

        cursor.close()
        self.conn.close()

    def start_commands(self):
        """Inicializa los comandos"""
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user.name} has connected to Discord!')
            try:
                print("Sincronizando comandos...")
                synced = await self.bot.tree.sync()
                print(f"Synced {len(synced)} command(s)")
            except Exception as e:
                print(e)

        @self.bot.event
        async def on_member_join(member):  # No se si funciona porque discord es un mierdolo y me ha dicho q he excedido el numero maximo de requests a mi bot :D
            channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

            msg = (
                f'Bienvenido/a {member.mention} a TRY NOT TO DELTA! '
                f'Esperemos que te lo pases bien por aquí!'
            )

            await channel.send(msg)

        @self.bot.tree.command(name="clear")
        async def clear(interaction: discord.Interaction, player: str, table_map_id: int):
            msg = (
                'Espero que no estés usando basura, enseguida se te asignarán los puntos.\n'
                '(Cualquier uso malicioso de este comando será castigado)'
                )
            await interaction.response.send_message(msg, ephemeral=True)

            # Detectar si el jugador esta dentro del archivo .json si no lo está añadirlo
            try:
                played_map_data = leer_mapas_jugados(player)
            except KeyError:
                crear_jugador_mapas_jugados(player)
                played_map_data = leer_mapas_jugados(player)

            if table_map_id in played_map_data:
                await interaction.followup.send("Ya has jugado ese mapa.")
            else:

                try:
                    escribir_mapas_jugados(player, table_map_id)
                    player_points = self.query(f"SELECT puntos FROM public.players WHERE nombre = '{player}';")
                    player_points = player_points[0][0]
                    map_points = self.query(f"SELECT puntos FROM public.tntd WHERE id = '{table_map_id}';")
                    map_points = map_points[0][0]
                    final_points = int(player_points) + int(map_points)
                except IndexError:
                    await interaction.followup.send(
                        "No se ha encontrado ese jugador. Pidele a un admin que lo agregue.",
                        ephemeral=True
                    )

                else:
                    self.insert(f"UPDATE public.players SET puntos = %s WHERE nombre = %s;", final_points, player)

                    msg = (
                        f"Jugador: {player}, Puntos: {final_points}"
                    )
                    embed = discord.Embed(
                        title="Puntos actualizados",
                        description=f"```{msg}```"
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)

                    channel = self.bot.get_channel(LOG_CLEAR_CHANNEL_ID)
                    msg = (f"Usuario: {interaction.user.name}\n"
                           "Comando utilizado: /clear (Tabla 4K)\n"
                           f"Parámetros:\n"
                           f"Player: {player}, Map_ID: {table_map_id}, Puntos sumados: {map_points}")
                    embed_msg = discord.Embed(
                        title="Comando clear ejecutado",
                        description=f"```{msg}```",
                        color=discord.Color.blue()
                    )

                    await channel.send(embed=embed_msg)

        @self.bot.tree.command(name="tabla")
        async def tabla(interaction: discord.Interaction):
            results = self.query("SELECT * FROM public.tntd ORDER BY id")
            
            # Obtener los encabezados de las columnas de la tabla
            # Crear una lista de filas para la tabla
            table_rows = []
            for row in results:
                table_rows.append(row)

            num_pages = math.ceil(len(table_rows) / ROWS_PER_PAGE)

            embed_list = []
            for page_num in range(num_pages):
                start_index = page_num * ROWS_PER_PAGE
                end_index = start_index + ROWS_PER_PAGE
                page_rows = table_rows[start_index:end_index]

                page_embed = discord.Embed(
                    title=f"Tabla de 4k (Página {page_num + 1}/{num_pages})"
                )
                
                for row in page_rows:
                    page_embed.add_field(name=f"Mapa {row[0]}: ", value=f"[{row[1]} - {row[4]}]({row[3]})", inline=True)
                    page_embed.add_field(name="Puntos: ", value=f"{row[2]}", inline=True)
                    page_embed.add_field(name="Requirement: ", value=f"{row[5]}, {row[6]}", inline=True)
                embed_list.append(page_embed)

            index = 0
            message = await interaction.response.send_message(embed=embed_list[index])
            canal = interaction.channel_id

            message_history = self.bot.get_channel(canal).history(limit=1)
            last_message = message_history.ag_frame.f_locals.get('self').last_message

            await last_message.add_reaction('⬅️')
            await last_message.add_reaction('➡️')

            def check(reaction, user):
                return user == interaction.user and str(reaction.emoji) in ['⬅️', '➡️']

            while True:
                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                    if str(reaction.emoji) == '⬅️':
                        index -= 1
                        if index < 0:
                            index = len(embed_list) - 1
                    elif str(reaction.emoji) == '➡️':
                        index += 1
                        if index >= len(embed_list):
                            index = 0

                    await last_message.edit(embed=embed_list[index])
                    await last_message.remove_reaction(reaction, interaction.user)
                except asyncio.TimeoutError:
                    break

        @self.bot.tree.command(name="players")
        async def players(interaction: discord.Interaction):
            results = self.query("SELECT NOMBRE, PUNTOS FROM public.players WHERE PUNTOS != '0'")
            # Ordenar los resultados de mayor a menor puntos
            sorted_results = sorted(
                results,
                key=lambda row: row[1],
                reverse=True
                )
            headers = ['Nombre', 'Puntos']
            formatted_player_list = (
                tabulate(sorted_results, headers, tablefmt='pipe')
                )
            embed = discord.Embed(
                title="Lista de jugadores de 4k.",
                description=f'```\n{formatted_player_list}\n```',
                color=discord.Color.blue()
                )
            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, nombre:str, puntos:int, link:str, diff:str, mods:str, clear:str):
            channel = self.bot.get_channel(ID_CANAL_VALIDACION_4K)

            message_content = f"Nombre: {nombre}\nPuntos: {puntos}\nLink: {link}\nDiff: {diff}\nMods: {mods}\nClear: {clear}"
            await channel.send(message_content)

            embed = discord.Embed(
                            title="Tu mapa ha sido enviado a la cola de validación",
                            description="Se paciente, que no se cobra por esto :moyai:",
                            color=discord.Color.green()
                            )
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
            
        @self.bot.event
        async def on_raw_reaction_add(payload):
            if payload.channel_id == CANAL_ID_4K:
                await handle_reaction_command_4k(payload)
            elif payload.channel_id == CANAL_ID_7K:
                await handle_reaction_command_7k(payload)
            elif payload.channel_id == CANAL_ID_ET:
                await handle_reaction_command_et(payload)

        async def handle_reaction_command_4k(payload):
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            content = message.content.split("\n")
            nombre = content[0].split(": ")[1].replace("'","")
            puntos = int(content[1].split(": ")[1])
            link = content[2].split(": ")[1]
            diff = content[3].split(": ")[1].replace("'","")
            mods = content[4].split(": ")[1]
            clear = content[5].split(": ")[1]

            self.start_db_connection()
            self.insert("INSERT INTO public.tntd (nombre, puntos, link, diff, mods, clear) VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(nombre, puntos, link, diff, mods, clear))

            await message.delete()
            output_channel = self.bot.get_channel(OUTPUT_CHANNEL_4K_ID)
            await output_channel.send(f"Se ha rankeado el mapa de 4k **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

        async def handle_reaction_command_7k(payload):
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            content = message.content.split("\n")
            nombre = content[0].split(": ")[1].replace("'","")
            puntos = int(content[1].split(": ")[1])
            link = content[2].split(": ")[1]
            diff = content[3].split(": ")[1].replace("'","")
            mods = content[4].split(": ")[1]
            clear = content[5].split(": ")[1]

            self.start_db_connection()
            self.insert("INSERT INTO public.tntd7k (nombre, puntos, link, diff, mods, clear) VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(nombre, puntos, link, diff, mods, clear))

            await message.delete()
            output_channel = self.bot.get_channel(OUTPUT_CHANNEL_7K_ID)
            await output_channel.send(f"Se ha rankeado el mapa  de 7k **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

        async def handle_reaction_command_et(payload):
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            content = message.content.split("\n")
            nombre = content[0].split(": ")[1].replace("'","")
            puntos = int(content[1].split(": ")[1])
            link = content[2].split(": ")[1]
            diff = content[3].split(": ")[1].replace("'","")
            mods = content[4].split(": ")[1]
            clear = content[5].split(": ")[1]

            self.start_db_connection()
            self.insert("INSERT INTO public.tntdet (nombre, puntos, link, diff, mods, clear) VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(nombre, puntos, link, diff, mods, clear))

            await message.delete()
            output_channel = self.bot.get_channel(OUTPUT_CHANNEL_ET_ID)
            await output_channel.send(f"Se ha rankeado el mapa de etterna **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

        @self.bot.tree.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            img_url = 'https://media.discordapp.net/attachments/851840942675722303/1115056731354038382/image.jpg'
            response = requests.get(img_url)
            image = Image.open(BytesIO(response.content))
            image.save("image.jpg")
            file = discord.File("image.jpg")
            msg = '\n'.join([f"{key}: {value}" for key, value in ayuda_comandos.items()])
            await interaction.response.send_message(content=msg, file=file)
