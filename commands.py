import discord
import psycopg2
from tabulate import tabulate


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

        @self.bot.tree.command(name="clear")
        async def clear(interaction: discord.Interaction):
            msg = (
                'Espero que no estés usando basura, '
                'enseguida se te asignarán los puntos.'
                )
            await interaction.response.send_message(msg, ephemeral=True)

        @self.bot.tree.command(name="tabla")
        async def tabla(interaction: discord.Interaction):
            # TODO: Estaria guay hacer que si esto llega a 4096
            # caracteres (maximo de los embeds de discord) se
            # dividiese en diferentes mensajes. (para poder
            # darle un formato guay con tabulate igual que en
            # el comando players)

            # Hacer consulta SQL
            results = self.query("SELECT * FROM public.tntd")

            half = len(results) // 2
            first_half = results[:half]
            second_half = results[half:]

            # Crear la descripcion del primer mensaje
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
            await interaction.response.send_message(embed=first_response,
                                                    ephemeral=True)
            await interaction.followup.send(embed=second_response,
                                            ephemeral=True)

        @self.bot.tree.command(name="players")
        async def players(interaction: discord.Interaction):
            # Hacer consulta SQL
            results = self.query("SELECT NOMBRE, PUNTOS  FROM public.players")

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
