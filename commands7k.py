from commands4k import Commands
from funciones_tablas import tabla_embed, crear_tabla_players
import discord
import asyncio


# Pensandolo mejor, toda esta clase nos la podríamos ahorrar
# con un input en cada comando (clear, tabla, players, requestmap)
# que sea modo 4k o 7k (o 5k o los que sean)
# y asi seria mucho mas facil :)
class Commands7k(Commands):
    def __init__(self, bot) -> None:
        super().__init__(bot)

    def start_commands(self):
        super().start_commands()

        @self.bot.tree.command(name="clear7k")
        async def clear7k(interaction: discord.Interaction):
            msg = (
                'Espero que no estés usando basura, '
                'enseguida se te asignarán los puntos.'
            )
            await interaction.response.send_message(msg, ephemeral=True)

        @self.bot.tree.command(name="tabla7k")
        async def tabla7k(interaction: discord.Interaction):
            results = self.query("SELECT * FROM public.tntd7k ORDER BY id")

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

        @self.bot.tree.command(name="players7k")
        async def players7k(interaction: discord.Interaction):
            results = self.query(
                "SELECT NOMBRE, PUNTOS FROM public.players7k"
                )

            players = crear_tabla_players(results)
            embed = discord.Embed(
                title="Lista de jugadores de 7k.",
                description=f"```\n{players}\n```",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)

        # La idea es quiza añadirle un parametro al comando de
        # requestmap original pero no se todavía que vamos a
        # hacer con la base de datos asi que asi se queda de momento
        @self.bot.tree.command(name="requestmap7k")
        async def request7kmap(interaction: discord.Interaction,
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
                "Modo: 7k"
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
