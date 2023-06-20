import psycopg2
import json
import requests
from PIL import Image
from io import BytesIO


# DATABASE
def start_db_connection():
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="TRY_NOT_TO_DELTA",
        user="postgres",
        password="admin"
    )
    return connection


def sql(operation: str, string: str, *args):
    results = None
    conn = start_db_connection()
    cursor = conn.cursor()
    cursor.execute(string, args)

    if operation == "insert":
        conn.commit()
    elif operation == "query":
        results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results


# TODO: Cuando la nueva base de datos esté operativa, cambiar el modo de almacenar esto y adaptarlo a la nueva base de
#       datos en vez de utilizar un json
def crear_jugador_mapas_jugados(player: str, modo: str):
    modo = modo.lower()
    if modo == "etterna":
        modo = "et"
    with open(f"mapas_jugados_{modo}.json", "r") as raw_data:
        map_data = json.load(raw_data)

    with open(f"mapas_jugados_{modo}.json", "w") as raw_data:
        map_data[player] = []
        json.dump(map_data, raw_data, indent=4)


def escribir_mapas_jugados(player: str, map_id: int, modo: str):
    modo = modo.lower()
    if modo == "etterna":
        modo = "et"
    with open(f"mapas_jugados_{modo}.json", "r") as raw_data:
        data = json.load(raw_data)
        data_list = data[player]
        data_list.append(map_id)

    with open(f"mapas_jugados_{modo}.json", "w") as raw_data:
        json.dump(data, raw_data, indent=4)


def leer_mapas_jugados(player, modo: str):
    modo = modo.lower()
    if modo == "etterna":
        modo = "et"
    with open(f"mapas_jugados_{modo}.json", "r") as raw_data:
        data = json.load(raw_data)
        player_map_data = data[player]
        return player_map_data


def calcular_puntos(player, table_map_id, modo):
    modo = modo.lower()
    if modo == "etterna":
        modo = "et"
    try:
        if modo == "7k":
            player_points = sql("query", f"SELECT puntos FROM public.players7k WHERE nombre = '{player}';")
            map_points = sql("query", f"SELECT puntos FROM public.tntd7k WHERE id = '{table_map_id}';")
        elif modo == "et":
            player_points = sql("query", f"SELECT puntos FROM public.playerset WHERE nombre = '{player}';")
            map_points = sql("query", f"SELECT puntos FROM public.tntdet WHERE id = '{table_map_id}';")
        else:
            player_points = sql("query", f"SELECT puntos FROM public.players WHERE nombre = '{player}';")
            map_points = sql("query", f"SELECT puntos FROM public.tntd WHERE id = '{table_map_id}';")

        player_points = player_points[0][0]
        map_points = map_points[0][0]
        final_points = int(player_points) + int(map_points)
    except IndexError:
        raise IndexError
    else:
        if modo == "4k":
            sql("insert", f"UPDATE public.players SET puntos = %s WHERE nombre = %s;", final_points, player)
        elif modo == "7k":
            sql("insert", f"UPDATE public.players7k SET puntos = %s WHERE nombre = %s;", final_points, player)
        elif modo == "et":
            sql("insert", f"UPDATE public.playerset SET puntos = %s WHERE nombre = %s;", final_points, player)

        escribir_mapas_jugados(player, table_map_id, modo)
        return final_points, map_points


def crear_mensaje_cmd_clear(interaction, player, table_map_id, map_points):
    msg = (f"Usuario: {interaction.user.name}\n"
           "Comando utilizado: /clear (Tabla 4K)\n"
           f"Parámetros:\n"
           f"Player: {player}, Map_ID: {table_map_id}, Puntos sumados: {map_points}")
    return msg


def crear_mensaje_bienvenida(member):
    msg = (
        f'Bienvenido/a {member.mention} a TRY NOT TO DELTA! '
        f'Esperemos que te lo pases bien por aquí!'
    )
    return msg


def obtener_imagen_notpx():
    img_url = "https://media.discordapp.net/attachments/851840942675722303/1115056731354038382/image.jpg"
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content))
    image.save("image.jpg")