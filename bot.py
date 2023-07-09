import asyncio
import discord
from discord.app_commands import CommandTree
from tabulate import tabulate
import constants as const
import general_functions as fnc
import math
import bot_exceptions as exc
import typing
from osrparse import Replay
from io import BytesIO


# COMMANDS
class TNTDBotCommands(CommandTree):
    def __init__(self, client):
        super().__init__(client)

        # TODO hacer que clear funcione con osrparse
        # TODO testing de clear y requestmap
        @self.command(name="clear")
        async def clear(interaction: discord.Interaction, replay: discord.Attachment):
            """Clears a map and adds the points to the player's score."""
            r = Replay.from_file(BytesIO(await replay.read()))

            # Find the beatmap in the database with the replay's hash
            modo = fnc.sql("query", "SELECT modo FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
            id_mapa = fnc.sql("query", "SELECT id FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
            nombre = fnc.sql("query", "SELECT nombre FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
            mods = fnc.sql("query", "SELECT mods FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
            clear = fnc.sql("query", "SELECT clear FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)

            fnc.process_requeriments(replay_data=r, modo=modo, id=id_mapa, nombre=nombre, mods=mods, clear=clear)

            embed = discord.Embed(
                title="Your play has been sent!",
                description="Please, be patient.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            channel = client.get_channel(const.LOG_CLEAR_CHANNEL_ID)
            # Creates the message to be sent in the log channel
            msg = fnc.crear_mensaje_cmd_clear(interaction, r.username, id_mapa, clear)
            embed_msg = discord.Embed(
                title="Comando clear ejecutado",
                description=f"```{msg}```",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed_msg)

        @self.command(name="tabla")
        async def tabla(interaction: discord.Interaction, modo: str):
            """Shows the current maps in the database of the selected mode."""

            modo = modo.lower()
            try:
                modo = fnc.modo_check(modo, "4k", "7k", "et", "etterna", "taiko")
                print(modo)
            except exc.IncorrectModeError:
                await interaction.response.send_message("modo incorrecto")
            else:
                results = fnc.sql("query", "SELECT * FROM public.bd_mapas WHERE modo = %s ORDER BY id", modo)
                table_rows = []
                for row in results:
                    table_rows.append(row)

                num_pages = math.ceil(len(table_rows) / const.ROWS_PER_PAGE)

                embed_list = []
                for page_num in range(num_pages):
                    start_index = page_num * const.ROWS_PER_PAGE
                    end_index = start_index + const.ROWS_PER_PAGE
                    page_rows = table_rows[start_index:end_index]

                    page_embed = discord.Embed(
                        title=f"Tabla de {modo} (Página {page_num + 1}/{num_pages})"
                    )

                    for row in page_rows:
                        page_embed.add_field(name=f"Mapa {row[0]}: ", value=f"[{row[1]} - {row[4]}]({row[3]})",
                                             inline=True)
                        page_embed.add_field(name="Puntos: ", value=f"{row[2]}", inline=True)
                        page_embed.add_field(name="Requirement: ", value=f"{row[5]}, {row[6]}", inline=True)
                    embed_list.append(page_embed)
                index = 0
                try:
                    await interaction.response.send_message(embed=embed_list[index])
                except IndexError:
                    await interaction.response.send_message("Map list is empty.")
                canal = interaction.channel_id

                message_history = client.get_channel(canal).history(limit=1)
                last_message = message_history.ag_frame.f_locals.get('self').last_message

                await last_message.add_reaction('⬅️')
                await last_message.add_reaction('➡️')

                def check(reaction, user):
                    return user == interaction.user and str(reaction.emoji) in ['⬅️', '➡️']

                while True:
                    try:
                        reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=check)

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

        @self.command(name="played")
        async def played(interaction: discord.Interaction, modo: str, nombre: str):
            """Gives a list of all the played maps of the player in the selected mode."""
            modo = modo.lower()
            try:
                modo = fnc.modo_check(modo, "4k", "7k", "et", "etterna", "taiko")
                print(modo)
            except exc.IncorrectModeError:
                await interaction.response.send_message("modo incorrecto")
            else:
                results = fnc.sql("query",
                                  "SELECT bm.id, bm.nombre, bm.link, bm.diff, bm.mods, bm.clear, s.nombre, bm.puntos, "
                                  "bm.clear from bd_mapas bm join submissions s on (bm.id = s.id_mapa) "
                                  "where s.nombre = '{nombre}' and s.modo = '{modo}' order by bm.puntos desc;")
                table_rows = []
                for row in results:
                    table_rows.append(row)

                num_pages = math.ceil(len(table_rows) / const.ROWS_PER_PAGE)

                embed_list = []
                for page_num in range(num_pages):
                    start_index = page_num * const.ROWS_PER_PAGE
                    end_index = start_index + const.ROWS_PER_PAGE
                    page_rows = table_rows[start_index:end_index]

                    page_embed = discord.Embed(
                        title=f"Top plays of {modo} from {nombre} (Página {page_num + 1}/{num_pages})"
                    )

                    for row in page_rows:
                        page_embed.add_field(name=f"Mapa {row[0]}: ", value=f"[{row[1]} - {row[3]}]({row[2]})",
                                             inline=True)
                        page_embed.add_field(name="Puntos: ", value=f"{row[7]}", inline=True)
                        page_embed.add_field(name="Requirement: ", value=f"{row[8]}", inline=True)
                    embed_list.append(page_embed)
                index = 0
                try:
                    await interaction.response.send_message(embed=embed_list[index])
                except IndexError:
                    await interaction.response.send_message("player has no maps played.")
                canal = interaction.channel_id

                message_history = client.get_channel(canal).history(limit=1)
                last_message = message_history.ag_frame.f_locals.get('self').last_message

                await last_message.add_reaction('⬅️')
                await last_message.add_reaction('➡️')

                def check(reaction, user):
                    return user == interaction.user and str(reaction.emoji) in ['⬅️', '➡️']

                while True:
                    try:
                        reaction, _ = await client.wait_for('reaction_add', timeout=60.0, check=check)

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

        # :D
        @self.command(name="players")
        async def players(interaction: discord.Interaction, modo: str):
            """Shows the current players in the database of the selected mode."""
            modo = modo.lower()
            try:
                # Depending on the mode, the query will be different.
                modo = fnc.modo_check(modo, "etterna", "et", "7k", "4k", "taiko")
                if modo == "et" or modo == "etterna":
                    results = fnc.sql("query",
                                      "SELECT NOMBRE, puntosetterna FROM public.bd_players")
                elif modo == "7k":
                    results = fnc.sql("query", "SELECT NOMBRE, puntos7k FROM public.bd_players")
                elif modo == "4k":
                    results = fnc.sql("query", "SELECT NOMBRE, puntos4k FROM public.bd_players")
                elif modo == "taiko":
                    results = fnc.sql("query", "SELECT NOMBRE, puntostaiko FROM public.bd_players")
                else:
                    results = None
            except exc.IncorrectModeError:
                await interaction.response.send_message("modo incorrecto.")
            else:
                # Sorts the results by points in descending order.
                sorted_results = sorted(results, key=lambda row: row[1], reverse=True)
                headers = ["Nombre", "Puntos"]
                # Formats the results into a table. (tabulate) is a library that does this.
                formatted_player_list = (tabulate(sorted_results, headers, tablefmt="pipe"))
                embed = discord.Embed(title=f"{'Etterna' if modo == 'et' else modo} player list.",
                                      description=f"```\n{formatted_player_list}\n```",
                                      color=discord.Color.blue())
                await interaction.response.send_message(embed=embed)

        @self.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, modo: str, puntos: int, link: str,
                             diff: str, mods: str, clear: str):
            """Request a map to be added to the database."""
            modo = modo.lower()
            channel = None
            try:
                modo = fnc.modo_check(modo, "et", "4k", "7k", "etterna", "taiko")
            except exc.IncorrectModeError:
                await interaction.response.send_message("modo incorrecto.")
            else:
                if modo == "et":
                    channel = client.get_channel(const.ID_CANAL_VALIDACION_ET)
                elif modo == "7k":
                    channel = client.get_channel(const.ID_CANAL_VALIDACION_7K)
                elif modo == "4k":
                    channel = client.get_channel(const.ID_CANAL_VALIDACION_4K)
                elif modo == "taiko":
                    channel = client.get_channel(const.ID_CANAL_VALIDACION_TAIKO)
                message_content = (
                    f"Link: {link}\nDiff: {diff}\nMods: {mods}\nClear: {clear}\nmodo: {modo}\npuntos: {puntos}")
                await channel.send(message_content)
                embed = discord.Embed(
                    title="Your map has been sent to the validation queue.",
                    description="be patient, we dont get paid for this. :moyai:",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.command(name="help")
        # Modulo "typing" importado sirve para implementar parametros opcionales.
        async def help(interaction: discord.Interaction, language: typing.Optional[str] = "Spanish"):
            """Shows the help menu."""
            language = language.lower()
            fnc.obtener_imagen_notpx()
            file = discord.File("image.jpg")
            if language == "spanish":
                embed = discord.Embed(
                    title="Command help",
                    description='\n\n'.join([f"**{key}**: {value}" for key, value in const.AYUDA_COMANDOS.items()]),
                    color=discord.Color.red()
                )
            elif language == "english":
                embed = discord.Embed(
                    title="Command help",
                    description='\n\n'.join([f"**{key}**: {value}" for key, value in const.AYUDA_COMANDOS_ENG.items()]),
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="**That language is not avaliable. Please choose Spanish or English.**",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, file=file)

        @self.command(name="register")
        async def register(interaction: discord.Interaction, nombre: str):
            """Register yourself in the database."""
            fnc.sql("insert",
                    "INSERT INTO public.bd_players (nombre, puntos4k, puntos7k, puntosetterna, puntostaiko) "
                    "VALUES (%s, 0, 0, 0, 0)",
                    (nombre,))
            embed = discord.Embed(
                title="you are registered.",
                description="Please, remember you start at 0 points!",
                color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)


class TNTDBot(discord.Client):
    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord!')
        try:
            print("Sincronizando comandos...")
            tree = TNTDBotCommands(self)
            # Syncs the commands with the server.
            synced = await tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    async def on_raw_reaction_add(self, payload):
        """Handles the reaction commands."""
        if payload.channel_id == const.ID_CANAL_VALIDACION_4K \
                or payload.channel_id == const.ID_CANAL_VALIDACION_7K \
                or payload.channel_id == const.ID_CANAL_VALIDACION_ET  \
                or payload.channel_id == const.ID_CANAL_VALIDACION_TAIKO:
            await self.handle_reaction_command(payload)

    async def handle_reaction_command(self, payload):
        """Handles the reaction commands."""
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        content = message.content.split("\n")
        link = content[0].split(": ")[1]
        diff = content[1].split(": ")[1].replace("'", "")
        mods = content[2].split(": ")[1]
        clear = content[3].split(": ")[1]
        modo = content[4].split(": ")[1]
        puntos = int(content[5].split(": ")[1])

        osu_file = fnc.download_osu_file(link, diff)
        metadata = fnc.get_osu_map_metadata(osu_file)

        nombre = metadata["Title"]
        hash = metadata["hash"]

        try:
            fnc.sql("insert",
                    "INSERT INTO public.bd_mapas_old (nombre, puntos, link, diff, mods, clear, modo, hash) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear, modo, hash)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command: {e}")

        await message.delete()
        output_channel = self.get_channel(const.RANKED_CHANNEL_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa de {modo} **{metadata['Artist']} - {metadata['Title']} - {diff}** con el "
            f"requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")
