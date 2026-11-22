"""CLI ve Tkinter sürümlerinin ortak oyun kuralları ve tur durumu."""

import json
import random
from bisect import bisect_left, bisect_right
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from time import monotonic


HEDEF_PUAN = 25
EN_KUCUK_SAYI = 10
EN_BUYUK_SAYI = 1000
SAYI_ADIMI = 10
DINAMIK_SAYI_ADIMI = 20
IPUCU_YARICAPI = 100
TUR_SURESI = 60
DONDURMA_SURESI = 5
HIZLI_TUR_SURESI = 12
HIZLI_TUR_HAKKI = 2
DINAMIK_TUR_SERISI = 3
DINAMIK_EN_YUKSEK_SEVIYE = 3
DINAMIK_ARALIK_ARTISI = 200
GUCLENDIRICILER = {
    "dondur": "Zamanı Durdur",
    "gozlem": "Gözlem",
    "kalkan": "Can Kurtarma",
}

def macera_verilerini_yukle(yol: Path) -> dict:
    with yol.open(encoding="utf-8") as dosya:
        veriler = json.load(dosya)

    def alanlari_dogrula(oge: object, konum: str, alanlar: dict[str, type]) -> None:
        if not isinstance(oge, dict):
            raise ValueError(f"{yol.name}: {konum} bir nesne olmalı.")
        for alan, beklenen in alanlar.items():
            deger = oge.get(alan)
            if type(deger) is not beklenen or (beklenen is str and not deger.strip()):
                raise ValueError(f"{yol.name}: {konum}.{alan} alanı geçersiz.")

    alanlari_dogrula(veriler, "macera", {"seviyeler": dict, "duraklar": list})
    seviyeler = veriler["seviyeler"]
    if set(seviyeler) != {"Kolay", "Orta", "Zor"}:
        raise ValueError(f"{yol.name}: Kolay, Orta ve Zor seviyeleri gerekli.")
    sayisal_alanlar = ("hak", "ipucu", "carpan", "ceza", "gosterilen_tahmin", "hizli_tur_serisi")
    metin_alanlari = ("renk", "harita", "hikaye", "engelli_yol", "son")
    for ad, ayar in seviyeler.items():
        alanlari_dogrula(ayar, ad, {
            **dict.fromkeys(sayisal_alanlar, int), **dict.fromkeys(metin_alanlari, str),
        })
        if any(ayar[alan] < 0 for alan in sayisal_alanlar) or min(
            ayar["hak"], ayar["carpan"], ayar["hizli_tur_serisi"],
        ) == 0:
            raise ValueError(f"{yol.name}: {ad} seviyesinde geçersiz sayısal ayar.")

    puanlar = []
    for i, durak in enumerate(veriler["duraklar"]):
        konum = f"duraklar[{i}]"
        alanlar = dict.fromkeys(("ad", "simge", "zemin", "yol", "resim"), str)
        if i:
            alanlar["hikaye"] = str
        alanlari_dogrula(durak, konum, {**alanlar, "puan": int})
        odak = durak.get("yatay_odak", 0.5)
        if type(odak) not in (int, float) or not 0 <= odak <= 1:
            raise ValueError(f"{yol.name}: {konum}.yatay_odak alanı geçersiz.")
        puanlar.append(durak["puan"])
    if not puanlar or puanlar[0] != 0 or puanlar[-1] >= HEDEF_PUAN or sorted(set(puanlar)) != puanlar:
        raise ValueError(f"{yol.name}: Durak puanları sıfırdan başlamalı ve hedefe kadar artmalı.")
    return veriler


_veriler = macera_verilerini_yukle(Path(__file__).with_name("macera_verileri.json"))
SEVIYELER = _veriler["seviyeler"]
DURAKLAR = _veriler["duraklar"]
YAKINLIK = (
    (30, "🔥 Çok yakın!"),
    (60, "😊 Yakın."),
    (100, "🙂 Biraz yakın."),
    (150, "🌡️ Yaklaşıyorsun."),
    (300, "😐 Biraz uzak."),
    (500, "🧊 Uzak."),
    (float("inf"), "❄️ Çok uzak!"),
)


@dataclass(frozen=True)
class Sonuc:
    durum: str
    yon: str = ""
    yakinlik: str = ""
    puan: int = 0
    yakinlik_araligi: str = ""
    sayi: int | None = None
    ilk_tahmin: bool = False
    hizli_tur: bool = False


def yakinlik_araliklari(ust_sinir: int = EN_BUYUK_SAYI) -> Iterator[tuple[float, str, str]]:
    alt = SAYI_ADIMI
    for esik, etiket in YAKINLIK:
        ust = min(esik, ust_sinir - EN_KUCUK_SAYI)
        yield esik, etiket, f"{alt}–{ust} sayı farkı"
        alt = ust + SAYI_ADIMI


def seviye_ozeti(ayar: Mapping[str, int | str]) -> str:
    return (
        f"{ayar['hak']} tahmin · {ayar['ipucu']} ipucu · "
        f"Başarısız tur −{ayar['ceza']} puan"
        + (f" · {ayar['carpan']}× kazanç" if ayar["carpan"] != 1 else "")
    )


def kurallar_metni(*, uyarlanabilir: bool = False) -> str:
    seviyeler = "\n".join(
        f"{ad}: {seviye_ozeti(ayar)}"
        for ad, ayar in SEVIYELER.items()
    )
    zorluk_metni = (
        f"Art arda {DINAMIK_TUR_SERISI} tur kazandığında sonraki turun sayı aralığı genişler "
        f"ve başarısız tur cezası artar. Zorluk en fazla {DINAMIK_EN_YUKSEK_SEVIYE} kez artar. "
        "Bir tur kaybetmek seriyi sıfırlar. "
        "Kazandığın zorluk artışı oyun açık kaldığı sürece devam eder."
        if uyarlanabilir
        else "Seçtiğin zorluk oyun bitene kadar sabit kalır."
    )
    return (
        f"🎯 Amaç: Toplam {HEDEF_PUAN} puana ulaş.\n\n"
        f"Sayılar {EN_KUCUK_SAYI}–{EN_BUYUK_SAYI} arasındaki {SAYI_ADIMI}'un katlarıdır. "
        "Geçersiz veya tekrarlanan tahminler hak götürmez.\n\n"
        "İlk tahminde 10 puan kazanırsın. Sonraki her tahminde kazanacağın puan 1 azalır. "
        "Toplam puanın 0'ın altına inmez.\n\n"
        f"{seviyeler}\n\n"
        f"T tuşu ipucu verir. {zorluk_metni}\n\n"
        "Yakınlık aralıkları\n"
        + "\n".join(f"{metin}  {aralik}" for _, metin, aralik in yakinlik_araliklari())
    )


class Oyun:
    def __init__(
        self,
        rastgele_sayi: Callable[[], int] | None = None,
        *,
        sureli: bool = False,
        saat: Callable[[], float] = monotonic,
        uyarlanabilir: bool = False,
    ) -> None:
        self.rastgele_sayi = rastgele_sayi
        self.sureli = sureli
        self.saat = saat
        self.uyarlanabilir = uyarlanabilir
        self._dogru_tur_serisi = 0
        self._kazanilan_dinamik_seviye = 0
        self.sifirla()

    def sifirla(self) -> None:
        self.toplam = 0
        self.tur = 0
        self.zorluk = None
        self.hedef = None
        self.kalan_hak = 0
        self.kalan_ipucu = 0
        self.gecmis: set[int] = set()
        self.aktif = False
        self.adim = SAYI_ADIMI
        self.dinamik_seviye = self._kazanilan_dinamik_seviye
        self.hizli_tur_serisi = 0
        self.kullanilan_guclendiriciler: set[str] = set()
        self.kalkan_aktif = False
        self.baslangic = None
        self.son_zaman = None
        self.donma_sonu = None
        self.duraklama_zamani = None

    @property
    def kazanildi(self) -> bool:
        return self.toplam >= HEDEF_PUAN

    def baslat(self, zorluk: str) -> None:
        if self.zorluk is not None or zorluk not in SEVIYELER:
            raise ValueError("Geçersiz zorluk veya başlamış oyun")
        self.zorluk = zorluk
        self.yeni_tur()

    def yeni_tur(self) -> None:
        if self.zorluk is None or self.aktif or self.kazanildi:
            raise ValueError("Yeni tur şu anda başlatılamaz")
        ayar = SEVIYELER[self.zorluk]
        self.tur += 1
        self.dinamik_seviye = self._kazanilan_dinamik_seviye
        self.adim = DINAMIK_SAYI_ADIMI if self.hizli_tur_serisi >= ayar["hizli_tur_serisi"] else SAYI_ADIMI
        self.hedef = self.rastgele_sayi() if self.rastgele_sayi else random.choice(self.adaylar)
        self.kalan_hak = ayar["hak"]
        self.kalan_ipucu = ayar["ipucu"]
        self.gecmis = set()
        self.baslangic = self.saat()
        self.son_zaman = self.baslangic + TUR_SURESI if self.sureli else None
        self.duraklama_zamani = self.donma_sonu = None
        self.aktif = True

    @property
    def adaylar(self) -> range:
        ilk = EN_KUCUK_SAYI + (-EN_KUCUK_SAYI % self.adim)
        ust = EN_BUYUK_SAYI + DINAMIK_ARALIK_ARTISI * self.dinamik_seviye
        return range(ilk, ust + 1, self.adim)

    @property
    def tur_cezasi(self) -> int:
        return SEVIYELER[self.zorluk]["ceza"] + self.dinamik_seviye

    @property
    def kalan_donma_suresi(self) -> float:
        if not self.aktif or self.donma_sonu is None:
            return 0
        return max(0, self.donma_sonu - self.simdi())

    def simdi(self) -> float:
        return self.duraklama_zamani if self.duraklama_zamani is not None else self.saat()

    @property
    def kalan_sure(self) -> float | None:
        if self.son_zaman is None:
            return None
        simdi = self.simdi()
        if self.donma_sonu is not None:
            simdi = max(simdi, self.donma_sonu)
        return max(0, self.son_zaman - simdi)

    def duraklat(self) -> None:
        if self.aktif and self.sureli and self.duraklama_zamani is None:
            self.duraklama_zamani = self.saat()

    def surdur(self) -> None:
        if self.duraklama_zamani is None:
            return
        gecikme = self.saat() - self.duraklama_zamani
        if self.donma_sonu is not None and self.donma_sonu > self.duraklama_zamani:
            self.donma_sonu += gecikme
        self.baslangic += gecikme
        self.son_zaman += gecikme
        self.duraklama_zamani = None

    def sureyi_kontrol_et(self) -> Sonuc | None:
        if self.aktif and self.kalan_sure == 0:
            return self.basarisiz_tur("sure_bitti")
        return None

    def guclendirici_kullan(self, ad: str) -> bool | tuple[int, ...] | None:
        if not self.aktif or ad not in GUCLENDIRICILER or ad in self.kullanilan_guclendiriciler:
            return None
        if ad == "dondur" and (not self.sureli or not self.kalan_sure):
            return None
        self.kullanilan_guclendiriciler.add(ad)
        if ad == "dondur":
            self.donma_sonu = self.saat() + DONDURMA_SURESI
            self.son_zaman += DONDURMA_SURESI
        elif ad == "kalkan":
            self.kalkan_aktif = True
        else:
            en_yakin = sorted(self.adaylar, key=lambda sayi: abs(sayi - self.hedef))[:3]
            return tuple(sorted(en_yakin))
        return True

    def tahmin_et(self, metin: str | int) -> Sonuc:
        if not self.aktif:
            return Sonuc("pasif")
        zaman_asimi = self.sureyi_kontrol_et()
        if zaman_asimi:
            return zaman_asimi
        try:
            sayi = int(str(metin).strip())
        except ValueError:
            return Sonuc("gecersiz_tamsayi")
        if sayi not in self.adaylar:
            return Sonuc("gecersiz_aralik")
        if sayi in self.gecmis:
            return Sonuc("tekrar")

        self.gecmis.add(sayi)
        self.kalan_hak -= 1
        if sayi == self.hedef:
            puan = max(1, 11 - len(self.gecmis)) * SEVIYELER[self.zorluk]["carpan"]
            self.toplam += puan
            self.aktif = False
            hizli_tur = (
                self.sureli
                and len(self.gecmis) <= HIZLI_TUR_HAKKI
                and self.saat() - self.baslangic <= HIZLI_TUR_SURESI
            )
            self.hizli_tur_serisi = self.hizli_tur_serisi + 1 if hizli_tur else 0
            if self.uyarlanabilir:
                self._dogru_tur_serisi += 1
                if self._dogru_tur_serisi % DINAMIK_TUR_SERISI == 0:
                    self._kazanilan_dinamik_seviye = min(
                        DINAMIK_EN_YUKSEK_SEVIYE, self._kazanilan_dinamik_seviye + 1
                    )
            return Sonuc(
                "dogru", puan=puan, sayi=sayi, ilk_tahmin=len(self.gecmis) == 1, hizli_tur=hizli_tur
            )
        if self.kalan_hak == 0:
            return self.basarisiz_tur("bitti", sayi=sayi)
        fark = abs(sayi - self.hedef)
        _, yakinlik, aralik = next(
            bant for bant in yakinlik_araliklari(self.adaylar[-1]) if fark <= bant[0]
        )
        return Sonuc(
            "yanlis", "buyuk" if sayi < self.hedef else "kucuk", yakinlik,
            yakinlik_araligi=aralik, sayi=sayi,
        )

    def basarisiz_tur(self, durum: str, *, sayi: int | None = None) -> Sonuc:
        ceza = 0 if self.kalkan_aktif else min(self.toplam, self.tur_cezasi)
        self.toplam -= ceza
        self.kalkan_aktif = False
        self.hizli_tur_serisi = 0
        self._dogru_tur_serisi = 0
        self.aktif = False
        return Sonuc(durum, puan=-ceza, sayi=sayi)

    def ipucu_kullan(self) -> tuple[int, ...] | None:
        if not self.aktif:
            return None
        if self.kalan_ipucu == 0:
            return ()
        self.kalan_ipucu -= 1
        adaylar = self.adaylar
        alt = bisect_left(adaylar, self.hedef - IPUCU_YARICAPI)
        ust = bisect_right(adaylar, self.hedef + IPUCU_YARICAPI) - 1
        return (adaylar[alt], adaylar[ust])
