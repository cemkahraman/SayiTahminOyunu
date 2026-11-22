"""Aynı oyunu geliştirici kontrolleriyle başlatır."""

import tkinter as tk
from tkinter import ttk

from macera_denetleyicisi import MaceraDenetleyicisi
from macera_kaydi import MaceraKaydi
from oyun_kurallari import DURAKLAR, HEDEF_PUAN, SEVIYELER
from sayi_tahmin_tkinter import ALTIN, IKINCIL, PANEL, SayiTahminOyunu


class GelistiriciDenetleyicisi(MaceraDenetleyicisi):
    def zor_acik(self) -> bool:
        return True


class GelistiriciOyunu(SayiTahminOyunu):
    def __init__(self, pencere: tk.Tk, *, oyun=None, kayit=None):
        normal_kayit = MaceraKaydi()
        gelistirici_kaydi = kayit if kayit is not None else MaceraKaydi(
            normal_kayit.yol.with_name("gelistirici.sqlite3"),
        )
        super().__init__(pencere, oyun=oyun, kayit=gelistirici_kaydi)
        self.denetleyici = GelistiriciDenetleyicisi(
            self.oyun, self.kayit, self.oyun_olayini_goster,
        )
        pencere.title("Sayı Tahmin Macerası · Geliştirici")
        self.baslik.configure(text="Sayı Tahmin Macerası · Geliştirici")
        self.seviye_butonlari["Zor"].configure(state="normal")
        self.zor_kilit_yazisi.configure(text="Geliştirici oturumu · Ayrı test kayıtları")
        pencere.bind("<F12>", lambda _olay: self.paneli_goster())
        self.panel_butonu = self.baglanti(pencere, "Geliştirici kontrolleri (F12)", self.paneli_goster)
        self.panel_butonu.pack(side="bottom", fill="x", before=self.baslik)
        self.panel = tk.Frame(pencere, bg=PANEL)
        self.panel.pack(side="bottom", fill="x", padx=24, pady=6, before=self.panel_butonu)
        govde = tk.Frame(self.panel, bg=PANEL, padx=12, pady=8)
        govde.pack(fill="both", expand=True)
        self.panel_durumu = self.etiket(govde, renk=ALTIN, boyut=10, stil="bold")
        self.panel_durumu.pack(anchor="w")
        satir = tk.Frame(govde, bg=PANEL)
        satir.pack(fill="x", pady=5)
        self.etiket(satir, "Puan").pack(side="left")
        self.puan_girdisi = ttk.Entry(satir, width=9)
        self.puan_girdisi.insert(0, "5")
        self.puan_girdisi.pack(side="left", padx=8)
        for metin, komut in (
            ("Ekle", lambda: self.puani_degistir("ekle")),
            ("Çıkar", lambda: self.puani_degistir("cikar")),
            ("Ayarla", lambda: self.puani_degistir("ayarla")),
        ):
            ttk.Button(satir, text=metin, command=komut, width=7).pack(side="left", padx=2)
        bolgeler = tk.Frame(govde, bg=PANEL)
        bolgeler.pack(fill="x", pady=4)
        self.etiket(bolgeler, "Bölge").pack(side="left", padx=(0, 8))
        for durak in DURAKLAR:
            ttk.Button(bolgeler, text=durak["ad"], command=lambda puan=durak["puan"]: self.puani_ayarla(puan)).pack(
                side="left", padx=(0, 6),
            )
        zorluklar = bolgeler
        self.zorluk_secimi = ttk.Combobox(zorluklar, values=list(SEVIYELER), state="readonly", width=10)
        self.zorluk_secimi.set("Kolay")
        self.zorluk_secimi.pack(side="left")
        ttk.Button(zorluklar, text="Zorluğu uygula", command=self.zorlugu_degistir).pack(side="left", padx=8)
        ttk.Button(satir, text="Sonraki tur", command=self.turu_atla).pack(side="left", padx=12)
        self.panel_mesaji = self.etiket(govde, renk=IKINCIL, boyut=10)
        self.panel_mesaji.pack(anchor="w")
        self.panel_zamanlayicisi = None
        self.paneli_guncelle()

    def paneli_goster(self):
        if self.panel.winfo_manager():
            self.panel.pack_forget()
        else:
            self.panel.pack(side="bottom", fill="x", padx=24, pady=6, before=self.panel_butonu)

    def paneli_guncelle(self):
        oyun = self.oyun
        self.panel_durumu.configure(
            text=f"{oyun.zorluk or 'Oyun başlamadı'} · Tur {oyun.tur} · {oyun.toplam} puan",
        )
        self.panel_zamanlayicisi = self.pencere.after(250, self.paneli_guncelle)

    def oyuna_don(self):
        if self.ekran in ("bilgi", "galeri"):
            self.onceki_ekrana_don()
        if self.oyun.zorluk is None:
            self.oyunu_baslat(self.zorluk_secimi.get())
        self.zamanlayicilari_durdur()
        self.harita.efekt_temizle()

    def puani_degistir(self, islem):
        try:
            miktar = int(self.puan_girdisi.get())
            if miktar < 0:
                raise ValueError
        except ValueError:
            self.panel_mesaji.configure(text="Sıfır veya pozitif bir tam sayı gir.")
            return
        toplam = self.oyun.toplam
        puan = {"ekle": toplam + miktar, "cikar": toplam - miktar, "ayarla": miktar}[islem]
        self.puani_ayarla(max(0, puan))

    def puani_ayarla(self, puan):
        self.oyuna_don()
        self.oyun.toplam = puan
        if self.oyun.kazanildi:
            self.oyun.aktif = False
            self.tur_bitti()
        elif not self.oyun.aktif:
            self.tekrar_butonu.pack_forget()
            self.denetleyici.yeni_tur()
        else:
            self.durum_guncelle()
            self.sureyi_guncelle()
        self.panel_mesaji.configure(text=f"Puan {puan} olarak ayarlandı.")

    def zorlugu_degistir(self):
        self.oyuna_don()
        self.oyun.zorluk = self.zorluk_secimi.get()
        self.seviye_yazisi.configure(
            text=f"{SEVIYELER[self.oyun.zorluk]['harita']}  ·  {self.oyun.zorluk}",
        )
        self.turu_atla()
        self.panel_mesaji.configure(text="Zorluk uygulandı ve yeni tur açıldı.")

    def turu_atla(self):
        self.oyuna_don()
        if self.oyun.kazanildi:
            self.panel_mesaji.configure(text=f"Yeni tur için puanı {HEDEF_PUAN}'in altına indir.")
            return
        self.oyun.aktif = False
        self.tekrar_butonu.pack_forget()
        self.denetleyici.yeni_tur()
        self.panel_mesaji.configure(text="Yeni tur açıldı.")

    def kapat(self):
        if getattr(self, "panel_zamanlayicisi", None) is not None:
            self.pencere.after_cancel(self.panel_zamanlayicisi)
        super().kapat()


if __name__ == "__main__":
    pencere = tk.Tk()
    uygulama = GelistiriciOyunu(pencere)
    pencere.mainloop()
