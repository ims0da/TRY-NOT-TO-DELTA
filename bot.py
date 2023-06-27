import asyncio
import discord
from discord.app_commands import CommandTree
from tabulate import tabulate
from constants import *
import general_functions as fnc
import math
from bot_exceptions import *
import typing


class TNTDBotCommands(CommandTree):
    def __init__(self, client):
        super().__init__(client)

        @self.command(name="clear")
        async def clear(interaction: discord.Interaction, modo: str, nombre: str, id_mapa: int, clear: str):
            fnc.sql(
                "insert",
                "INSERT INTO public.submissions (modo, nombre, id_mapa, clear) VALUES (%s, %s, %s, %s)",
                modo, nombre, id_mapa, clear
            )
            embed = discord.Embed(
                title="Your play has been sent!",
                description="Please, be patient.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            channel = client.get_channel(LOG_CLEAR_CHANNEL_ID)
            msg = fnc.crear_mensaje_cmd_clear(interaction, nombre, id_mapa, clear)
            print(f"msg: {msg}")
            embed_msg = discord.Embed(
                title="Comando clear ejecutado",
                description=f"```{msg}```",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed_msg)

        @self.command(name="tabla")
        async def tabla(interaction: discord.Interaction, modo: str):
            modo = modo.lower()
            try:
                modo = fnc.modo_check(modo, "4k", "7k", "et", "etterna")
                print(modo)
            except IncorrectModeError:
                await interaction.response.send_message("modo incorrecto")
            else:
                results = fnc.sql("query", "SELECT * FROM public.bd_mapas WHERE modo = %s ORDER BY id", modo)
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

        # :D
        @self.command(name="players")
        async def players(interaction: discord.Interaction, modo: str):
            modo = modo.lower()
            try:
                modo = fnc.modo_check(modo, "etterna", "et", "7k", "4k")
                if modo == "et" or "etterna":
                    results = fnc.sql("query",
                                      "SELECT NOMBRE, puntosetterna FROM public.bd_players WHERE puntosetterna <> 0")
                elif modo == "7k":
                    results = fnc.sql("query", "SELECT NOMBRE, puntos7k FROM public.bd_players WHERE puntos7k <> 0")
                elif modo == "4k":
                    results = fnc.sql("query", "SELECT NOMBRE, puntos4k FROM public.bd_players WHERE puntos4k <> 0")
                else:
                    results = None
            except IncorrectModeError:
                await interaction.response.send_message("modo incorrecto.")
            else:
                sorted_results = sorted(results, key=lambda row: row[1], reverse=True)
                headers = ["Nombre", "Puntos"]
                formatted_player_list = (tabulate(sorted_results, headers, tablefmt="pipe"))
                embed = discord.Embed(title=f"{'Etterna' if modo == 'et' else modo} player list.",
                                      description=f"```\n{formatted_player_list}\n```",
                                      color=discord.Color.blue())
                await interaction.response.send_message(embed=embed)

        @self.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, modo: str, nombre: str, puntos: int, link: str,
                             diff: str, mods: str, clear: str):
            modo = modo.lower()
            channel = None
            try:
                modo = fnc.modo_check(modo, "et", "4k", "7k", "etterna")
            except IncorrectModeError:
                await interaction.response.send_message("modo incorrecto.")
            else:
                if modo == "et":
                    channel = client.get_channel(ID_CANAL_VALIDACION_ET)
                elif modo == "7k":
                    channel = client.get_channel(ID_CANAL_VALIDACION_7K)
                elif modo == "4k":
                    channel = client.get_channel(ID_CANAL_VALIDACION_4K)

                message_content = f"Nombre: {nombre}\nPuntos: {puntos}\nLink: {link}\nDiff: {diff}\nMods: {mods}\nClear: {clear}\nmodo: {modo}"
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
            language = language.lower()
            fnc.obtener_imagen_notpx()
            file = discord.File("image.jpg")
            if language == "spanish":
                embed = discord.Embed(
                    title="Command help",
                    description='\n\n'.join([f"**{key}**: {value}" for key, value in AYUDA_COMANDOS.items()]),
                    color=discord.Color.red()
                )
            elif language == "english":
                embed = discord.Embed(
                    title="Command help",
                    description='\n\n'.join([f"**{key}**: {value}" for key, value in AYUDA_COMANDOS_ENG.items()]),
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
            fnc.sql("insert",
                    "INSERT INTO public.bd_players (nombre, puntos4k, puntos7k, puntosetterna) VALUES (%s, 0, 0, 0)",
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
            synced = await tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == ID_CANAL_VALIDACION_4K \
                or payload.channel_id == ID_CANAL_VALIDACION_7K \
                or payload.channel_id == ID_CANAL_VALIDACION_ET:
            await self.handle_reaction_command(payload)

    async def handle_reaction_command(self, payload):
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        content = message.content.split("\n")
        nombre = content[0].split(": ")[1].replace("'", "")
        puntos = int(content[1].split(": ")[1])
        link = content[2].split(": ")[1]
        diff = content[3].split(": ")[1].replace("'", "")
        mods = content[4].split(": ")[1]
        clear = content[5].split(": ")[1]
        modo = content[6].split(": ")[1]
        try:
            fnc.sql("insert",
                    "INSERT INTO public.bd_mapas_old (nombre, puntos, link, diff, mods, clear, modo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear, modo)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command: {e}")

        await message.delete()
        output_channel = self.get_channel(RANKED_CHANNEL_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa de {modo} **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")
