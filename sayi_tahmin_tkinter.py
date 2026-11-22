import sqlite3
import tkinter as tk
from math import ceil
from time import monotonic
from tkinter import ttk

from macera_denetleyicisi import MaceraDenetleyicisi, TahminDegerlendirildi, TurBasladi
from macera_haritasi import MaceraHaritasi
from macera_kaydi import BASARILAR, MaceraKaydi
from macera_sahnesi import MaceraSahnesi, SahneYazisi
from macera_sesi import MaceraSesi
from oyun_kurallari import (
    DINAMIK_SAYI_ADIMI, DINAMIK_TUR_SERISI, DONDURMA_SURESI, EN_BUYUK_SAYI, EN_KUCUK_SAYI,
    GUCLENDIRICILER,
    HEDEF_PUAN, HIZLI_TUR_HAKKI, HIZLI_TUR_SURESI, Oyun, SAYI_ADIMI,
    SEVIYELER, TUR_SURESI,
    seviye_ozeti, yakinlik_araliklari,
)


ZEMIN = "#111d1b"
PANEL = "#1c2e29"
METIN = "#f2f5eb"
IKINCIL = "#bfd0c4"
ALTIN = "#f9d77e"
YESIL = "#a0e7b3"
KIRMIZI = "#ffaaa8"


class SayiTahminOyunu:
    def __init__(self, pencere: tk.Tk, oyun: Oyun | None = None, kayit: MaceraKaydi | None = None):
        self.pencere = pencere
        self.oyun = oyun if oyun is not None else Oyun(sureli=True, uyarlanabilir=True)
        self.kayit = kayit if kayit is not None else MaceraKaydi()
        self.denetleyici = MaceraDenetleyicisi(self.oyun, self.kayit, self.oyun_olayini_goster)
        self.ses = MaceraSesi()
        self.ekran = None
        self.donulecek_ekran = "menu"
        self.tur_zamanlayicisi = None
        self.sure_zamanlayicisi = None
        self.ipucu_zamanlayicisi = None
        self.yakinlik_araligi = ""
        self.sonraki_kalp_sesi = 0
        self.tahmin_isaretleri = []
        self.gozlem_sayilari = ()

        pencere.title("Sayı Tahmin Macerası")
        pencere.geometry("1000x700")
        pencere.minsize(720, 580)
        pencere.configure(bg=ZEMIN)
        if pencere.tk.call("tk", "windowingsystem") == "win32":
            pencere.state("zoomed")
        pencere.protocol("WM_DELETE_WINDOW", self.kapat)

        self.sahne = MaceraSahnesi(pencere, ZEMIN)
        self.baslik = SahneYazisi(self.sahne, pencere, "Sayı Tahmin Macerası", 24, "bold", ALTIN)
        self.baslik.pack(pady=(9, 4))
        alt = self.sahne.yuzey(pencere)
        alt.pack(side="bottom", fill="x", padx=24, pady=(3, 9))
        self.geri_butonu = self.baglanti(alt, "Geri", self.onceki_ekrana_don)
        self.yeni_buton = self.baglanti(alt, "Yeni oyun", self.yeni_oyun)
        self.bilgi_butonu = self.baglanti(alt, "Bilgi (I)", self.bilgi_goster)
        self.bilgi_butonu.pack(side="right")
        self.galeri_butonu = self.baglanti(alt, "Galeri", self.galeri_goster)
        self.galeri_butonu.pack(side="right", padx=6)
        self.ses_butonu = self.baglanti(alt, "", self.ses_degistir)
        self.ses_butonu.pack(side="right")
        self.ses_paneli = tk.Frame(alt, bg=ZEMIN)
        self.ses_kaydiricisi = tk.Scale(
            self.ses_paneli, from_=0, to=100, orient="horizontal", length=150,
            bg=ZEMIN, fg=METIN, troughcolor=PANEL, highlightthickness=0,
            label="Ses düzeyi", command=self.ses_duzeyini_degistir,
        )
        self.ses_kaydiricisi.set(self.ses.duzey)
        self.ses_kaydiricisi.pack()
        if not self.ses.destekleniyor:
            self.ses_butonu.configure(state="disabled")
        self.ses_dugmesini_guncelle()

        yuva = self.sahne.yuzey(pencere)
        yuva.pack(fill="both", expand=True, padx=24, pady=4)
        govde = self.sahne.yuzey(yuva)
        govde.place(relx=0.5, relheight=1, anchor="n")
        yuva.bind("<Configure>", lambda olay: govde.place_configure(width=min(olay.width, 1120)))
        self.ekranlar = {ad: tk.Frame(govde, bg=ZEMIN) for ad in ("menu", "bilgi", "galeri")}
        self.ekranlar["oyun"] = self.sahne.yuzey(govde)
        self.menu_kur(self.ekranlar["menu"])
        self.oyun_ekrani_kur(self.ekranlar["oyun"])
        self.bilgi_ekrani_kur(self.ekranlar["bilgi"])
        self.galeri_icerik = self.kaydirilabilir_panel(self.ekranlar["galeri"])

        for tus in ("i", "I"):
            pencere.bind(f"<KeyPress-{tus}>", self.bilgi_kisayol)
            self.giris.bind(f"<KeyPress-{tus}>", self.bilgi_kisayol)
        for tus in ("t", "T"):
            pencere.bind(f"<KeyPress-{tus}>", self.ipucu_kisayol)
            self.giris.bind(f"<KeyPress-{tus}>", self.ipucu_kisayol)
        pencere.bind("<Escape>", self.onceki_ekrana_don)
        self.ekrani_goster("menu")

    @staticmethod
    def etiket(ebeveyn, metin="", boyut=11, stil="normal", renk=METIN, **ayarlar):
        zemin = ayarlar.pop("bg", ebeveyn["bg"])
        return tk.Label(ebeveyn, text=metin, font=("Segoe UI", boyut, stil),
                        fg=renk, bg=zemin, **ayarlar)

    @staticmethod
    def buton(ebeveyn, metin, komut, renk="#2c473e", *, etkin_renk="#3d5c50"):
        return tk.Button(ebeveyn, text=metin, command=komut, font=("Segoe UI", 10, "bold"),
                         fg="white", bg=renk, activebackground=etkin_renk, activeforeground="white",
                         disabledforeground="#a3b3a9", relief="flat", padx=9, pady=5, cursor="hand2")

    def baglanti(self, ebeveyn, metin, komut):
        return SahneYazisi(self.sahne, ebeveyn, metin, 10, "bold", komut=komut)

    @staticmethod
    def bolum(ebeveyn, zemin=PANEL):
        return tk.Frame(ebeveyn, bg=zemin, padx=13, pady=7)

    def paragraf(self, ebeveyn, metin, renk=IKINCIL):
        yazi = self.etiket(ebeveyn, metin, renk=renk, justify="left", anchor="w")
        yazi.pack(fill="x", pady=(2, 5))
        yazi.bind("<Configure>", lambda olay: yazi.configure(wraplength=max(40, olay.width - 8)))
        return yazi

    def kaydirilabilir_panel(self, ebeveyn):
        canvas = tk.Canvas(ebeveyn, bg=PANEL, highlightthickness=0)
        kaydirma = ttk.Scrollbar(ebeveyn, orient="vertical", command=canvas.yview)
        kaydirma.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=kaydirma.set, yscrollincrement=18)
        icerik = self.bolum(canvas)
        kimlik = canvas.create_window(0, 0, window=icerik, anchor="nw")
        canvas.bind("<Configure>", lambda olay: canvas.itemconfigure(kimlik, width=olay.width))
        icerik.bind("<Configure>", lambda _olay: canvas.configure(scrollregion=canvas.bbox("all")))

        def tekerlek(olay):
            canvas.yview_scroll(-int(olay.delta / 120) * 3, "units")
            return "break"

        ebeveyn.bind("<Map>", lambda _olay: self.pencere.bind("<MouseWheel>", tekerlek))
        ebeveyn.bind("<Unmap>", lambda _olay: self.pencere.unbind("<MouseWheel>"))
        return icerik

    def menu_kur(self, ebeveyn):
        self.etiket(ebeveyn, "Zorluk seç", 17, "bold").pack(pady=(9, 8))
        secimler = tk.Frame(ebeveyn, bg=ZEMIN)
        secimler.pack(fill="x", pady=(0, 11))
        self.seviye_butonlari = {}
        kart_renkleri = {
            "Orta": ("#203849", "#b9e6ff", "#3a7398"),
            "Zor": ("#3c2323", "#ffc0a0", "#a94a37"),
        }
        for i, (ad, ayar) in enumerate(SEVIYELER.items()):
            secimler.columnconfigure(i, weight=1, uniform="seviye")
            kart_zemini, baslik_rengi, etkin_renk = kart_renkleri.get(ad, (PANEL, ALTIN, "#3d5c50"))
            kart = self.bolum(secimler, kart_zemini)
            kart.grid(row=0, column=i, sticky="nsew", padx=4)
            b = self.buton(kart, ad, lambda secim=ad: self.oyunu_baslat(secim),
                           ayar["renk"], etkin_renk=etkin_renk)
            b.pack(fill="x", pady=(0, 5))
            self.seviye_butonlari[ad] = b
            self.etiket(kart, ayar["harita"], 11, "bold", baslik_rengi).pack(anchor="w")
            self.paragraf(kart, ayar["hikaye"])
            ozet = seviye_ozeti(ayar).replace(" · Başarısız", "\nBaşarısız")
            self.paragraf(kart, ozet, METIN)

        bilgi = self.bolum(ebeveyn, "#252d2d")
        bilgi.pack(fill="x", padx=4)
        self.etiket(bilgi, "Nasıl oynanır?", 13, "bold").pack(anchor="w")
        self.paragraf(bilgi, f"Her turda gizli sayıyı bul. Orman, buzul ve volkanı geçip {HEDEF_PUAN} puanda hazineye ulaş.")
        self.paragraf(bilgi, f"Turlar {TUR_SURESI} saniye sürer. Sayılar {EN_KUCUK_SAYI}–{EN_BUYUK_SAYI} "
                             f"arasındadır ve başlangıçta {SAYI_ADIMI}'un katıdır. "
                             "Geçersiz ve tekrarlanan girişler tahmin hakkı harcamaz.")
        self.paragraf(bilgi, "İpucu için T, kurallar ve yakınlık aralıkları için I tuşunu kullan.")
        self.zor_kilit_yazisi = self.etiket(bilgi, renk=ALTIN)
        self.zor_kilit_yazisi.pack(anchor="w")

    def oyun_ekrani_kur(self, ebeveyn):
        ust = self.sahne.yuzey(ebeveyn)
        ust.pack(fill="x")
        self.seviye_yazisi = SahneYazisi(self.sahne, ust, boyut=13, stil="bold")
        self.seviye_yazisi.pack(side="left")
        self.durum = SahneYazisi(self.sahne, ust, stil="bold", fg=ALTIN)
        self.durum.pack(side="right")
        self.ilerleme = tk.Canvas(ebeveyn, height=8, bg="#30433c", highlightthickness=0)
        self.ilerleme.pack(fill="x", pady=(5, 6))
        self.ilerleme.bind("<Configure>", lambda _olay: self.ilerlemeyi_ciz())
        self.harita = MaceraHaritasi(ebeveyn, height=105, bg=PANEL, highlightthickness=0)
        self.harita.pack(fill="x")
        self.hikaye_yazisi = self.etiket(ebeveyn, boyut=10, renk=IKINCIL, justify="center")
        self.hikaye_yazisi.pack(fill="x", pady=(3, 0))

        self.sayi_dogrusu_kutu = self.bolum(ebeveyn)
        self.sayi_dogrusu_baslik = self.etiket(self.sayi_dogrusu_kutu, boyut=9, stil="bold", renk=IKINCIL)
        self.sayi_dogrusu_baslik.pack(anchor="w")
        self.sayi_dogrusu = tk.Canvas(self.sayi_dogrusu_kutu, height=48, bg=PANEL, highlightthickness=0)
        self.sayi_dogrusu.pack(fill="x")
        self.sayi_dogrusu.bind("<Configure>", lambda _olay: self.sayi_dogrusu_ciz())

        self.kart = self.bolum(ebeveyn)
        self.kart.pack(fill="x", pady=(5, 0))
        satir = tk.Frame(self.kart, bg=PANEL)
        satir.pack(fill="x")
        self.tur_yazisi = self.etiket(satir, boyut=10, stil="bold")
        self.tur_yazisi.pack(side="left")
        self.sure_yazisi = self.etiket(satir, boyut=11, stil="bold", renk=ALTIN)
        self.sure_yazisi.pack(side="right")

        giris_satiri = tk.Frame(self.kart, bg=PANEL)
        giris_satiri.pack(pady=(4, 0))
        self.ipucu_buton = self.buton(giris_satiri, "İpucu (T)", self.ipucu_kullan)
        self.ipucu_buton.pack(side="left", padx=(0, 8))
        self.giris = tk.Entry(giris_satiri, font=("Segoe UI", 13), width=14, justify="center", relief="flat")
        self.giris.pack(side="left", ipady=4)
        self.giris.bind("<Return>", lambda _olay: self.tahmin_et())
        self.tahmin_buton = self.buton(giris_satiri, "Tahmin et", self.tahmin_et, "#227548")
        self.tahmin_buton.pack(side="left", padx=(8, 0))

        self.geri_bildirim = SahneYazisi(self.sahne, ebeveyn, stil="bold")
        self.geri_bildirim.pack(pady=(4, 0))
        self.yakinlik_yazisi = SahneYazisi(self.sahne, ebeveyn, stil="bold", fg=ALTIN)
        self.yakinlik_yazisi.pack()
        self.yakinlik_yazisi.bind("<Enter>", self.yakinlik_ipucu_zamanla)
        self.yakinlik_yazisi.bind("<Leave>", self.yakinlik_ipucu_gizle)
        self.yakinlik_ipucu = self.etiket(ebeveyn, boyut=10, bg="#eaf1dc", renk="#172720", padx=8, pady=4)
        self.istatistik = SahneYazisi(self.sahne, ebeveyn, boyut=10, fg=IKINCIL)
        self.istatistik.pack()
        self.basari_yazisi = SahneYazisi(self.sahne, ebeveyn, boyut=10, fg=ALTIN)
        self.tekrar_butonu = self.baglanti(ebeveyn, "Tekrar oyna", self.yeni_oyun)

        self.gucler = self.sahne.yuzey(ebeveyn)
        self.guclendirici_butonlari = {}
        for ad, metin in GUCLENDIRICILER.items():
            b = self.baglanti(self.gucler, metin, lambda secim=ad: self.guclendirici_kullan(secim))
            b.pack(side="left", padx=3)
            self.guclendirici_butonlari[ad] = b

    def bilgi_ekrani_kur(self, ebeveyn):
        icerik = self.kaydirilabilir_panel(ebeveyn)
        self.etiket(icerik, "Oyun kuralları", 16, "bold", ALTIN).pack(anchor="w")
        self.paragraf(icerik, f"Hazineye ulaşmak için {HEDEF_PUAN} puan topla. İlk tahminde 10 puan kazanırsın. "
                             "Sonraki her tahminde kazanacağın puan 1 azalır. Zor seviyede kazanç iki katına çıkar.")
        self.paragraf(icerik, f"Her tur {TUR_SURESI} saniye sürer. Hakların veya süren biterse seviyene göre puan "
                             "kaybedersin. Toplam puanın 0'ın altına inmez. Bilgi veya Galeri ekranındayken süre durur.")
        for ad, ayar in SEVIYELER.items():
            self.etiket(icerik, f"{ad} · {seviye_ozeti(ayar)}", boyut=10).pack(anchor="w")
        self.paragraf(icerik, "Sayı doğrusu Kolay'da tüm tahminleri, Orta'da son tahmini gösterir. "
                             "Zor'da yalnızca Gözlem kullanıldığında açılır. Haritada önceki yanlış tahminlerini görebilirsin.")
        if self.oyun.uyarlanabilir:
            self.paragraf(icerik, f"Art arda {DINAMIK_TUR_SERISI} tur çözdüğünde sayı aralığı ve başarısız tur cezası artar. "
                                 "Uyarlama seviyesi oyun açık kaldığı sürece yeni maceralara taşınır.")
        self.paragraf(icerik, f"Her güçlendiriciyi oyun başına bir kez kullanabilirsin. Zamanı Durdur "
                             f"süreyi {DONDURMA_SURESI} saniye dondurur. Gözlem doğru sayıya en yakın üç adayı "
                             "işaretler. Can Kurtarma bir sonraki başarısız turun puan kaybını önler.")
        self.paragraf(icerik, f"En çok {HIZLI_TUR_HAKKI} tahminde ve {HIZLI_TUR_SURESI} saniyede çözülen tur hızlı sayılır. "
                             f"Kolay ve Orta'da art arda {SEVIYELER['Kolay']['hizli_tur_serisi']}, "
                             f"Zor'da {SEVIYELER['Zor']['hizli_tur_serisi']} hızlı turdan sonra "
                             f"{DINAMIK_SAYI_ADIMI}'nin katları kullanılır.")
        self.etiket(icerik, "Yakınlık aralıkları", 13, "bold", ALTIN).pack(anchor="w", pady=(5, 0))
        self.yakinlik_araligi_etiketleri = []
        for _ in yakinlik_araliklari():
            etiket = self.etiket(icerik, boyut=10)
            etiket.pack(anchor="w")
            self.yakinlik_araligi_etiketleri.append(etiket)

    def galeri_goster(self):
        for widget in self.galeri_icerik.winfo_children():
            widget.destroy()
        icerik = self.galeri_icerik
        self.etiket(icerik, "Gezgin profili", 16, "bold", ALTIN).pack(anchor="w")
        try:
            haritalar, rekorlar, zor_galibiyet = self.kayit.galeri()
            basarilar = self.kayit.basarilar()
        except (OSError, sqlite3.Error):
            self.paragraf(icerik, "Galeri kaydı okunamadı.", KIRMIZI)
        else:
            galibiyet = sum(adet for _, adet, _ in haritalar)
            self.paragraf(icerik, f"{galibiyet} tamamlanan macera · {len(haritalar)} kazanılan harita")
            self.etiket(icerik, "Başarılar", 13, "bold", ALTIN).pack(anchor="w", pady=(5, 0))
            for metin, kazanildi in (
                *((metin, ad in basarilar) for ad, metin in BASARILAR.items()),
                ("Üç haritayı tamamla", len(haritalar) >= len(SEVIYELER)),
                ("Zor seviyede kazan", zor_galibiyet > 0),
            ):
                self.etiket(icerik, f"{'✓' if kazanildi else '○'}  {metin}",
                            renk=YESIL if kazanildi else IKINCIL).pack(anchor="w")
            self.etiket(icerik, "Kazanılan haritalar", 13, "bold", ALTIN).pack(anchor="w", pady=(7, 0))
            for harita, adet, en_iyi in haritalar:
                self.paragraf(icerik, f"{harita} · {adet} galibiyet · En iyi puan {en_iyi}")
            if not haritalar:
                self.paragraf(icerik, "İlk galibiyetinden sonra haritan burada görünecek.")
            self.etiket(icerik, "En yüksek puanlar", 13, "bold", ALTIN).pack(anchor="w", pady=(7, 0))
            for i, (puan, harita, zorluk, tur, tarih) in enumerate(rekorlar, 1):
                self.paragraf(icerik, f"{i}.  {puan} puan · {harita} ({zorluk}) · {tur} tur · {tarih}")
            if not rekorlar:
                self.paragraf(icerik, "Henüz puan kaydı yok.")
        self.yardim_ekranina_gec("galeri")

    def ekrani_goster(self, ad):
        if self.ekran == ad:
            return
        if self.ekran is not None:
            self.ekranlar[self.ekran].pack_forget()
        self.ekran = ad
        self.ekranlar[ad].pack(fill="both", expand=True)
        if ad == "bilgi":
            for etiket, (_, metin, aralik) in zip(
                self.yakinlik_araligi_etiketleri, yakinlik_araliklari(self.oyun.adaylar[-1]),
            ):
                etiket.configure(text=f"{metin}  ·  {aralik}")
        self.zemini_guncelle()
        self.geri_butonu.pack_forget()
        self.yeni_buton.pack_forget()
        if ad == "oyun":
            self.yeni_buton.pack(side="left")
        elif ad == "menu":
            zor_acik = self.denetleyici.zor_acik()
            self.seviye_butonlari["Zor"].configure(state="normal" if zor_acik else "disabled")
            self.zor_kilit_yazisi.configure(
                text="Zor seviyeyi açmak için ilk maceranı tamamla." if not zor_acik else "",
            )
            self.seviye_butonlari["Kolay"].focus_set()
        else:
            metin = "Oyuna dön" if self.donulecek_ekran == "oyun" else "Başlangıca dön"
            self.geri_butonu.configure(text=metin)
            self.geri_butonu.pack(side="left")
            self.geri_butonu.focus_set()
        self.bilgi_butonu.configure(state="disabled" if ad == "bilgi" else "normal")
        self.galeri_butonu.configure(state="disabled" if ad == "galeri" else "normal")

    def yardim_ekranina_gec(self, ad):
        if self.ekran in ("menu", "oyun"):
            self.donulecek_ekran = self.ekran
        if self.ekran == "oyun":
            self.denetleyici.duraklat()
            self.zamanlayicilari_durdur()
            self.harita.efekt_temizle()
            self.ses.sustur()
        self.ekrani_goster(ad)

    def onceki_ekrana_don(self, _olay=None):
        if self.ekran not in ("bilgi", "galeri"):
            return
        self.ekrani_goster(self.donulecek_ekran)
        if self.ekran == "oyun":
            if self.oyun.aktif:
                self.denetleyici.surdur()
                self.giris.focus_set()
                self.sureyi_guncelle()
            elif not self.oyun.kazanildi:
                self.tur_zamanlayicisi = self.pencere.after(2100, self.yeni_tur)
            else:
                self.tekrar_butonu.focus_set()

    def bilgi_goster(self):
        self.yardim_ekranina_gec("bilgi")

    def bilgi_kisayol(self, _olay=None):
        if self.ekran == "bilgi":
            self.onceki_ekrana_don()
        else:
            self.bilgi_goster()
        return "break"

    def ipucu_kisayol(self, _olay=None):
        self.ipucu_kullan()
        return "break"

    def ses_dugmesini_guncelle(self):
        self.ses_butonu.configure(text=f"Ses %{self.ses.duzey}")

    def ses_degistir(self):
        if self.ses_paneli.winfo_manager():
            self.ses_paneli.pack_forget()
        else:
            self.ses_paneli.pack(side="right", before=self.ses_butonu, padx=8)

    def ses_duzeyini_degistir(self, deger):
        try:
            self.ses.ses_duzeyini_ayarla(round(float(deger)))
        except OSError:
            return
        self.ses_dugmesini_guncelle()

    def ilerlemeyi_ciz(self):
        canvas = self.ilerleme
        oran = min(self.oyun.toplam / HEDEF_PUAN, 1)
        canvas.delete("all")
        if oran:
            renk = "#ee8980" if oran >= 0.75 else ALTIN if oran >= 0.4 else YESIL
            canvas.create_rectangle(0, 0, canvas.winfo_width() * oran, 8, outline="", fill=renk)

    def sayi_dogrusu_ciz(self):
        canvas = self.sayi_dogrusu
        canvas.delete("all")
        sol, sag, y = 22, max(canvas.winfo_width(), 500) - 22, 23
        ust_sinir = self.oyun.adaylar[-1]
        canvas.create_line(sol, y, sag, y, fill="#769488", width=2)
        etiket_adimi = 100 if ust_sinir <= EN_BUYUK_SAYI else 200
        for deger in range(0, ust_sinir + 1, etiket_adimi):
            x = sol + (sag - sol) * deger / ust_sinir
            canvas.create_line(x, y - 4, x, y + 4, fill=IKINCIL)
            canvas.create_text(x, y + 15, text=str(deger), fill=IKINCIL, font=("Segoe UI", 8))
        for i, tahmin in enumerate(self.tahmin_isaretleri):
            x = sol + (sag - sol) * tahmin / ust_sinir
            renk = ("#7dd3fc", "#c4b5fd", "#f9a8d4")[i % 3]
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=renk, outline="")
            canvas.create_text(x, 12 - (i % 2) * 6, text=str(tahmin), fill=renk, font=("Segoe UI", 8))
        for sayi in self.gozlem_sayilari:
            x = sol + (sag - sol) * sayi / ust_sinir
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5, outline=ALTIN, width=2)

    def sayi_dogrusu_goster(self):
        if SEVIYELER[self.oyun.zorluk]["gosterilen_tahmin"] or self.gozlem_sayilari:
            baslik = "Sayı doğrusu · Altın halkalar Gözlem adayları" if self.gozlem_sayilari else "Tahminlerin sayı doğrusunda"
            self.sayi_dogrusu_baslik.configure(text=baslik)
            self.sayi_dogrusu_kutu.pack(fill="x", pady=(5, 0), after=self.harita)
            self.sayi_dogrusu_ciz()
        else:
            self.sayi_dogrusu_kutu.pack_forget()

    def oyunu_baslat(self, ad: str) -> None:
        if self.ekran != "menu" or self.oyun.zorluk is not None:
            return
        self.denetleyici.baslat(ad)

    def yeni_tur(self) -> None:
        self.tur_zamanlayicisi = None
        self.denetleyici.yeni_tur()

    def oyun_olayini_goster(self, olay: TurBasladi | TahminDegerlendirildi) -> None:
        if isinstance(olay, TurBasladi):
            if self.oyun.tur == 1:
                self.harita.yeni_rota()
                ad = self.oyun.zorluk
                self.seviye_yazisi.configure(text=f"{SEVIYELER[ad]['harita']}  ·  {ad}")
                self.ekrani_goster("oyun")
            self.turu_goster()
        else:
            self.tahmin_sonucunu_goster(olay)

    def turu_goster(self) -> None:
        self.tahmin_isaretleri.clear()
        self.harita.tahmin_izlerini_temizle()
        self.basari_yazisi.pack_forget()
        self.gozlem_sayilari = ()
        self.sonraki_kalp_sesi = 0
        self.sayi_dogrusu_goster()
        self.gucler.pack(pady=(5, 0))
        self.tur_yazisi.configure(text=f"Tur {self.oyun.tur}  ·  {self.gecerli_sayilar()}")
        self.bildirim("Tahminini gir ve Enter'a bas.")
        self.giris.configure(state="normal")
        self.giris.delete(0, "end")
        self.giris.focus_set()
        self.durum_guncelle()
        self.sureyi_guncelle()

    def gecerli_sayilar(self) -> str:
        ek = "un" if self.oyun.adim == SAYI_ADIMI else "nin"
        return f"{self.oyun.adaylar.start}–{self.oyun.adaylar[-1]} arası  ·  {self.oyun.adim}'{ek} katları"

    def durum_guncelle(self):
        self.durum.configure(text=f"{self.oyun.toplam} / {HEDEF_PUAN} puan")
        self.zemini_guncelle()
        self.harita.ciz(self.oyun.toplam)
        self.hikaye_yazisi.configure(text=self.denetleyici.hikaye())
        self.ilerlemeyi_ciz()
        kalkan = "   ·   Can Kurtarma etkin" if self.oyun.kalkan_aktif else ""
        uyarlama = f"   ·   Başarısız tur −{self.oyun.tur_cezasi} puan" if self.oyun.dinamik_seviye else ""
        self.istatistik.configure(
            text=f"{self.oyun.kalan_hak} tahmin   ·   {self.oyun.kalan_ipucu} ipucu{kalkan}{uyarlama}",
        )
        durum = "normal" if self.oyun.aktif else "disabled"
        self.tahmin_buton.configure(state=durum)
        self.ipucu_buton.configure(state=durum)
        for ad, buton in self.guclendirici_butonlari.items():
            buton.configure(state="disabled" if ad in self.oyun.kullanilan_guclendiriciler else durum)

    def zemini_guncelle(self):
        if self.ekran == "oyun":
            durak = self.denetleyici.bolge()
            self.sahne.bolge_sec(durak.get("resim"), durak.get("yatay_odak", 0.5))
            self.ses.ortam_degistir(durak["ad"])
        else:
            self.sahne.bolge_sec(None)
            self.ses.ortam_degistir(None)

    def sureyi_guncelle(self):
        self.sure_zamanlayicisi = None
        if not self.oyun.aktif or self.ekran != "oyun":
            return
        if not self.sureyi_denetle():
            return
        kalan = self.oyun.kalan_sure
        if kalan is None:
            return
        simdi = monotonic()
        donma = self.oyun.kalan_donma_suresi
        self.sureyi_yaz(kalan, donma)
        if kalan <= 8 and not donma and simdi >= self.sonraki_kalp_sesi:
            self.ses_cal("kalp")
            self.sonraki_kalp_sesi = simdi + 0.34 + kalan * 0.085
        self.sure_zamanlayicisi = self.pencere.after(100, self.sureyi_guncelle)

    def sureyi_yaz(self, kalan, donma):
        metin = f"{ceil(kalan)} sn"
        if donma:
            metin += f" · Süre {ceil(donma)} saniye durdu"
        self.sure_yazisi.configure(text=metin, fg=YESIL if donma else KIRMIZI if kalan <= 8 else ALTIN)

    def sureyi_denetle(self) -> bool:
        return self.denetleyici.sureyi_denetle()

    def tahmin_et(self) -> None:
        if self.ekran != "oyun" or not self.oyun.aktif:
            return
        self.denetleyici.tahmin_et(self.giris.get())

    def tahmin_sonucunu_goster(self, olay: TahminDegerlendirildi) -> None:
        sonuc = olay.sonuc
        if sonuc.durum == "gecersiz_tamsayi":
            self.bildirim("Tam sayı gir. Tahmin hakkın azalmadı.", ALTIN)
            return
        if sonuc.durum == "gecersiz_aralik":
            self.bildirim(f"Bu tur için {self.gecerli_sayilar()} geçerli. Hakkın azalmadı.", ALTIN)
            return
        if sonuc.durum == "tekrar":
            self.bildirim("Bu sayıyı zaten denedin. Hakkın azalmadı.", ALTIN)
            return
        if sonuc.durum == "sure_bitti":
            self.basarisiz_tur(sonuc)
            return

        if sonuc.sayi is not None:
            gosterilen = SEVIYELER[self.oyun.zorluk]["gosterilen_tahmin"]
            if gosterilen:
                self.tahmin_isaretleri.append(sonuc.sayi)
                self.tahmin_isaretleri[:] = self.tahmin_isaretleri[-gosterilen:]
            if sonuc.durum in ("yanlis", "bitti"):
                self.harita.tahmin_izi_ekle(sonuc.sayi)
            self.sayi_dogrusu_ciz()
        self.giris.delete(0, "end")
        if sonuc.durum == "dogru":
            self.bildirim(f"Doğru! Sayı {self.oyun.hedef}. +{sonuc.puan} puan.", YESIL)
            self.tur_bitti(kazanilan_puan=sonuc.puan, kayit_hatasi=olay.kayit_hatasi)
            self.ses_cal("dogru")
            self.harita.parilti()
            if self.oyun.kazanildi:
                self.harita.konfeti()
            if olay.yeni_basarilar:
                metin = " · ".join(BASARILAR[ad] for ad in olay.yeni_basarilar)
                self.basari_yazisi.configure(text=f"Başarı açıldı · {metin}")
                self.basari_yazisi.pack(after=self.istatistik)
            elif olay.kayit_hatasi and not self.oyun.kazanildi:
                self.basari_yazisi.configure(text="Başarı kaydı yazılamadı.")
                self.basari_yazisi.pack(after=self.istatistik)
        elif sonuc.durum == "bitti":
            self.ses_cal("tahmin")
            self.basarisiz_tur(sonuc)
        else:
            yon = "↑ Daha büyük bir sayı dene." if sonuc.yon == "buyuk" else "↓ Daha küçük bir sayı dene."
            self.bildirim(yon, yakinlik=sonuc.yakinlik, aralik=sonuc.yakinlik_araligi)
            self.durum_guncelle()
            self.ses_cal("tahmin")

    def ipucu_kullan(self):
        if self.ekran != "oyun" or not self.oyun.aktif or not self.sureyi_denetle():
            return
        ipucu = self.denetleyici.ipucu_kullan()
        if not ipucu:
            self.bildirim("Bu turda ipucu hakkın kalmadı.", ALTIN)
            return
        self.bildirim(f"Gizli sayı {ipucu[0]}–{ipucu[1]} aralığında.", "#c4b5fd")
        self.durum_guncelle()
        self.giris.focus_set()

    def guclendirici_kullan(self, ad):
        if self.ekran != "oyun" or not self.oyun.aktif or not self.sureyi_denetle():
            return
        sonuc = self.denetleyici.guclendirici_kullan(ad)
        if sonuc is None:
            return
        if ad == "gozlem":
            self.gozlem_sayilari = sonuc
            self.sayi_dogrusu_goster()
            adaylar = ", ".join(map(str, sonuc))
            self.bildirim(f"Gözlem adayları · {adaylar}", ALTIN)
        elif ad == "dondur":
            self.sureyi_yaz(self.oyun.kalan_sure, self.oyun.kalan_donma_suresi)
        else:
            self.bildirim("Can Kurtarma hazır. Bir sonraki başarısız turda puanını koruyacak.", YESIL)
        self.durum_guncelle()
        self.giris.focus_set()

    def bildirim(self, metin, renk=METIN, *, yakinlik="", aralik=""):
        self.yakinlik_ipucu_gizle()
        self.geri_bildirim.configure(text=metin, fg=renk)
        self.yakinlik_yazisi.configure(text=yakinlik)
        self.yakinlik_araligi = aralik

    def yakinlik_ipucu_zamanla(self, _olay=None):
        self.yakinlik_ipucu_gizle()
        if self.yakinlik_araligi:
            self.ipucu_zamanlayicisi = self.pencere.after(1000, self.yakinlik_ipucu_goster)

    def yakinlik_ipucu_goster(self):
        self.ipucu_zamanlayicisi = None
        if self.ekran == "oyun" and self.yakinlik_araligi:
            self.yakinlik_ipucu.configure(text=self.yakinlik_araligi)
            self.yakinlik_ipucu.place(in_=self.yakinlik_yazisi, relx=0.5, y=-2, anchor="s")
            self.yakinlik_ipucu.lift()

    def yakinlik_ipucu_gizle(self, _olay=None):
        if self.ipucu_zamanlayicisi is not None:
            self.pencere.after_cancel(self.ipucu_zamanlayicisi)
            self.ipucu_zamanlayicisi = None
        self.yakinlik_ipucu.place_forget()

    def basarisiz_tur(self, sonuc):
        neden = "Süre doldu." if sonuc.durum == "sure_bitti" else "Tahmin hakların bitti."
        puan = f"−{-sonuc.puan} puan." if sonuc.puan else "Puan kaybı olmadı."
        self.bildirim(f"{neden} Sayı {self.oyun.hedef} idi. {puan}", KIRMIZI)
        self.tur_bitti()
        if sonuc.puan < 0:
            self.harita.sars()

    def tur_bitti(self, *, kazanilan_puan: int = 0, kayit_hatasi: bool = False) -> None:
        self.zamanlayicilari_durdur()
        self.giris.configure(state="disabled")
        self.sure_yazisi.configure(text="")
        self.durum_guncelle()
        if not self.oyun.kazanildi:
            self.tur_zamanlayicisi = self.pencere.after(2100, self.yeni_tur)
            return
        ayar = SEVIYELER[self.oyun.zorluk]
        mesaj = f"Hazineyi buldun! +{kazanilan_puan} puan. {ayar['son']}"
        if kayit_hatasi:
            mesaj += "\nGaleri kaydı yazılamadı."
        self.bildirim(mesaj, ALTIN)
        self.gucler.pack_forget()
        self.tekrar_butonu.pack(pady=(4, 0), before=self.istatistik)
        self.tekrar_butonu.focus_set()

    def ses_cal(self, ad):
        self.ses.cal(ad)
        self.ses_dugmesini_guncelle()

    def zamanlayicilari_durdur(self):
        self.yakinlik_ipucu_gizle()
        if self.tur_zamanlayicisi is not None:
            self.pencere.after_cancel(self.tur_zamanlayicisi)
            self.tur_zamanlayicisi = None
        if self.sure_zamanlayicisi is not None:
            self.pencere.after_cancel(self.sure_zamanlayicisi)
            self.sure_zamanlayicisi = None

    def yeni_oyun(self):
        self.zamanlayicilari_durdur()
        self.harita.efekt_temizle()
        self.ses.sustur()
        self.tekrar_butonu.pack_forget()
        self.harita.tahmin_izlerini_temizle()
        self.denetleyici.sifirla()
        self.ekrani_goster("menu")

    def kapat(self):
        self.zamanlayicilari_durdur()
        self.harita.efekt_temizle()
        try:
            self.ses.kapat()
        finally:
            self.pencere.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    uygulama = SayiTahminOyunu(root)
    root.mainloop()
