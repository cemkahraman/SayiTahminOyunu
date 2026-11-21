"""Tek bir arka planı, Tk yerleşim yüzeylerinin altında kesintisiz gösterir."""

import tkinter as tk
from math import ceil
from pathlib import Path
from tkinter.font import Font


class MaceraSahnesi:
    def __init__(self, pencere, zemin):
        self.pencere = pencere
        self.zemin = zemin
        self.resim_adi = None
        self.yatay_odak = 0.5
        self.kaynaklar = {}
        self.resim = None
        self.olcek = None
        self.yuzeyler = {}
        self.bekleyen = None
        self.yuzey(pencere).place(relwidth=1, relheight=1)
        pencere.bind("<Configure>", self.yenileme_planla, add="+")
        pencere.bind("<Map>", self.yenileme_planla, add="+")

    def yuzey(self, ebeveyn):
        return self.kaydet(tk.Canvas(ebeveyn, bg=self.zemin, bd=0, highlightthickness=0))

    def kaydet(self, yuzey):
        self.yuzeyler[yuzey] = yuzey.create_image(0, 0, anchor="nw")
        return yuzey

    def bolge_sec(self, resim_adi, yatay_odak=0.5):
        if (self.resim_adi, self.yatay_odak) != (resim_adi, yatay_odak):
            self.resim_adi = resim_adi
            self.yatay_odak = yatay_odak
            self.yenileme_planla()

    def yenileme_planla(self, _olay=None):
        if self.bekleyen is None:
            self.bekleyen = self.pencere.after_idle(self.yenile)

    def yenile(self):
        self.bekleyen = None
        genislik = self.pencere.winfo_width()
        yukseklik = self.pencere.winfo_height()
        resim = None
        if self.resim_adi is not None:
            if self.resim_adi not in self.kaynaklar:
                yol = Path(__file__).with_name("bolgeler") / self.resim_adi
                self.kaynaklar[self.resim_adi] = tk.PhotoImage(master=self.pencere, file=str(yol))
            kaynak = self.kaynaklar[self.resim_adi]
            oran = max(genislik / kaynak.width(), yukseklik / kaynak.height())
            # Bucket widths so a window drag doesn't resample for every pixel.
            hedef_genislik = ceil(kaynak.width() * oran / 128) * 128
            hedef_yukseklik = ceil(kaynak.height() * hedef_genislik / kaynak.width())
            olcek = (self.resim_adi, hedef_genislik, hedef_yukseklik)
            if olcek != self.olcek:
                self.resim = self.boyutlandir(kaynak, hedef_genislik, hedef_yukseklik)
                self.olcek = olcek
            resim = self.resim

        x = self.pencere.winfo_rootx()
        y = self.pencere.winfo_rooty()
        if resim is not None:
            x += round((genislik - resim.width()) * self.yatay_odak)
            y += (yukseklik - resim.height()) // 2
        for yuzey, oge in self.yuzeyler.items():
            if yuzey.winfo_ismapped():
                yuzey.itemconfigure(oge, image=resim or "")
                yuzey.coords(oge, x - yuzey.winfo_rootx(), y - yuzey.winfo_rooty())

    def boyutlandir(self, kaynak, genislik, yukseklik):
        # Tk 8.6 exposes RGB pixels via PPM but only integer scaling factors.
        girdi = kaynak.tk.call(kaynak, "data", "-format", "ppm").split(b"\n", 3)[3]
        kaynak_en, kaynak_boy = kaynak.width(), kaynak.height()
        satir_boyu = kaynak_en * 3
        sutunlar = [3 * (x * kaynak_en // genislik) for x in range(genislik)]
        satirlar = {}
        cikti = bytearray(f"P6\n{genislik} {yukseklik}\n255\n".encode("ascii"))
        for y in range(yukseklik):
            satir = y * kaynak_boy // yukseklik
            if satir not in satirlar:
                bas = satir * satir_boyu
                satirlar[satir] = b"".join(girdi[bas + x:bas + x + 3] for x in sutunlar)
            cikti.extend(satirlar[satir])
        return tk.PhotoImage(master=self.pencere, data=bytes(cikti), format="ppm")


class SahneYazisi(tk.Canvas):
    def __init__(self, sahne, ebeveyn, text="", boyut=11, stil="normal", fg="#f2f5eb", komut=None):
        super().__init__(ebeveyn, bg=sahne.zemin, bd=0, highlightthickness=0,
                         takefocus=int(komut is not None))
        sahne.kaydet(self)
        self.font = Font(root=self, family="Segoe UI", size=boyut, weight=stil)
        self.metin = text
        self.renk = fg
        self.komut = komut
        self.etkin = True
        self.uzerinde = False
        self.oge = self.create_text(0, 0, anchor="center", justify="center", font=self.font)
        self.bind("<Configure>", lambda olay: self.coords(self.oge, olay.width / 2, olay.height / 2))
        if komut is not None:
            self.bind("<Enter>", lambda _olay: self.vurgu(True))
            self.bind("<Leave>", lambda _olay: self.vurgu(False))
            self.bind("<FocusIn>", lambda _olay: self.yaziyi_guncelle())
            self.bind("<FocusOut>", lambda _olay: self.after_idle(self.yaziyi_guncelle))
            self.bind("<ButtonPress-1>", lambda _olay: self.focus_set() if self.etkin else None)
            self.bind("<ButtonRelease-1>", self.tikla)
            self.bind("<Return>", self.klavye_ile_calistir)
            self.bind("<space>", self.klavye_ile_calistir)
        self.configure()

    def configure(self, *, text=None, fg=None, state=None):
        if text is not None:
            self.metin = text
        if fg is not None:
            self.renk = fg
        if state is not None:
            self.etkin = state != "disabled"
        satirlar = self.metin.split("\n")
        bosluk = 8 if self.komut else 3
        super().configure(width=max(1, max(map(self.font.measure, satirlar)) + 2 * bosluk),
                          height=self.font.metrics("linespace") * len(satirlar) + 2 * bosluk,
                          takefocus=int(self.etkin and self.komut is not None))
        self.yaziyi_guncelle()

    def yaziyi_guncelle(self):
        vurgulu = self.etkin and (self.uzerinde or self.focus_get() == self)
        self.font.configure(underline=vurgulu)
        self.itemconfigure(self.oge, text=self.metin, fill=self.renk if self.etkin else "#a7b0af")
        super().configure(cursor="hand2" if self.komut and self.etkin else "")

    def vurgu(self, uzerinde):
        self.uzerinde = uzerinde
        self.yaziyi_guncelle()

    def tikla(self, olay):
        if 0 <= olay.x < self.winfo_width() and 0 <= olay.y < self.winfo_height():
            self.invoke()

    def invoke(self):
        if self.etkin and self.komut:
            self.komut()

    def klavye_ile_calistir(self, _olay):
        self.invoke()
        return "break"
