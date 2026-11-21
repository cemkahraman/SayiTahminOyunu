"""Bu bilgisayarda bitirilen maceraların yerel kaydı."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path


class MaceraKaydi:
    def __init__(self, yol=None):
        uygulama_verileri = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.yol = Path(yol) if yol else uygulama_verileri / "SayiTahminMacerasi" / "maceralar.sqlite3"

    def baglan(self):
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.yol)

    def kaydet(self, zorluk, harita, puan, tur):
        with closing(self.baglan()) as baglanti, baglanti:
            baglanti.execute("""
                CREATE TABLE IF NOT EXISTS maceralar (
                    id INTEGER PRIMARY KEY,
                    zorluk TEXT NOT NULL,
                    harita TEXT NOT NULL,
                    puan INTEGER NOT NULL,
                    tur INTEGER NOT NULL,
                    tarih TEXT NOT NULL DEFAULT (date('now', 'localtime'))
                )
            """)
            baglanti.execute(
                "INSERT INTO maceralar (zorluk, harita, puan, tur) VALUES (?, ?, ?, ?)",
                (zorluk, harita, puan, tur),
            )

    def galeri(self):
        if not self.yol.exists():
            return [], [], 0
        with closing(self.baglan()) as baglanti:
            haritalar = baglanti.execute("""
                SELECT harita, COUNT(*), MAX(puan) FROM maceralar
                GROUP BY harita ORDER BY MAX(puan) DESC, harita
            """).fetchall()
            rekorlar = baglanti.execute("""
                SELECT puan, harita, zorluk, tur, tarih FROM maceralar
                ORDER BY puan DESC, tur ASC, id DESC LIMIT 10
            """).fetchall()
            zor_galibiyet = baglanti.execute(
                "SELECT COUNT(*) FROM maceralar WHERE zorluk = ?", ("Zor",)
            ).fetchone()[0]
        return haritalar, rekorlar, zor_galibiyet
