"""Bu bilgisayarda bitirilen maceraların ve kazanılan başarıların yerel kaydı."""

import os
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path


BASARILAR = {
    "ilk_galibiyet": "İlk Galibiyet",
    "hatasiz_tur": "Hatasız Tur",
    "hiz_canavari": "Hız Canavarı",
}


class MaceraKaydi:
    def __init__(self, yol: str | os.PathLike[str] | None = None) -> None:
        uygulama_verileri = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        self.yol = Path(yol) if yol else uygulama_verileri / "SayiTahminMacerasi" / "maceralar.sqlite3"

    def baglan(self) -> sqlite3.Connection:
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.yol)

    @staticmethod
    def tablolari_olustur(baglanti: sqlite3.Connection) -> None:
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
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS basarilar (
                ad TEXT PRIMARY KEY NOT NULL
            )
        """)

    @staticmethod
    def _basarilari_ekle(
        baglanti: sqlite3.Connection, basarilar: Iterable[str]
    ) -> tuple[str, ...]:
        yeni = []
        for ad in basarilar:
            if ad not in BASARILAR or ad == "ilk_galibiyet":
                raise ValueError(f"Geçersiz tur başarısı: {ad}")
            eklenen = baglanti.execute("INSERT OR IGNORE INTO basarilar (ad) VALUES (?)", (ad,))
            if eklenen.rowcount:
                yeni.append(ad)
        return tuple(yeni)

    def kaydet(
        self, zorluk: str, harita: str, puan: int, tur: int, *, basarilar: Iterable[str] = ()
    ) -> tuple[str, ...]:
        with closing(self.baglan()) as baglanti, baglanti:
            self.tablolari_olustur(baglanti)
            ilk_galibiyet = baglanti.execute("""
                INSERT OR IGNORE INTO basarilar (ad)
                SELECT 'ilk_galibiyet' WHERE NOT EXISTS (SELECT 1 FROM maceralar)
            """).rowcount
            baglanti.execute(
                "INSERT INTO maceralar (zorluk, harita, puan, tur) VALUES (?, ?, ?, ?)",
                (zorluk, harita, puan, tur),
            )
            yeni = self._basarilari_ekle(baglanti, basarilar)
            return ("ilk_galibiyet", *yeni) if ilk_galibiyet else yeni

    def basari_kaydet(self, *basarilar: str) -> tuple[str, ...]:
        if not basarilar:
            return ()
        with closing(self.baglan()) as baglanti, baglanti:
            self.tablolari_olustur(baglanti)
            return self._basarilari_ekle(baglanti, basarilar)

    def basarilar(self) -> frozenset[str]:
        if not self.yol.exists():
            return frozenset()
        with closing(self.baglan()) as baglanti:
            tablolar = {
                ad for (ad,) in baglanti.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            kazanilan = set()
            if "basarilar" in tablolar:
                kazanilan.update(ad for (ad,) in baglanti.execute("SELECT ad FROM basarilar"))
            if "maceralar" in tablolar and baglanti.execute("SELECT 1 FROM maceralar LIMIT 1").fetchone():
                kazanilan.add("ilk_galibiyet")
            return frozenset(kazanilan)

    def zor_acik(self) -> bool:
        return "ilk_galibiyet" in self.basarilar()

    def galeri(self) -> tuple[
        list[tuple[str, int, int]], list[tuple[int, str, str, int, str]], int
    ]:
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
