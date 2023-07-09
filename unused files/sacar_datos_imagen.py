import os
import pytesseract
# from io import BytesIO
from PIL import Image

RES_REFERENCIA_X = 2560
RES_REFERENCIA_Y = 1440

# Codigo incompleto. Utiliza pytesseract para sacar el nombre del jugador de una imagen. (puede servir para mas cosas)
# - Nupi.

def sacar_nombre_jugador(ancho, alto, imagen):
    coord_punto_inicio_region_x = 10 / RES_REFERENCIA_X
    coord_punto_inicio_region_y = 105 / RES_REFERENCIA_Y
    coord_punto_final_region_x = 770 / RES_REFERENCIA_X
    coord_punto_final_region_y = 153 / RES_REFERENCIA_Y

    x1 = int(coord_punto_inicio_region_x * ancho)
    y1 = int(coord_punto_inicio_region_y * alto)
    x2 = int(coord_punto_final_region_x * ancho)
    y2 = int(coord_punto_final_region_y * alto)

    region = (x1, y1, x2, y2)

    region_imagen = imagen.crop(region)
    text = pytesseract.image_to_string(region_imagen)
    splitted_text = text.split("by ")
    text = splitted_text[1].split(" on")[0]
    return text


path = os.path.join("C:", "Program Files", "Tesseract-OCR", "tesseract.exe")
pytesseract.pytesseract.tesseract_cmd = path

# imagen = BytesIO(await imagen.read())
imagen = Image.open("screenshot065.jpg")

ancho, alto = imagen.size

text = sacar_nombre_jugador(ancho, alto, imagen)

print(text)
