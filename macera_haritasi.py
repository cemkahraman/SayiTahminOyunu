"""Macera yolunu ve Canvas üzerindeki kısa oyun efektlerini çizer."""

import random
import tkinter as tk

from oyun_kurallari import DURAKLAR, HEDEF_PUAN


class MaceraHaritasi(tk.Canvas):
    def __init__(self, ebeveyn, **ayarlar):
        super().__init__(ebeveyn, **ayarlar)
        self.puan = 0
        self.kivrimlar = ()
        self.zamanlayici = None
        self.yeni_rota()
        self.bind("<Configure>", lambda _olay: self.ciz(self.puan))

    def yeni_rota(self):
        self.kivrimlar = [random.randint(26, 66) for _ in range(7)]

    def ciz(self, puan):
        self.puan = puan
        self.delete("rota")
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
            self.create_text((x0 + x1) / 2, 94, text=durak["ad"], fill="#edf3ee",
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
        self.create_text(x, max(13, y - 15), text="🧙", font=("Segoe UI Emoji", 17), tags="rota")
        self.tag_lower("rota")

    def efekt_temizle(self):
        if self.zamanlayici is not None:
            self.after_cancel(self.zamanlayici)
            self.zamanlayici = None
        self.delete("konfeti")
        self.ciz(self.puan)

    def sars(self):
        self.efekt_temizle()

        def kare(kare_no):
            desen = (0, 4, -3, 2, -1, 0)
            self.move("rota", desen[kare_no] - desen[kare_no - 1], 0)
            self.zamanlayici = self.after(32, kare, kare_no + 1) if kare_no + 1 < len(desen) else None

        kare(1)

    def konfeti(self):
        self.efekt_temizle()
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

        def kare(kalan):
            for kimlik, yatay, dikey in parcalar:
                self.move(kimlik, yatay, dikey)
            if kalan:
                self.zamanlayici = self.after(26, kare, kalan - 1)
            else:
                self.efekt_temizle()

        kare(42)
