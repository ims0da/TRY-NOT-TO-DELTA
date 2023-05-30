import discord
import psycopg2


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
            # FIXME: Estaria bien hacer este codigo mas legible
            # de algun modo ya que a mi me cuesta entenderlo.
            # Iniciar conexión a base de datos
            self.start_db_connection()

            # Hacer consulta SQL
            results = self.query("SELECT * FROM public.tntd")

            # Dividir los resultados en dos partes
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
            # Establecer la conexión a la base de datos
            self.start_db_connection()

            # Hacer consulta SQL
            results = self.query("SELECT NOMBRE, PUNTOS  FROM public.players")

            # Formatear los resultados como un mensaje de Discord
            player_list = '\n'.join([
                f'{row[0]} - Puntos: {row[1]}' for row in results
                ])
            embed = discord.Embed(
                title="Lista de jugadores",
                description=player_list,
                color=discord.Color.blue()
                )
            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
