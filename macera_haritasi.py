"""Macera yolunu ve Canvas üzerindeki kısa oyun efektlerini çizer."""

import math
import random
import tkinter as tk

from oyun_kurallari import DURAKLAR, HEDEF_PUAN


class MaceraHaritasi(tk.Canvas):
    def __init__(self, ebeveyn, **ayarlar):
        super().__init__(ebeveyn, **ayarlar)
        self.puan = 0
        self.kivrimlar = ()
        self.tahmin_izleri: list[int] = []
        self.oyuncu_konumu: tuple[float, float] | None = None
        self.zamanlayici = None
        self.parilti_zamanlayici = None
        self.sarsinti = 0
        self.yeni_rota()
        self.bind("<Configure>", lambda _olay: self.ciz(self.puan))
        self.bind("<Destroy>", lambda _olay: self.zamanlayicilari_iptal_et(), add="+")

    def yeni_rota(self) -> None:
        self.kivrimlar = [random.randint(26, 66) for _ in range(7)]
        self.tahmin_izlerini_temizle()

    def ciz(self, puan: int) -> None:
        self.puan = puan
        self.delete("rota")
        self.oyuncu_konumu = None
        genislik = self.winfo_width()
        if genislik < 100:
            return
        sol, sag = 34, genislik - 34
        konumlar = []
        for nokta in range(HEDEF_PUAN + 1):
            oran = nokta / HEDEF_PUAN
            segment = oran * (len(self.kivrimlar) - 1)
            i = min(int(segment), len(self.kivrimlar) - 2)
            pay = segment - i
            yumusak = pay * pay * (3 - 2 * pay)
            y = self.kivrimlar[i] * (1 - yumusak) + self.kivrimlar[i + 1] * yumusak
            konumlar.append((sol + (sag - sol) * oran, y))

        for i, durak in enumerate(DURAKLAR):
            ilk = durak["puan"]
            son = DURAKLAR[i + 1]["puan"] if i + 1 < len(DURAKLAR) else HEDEF_PUAN
            x0 = 0 if i == 0 else konumlar[ilk][0]
            x1 = genislik if son == HEDEF_PUAN else konumlar[son][0]
            self.create_rectangle(x0, 0, x1, 116, fill=durak["zemin"], outline="", tags="rota")
            for j, oran in enumerate((0.16, 0.38, 0.68, 0.87)):
                self.create_text(x0 + (x1 - x0) * oran, 26 + (j % 2) * 40,
                                 text=durak["simge"], fill=durak["yol"],
                                 font=("Segoe UI Emoji", 10 + (j % 3) * 3), tags="rota")
            self.create_text((x0 + x1) / 2, 81, text=durak["ad"], fill="#edf3ee",
                             font=("Segoe UI", 9, "bold"), tags="rota")
            self.create_line(*[v for nokta in konumlar[ilk:son + 1] for v in nokta],
                             fill=durak["yol"], width=4, tags="rota")

        for i, (x, y) in enumerate(konumlar):
            r = 5 if i in {durak["puan"] for durak in DURAKLAR} or i == HEDEF_PUAN else 2.5
            self.create_oval(x - r, y - r, x + r, y + r, fill="#f9d77e" if i <= puan else "#b8c6b9",
                             outline="#283736", tags="rota")
        x, y = konumlar[-1]
        self.create_text(x, max(13, y - 16), text="🏆", font=("Segoe UI Emoji", 15), tags="rota")
        x, y = konumlar[min(puan, HEDEF_PUAN)]
        self.oyuncu_konumu = (x, y)
        self.create_text(x, max(13, y - 15), text="🧙", font=("Segoe UI Emoji", 17), tags="rota")
        self.tahmin_izlerini_ciz()
        self.move("rota", self.sarsinti, 0)
        self.tag_lower("rota")

    def tahmin_izi_ekle(self, sayi: int) -> None:
        self.tahmin_izleri.append(sayi)
        self.ciz(self.puan)

    def tahmin_izlerini_temizle(self) -> None:
        self.tahmin_izleri.clear()
        self.delete("tahmin_izi")

    def tahmin_izlerini_ciz(self) -> None:
        if not self.tahmin_izleri:
            return
        genislik = self.winfo_width()
        # Haritadaki yol puanı gösterir. Tahminler ayrı bir satırda tutulur.
        etiketler = [str(sayi) for sayi in self.tahmin_izleri]
        adim = 14 + 7 * max(map(len, etiketler))
        gorunenler = etiketler[-max(1, (genislik - 16) // adim):]
        sol = (genislik - (len(gorunenler) - 1) * adim) / 2
        for i, sayi in enumerate(gorunenler):
            x = sol + i * adim
            self.create_text(x, 97, text=sayi, fill="#afc6ba", font=("Segoe UI", 8),
                             tags=("rota", "tahmin_izi"))

    def zamanlayicilari_iptal_et(self) -> None:
        if self.zamanlayici is not None:
            self.after_cancel(self.zamanlayici)
            self.zamanlayici = None
        if self.parilti_zamanlayici is not None:
            self.after_cancel(self.parilti_zamanlayici)
            self.parilti_zamanlayici = None

    def efekt_temizle(self) -> None:
        self.zamanlayicilari_iptal_et()
        self.sarsinti = 0
        self.delete("konfeti")
        self.delete("parilti")
        self.ciz(self.puan)

    def sars(self) -> None:
        self.efekt_temizle()

        def kare(kare_no: int) -> None:
            desen = (4, -3, 2, -1, 0)
            self.move("rota", desen[kare_no] - self.sarsinti, 0)
            self.sarsinti = desen[kare_no]
            self.zamanlayici = self.after(32, kare, kare_no + 1) if kare_no + 1 < len(desen) else None

        kare(0)

    def parilti(self) -> None:
        if self.parilti_zamanlayici is not None:
            self.after_cancel(self.parilti_zamanlayici)

        def kare(adim: int) -> None:
            self.parilti_zamanlayici = None
            self.delete("parilti")
            if adim == 12 or self.oyuncu_konumu is None:
                return
            x, y = self.oyuncu_konumu
            uzaklik = 7 + adim * 2
            for i in range(8):
                aci = i * math.tau / 8
                nokta_x = x + math.cos(aci) * uzaklik
                nokta_y = y + math.sin(aci) * uzaklik
                boyut = 3 - adim / 5
                renk = "#fff0a3" if i % 2 == 0 else "#f9c462"
                self.create_oval(nokta_x - boyut, nokta_y - boyut, nokta_x + boyut,
                                 nokta_y + boyut, fill=renk, outline="", tags="parilti")
            self.parilti_zamanlayici = self.after(30, kare, adim + 1)

        kare(0)

    def konfeti(self) -> None:
        if self.zamanlayici is not None:
            self.after_cancel(self.zamanlayici)
            self.zamanlayici = None
        self.move("rota", -self.sarsinti, 0)
        self.sarsinti = 0
        self.delete("konfeti")
        genislik = self.winfo_width()
        renkler = ("#f9d77e", "#9ae6b4", "#7dd3fc", "#f9a8d4")
        parcalar = []
        for _ in range(48):
            x = random.uniform(0.04, 0.96) * genislik
            y = random.randint(-88, 12)
            boyut = random.randint(3, 7)
            kimlik = self.create_rectangle(x, y, x + boyut, y + boyut, fill=random.choice(renkler),
                                           outline="", tags="konfeti")
            parcalar.append((kimlik, random.uniform(-1.4, 1.4), random.uniform(2, 5)))

        def kare(kalan: int) -> None:
            for kimlik, yatay, dikey in parcalar:
                self.move(kimlik, yatay, dikey)
            if kalan:
                self.zamanlayici = self.after(26, kare, kalan - 1)
            else:
                self.zamanlayici = None
                self.delete("konfeti")

        kare(42)
