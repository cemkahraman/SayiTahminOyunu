import io
import tempfile
import tkinter as tk
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import sayi_tahmin_cesitli as terminal
from macera_kaydi import MaceraKaydi
from oyun_kurallari import Oyun
from sayi_tahmin_tkinter import SayiTahminOyunu


class OyunPuanlamaTesti(unittest.TestCase):
    def test_ilk_ikinci_ve_son_hakta_dogru_tahmin(self):
        for zorluk, hak, puanlar in (
            ("Kolay", 8, (10, 9, 3)),
            ("Orta", 6, (10, 9, 5)),
            ("Zor", 4, (20, 18, 14)),
        ):
            for deneme, beklenen in zip((1, 2, hak), puanlar):
                with self.subTest(zorluk=zorluk, deneme=deneme):
                    oyun = Oyun(lambda: 100)
                    oyun.baslat(zorluk)
                    for sira in range(1, deneme):
                        self.assertEqual(oyun.tahmin_et(sira * 10).durum, "yanlis")
                    sonuc = oyun.tahmin_et(100)
                    self.assertEqual((sonuc.durum, sonuc.puan), ("dogru", beklenen))
                    self.assertEqual((oyun.toplam, oyun.kalan_hak), (beklenen, hak - deneme))
                    self.assertFalse(oyun.aktif)

    def test_gecersiz_tekrar_ve_yanlis_tahminler(self):
        oyun = Oyun(lambda: 100)
        oyun.baslat("Kolay")
        for girdi, durum, kalan in (
            ("abc", "gecersiz_tamsayi", 8),
            (0, "gecersiz_aralik", 8),
            (95, "gecersiz_aralik", 8),
            (90, "yanlis", 7),
            (90, "tekrar", 7),
            (110, "yanlis", 6),
        ):
            with self.subTest(girdi=girdi, durum=durum):
                sonuc = oyun.tahmin_et(girdi)
                self.assertEqual((sonuc.durum, sonuc.puan), (durum, 0))
                self.assertEqual((oyun.toplam, oyun.kalan_hak), (0, kalan))
                if durum == "yanlis":
                    self.assertEqual(sonuc.yon, "buyuk" if girdi < 100 else "kucuk")
                    self.assertTrue(sonuc.yakinlik)
        self.assertEqual(oyun.tahmin_et(100).puan, 8)

    def test_son_yanlis_tahminde_ceza_ve_sifir_siniri(self):
        for zorluk, hak, ceza in (("Kolay", 8, 1), ("Orta", 6, 2), ("Zor", 4, 4)):
            for toplam, kayip in ((10, ceza), (1, 1), (0, 0)):
                with self.subTest(zorluk=zorluk, toplam=toplam):
                    oyun = Oyun(lambda: 100)
                    oyun.baslat(zorluk)
                    oyun.toplam = toplam
                    for sira in range(1, hak):
                        self.assertEqual(oyun.tahmin_et(sira * 10).durum, "yanlis")
                    sonuc = oyun.tahmin_et(hak * 10)
                    self.assertEqual((sonuc.durum, sonuc.puan), ("bitti", -kayip))
                    self.assertEqual((oyun.toplam, oyun.kalan_hak), (toplam - kayip, 0))
                    self.assertEqual(oyun.tahmin_et(100).durum, "pasif")


class TerminalPuanlamaTesti(unittest.TestCase):
    def terminali_calistir(self, girdiler):
        cikti = io.StringIO()
        with patch.object(terminal, "Oyun", return_value=Oyun(lambda: 100)):
            with patch("builtins.input", side_effect=girdiler), redirect_stdout(cikti):
                terminal.main()
        return cikti.getvalue()

    def test_ipucu_tahmin_hakki_ve_odulu_degistirmez(self):
        cikti = self.terminali_calistir([
            "i", "", "", "1", "t", "abc", "95", "90", "90", "110", "100", "q",
        ])
        for metin in (
            "İlk tahminde 10 puan", "her tahminde kazanacağın puan 1 azalır", "2× kazanç",
            "Kalan tahmin: 8     Kalan ipucu: 2", "Tam sayı gir", "10'un katı gir",
            "Daha büyük bir sayı dene", "zaten denedin", "Daha küçük bir sayı dene",
            "+8 puan", "GÜNCEL TOPLAM: 8 / 25",
        ):
            self.assertIn(metin, cikti)

    def test_ceza_mesaji_ve_toplam_birbiriyle_uyumlu(self):
        yanlislar = ["10", "20", "30", "40"]
        cikti = self.terminali_calistir(["", "3", *yanlislar, "", "100", "", *yanlislar, "q"])
        self.assertIn("Toplam puanın değişmedi.", cikti)
        self.assertIn("GÜNCEL TOPLAM: 0 / 25", cikti)
        self.assertIn("+20 puan", cikti)
        self.assertIn("GÜNCEL TOPLAM: 20 / 25", cikti)
        self.assertIn("4 puan kaybettin.", cikti)
        self.assertIn("GÜNCEL TOPLAM: 16 / 25", cikti)

    def test_hedefe_esit_ve_hedefi_asan_toplamda_oyun_biter(self):
        for son_tur, beklenen in ((["10", "20", "30", "40", "50", "100"], 25), (["100"], 30)):
            with self.subTest(beklenen=beklenen):
                cikti = self.terminali_calistir(["", "1", "100", "", "100", "", *son_tur])
                self.assertIn("TUR 3", cikti)
                self.assertIn(f"GÜNCEL TOPLAM: {beklenen} / 25", cikti)
                self.assertIn("KAZANDIN!", cikti)
                self.assertNotIn("TUR 4", cikti)


class TkinterPuanlamaTesti(unittest.TestCase):
    def setUp(self):
        try:
            self.pencere = tk.Tk()
        except tk.TclError as hata:
            self.skipTest(f"Tk penceresi açılamadı: {hata}")
        self.addCleanup(self.pencereyi_kapat)
        gecici = self.enterContext(tempfile.TemporaryDirectory())
        self.kayit = MaceraKaydi(Path(gecici) / "test.sqlite3")
        self.zaman = 0
        self.oyun = Oyun(lambda: 100, sureli=True, saat=lambda: self.zaman)
        self.arayuz = SayiTahminOyunu(self.pencere, oyun=self.oyun, kayit=self.kayit)
        self.arayuz.ses.acik = False
        self.arayuz.oyunu_baslat("Orta")
        self.pencere.update()

    def pencereyi_kapat(self):
        for zamanlayici in self.pencere.tk.call("after", "info"):
            # Görevleri durdur, Tcl komutlarını sahibi olan bileşenler silsin.
            self.pencere.tk.call("after", "cancel", zamanlayici)
        self.pencere.destroy()

    @staticmethod
    def gorunen_metin(bilesen):
        return bilesen.itemcget(bilesen.oge, "text")

    def tahmin_gonder(self, metin, *, enter=False):
        giris = self.arayuz.giris
        giris.delete(0, "end")
        giris.insert(0, metin)
        if enter:
            giris.focus_force()
            giris.event_generate("<Return>")
        else:
            self.arayuz.tahmin_buton.invoke()

    def sonraki_turu_ac(self):
        zamanlayici = self.arayuz.tur_zamanlayicisi
        self.assertIsNotNone(zamanlayici)
        self.pencere.after_cancel(zamanlayici)
        self.arayuz.yeni_tur()

    def test_enter_ve_dugme_ayni_odulu_verir_bolgeler_guncellenir(self):
        self.assertEqual(self.arayuz.sahne.resim_adi, "orman.png")
        for enter, toplam, resim in ((True, 9, "buzul.png"), (False, 18, "volkan.png")):
            with self.subTest(enter=enter):
                self.tahmin_gonder("90", enter=enter)
                self.assertIn("Daha büyük", self.gorunen_metin(self.arayuz.geri_bildirim))
                self.tahmin_gonder("100", enter=enter)
                self.assertIn("+9 puan", self.gorunen_metin(self.arayuz.geri_bildirim))
                self.assertEqual(self.gorunen_metin(self.arayuz.durum), f"{toplam} / 25 puan")
                self.assertEqual(self.arayuz.harita.puan, toplam)
                self.assertEqual(self.arayuz.sahne.resim_adi, resim)
                self.sonraki_turu_ac()

    def test_gecersiz_ve_tekrar_tahmin_hak_ve_puan_degistirmez(self):
        for metin, bildirim, hak in (
            ("abc", "Tam sayı gir", 6),
            ("95", "Hakkın azalmadı", 6),
            ("110", "Daha küçük", 5),
            ("110", "zaten denedin", 5),
        ):
            self.tahmin_gonder(metin)
            self.assertIn(bildirim, self.gorunen_metin(self.arayuz.geri_bildirim))
            self.assertEqual((self.oyun.toplam, self.oyun.kalan_hak), (0, hak))
        self.tahmin_gonder("100")
        self.assertIn("+9 puan", self.gorunen_metin(self.arayuz.geri_bildirim))

    def test_galibiyette_ilerleme_dolar_ve_gercek_puan_bir_kez_kaydedilir(self):
        for onceki_toplam, beklenen, kayitli_puanlar in ((15, 25, [25]), (16, 26, [26, 25])):
            with self.subTest(beklenen=beklenen):
                self.oyun.toplam = onceki_toplam
                self.tahmin_gonder("100")
                self.assertIsNone(self.arayuz.tur_zamanlayicisi)
                self.assertIn("Hazineyi buldun!", self.gorunen_metin(self.arayuz.geri_bildirim))
                self.assertEqual(self.gorunen_metin(self.arayuz.durum), f"{beklenen} / 25 puan")
                canvas = self.arayuz.ilerleme
                self.assertEqual(canvas.coords(canvas.find_all()[0])[2], canvas.winfo_width())
                self.arayuz.tahmin_buton.invoke()
                rekorlar = self.kayit.galeri()[1]
                self.assertEqual([rekor[0] for rekor in rekorlar], kayitli_puanlar)
                if beklenen == 25:
                    self.arayuz.yeni_oyun()
                    self.arayuz.oyunu_baslat("Orta")

    def test_sure_biterken_gonderilen_tahmin_tek_ceza_alir(self):
        for once_tahmin in (True, False):
            with self.subTest(once_tahmin=once_tahmin):
                self.zaman = self.oyun.son_zaman
                self.oyun.toplam = 5
                if once_tahmin:
                    self.tahmin_gonder("100")
                    self.arayuz.sureyi_denetle()
                else:
                    self.arayuz.sureyi_denetle()
                    self.arayuz.tahmin_buton.invoke()
                self.assertEqual(self.oyun.toplam, 3)
                bildirim = self.gorunen_metin(self.arayuz.geri_bildirim)
                self.assertIn("Süre doldu.", bildirim)
                self.assertIn("−2 puan", bildirim)
                self.sonraki_turu_ac()

    def test_can_kurtarma_son_yanlis_tahminde_puani_korur(self):
        self.oyun.toplam = 5
        self.arayuz.guclendirici_butonlari["kalkan"].invoke()
        self.assertTrue(self.oyun.kalkan_aktif)
        for sayi in (10, 20, 30, 40, 50, 60):
            self.tahmin_gonder(str(sayi))
        bildirim = self.gorunen_metin(self.arayuz.geri_bildirim)
        self.assertIn("Tahmin hakların bitti.", bildirim)
        self.assertIn("Puan kaybı olmadı.", bildirim)
        self.assertEqual(self.oyun.toplam, 5)
        self.assertFalse(self.oyun.kalkan_aktif)
        self.sonraki_turu_ac()

    def test_bilgi_ekrani_odulu_ve_zor_seviye_carpanini_aciklar(self):
        self.arayuz.bilgi_butonu.invoke()
        self.assertEqual(self.arayuz.ekran, "bilgi")
        bekleyen = [self.arayuz.ekranlar["bilgi"]]
        metinler = []
        while bekleyen:
            bilesen = bekleyen.pop()
            bekleyen.extend(bilesen.winfo_children())
            if isinstance(bilesen, tk.Label):
                metinler.append(bilesen.cget("text"))
        metin = "\n".join(metinler)
        self.assertIn("İlk tahminde 10 puan", metin)
        self.assertIn("her tahminde kazanacağın puan 1 azalır", metin)
        self.assertIn("Zor seviyede kazanç iki katına çıkar", metin)
