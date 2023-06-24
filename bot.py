import asyncio
import discord
from discord.app_commands import CommandTree
from tabulate import tabulate
from constants import *
import general_functions as fnc
import math


class TNTDBotCommands(CommandTree):
    def __init__(self, client):
        super().__init__(client)

        @self.command(name="clear")
        async def clear(interaction: discord.Interaction, modo: str, player: str, table_map_id: int):
            msg = (
                "Espero que no estés usando basura, enseguida se te asignarán los puntos.\n"
            )
            await interaction.response.send_message(msg, ephemeral=True)

            try:
                played_map_data = fnc.leer_mapas_jugados(player, modo)
            except KeyError:
                fnc.crear_jugador_mapas_jugados(player, modo)
                played_map_data = fnc.leer_mapas_jugados(player, modo)

            if table_map_id in played_map_data:
                await interaction.followup.send("Ya has jugado ese mapa.")
            else:
                try:
                    final_points, map_points = fnc.calcular_puntos(player=player, table_map_id=table_map_id, modo=modo)
                except IndexError:
                    await interaction.followup.send("No se ha encontrado ese jugador. Pidele a un admin que lo agregue",
                                                    ephemeral=True)
                else:
                    msg = f"Jugador: {player}, Puntos: {final_points}"
                    embed = discord.Embed(title="Puntos actualizados", description=f"```{msg}```")
                    await interaction.followup.send(embed=embed, ephemeral=True)

                    channel = client.get_channel(LOG_CLEAR_CHANNEL_ID)
                    msg = fnc.crear_mensaje_cmd_clear(interaction, player, table_map_id, map_points)
                    embed_msg = discord.Embed(title="Comando clear ejecutado", description=f"```{msg}```", color=discord.Color.blue())
                    await channel.send(embed=embed_msg)

        @self.command(name="tabla")
        async def tabla(interaction: discord.Interaction, modo: str):
            modo = modo.lower()
            if modo == "etterna":
                modo = "et"
            if modo == "7k":
                results = fnc.sql("query", "SELECT * FROM public.tntd7k ORDER BY id")
            elif modo == "et":
                results = fnc.sql("query", "SELECT * FROM public.tntdet ORDER BY id")
            else:
                results = fnc.sql("query", "SELECT * FROM public.tntd ORDER BY id")

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
                    title=f"Tabla de {modo} (Página {page_num + 1}/{num_pages})"
                )

                for row in page_rows:
                    page_embed.add_field(name=f"Mapa {row[0]}: ", value=f"[{row[1]} - {row[4]}]({row[3]})", inline=True)
                    page_embed.add_field(name="Puntos: ", value=f"{row[2]}", inline=True)
                    page_embed.add_field(name="Requirement: ", value=f"{row[5]}, {row[6]}", inline=True)
                embed_list.append(page_embed)
            index = 0
            await interaction.response.send_message(embed=embed_list[index])
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

        @self.command(name="players")
        async def players(interaction: discord.Interaction, modo: str):
            modo = modo.lower()
            if modo == "etterna":
                modo = "et"
            if modo == "7k":
                results = fnc.sql("query", "SELECT NOMBRE, PUNTOS FROM public.players7k WHERE PUNTOS != '0'")
            elif modo == "etterna":
                results = fnc.sql("query", "SELECT NOMBRE, PUNTOS FROM public.playerset WHERE PUNTOS != '0'")
            else:
                results = fnc.sql("query", "SELECT NOMBRE, PUNTOS FROM public.players WHERE PUNTOS != '0'")

            sorted_results = sorted(results, key=lambda row: row[1], reverse=True)
            headers = ["Nombre", "Puntos"]
            formatted_player_list = (tabulate(sorted_results, headers, tablefmt="pipe"))
            embed = discord.Embed(title="Lista de jugadores de 4k.", description=f"```\n{formatted_player_list}\n```",
                                  color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

        # TODO: Añadir parametro "Modo" (4k, 7k, et)
        @self.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, modo: str, nombre: str, puntos: int, link: str, diff: str, mods: str, clear: str):
            modo = modo.lower()
            if modo == "etterna":
                modo = "et"
            if modo == "7k":
                channel = client.get_channel(ID_CANAL_VALIDACION_7K)
            elif modo == "et":
                channel = client.get_channel(ID_CANAL_VALIDACION_ET)
            else:
                channel = client.get_channel(ID_CANAL_VALIDACION_4K)
            message_content = f"Nombre: {nombre}\nPuntos: {puntos}\nLink: {link}\nDiff: {diff}\nMods: {mods}\nClear: {clear}"
            await channel.send(message_content)

            embed = discord.Embed(
                title="Tu mapa ha sido enviado a la cola de validación",
                description="Se paciente, que no se cobra por esto :moyai:",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            fnc.obtener_imagen_notpx()
            file = discord.File("image.jpg")
            msg = '\n'.join([f"{key}: {value}" for key, value in AYUDA_COMANDOS.items()])
            await interaction.response.send_message(content=msg, file=file)


class TNTDBot(discord.Client):
    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord!')
        try:
            print("Sincronizando comandos...")
            tree = TNTDBotCommands(self)
            synced = await tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    async def on_member_join(self, member):
        channel = self.get_channel(WELCOME_CHANNEL_ID)
        msg = fnc.crear_mensaje_bienvenida(member)
        await channel.send(msg)

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == ID_CANAL_VALIDACION_4K:
            await self.handle_reaction_command_4k(payload)
        elif payload.channel_id == ID_CANAL_VALIDACION_7K:
            await self.handle_reaction_command_7k(payload)
        elif payload.channel_id == ID_CANAL_VALIDACION_ET:
            await self.handle_reaction_command_et(payload)

    async def handle_reaction_command_4k(self, payload):
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        content = message.content.split("\n")
        nombre = content[0].split(": ")[1].replace("'", "")
        puntos = int(content[1].split(": ")[1])
        link = content[2].split(": ")[1]
        diff = content[3].split(": ")[1].replace("'", "")
        mods = content[4].split(": ")[1]
        clear = content[5].split(": ")[1]

        try:
            fnc.sql("insert", "INSERT INTO public.tntd (nombre, puntos, link, diff, mods, clear) VALUES (%s, %s, %s, %s, %s, %s)", nombre, puntos, link, diff, mods, clear)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_4k: {e}")

        await message.delete()
        output_channel = self.get_channel(OUTPUT_CHANNEL_4K_ID)
        await output_channel.send(f"Se ha rankeado el mapa de 4k **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

    async def handle_reaction_command_7k(self, payload):
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        content = message.content.split("\n")
        nombre = content[0].split(": ")[1].replace("'", "")
        puntos = int(content[1].split(": ")[1])
        link = content[2].split(": ")[1]
        diff = content[3].split(": ")[1].replace("'", "")
        mods = content[4].split(": ")[1]
        clear = content[5].split(": ")[1]

        try:
            fnc.sql("insert",
                    "INSERT INTO public.tntd7k (nombre, puntos, link, diff, mods, clear) VALUES (%s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_7k: {e}")

        await message.delete()
        output_channel = self.get_channel(OUTPUT_CHANNEL_7K_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa  de 7k **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

    async def handle_reaction_command_et(self, payload):
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        content = message.content.split("\n")
        nombre = content[0].split(": ")[1].replace("'", "")
        puntos = int(content[1].split(": ")[1])
        link = content[2].split(": ")[1]
        diff = content[3].split(": ")[1].replace("'", "")
        mods = content[4].split(": ")[1]
        clear = content[5].split(": ")[1]

        try:
            fnc.sql("insert",
                    "INSERT INTO public.tntdet (nombre, puntos, link, diff, mods, clear) VALUES (%s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_et: {e}")

        await message.delete()
        output_channel = self.get_channel(OUTPUT_CHANNEL_ET_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa de etterna **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")