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
    # Funcion que itera sobre todos los mapas de la base de datos y les calcula el hash. - Nupi
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
    # Funcion que sirve para descargar los mapas de osu desde un link de discord. - Nupi
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


def search_osu_in_osz(osz_zip, diff: str):
    # Esta funcion busca el archivo .osu dentro del .osz de la dificultad escogida. (por eso es importante poner las
    # dificultados sin corchetes y exactamente igual que en el mapa.) - Nupi
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


def calculate_osu_map_hash(file):
    # Obtener el hash para los mapas de osu descargados de otras fuentes (como google drive etc. NO ES NECESARIO PARA
    # MAPAS OFICIALES DE OSU) - Nupi
    with file as db:
        data = db.read()
        hash = hashlib.md5(data).hexdigest()
        return hash


def get_osu_map_metadata(osu_map):
    # Esta funcion principalmente abre el archivo .osu y busca la metadata del mapa. - Nupi
    metadata = {}

    osu_map_text = osu_map.read().decode("utf-8")
    lines = osu_map_text.split("\n")

    in_metadata_section = False
    for line in lines:
        line = line.strip()

        # Este bloque de codigo busca cuando empieza la linea de metadata y cuando termina. - Nupi
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
    if clear.endswith("%"):
        return "accuracy"
    # re.match busca un patron en un string. En este caso, busca un numero de 1 a 6 digitos (ej: 999999) - Nupi
    elif re.match(r"\d{3}k", clear):
        return "score"
    else:
        return clear


def get_db_data(r):
    """Output: modo, id_mapa, nombre, mods, clear"""
    # Gracias shiro
    # Esta funcion sirve para obtener los datos de la base de datos donde el hash sea igual al hash de la replay.
    # si esta repetido se obtienen 2 datos o mas en una lista y se itera sobre ellos. - Nupi
    modo = sql("query", "SELECT modo FROM public.bd_mapas WHERE hash in "
               "(SELECT hash from public.bd_mapas where hash = %s group by hash having count(*) > 1)", r.beatmap_hash)
    if modo == []:
        modo = sql("query", "SELECT modo FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
    id_mapa = sql("query", "SELECT id FROM public.bd_mapas WHERE hash in "
                  "(SELECT hash from public.bd_mapas where hash = %s group by hash having count(*) > 1)", r.beatmap_hash
                  )
    if id_mapa == []:
        id_mapa = sql("query", "SELECT id FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
    nombre_usuario = r.username
    mods = sql("query", "SELECT mods FROM public.bd_mapas WHERE hash in "
               "(SELECT hash from public.bd_mapas where hash = %s group by hash having count(*) > 1)", r.beatmap_hash)
    if mods == []:
        mods = sql("query", "SELECT mods FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
    clear = sql("query", "SELECT clear FROM public.bd_mapas WHERE hash in "
                "(SELECT hash from public.bd_mapas WHERE hash = %s group by hash having count(*) > 1)", r.beatmap_hash)
    if clear == []:
        clear = sql("query", "SELECT clear FROM public.bd_mapas WHERE hash = %s", r.beatmap_hash)
    return modo, id_mapa, nombre_usuario, mods, clear


def clear_map(modo, nombre, id_mapa, clear):
    # Funcion que simplemente inserta los valores obtenidos en la db y antes de eso chequea si ya se ha hecho ese
    # clear. - Nupi
    result = sql(
        "query",
        "SELECT count(*) FROM public.submissions WHERE modo = %s AND nombre = %s AND id_mapa = %s",
        modo, nombre, id_mapa
    )
    if not result[0][0] == 0:
        raise exc.MapAlreadyClearedError

    try:
        sql(
            "insert",
            "INSERT INTO public.submissions (modo, nombre, id_mapa, clear) VALUES (%s, %s, %s, %s)",
            modo, nombre, id_mapa, clear
        )
    except Exception as e:
        raise Exception(f"Error inserting clear into database: {e}")


def get_osu_username_from_profile(profile_link):
    # Funcion que parte el link de un perfil de osu por "/" y devuelve el id de usuario. - Nupi
    parts = profile_link.split("/")
    if len(parts) >= 4:
        username = parts[4]
        return username
    else:
        return None


def process_requeriments(replay_data, modo, id, nombre, mods, clear):
    """map_requeriments: list of the requeriments of the map.
    replay_data: replay data."""
    # Procesa los requerimientos del mapa segun los datos de la replay. (sentios libres de modificarlo para modularizar
    # el codigo, yo lo hice asi porque me parecio mas facil). Esta es la funcion mas larga y compleja. - Nupi

    # Este bloque de codigo es para obtener los datos y ponerlos en un formato especifico. - Nupi
    # Lo unico que hago es acceder a datos en distintas listas simplemente por la forma en la que se guardan en la db.
    print(modo)
    print(modo[0][0])
    modo = modo[0][0]
    id = id[0][0]
    mods = mods[0]
    mods = list(mods)
    mods = [mod.strip() for mod in mods]
    mods = [mod.lower() for mod in mods]
    clear = clear[0][0]

    modo = modo.strip()
    id = str(id).strip()
    nombre = nombre.strip()
    clear = clear.strip()

    if clear == "SS":
        clear = "100%"

    # Aqui obtengo los datos de la replay y los pongo en variables. - Nupi

    nombre_db = sql("query", "SELECT nombre FROM public.bd_players WHERE nombre = %s", nombre)
    print(nombre_db)

    if nombre_db == []:
        raise exc.PlayerNotFoundError

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

    # Esto es un check para ver si el usuario tiene nightcore y si lo tiene lo cambia por doubletime. (como es lo
    # mismo doubletime que nightcore pues asi nos ahorramos problemas). - Nupi
    if "nightcore" in splitted_mods:
        splitted_mods.remove("nightcore")
        splitted_mods.append("doubletime")

    if "mirror" in splitted_mods:
        splitted_mods.remove("mirror")
        splitted_mods.append("nomod")

    # Esto chequea si el clear es de acc de combo o de lo que sea para hacer una cosa u otra.
    clear_type = check_clear(clear).lower()

    user_mods = user_mods.lower()

    # Esto es el bloque de ifs mas grande de mi vida sirve para formatear todos los mods a una forma especifica para
    # que se puedan comparar con los mods de la db. - Nupi
    if "nm" in mods:
        mods = [mod.replace("nm", "nomod") for mod in mods]
    if "hr" in mods:
        mods = [mod.replace("hr", "hardrock") for mod in mods]
    if "hd" in mods:
        mods = [mod.replace("hd", "hidden") for mod in mods]
    if "dt" in mods or "nc" in mods:
        mods = [mod.replace("dt", "doubletime") for mod in mods]
    if "ez" in mods:
        mods = [mod.replace("ez", "easy") for mod in mods]
    if "ht" in mods:
        mods = [mod.replace("ht", "halftime") for mod in mods]
    if "fl" in mods:
        mods = [mod.replace("fl", "flashlight") for mod in mods]
    if "rx" in mods:
        mods = [mod.replace("rx", "relax") for mod in mods]
    if "v2" in mods:
        mods = [mod.replace("v2", "scorev2") for mod in mods]
    if "nf" in mods:
        mods = [mod.replace("nf", "nofail") for mod in mods]
    # https://i.kym-cdn.com/entries/icons/facebook/000/032/492/cover3.jpg - Nupi

    # Check para comprobar que el usuario haya hecho el clear con los mods que dijo que uso. - Nupi
    if mods != splitted_mods:
        # Si se raisea esto, hay un for loop que vuelve a ejecutar esta funcion las veces que se repita el mapa en la db
        # así podemos chequear diferentes clear requeriments.
        raise exc.ModsDontMatchError()

    # Aqui es donde utilizo lo del clear_type. (que simplemente devolvia una string con el tipo de clear que era).
    if clear_type == "accuracy":
        # Aqui creo clear acc para poder trabajar con el valor de clear sin el %. - Nupi
        clear_acc = float(clear.strip("%"))
        # Dependiendo del modo calculo la accuracy de una forma u otra. - Nupi
        if modo == "standard":
            accuracy = standard_accuracy_calculation_formula(count_300, count_100, count_50, misses)
        elif modo == "4k" or modo == "7k":
            accuracy = mania_accuracy_calculation_formula(count_320, count_300, count_200, count_100, count_50, misses)
        elif modo == "taiko":
            accuracy = taiko_accuracy_calculation_formula(count_300, count_100, misses)
        else:
            return "Modo no reconocido"

        if accuracy >= clear_acc:
            clear_map(modo, nombre, id, clear)
        else:
            raise exc.ClearNotAcceptedError

    elif clear_type == "score":
        # Aqui hago un check para ver si el clear es en k (ej: 1k = 1000) y si es asi, lo convierto a un numero entero
        # (ej: 1000) - Nupi
        if len(clear) == 4 and clear[-1] == "k":
            clear_without_k = clear[:-1] + "000"
        if score >= clear_without_k:
            clear_map(modo, nombre, id, clear)
        else:
            raise exc.ClearNotAcceptedError

    elif clear_type == "fc":
        if misses == 0:
            clear_map(modo, nombre, id, clear)
        else:
            raise exc.ClearNotAcceptedError

    # Good FC = FC solo con greats. (por favor dejad de inventaros estas nomenclaturas extrañas gracias) - Nupi
    elif clear_type == "gfc":
        if misses == 0 and count_50 == 0 and count_100 == 0 and count_300 >= 1:
            clear_map(modo, nombre, id, clear)
        else:
            raise exc.ClearNotAcceptedError

    # Perfect FC = FC solo con perfects (usualmente utilizado en mapas V2) - Nupi
    elif clear_type == "pfc":
        if misses == 0 and count_50 == 0 and count_100 == 0 and count_200 == 0 and count_300 >= 1:
            clear_map(modo, nombre, id, clear)
        else:
            raise exc.ClearNotAcceptedError

    else:
        raise Exception("Something went wrong. Please contact the developer.")


# ACC CALCULATIONS
def standard_accuracy_calculation_formula(three_hundred_count, one_hundred_count, fifty_count, miss_count):
    """Standard accuracy calculation formula."""
    # Esto está aqui por si acaso hace falta algún dia. - Nupi
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
