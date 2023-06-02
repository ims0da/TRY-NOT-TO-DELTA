import math
import discord
from tabulate import tabulate

ROWS_PER_PAGE = 8


def tabla_embed(results):
    page_list = []
    table_rows = [row for row in results]

    num_pages = math.ceil(len(table_rows) / ROWS_PER_PAGE)

    for page in range(num_pages):
        start_index = page * ROWS_PER_PAGE
        end_index = start_index + ROWS_PER_PAGE
        page_rows = table_rows[start_index:end_index]

        page_embed = discord.Embed(
            title=f"Tabla (Página {page + 1}/{num_pages})"
            )

        for row in page_rows:
            page_embed.add_field(
                name=f"Mapa {row[0]}: ",
                value=f"[{row[1]} - {row[4]}]({row[3]})",
                inline=True
                )
            page_embed.add_field(
                name="Puntos: ",
                value=f"{row[2]}",
                inline=True
                )
            page_embed.add_field(
                name="Requirement: ",
                value=f"{row[5]}, {row[6]}",
                inline=True
                )
        page_list.append(page_embed)
        return page_list


def crear_tabla_players(results):
    sorted_results = sorted(
        results,
        key=lambda row: row[1],
        reverse=True
        )
    headers = ['Nombre', 'Puntos']
    formatted_player_list = (
        tabulate(sorted_results, headers, tablefmt='pipe')
        )
    return formatted_player_list
