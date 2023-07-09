import psycopg2
import requests
from PIL import Image
from io import BytesIO
import bot_exceptions as exc
import re
import zipfile
import hashlib
import constants as const


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


def download_osu_file(url, diff):
    # Dependiendo del link que se le pase, va a descargar el archivo de distintas maneras.
    if url.startswith("https://drive.google.com"):
        return download_google_drive(url, diff)
    elif url.startswith("https://www.mediafire.com"):
        return download_mediafire(url, diff)
    elif url.startswith("https://mega.nz"):
        return download_mega(url, diff)
    elif url.startswith("https://osu.ppy.sh/beatmapsets"):
        return osu_ppy_get_md5(url)
    elif url.startswith("https://cdn.discordapp.com/attachments/"):
        return download_discord(url, diff)


def process_map(map_id, map_link, map_diff):
    # Todavía no se bien como utilizarlo. Es parte del programa que sacaba los hashes de todos los mapas de la db y los
    # guardaba en la columna nueva. - Nupi
    try:
        osu_file_content = download_osu_file(map_link, map_diff)
        if map_link.startswith("https://osu.ppy.sh/beatmapsets"):
            sql("insert", "UPDATE bd_mapas SET hash = %s WHERE id = %s", osu_file_content, map_id)
        else:
            osu_file_hash = calculate_osu_map_hash(osu_file_content)
            sql("insert", "UPDATE bd_mapas SET hash = %s WHERE id = %s", osu_file_hash, map_id)

        print(f"finished {map_id}. Link: {map_link}")
    except Exception as e:
        print(f"Error on map {map_id}: {str(e)}. Link: {map_link}.")


def download_discord(url, diff):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error downloading file from discord")

    osz_file = BytesIO(response.content)
    osz_zip = zipfile.ZipFile(osz_file)

    return search_osu_in_osz(osz_zip, diff)


def osu_ppy_get_md5(url):
    # Obtiene el hash de un mapa de osu.ppy.sh a traves de la API v1. - Nupi
    beatmap_id = re.search(r"https://osu.ppy.sh/beatmapsets/.*?#.*?/(\d+)", url).group(1)
    url = f"https://osu.ppy.sh/api/get_beatmaps?k={const.OSU_API_V1}&b={beatmap_id}"
    response = requests.get(url)

    data = response.json()

    if len(data) == 0:
        raise Exception(f"No map data found for map id: {beatmap_id}")

    osu_hash = data[0].get("file_md5")

    if response.status_code != 200:
        raise Exception(f"Map not found in osu.ppy.sh. Response: {response.text}. Map: {beatmap_id}")

    return osu_hash


# Esta funcion busca el archivo .osu dentro del .osz de la dificultad escogida. (por eso es importante poner las
# dificultados sin corchetes y exactamente igual que en el mapa.) - Nupi
def search_osu_in_osz(osz_zip, diff: str):
    osu_file_name = None
    diff = f"[{diff}]"
    for file_name in osz_zip.namelist():
        if file_name.endswith(".osu") and diff in file_name:
            osu_file_name = file_name
            break

    if osu_file_name is None:
        raise Exception("No osu file found in the .osz file.")

    osu_file_content = osz_zip.read(osu_file_name)
    osu_map = BytesIO(osu_file_content)

    return osu_map


def download_google_drive(url, diff):
    # Sirve para descargar archivos de google drive (mapas unsubmitted de la db) - Nupi
    url = "https://drive.google.com/file/d/157o99lCKm2_X6fNAkh7t2kfRe8WrMh-U/view?usp=sharing"
    # re.search sirve para obtener el link directo de descarga. Es como una forma de buscar. - Nupi
    file_id = re.search("/file/d/(.*?)/", url).group(1)
    direct_download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

    response = requests.get(direct_download_link)
    if response.status_code != 200:
        print(response.status_code)
        raise Exception("Error downloading file from google drive")

    osz_file = BytesIO(response.content)
    osz_zip = zipfile.ZipFile(osz_file)

    return search_osu_in_osz(osz_zip, diff)


def download_mediafire(url, diff):
    # Sirve para descargar archivos de mediafire (mapas unsubmitted de la db) - Nupi
    # re.search sirve para obtener el link directo de descarga. Es como una forma de buscar. - Nupi
    file_id = re.search("https://www.mediafire.com/file/(.*?)/", url).group(1)
    direct_download_link = f"https://download1653.mediafire.com/{file_id}/"

    response = requests.get(direct_download_link)
    if response.status_code != 200:
        raise Exception("Error downloading file from mediafire.com")

    osz_file = BytesIO(response.content)
    osz_zip = zipfile.ZipFile(osz_file)

    return search_osu_in_osz(osz_zip, diff)


def download_mega(url, diff):
    # Sirve para descargar archivos de mega.nz (mapas unsubmitted de la db) - Nupi
    # re.search sirve para obtener el link directo de descarga. Es como una forma de buscar. - Nupi
    file_id = re.search("https://mega.nz/file/(.*?)#", url).group(1)
    direct_download_link = f"https://mega.nz/file/{file_id}#"

    response = requests.get(direct_download_link)
    if response.status_code != 200:
        raise Exception("Error downloading file from mega.nz")

    osz_file = BytesIO(response.content)
    osz_zip = zipfile.ZipFile(osz_file)

    return search_osu_in_osz(osz_zip, diff)


# Obtener el hash para los mapas de osu descargados de otras fuentes (como google drive etc. NO ES NECESARIO PARA MAPAS
# OFICIALES DE OSU) - Nupi
def calculate_osu_map_hash(file):
    with file as db:
        data = db.read()
        hash = hashlib.md5(data).hexdigest()
        return hash


# Esta funcion principalmente abre el archivo .osu y busca la metadata del mapa. - Nupi
def get_osu_map_metadata(osu_map):
    metadata = {}

    osu_map_text = osu_map.read().decode("utf-8")
    lines = osu_map_text.split("\n")

    in_metadata_section = False
    for line in lines:
        line = line.strip()

        if line == "[Metadata]":
            in_metadata_section = True
        elif line == "":
            in_metadata_section = False
        elif in_metadata_section:
            key_value = line.split(":")
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                metadata[key] = value

    metadata["hash"] = calculate_osu_map_hash(osu_map)

    return metadata


def check_clear(clear):
    # re.search busca un patron en un string. En este caso, busca un numero seguido de un % (ej: 99%) - Nupi
    if re.search(r"\d+%", clear):
        return "accuracy"
    # re.match busca un patron en un string. En este caso, busca un numero de 1 a 6 digitos (ej: 999999) - Nupi
    elif re.match(r"\d{3}k", clear) or re.match(r"\d{6}", clear) or \
            (re.match(r"\d{1,6}", clear) and int(clear)):
        return "score"
    else:
        return clear


def clear_map(modo, nombre, id_mapa, clear):
    # Funcion que simplemente inserta los valores obtenidos en la db. - Nupi
    sql(
        "insert",
        "INSERT INTO public.submissions (modo, nombre, id_mapa, clear) VALUES (%s, %s, %s, %s)",
        modo, nombre, id_mapa, clear
    )


# Procesa los requerimientos del mapa segun los datos de la replay. (sentios libres de modificarlo para modularizar el
# codigo, yo lo hice asi porque me parecio mas facil) - Nupi
def process_requeriments(replay_data, modo, id, nombre, mods, clear):
    """map_requeriments: list of the requeriments of the map.
    replay_data: replay data."""

    r = replay_data

    count_320 = r.count_geki
    count_300 = r.count_300
    count_200 = r.count_katu
    count_100 = r.count_100
    count_50 = r.count_50
    misses = r.count_miss
    score = r.score
    user_mods = r.mods.name
    # Esto es para que los mods esten en minusculas y sin ningun caracter extraño y que esten divididos en una lista.
    # - Nupi
    unsplitted_user_mods = user_mods.split("|")
    splitted_mods = [mod.lower() for mod in unsplitted_user_mods]

    clear_type = check_clear(clear).lower()

    mods = mods.lower()

    # Check para comprobar que el usuario haya hecho el clear con los mods que dijo que uso. - Nupi
    if splitted_mods != mods.split(" "):
        return "Mods no coinciden"

    if clear_type == "accuracy":
        # Aqui creo clear acc para poder trabajar con el valor de clear sin el %. - Nupi
        clear_acc = float(clear.strip("%"))
        if modo == "standard":
            accuracy = standard_accuracy_calculation_formula(count_300, count_100, count_50, misses)
        elif modo == "mania":
            accuracy = mania_accuracy_calculation_formula(count_320, count_300, count_200, count_100, count_50, misses)
        elif modo == "taiko":
            accuracy = taiko_accuracy_calculation_formula(count_300, count_100, misses)
        else:
            return "Modo no reconocido"

        if accuracy >= clear_acc:
            clear_map(modo, nombre, id, clear)
        else:
            return "No se ha cumplido el requerimiento de accuracy"

    elif clear_type == "score":
        # Aqui hago un check para ver si el clear es en k (ej: 1k = 1000) y si es asi, lo convierto a un numero entero
        # (ej: 1000) - Nupi
        if len(clear) == 4 and clear[-1] == "k":
            clear_without_k = clear[:-1] + "000"
        if score >= clear_without_k:
            clear_map(modo, nombre, id, clear)
        else:
            return "No se ha cumplido el requerimiento de score"

    elif clear_type == "fc":
        if misses == 0:
            clear_map(modo, nombre, id, clear)
        else:
            return "No se ha cumplido el requerimiento de FC"

    # Good FC = FC solo con greats. (por favor dejad de inventaros estas nomenclaturas extrañas gracias) - Nupi
    elif clear_type == "gfc":
        if misses == 0 and count_50 == 0 and count_100 == 0 and count_300 >= 1:
            clear_map(modo, nombre, id, clear)
        else:
            return "No se ha cumplido el requerimiento de GFC"

    # Perfect FC = FC solo con perfects (usualmente utilizado en mapas V2) - Nupi
    elif clear_type == "pfc":
        if misses == 0 and count_50 == 0 and count_100 == 0 and count_200 == 0 and count_300 >= 1:
            clear_map(modo, nombre, id, clear)
        else:
            return "No se ha cumplido el requerimiento de PFC"


# ACC CALCULATIONS
# Esto está aqui por si acaso hace falta algún dia. - Nupi
def standard_accuracy_calculation_formula(three_hundred_count, one_hundred_count, fifty_count, miss_count):
    """Standard accuracy calculation formula."""
    formula = (
        (three_hundred_count * 300) + (one_hundred_count * 100) + (fifty_count * 50)
        ) / (
        300 * (three_hundred_count + one_hundred_count + fifty_count + miss_count)
        )
    formula = formula * 100
    formula = round(formula, 2)
    return formula


def mania_accuracy_calculation_formula(count_320, count_300, count_200, count_100, count_50, misses, v2=False):
    """Mania accuracy calculation formula."""
    # Aqui he añadido un if else para que se pueda calcular la accuracy de mapas con Score V2. - Nupi
    if v2:
        formula = ((305 * count_320) + (300 * count_300) + (200 * count_200) + (100 * count_100) + (50 * count_50)
                   ) / (
            305 * (count_320 + count_300 + count_200 + count_100 + count_50 + misses))
        formula = formula * 100
        formula = round(formula, 2)
    else:
        formula = (300 * (count_320 + count_300) + (count_200 * 200) + (count_100 * 100) + (count_50 * 50)
                   ) / (
            300 * (count_320 + count_300 + count_200 + count_100 + count_50 + misses))
        formula = formula * 100
        formula = round(formula, 2)
    return formula


def taiko_accuracy_calculation_formula(count_300, count_100, count_50, misses):
    """Taiko accuracy calculation formula."""
    formula = (count_300 + (0.5 * count_100)) / (count_300 + count_100 + count_50 + misses)
    formula = formula * 100
    formula = round(formula, 2)
    return formula


# TODO Catch accuracy calculation formula. (pendiente de añadir cuando se de soporte a este modo, que ademas, es un
# TODO pelmazo de calcular) - Nupi


if __name__ == "__main__":
    pass
