"""Tkinter girişleri, oyun durumu ve kayıt işlemleri arasındaki bağlantı."""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from macera_kaydi import MaceraKaydi
from oyun_kurallari import DURAKLAR, SEVIYELER, Oyun, Sonuc


@dataclass(frozen=True)
class TurBasladi:
    pass


@dataclass(frozen=True)
class TahminDegerlendirildi:
    sonuc: Sonuc
    yeni_basarilar: tuple[str, ...] = ()
    kayit_hatasi: bool = False


class MaceraDenetleyicisi:
    def __init__(
        self,
        oyun: Oyun,
        kayit: MaceraKaydi,
        yayinla: Callable[[TurBasladi | TahminDegerlendirildi], None],
    ) -> None:
        self.oyun = oyun
        self.kayit = kayit
        self.yayinla = yayinla
        self.basarisiz_tur_sayisi = 0

    def zor_acik(self) -> bool:
        try:
            return self.kayit.zor_acik()
        except (OSError, sqlite3.Error):
            return False

    def baslat(self, zorluk: str) -> bool:
        if zorluk == "Zor" and not self.zor_acik():
            return False
        self.oyun.baslat(zorluk)
        self.yayinla(TurBasladi())
        return True

    def yeni_tur(self) -> None:
        self.oyun.yeni_tur()
        self.yayinla(TurBasladi())

    def sifirla(self) -> None:
        self.oyun.sifirla()
        self.basarisiz_tur_sayisi = 0

    def tahmin_et(self, metin: str) -> None:
        self.sonucu_yayinla(self.oyun.tahmin_et(metin))

    def sureyi_denetle(self) -> bool:
        sonuc = self.oyun.sureyi_kontrol_et()
        if sonuc is None:
            return True
        self.sonucu_yayinla(sonuc)
        return False

    def ipucu_kullan(self) -> tuple[int, ...] | None:
        return self.oyun.ipucu_kullan()

    def guclendirici_kullan(self, ad: str) -> tuple[int, ...] | bool | None:
        return self.oyun.guclendirici_kullan(ad)

    def duraklat(self) -> None:
        self.oyun.duraklat()

    def surdur(self) -> None:
        self.oyun.surdur()

    def bolge(self) -> dict:
        return next(durak for durak in reversed(DURAKLAR) if durak["puan"] <= self.oyun.toplam)

    def hikaye(self) -> str:
        ayar = SEVIYELER[self.oyun.zorluk]
        if self.basarisiz_tur_sayisi >= 2:
            return ayar["engelli_yol"]
        durak = self.bolge()
        return ayar["hikaye"] if durak["puan"] == 0 else durak["hikaye"]

    def sonucu_yayinla(self, sonuc: Sonuc) -> None:
        if sonuc.durum in ("sure_bitti", "bitti"):
            self.basarisiz_tur_sayisi += 1
        if sonuc.durum != "dogru":
            self.yayinla(TahminDegerlendirildi(sonuc))
            return

        basarilar = tuple(ad for ad, kazanildi in (
            ("hatasiz_tur", sonuc.ilk_tahmin),
            ("hiz_canavari", sonuc.hizli_tur),
        ) if kazanildi)
        try:
            if self.oyun.kazanildi:
                zorluk = self.oyun.zorluk
                yeni_basarilar = self.kayit.kaydet(
                    zorluk, SEVIYELER[zorluk]["harita"], self.oyun.toplam, self.oyun.tur,
                    basarilar=basarilar,
                )
            else:
                yeni_basarilar = self.kayit.basari_kaydet(*basarilar) if basarilar else ()
        except (OSError, sqlite3.Error):
            self.yayinla(TahminDegerlendirildi(sonuc, kayit_hatasi=True))
        else:
            self.yayinla(TahminDegerlendirildi(sonuc, yeni_basarilar))
