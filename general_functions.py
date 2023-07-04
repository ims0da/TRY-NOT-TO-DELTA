import psycopg2
import requests
from PIL import Image
from io import BytesIO
import bot_exceptions as exc


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
    """operation: insert or query"""
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
    """Crea un mensaje para el canal de logs de comandos."""
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


def modo_check(modo, *args):
    # args: "et", "4k", "7k" etc
    if modo in args:
        print("Check sucessful.")
        if modo == "etterna":
            modo = "et"
    else:
        raise exc.IncorrectModeError
    return modo
