import psycopg2
import json
import requests
from PIL import Image
from io import BytesIO


# DATABASE
def start_db_connection():
    connection = psycopg2.connect(
        host="162.55.178.187",
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


def crear_mensaje_cmd_clear(interaction, nombre, id_mapa, clear):
    msg = (f"Player: {interaction.user.name}\n"
           "Comando utilizado: /clear \n"
           f"Parámetros:\n"
           f"Player: {nombre}, Map_ID: {id_mapa}, clear: {clear}")
    return msg


def obtener_imagen_notpx():
    img_url = "https://media.discordapp.net/attachments/851840942675722303/1115056731354038382/image.jpg"
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content))
    image.save("image.jpg")