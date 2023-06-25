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


def sql(action, string, args):
    conn = psycopg2.connect(database="TRY_NOT_TO_DELTA", user="postgres", password="admin", host="162.55.178.187", port="5432")
    cursor = conn.cursor()

    if action == "insert":
        cursor.execute(string, args)
        conn.commit()

    cursor.close()
    conn.close()


def crear_mensaje_cmd_clear(interaction, player, table_map_id, map_points):
    msg = (f"Usuario: {interaction.user.name}\n"
           "Comando utilizado: /clear (Tabla 4K)\n"
           f"Parámetros:\n"
           f"Player: {player}, Map_ID: {table_map_id},")
    return msg




def obtener_imagen_notpx():
    img_url = "https://media.discordapp.net/attachments/851840942675722303/1115056731354038382/image.jpg"
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content))
    image.save("image.jpg")