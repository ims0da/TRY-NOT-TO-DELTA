import general_functions as fnc
import time

# Sirve para obtener el hash de los mapas que no lo tienen y meterlos en la db. - Nupi


maps = fnc.sql("query", "SELECT id, link, diff FROM bd_mapas WHERE hash IS NULL")

threads = []

for map in maps:
    map_id = map[0]
    map_link = map[1]
    map_link = map_link.strip()
    map_diff = map[2]
    map_diff = map_diff.strip()
    if map_diff.startswith("["):
        map_diff = map_diff.strip("[")
    if map_diff.endswith("]"):
        map_diff = map_diff.strip("]")

    fnc.process_map(map_id, map_link, map_diff)
    time.sleep(0.5)

print("tasks finished.")
