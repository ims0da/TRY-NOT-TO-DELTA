import discord
import psycopg2
from funciones_tablas import tabla_embed, crear_tabla_players
import asyncio

ayuda_comandos = {
    "/players": "Muestra la leaderboard con los puntos actuales.",
    "/tabla": "Muestra la base de datos de mapas con el link del mapa, "
              "el nombre, la diff name, el mod y el clear.",
    "/clear": "Has hecho un clear a un mapa y requieres de tus puntos",
    "/ayuda": "Muestra este comando",
    "/requestmap": "Requestea un mapa"
}


class Commands:
    WELCOME_CHANNEL_ID = 1112809557396299777
    VALIDACION_CHANNEL_ID = 1113157312723550339
    VALIDAR_MAPAS_CHANNEL_ID = 1113157312723550339
    MAPAS_RANKEADOS_CHANNEL_ID = 1113929255517171742

    def __init__(self, bot) -> None:
        self.bot = bot
        self.conn = None

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
    def query(self, string: str):
        self.start_db_connection()

        cursor = self.conn.cursor()
        cursor.execute(string)
        results = cursor.fetchall()

        cursor.close()
        self.conn.close()

        return results

    def insert(self, string: str):  # <- este es lo mismo que el metodo query
        # de arriba, solo que cuando quieres insertar, modificar o eliminar, no
        # puedes hacer un fetch.
        self.start_db_connection()  # <- por eso no hay un return, porque no
        # hay nada que devolver, solo se ejecuta la consulta y ya, es "interno"

        cursor = self.conn.cursor()
        cursor.execute(string)

        # Si la consulta es una operación de modificación
        # (como INSERT, UPDATE o DELETE),
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
        async def on_member_join(member):
            channel = self.bot.get_channel(self.WELCOME_CHANNEL_ID)
            msg = (
                f'Bienvenido/a {member.mention} a TRY NOT TO DELTA! '
                f'Esperemos que te lo pases bien por aquí!'
            )
            await channel.send(msg)

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

            embed_page_list = tabla_embed(results)

            index = 0
            await interaction.response.send_message(
                embed=embed_page_list[index]
                )
            canal = interaction.channel_id

            message_history = self.bot.get_channel(canal).history(limit=1)
            last_message = (
                message_history.ag_frame.f_locals.get('self').last_message
                )

            await last_message.add_reaction('⬅️')
            await last_message.add_reaction('➡️')

            def check(reaction, user):
                return user == (
                    interaction.user and str(reaction.emoji) in ['⬅️', '➡️']
                    )

            while True:
                try:
                    reaction, _ = await self.bot.wait_for(
                        'reaction_add',
                        timeout=60.0,
                        check=check
                        )

                    if str(reaction.emoji) == '⬅️':
                        index -= 1
                        if index < 0:
                            index = len(embed_page_list) - 1
                    elif str(reaction.emoji) == '➡️':
                        index += 1
                        if index >= len(embed_page_list):
                            index = 0

                    await last_message.edit(embed=embed_page_list[index])
                    await last_message.remove_reaction(reaction,
                                                       interaction.user)
                except asyncio.TimeoutError:
                    break

        @self.bot.tree.command(name="players")
        async def players(interaction: discord.Interaction):
            results = self.query(
                "SELECT NOMBRE, PUNTOS FROM public.players WHERE PUNTOS != '0'"
                )

            players = crear_tabla_players(results)
            embed = discord.Embed(
                title="Lista de jugadores",
                description=f'```\n{players}\n```',
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction,
                             nombre: str, puntos: int, link: str,
                             diff: str, mods: str, clear: str):
            channel = self.bot.get_channel(self.VALIDACION_CHANNEL_ID)
            message_content = (
                f"Nombre: {nombre}\n"
                f"Puntos: {puntos}\n"
                f"Link: {link}\n"
                f"Diff: {diff}\n"
                f"Mods: {mods}\n"
                f"Clear: {clear}"
                )
            await channel.send(message_content)
            embed = (
                discord.Embed(
                    title="Tu mapa ha sido enviado a la cola de validación",
                    description="Se paciente, "
                                "que no se cobra por esto :moyai:",
                    color=discord.Color.green()
                    )
            )
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)

        @self.bot.event
        async def on_raw_reaction_add(payload):
            if payload.channel_id == self.VALIDAR_MAPAS_CHANNEL_ID:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                content = message.content.split("\n")
                nombre = content[0].split(": ")[1]
                puntos = int(content[1].split(": ")[1])
                link = content[2].split(": ")[1]
                diff = content[3].split(": ")[1]
                mods = content[4].split(": ")[1]
                clear = content[5].split(": ")[1]

                self.start_db_connection()
                self.insert(
                            "INSERT INTO public.tntd "
                            "(nombre, puntos, link, diff, mods, clear) "
                            "VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(
                                nombre, puntos, link, diff, mods, clear
                                )
                            )
                await message.delete()
                output_channel = (
                    self.bot.get_channel(self.MAPAS_RANKEADOS_CHANNEL_ID)
                    )
                msg = (
                    f"Se ha rankeado el mapa **{nombre}-{diff}** "
                    f"con el requerimiento de: **{clear}** "
                    f"y con el valor de **{puntos}** puntos."
                )
                await output_channel.send(msg)

        @self.bot.tree.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            image_path = (
                'C:/Users/Alejandro/Desktop/BOT_DISCORD/'
                'IMG_20230309_161106.jpg'
                )
            file = discord.File(image_path, filename='IMG_20230309_161106.jpg')

            help_msg = '\n'.join([
                f"{key}: {value}" for key, value in ayuda_comandos.items()
                ])

            # Enviar el mensaje con la imagen adjunta
            await interaction.response.send_message(content=help_msg,
                                                    file=file)
