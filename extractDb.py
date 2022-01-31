import os
import sqlite3
import numpy
import pandas as pd
import time


def extract():
    db = str(input(r"Entrez le chemin de la bdd: "))
    connexion = sqlite3.connect(db)
    cursor = connexion.cursor()

    path = os.path.join("/Users", os.getlogin(), "Desktop")

    jour = f"{time.localtime().tm_mday}-{time.localtime().tm_mon}-{time.localtime().tm_year}({time.localtime().tm_hour}-{time.localtime().tm_min}-{time.localtime().tm_sec})"
    columHeaders = ["designation", "prix", "qtt", "codebar"]

    df = pd.DataFrame(columns=columHeaders)

    cursor.execute("SELECT title, prix, qtt, barcode FROM posts")
    datas = cursor.fetchall()
    cursor.execute("SELECT vendu FROM posts")
    vendus = cursor.fetchall()
    print(vendus)
    i = 0
    x = 0
    init = 0
    for row in datas:
        y = 0
        for ro in row:
            if y == 2:
                try:
                    df.at[i, columHeaders[y]] = int(ro) - int(vendus[x][init])
                except:
                    df.at[i, columHeaders[y]] = int(ro) - int(vendus[0][int(x) - 1])
            else:
                df.at[i, columHeaders[y]] = str(ro)

            y += 1
        i += 1
        x += 1
    df.to_html(f'{path}/produits{jour}.html', index=False)
    df.to_excel(f'{path}/produits{jour}.xlsx', index=False)

    cursor.close()
    connexion`.close()


extract()
