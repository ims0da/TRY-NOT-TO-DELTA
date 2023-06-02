import discord
from funciones_tablas import tabla_embed, crear_tabla_players
from commands7k import Commands7k
import asyncio


class Commandset(Commands7k):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.start_commands()

    def start_commands(self):
        super().start_commands()

        @self.bot.tree.command(name="tablaet")
        async def tablaet(interaction: discord.Interaction):
            results = self.query("SELECT * FROM public.tntdet ORDER BY id")

            embed_page_list = tabla_embed(results)

            index = 0
            await interaction.response.send_message(
                embed=embed_page_list[index]
            )
            canal = interaction.channel_id

            message_history = self.bot.get_channel(canal).history(limit=1)
            last_message = (
                message_history.ag_frame.f_locals.get("self").last_message
            )

            await last_message.add_reaction("⬅️")
            await last_message.add_reaction("➡️")

            def check(reaction, user):
                return user == (
                    interaction.user and str(reaction.emoji) in ["⬅️", "➡️"]
                )

            while True:
                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add",
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

        @self.bot.tree.command(name="playerset")
        async def players(interaction: discord.Interaction):
            results = self.query(
                "SELECT NOMBRE, PUNTOS FROM "
                "public.playerset WHERE PUNTOS != '0'"
            )

            players = crear_tabla_players(results)
            embed = discord.Embed(
                title="Lista de jugadores de etterna",
                description=f"```\n{players}\n```",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name="requestmapet")
        async def requestmapet(interaction: discord.Interaction,
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
