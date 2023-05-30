import discord
import psycopg2
from tabulate import tabulate


ayuda_comandos = {
    "/players" : "Muestra la leaderboard con los puntos actuales.",
    "/tabla" : "Muestra la base de datos de mapas con el link del mapa, el nombre, la diff name, el mod y el clear.",
    "/clear"  : "Has hecho un clear a un mapa y requieres de tus puntos",
    "/ayuda" : "Muestra este comando",
}



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

    
    def insert(self, string: str): # <- este es lo mismo que el metodo query de arriba, solo que cuando quieres insertar, modificar o eliminar, no puedes hacer un fetch.
        self.start_db_connection() # <- por eso no hay un return, porque no hay nada que devolver, solo se ejecuta la consulta y ya, es digamos "interno"

        cursor = self.conn.cursor()
        cursor.execute(string)

        # Si la consulta es una operación de modificación (como INSERT, UPDATE o DELETE),
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

            await interaction.response.send_message(embed=embed,
                                                    ephemeral=True)
    
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
            if payload.channel_id == canal_id:
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
                self.insert("INSERT INTO public.tntd (nombre, puntos, link, diff, mods, clear) VALUES ('{}', {}, '{}', '{}', '{}', '{}')".format(nombre, puntos, link, diff, mods, clear))
                
                await message.delete()



        @self.bot.tree.command(name="ayuda")
        async def ayuda(interaction: discord.Interaction):
            msg = '\n'.join([f"{key}: {value}" for key, value in ayuda_comandos.items()])
            await interaction.response.send_message(msg)

