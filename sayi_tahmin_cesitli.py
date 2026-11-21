"""Sayı tahmin oyununun komut satırı arayüzü."""

from oyun_kurallari import HEDEF_PUAN, Oyun, SEVIYELER, kurallar_metni, seviye_ozeti


def baslik(metin):
    print("\n" + "=" * 52)
    print(f"  {metin}")
    print("=" * 52)


def seviye_sec():
    baslik("ZORLUK SEÇİMİ")
    adlar = list(SEVIYELER)
    for no, ad in enumerate(adlar, 1):
        print(f"  {no}) {ad} · {seviye_ozeti(SEVIYELER[ad])}")
    while True:
        secim = input("  Seçimin (1-3): ").strip()
        if secim in ("1", "2", "3"):
            return adlar[int(secim) - 1]
        print("  Geçersiz seçim. Lütfen 1, 2 veya 3 girin.\n")


def tur_oyna(oyun):
    baslik(f"TUR {oyun.tur}  |  {oyun.zorluk.upper()} SEVİYE")
    print(f"  Toplam puanın : {oyun.toplam} / {HEDEF_PUAN}")
    while oyun.aktif:
        print(f"\n  Kalan tahmin: {oyun.kalan_hak}     Kalan ipucu: {oyun.kalan_ipucu}")
        metin = input("  Tahminin veya ipucu için T: ").strip()
        if metin.lower() == "t":
            ipucu = oyun.ipucu_kullan()
            if ipucu:
                print(f"\n  💡 İpucu: Sayı {ipucu[0]} ile {ipucu[1]} arasında.")
            else:
                print("\n  İpucu hakkın kalmadı.")
            continue
        sonuc = oyun.tahmin_et(metin)
        if sonuc.durum == "gecersiz_tamsayi":
            print("\n  ⚠️ Tam sayı gir. Tahmin hakkın azalmadı.")
        elif sonuc.durum == "gecersiz_aralik":
            print("\n  ⚠️ 10–1000 arasında 10'un katı gir. Hakkın azalmadı.")
        elif sonuc.durum == "tekrar":
            print("\n  Bu sayıyı zaten denedin. Hakkın azalmadı.")
        elif sonuc.durum == "dogru":
            print(f"\n  🎉 Doğru! Tuttuğum sayı {oyun.hedef} idi. +{sonuc.puan} puan!")
        elif sonuc.durum == "bitti":
            puan = f"{-sonuc.puan} puan kaybettin." if sonuc.puan else "Toplam puanın değişmedi."
            print(f"\n  😢 Tahmin hakların bitti. Sayı {oyun.hedef} idi. {puan}")
        elif sonuc.durum == "yanlis":
            print("\n  ⬆️ Daha büyük bir sayı dene." if sonuc.yon == "buyuk" else "\n  ⬇️ Daha küçük bir sayı dene.")
            print(f"  {sonuc.yakinlik}")


def main():
    baslik("🎯 SAYI TAHMİN OYUNU")
    print(f"  Hedef: {HEDEF_PUAN} puan")
    print("\n  Kuralları görmek için I, oyuna başlamak için Enter'a bas.")
    while input("  Seçimin: ").strip().lower() == "i":
        baslik("OYUN BİLGİSİ")
        print(kurallar_metni())
        input("\n  Menüye dönmek için Enter'a bas...")
    oyun = Oyun()
    oyun.baslat(seviye_sec())
    while True:
        tur_oyna(oyun)
        print(f"\n  ⭐ GÜNCEL TOPLAM: {oyun.toplam} / {HEDEF_PUAN}")
        if oyun.kazanildi:
            baslik(f"🏆 KAZANDIN! {HEDEF_PUAN} PUANA ULAŞTIN!")
            break
        if input("\n  Devam etmek için Enter, çıkmak için Q: ").strip().lower() == "q":
            break
        oyun.yeni_tur()
    print("\n  Oynadığın için teşekkürler! 👋\n")


if __name__ == "__main__":
    main()
