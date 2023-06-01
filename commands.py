import discord
import sqlite3
from tabulate import tabulate
import math
import asyncio

ayuda_comandos = {
    "/players": "Muestra la leaderboard con los puntos actuales.",
    "/tabla": "Muestra la base de datos de mapas con el link del mapa, el nombre, la diff name, el mod y el clear.",
    "/clear": "Has hecho un clear a un mapa y requieres de tus puntos",
    "/ayuda": "Muestra este comando",
    "/requestmap": "Pide un mapa para que sea añadido a la base de datos, te pedirá el link del mapa, el nombre, la diff name, el mod y el clear.",
}

class Commands:
    def __init__(self, bot) -> None:
        self.bot = bot
        self.conn = None
        self.start_commands()

    def start_db_connection(self):
        """Inicializa la conexión a la base de datos"""
        self.conn = sqlite3.connect("database/db.sqlite")



    # Consulta a base de datos
    def query(self, string: str):
        # Iniciar conexión a base de datos
        self.start_db_connection()

        # Crear una consulta SQL para seleccionar toda la tabla
        cursor = self.conn.cursor()
        cursor.execute(string)
        results = cursor.fetchall()

        # Cerrar el cursor y la conexión
        cursor.close()
        self.conn.close()

        # Devolver el resultado
        return results


    def insert(self, string: str): # <- este es lo mismo que el metodo query de arriba, solo que cuando quieres insertar, modificar o eliminar, no puedes hacer un fetch.
        self.start_db_connection() # <- por eso no hay un return, porque no hay nada que devolver, solo se ejecuta la consulta y ya, es digamos "interno"

        cursor = self.conn.cursor()
        cursor.execute(string)

        # Si la consulta es una operación de modificación (como INSERT, UPDATE o DELETE),
        # puedes realizar un commit en la conexión
        self.conn.commit()

        cursor.close()
        self.conn.close()


    def get_players(self):
        return self.query("""
                    SELECT user_name, sum(map.points) total_points
                    FROM
                     PLAYERS
                     LEFT JOIN ACHIEVEMENT ON ACHIEVEMENT.player_id = PLAYERS.discord_id
                     LEFT JOIN MAP ON ACHIEVEMENT.map_hash = MAP.map_hash

                    GROUP BY user_name
                    """)

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
            welcome_chann_id = 1112809557396299777
            welcome_chann = self.bot.get_channel(welcome_chann_id)

            msg = (
                f'Bienvenido/a {member.mention} a TRY NOT TO DELTA! '
                f'Esperemos que te lo pases bien por aquí!'
            )

            await welcome_chann.send(msg)

        @self.bot.tree.command(name="clear")
        async def clear(interaction: discord.Interaction):
            msg = (
                'Espero que no estés usando basura, '
                'enseguida se te asignarán los puntos.'
            )

            await interaction.response.send_message(msg, ephemeral=True)

        @self.bot.tree.command(name="tabla")
        async def tabla(interaction: discord.Interaction):

            results = self.query("SELECT * FROM public.tntd ORDER BY id")

            # Obtener los encabezados de las columnas de la tabla
            # Crear una lista de filas para la tabla
            table_rows = []
            for row in results:
                table_rows.append(row)

            rows_per_page = 8 # Número de filas por página
            num_pages = math.ceil(len(table_rows) / rows_per_page)


            embed_list = []
            for page_num in range(num_pages):
                start_index = page_num * rows_per_page
                end_index = start_index + rows_per_page
                page_rows = table_rows[start_index:end_index]

                page_embed = discord.Embed(
                title=f"Tabla (Página {page_num + 1}/{num_pages})"
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
            # Hacer consulta SQL
            results = self.get_players()

            # Ordenar los resultados de mayor a menor puntos
            sorted_results = sorted(
                results,
                key=lambda row: row[1],
                reverse=True
                )

            # Crear headers de la tabla
            headers = ['Nombre', 'Puntos']

            # Crear la lista en forma de tabla
            formatted_player_list = (
                tabulate(sorted_results, headers, tablefmt='pipe')
                )

            # Formatear los resultados como un mensaje de Discord
            embed = discord.Embed(
                title="Lista de jugadores",
                description=f'```\n{formatted_player_list}\n```',
                color=discord.Color.blue()
                )

            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, nombre:str, puntos:int, link:str, diff:str, mods:str, clear:str):
            id_canal_validacion = 1113157312723550339
            channel = self.bot.get_channel(id_canal_validacion)

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
            canal_id = 1113157312723550339
            output_channel_id = 1113929255517171742
            if payload.channel_id == canal_id:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                content = message.content.split("\n")
                nombre = content[0].split(": ")[1].replace("'", "")
                puntos = int(content[1].split(": ")[1])
                link = content[2].split(": ")[1]
                diff = content[3].split(": ")[1].replace("'", "")
                mods = content[4].split(": ")[1]
                clear = content[5].split(": ")[1]

                self.insert("INSERT INTO public.tntd (nombre, puntos, link, diff, mods, clear) VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(nombre, puntos, link, diff, mods, clear))

                await message.delete()
                output_channel = self.bot.get_channel(output_channel_id)
                await output_channel.send(f"Se ha rankeado el mapa **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

        @self.bot.tree.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            # Ruta de la imagen que quieres enviar
            image_path = 'C:/Users/Alejandro/Desktop/BOT_DISCORD/IMG_20230309_161106.jpg'

            # Cargar la imagen como un objeto de archivo discord.File
            file = discord.File(image_path, filename='IMG_20230309_161106.jpg')

            # Mensaje con el contenido de ayuda
            msg = '\n'.join([f"{key}: {value}" for key, value in ayuda_comandos.items()])

            # Enviar el mensaje con la imagen adjunta
            await interaction.response.send_message(content=msg, file=file)

        @self.bot.tree.command(name="register")
        async def register(interaction: discord.Interaction):
            self.insert(f"""
            INSERT OR IGNORE INTO PLAYERS (discord_id,user_name)
            VALUES ({interaction.user.id},'{interaction.user.display_name}');
            """)
            await interaction.response.send_message("User successfully registered!", ephemeral=True)
