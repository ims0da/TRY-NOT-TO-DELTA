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
        async def clear(interaction: discord.Interaction, modo: str, nombre: str, id_mapa: int, clear: str):
            fnc.sql("insert", "INSERT INTO public.submissions (modo, nombre, id_mapa, clear) VALUES (%s, %s, %s, %s)", (modo, nombre, id_mapa, clear))
            embed = discord.Embed(
                title="Your play has been sent!",
                description="Please, be patient.",
                color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True) 

            channel = client.get_channel(LOG_CLEAR_CHANNEL_ID)
            msg = fnc.crear_mensaje_cmd_clear(interaction, nombre, id_mapa, clear)
            embed_msg = discord.Embed(title="Comando clear ejecutado", description=f"```{msg}```", color=discord.Color.blue())
            await channel.send(embed=embed_msg)

        @self.command(name="tabla")
        async def tabla(interaction: discord.Interaction, modo: str):
            modo = modo.lower()
            if modo == "et" or modo == "etterna":
                results = fnc.sql("query", "SELECT * FROM public.bd_mapas WHERE modo = 'et' ORDER BY id")
            elif modo == "7k":
                results = fnc.sql("query", "SELECT * FROM public.bd_mapas WHERE modo = '7k' ORDER BY id")
            elif modo == "4k":
                results = fnc.sql("query", "SELECT * FROM public.bd_mapas WHERE modo = '4k' ORDER BY id")
            else:
                await interaction.followup.send("modo incorrecto.")
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
            if modo == "etterna" or modo == "et":
                results = fnc.sql("query", "SELECT NOMBRE, puntosetterna FROM public.bd_players")
            elif modo == "7k":
                results = fnc.sql("query", "SELECT NOMBRE, puntos7k FROM public.bd_players")
            elif modo == "4k":
                results = fnc.sql("query", "SELECT NOMBRE, puntos4k FROM public.bd_players")
            else:
                await interaction.followup.send("modo incorrecto.")

            sorted_results = sorted(results, key=lambda row: row[1], reverse=True)
            headers = ["Nombre", "Puntos"]
            formatted_player_list = (tabulate(sorted_results, headers, tablefmt="pipe"))
            embed = discord.Embed(title=f"Lista de jugadores de {modo}.", description=f"```\n{formatted_player_list}\n```",
                                  color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

        @self.command(name="requestmap")
        async def requestmap(interaction: discord.Interaction, modo: str, nombre: str, puntos: int, link: str, diff: str, mods: str, clear: str):
            modo = modo.lower()
            if modo == "etterna" or modo == "et":
                channel = client.get_channel(ID_CANAL_VALIDACION_ET)
            elif modo == "7k":
                channel = client.get_channel(ID_CANAL_VALIDACION_7K)
            elif modo == "4k":
                channel = client.get_channel(ID_CANAL_VALIDACION_4K)
            else:
                await interaction.followup.send("modo incorrecto.")
            message_content = f"Nombre: {nombre}\nPuntos: {puntos}\nLink: {link}\nDiff: {diff}\nMods: {mods}\nClear: {clear}\nmodo: {modo}"
            await channel.send(message_content)
            embed = discord.Embed(
                title="Your map has been sent to the validation queue.",
                description="be patient, we dont get paid for this. :moyai:",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            fnc.obtener_imagen_notpx()
            file = discord.File("image.jpg")
            msg = '\n'.join([f"{key}: {value}" for key, value in AYUDA_COMANDOS.items()])
            await interaction.response.send_message(content=msg, file=file)

        @self.command(name="register")
        async def register(interaction: discord.Interaction, nombre: str):
            fnc.sql("insert", "INSERT INTO public.bd_players (nombre, puntos4k, puntos7k, puntosetterna) VALUES (%s, 0, 0, 0)", (nombre,))
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
        modo = content[6].split(": ")[1]
        try:
            fnc.sql("insert", "INSERT INTO public.bd_mapas_old (nombre, puntos, link, diff, mods, clear, modo) VALUES (%s, %s, %s, %s, %s, %s, %s)", nombre, puntos, link, diff, mods, clear, modo)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_4k: {e}")

        await message.delete()
        #cambiar el output_channel 4k este de la polla a un canal global para todos los rankeds. 
        output_channel = self.get_channel(OUTPUT_CHANNEL_4K_ID)
        await output_channel.send(f"Se ha rankeado el mapa de {modo} **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

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
        modo = content[6].split(": ")[1]
        try:
            fnc.sql("insert",
                    "INSERT INTO public.bd_mapas_old (nombre, puntos, link, diff, mods, clear, modo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear, modo)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_7k: {e}")

        await message.delete()
        output_channel = self.get_channel(OUTPUT_CHANNEL_7K_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa  de {modo} **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")

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
        modo = content[6].split(": ")[1]
        try:
            fnc.sql("insert",
                    "INSERT INTO public.bd_mapas_old (nombre, puntos, link, diff, mods, clear, modo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    nombre, puntos, link, diff, mods, clear, modo)
        except Exception as e:
            print(f"Something went wrong in handle_reaction_command_et: {e}")

        await message.delete()
        output_channel = self.get_channel(OUTPUT_CHANNEL_ET_ID)
        await output_channel.send(
            f"Se ha rankeado el mapa de  {modo} **{nombre}-{diff}** con el requerimiento de: **{clear}** y con el valor de **{puntos}** puntos.")