# Sayı Tahmin Oyunu kod yol haritası

Son doğrulama 22 Kasım 2026. Depo `cemkahraman/SayiTahminOyunu`.

## Güncellik ve kaynak

Graphify dosya komşulukları 22 Kasım 2026 tarihinde sorgulandı. Grafik ve yerel HEAD aynı commit'i gösteriyor.

`bf3e6192f7c6113bdbd06d70703cd1a20bae437f`

Çalışma ağacında bu commit üzerine değişiklikler ve yeni dosyalar bulunuyor. Aşağıdaki güncel modül ve sembol listesi yerel Python kaynaklarından doğrulandı. Graphify'nin bu commit'e ait grafiğinde yeni denetleyici, geliştirici arayüzü, ses varlıkları ve son ses kontrolleri henüz yer almıyor.

Yeni görevde önce `git status --short` ve `git rev-parse HEAD` ile güncelliği kontrol et. Graphify yanıtındaki commit ile HEAD aynı olsa bile görevle ilgili yerel değişmiş veya yeni dosyayı oku. Yol haritasını başlangıç rehberi olarak kullan ve ilgili sembol değişmişse kaydı düzelt.

## Başlatıcılar

| Kullanım | Giriş | Çalışan kod |
|---|---|---|
| Normal oyun | `OyunuBaslat.vbs` | `sayi_tahmin_tkinter.py`, `SayiTahminOyunu` |
| Geliştirici oyunu | `GelistiriciBaslat.vbs` | `gelistirici_arayuzu.py`, `GelistiriciOyunu` |
| Terminal | `python -B sayi_tahmin_cesitli.py` | `main`, `tur_oyna`, ortak `Oyun` |

Python başlatıcıları aynı klasördeki kaynakları kullanır. `SayiTahminMacerasi.exe` ayrı bir derlenmiş çıktıdır. Kaynak değişikliklerinin bu çıktıya aktarılması yeniden paketleme gerektirir.

## Göreve göre ilk okunacak yollar

| Görev | Başlangıç dosyası ve semboller | Gerektiğinde devam edilecek yollar |
|---|---|---|
| Puan, ödül, ceza, geçerli tahmin | `oyun_kurallari.py` → `Oyun.tahmin_et`, `basarisiz_tur`, `Sonuc` | `macera_denetleyicisi.py` → `sonucu_yayinla`, Tkinter → `tahmin_sonucunu_goster`, terminal → `tur_oyna` |
| Tur ve oyun yaşam döngüsü | `oyun_kurallari.py` → `baslat`, `yeni_tur`, `sifirla`, `kazanildi` | Denetleyici → `TurBasladi`, Tkinter → `oyun_olayini_goster`, `turu_goster`, `tur_bitti` |
| Zorluk, haklar ve uyarlama | `macera_verileri.json` → `seviyeler`, `oyun_kurallari.py` → `adaylar`, `tur_cezasi`, `yeni_tur`, `tahmin_et` | Tkinter → `gecerli_sayilar`, `durum_guncelle`, `bilgi_ekrani_kur` |
| Süre, duraklatma, tek seferlik zaman aşımı | `oyun_kurallari.py` → `kalan_sure`, `sureyi_kontrol_et`, `duraklat`, `surdur` | Denetleyici → `sureyi_denetle`, Tkinter → `sureyi_guncelle`, `zamanlayicilari_durdur`, `yardim_ekranina_gec`, `onceki_ekrana_don` |
| İpucu ve güçlendirici | `oyun_kurallari.py` → `ipucu_kullan`, `guclendirici_kullan` | Denetleyicide aynı adlı yöntemler, Tkinter → `ipucu_kullan`, `guclendirici_kullan`, `sayi_dogrusu_ciz` |
| Menü kartları, renkler, yerleşim | `sayi_tahmin_tkinter.py` → `menu_kur`, `bolum`, `etiket`, `buton` | `macera_verileri.json` → seviye `renk`, `harita`, `hikaye` alanları |
| Oyun içi metin ve ekran geçişleri | `sayi_tahmin_tkinter.py` → `oyun_ekrani_kur`, `bildirim`, `ekrani_goster` | `macera_sahnesi.py` → `SahneYazisi` |
| Geliştirici paneli ve komutları | `gelistirici_arayuzu.py` → `GelistiriciOyunu`, `paneli_goster`, `puani_ayarla`, `zorlugu_degistir`, `turu_atla` | Ortak ekran davranışı gerekiyorsa `sayi_tahmin_tkinter.py` |
| Bölge resmi, odak, ölçekleme | Tkinter → `zemini_guncelle`, `macera_sahnesi.py` → `bolge_sec`, `yenile`, `boyutlandir` | `macera_verileri.json` → `duraklar`, `bolgeler/` |
| Yol haritası çizimi ve efektler | `macera_haritasi.py` → `ciz`, `tahmin_izi_ekle`, `parilti`, `sars`, `konfeti`, `efekt_temizle` | Tkinter → `durum_guncelle`, `tahmin_sonucunu_goster`, `basarisiz_tur` |
| Hikâye ve bölge eşikleri | `macera_verileri.json`, `macera_denetleyicisi.py` → `bolge`, `hikaye` | Tkinter → `durum_guncelle`, `zemini_guncelle` |
| Başarılar, galeri, Zor kilidi | `macera_kaydi.py` → `BASARILAR`, `kaydet`, `basari_kaydet`, `basarilar`, `zor_acik`, `galeri` | Denetleyici → `sonucu_yayinla`, `zor_acik`, Tkinter → `galeri_goster`, `ekrani_goster` |
| Mevcut bölge sesini değiştirme | `sesler/Ses_Dosyalari.md`, ilgili `sesler/*.wav` | Dosya eşlemesi gerekiyorsa `macera_sesi.py` → `ORTAMLAR`, `_ses_yolu` |
| Ses üretimi | `macera_sesi.py` → `_orman_fonu_yaz`, `_ortam_sesi_yaz`, `ses_yaz` | Oyunun kullandığı mevcut WAV dosyasını da yenile |
| Ses düzeyi, döngü ve oynatma | `macera_sesi.py` → `MaceraSesi.ses_duzeyini_ayarla`, `ortam_degistir`, `cal`, `WindowsEfektSesi` | Tkinter → `ses_degistir`, `ses_duzeyini_degistir`, `ses_dugmesini_guncelle` |
| Veri dosyası hatası | `oyun_kurallari.py` → `macera_verilerini_yukle` | `macera_verileri.json` |

## Çağrı akışları

Tkinter tahmini `SayiTahminOyunu.tahmin_et` üzerinden `MaceraDenetleyicisi.tahmin_et` ve `Oyun.tahmin_et` yöntemlerine ulaşır. Model `Sonuc` döndürür. Denetleyici `sonucu_yayinla` içinde gereken başarı ve macera kaydını yapar. Ardından `TahminDegerlendirildi` olayı `oyun_olayini_goster` ve `tahmin_sonucunu_goster` üzerinden arayüzü günceller.

Tur başlangıcı denetleyiciden `TurBasladi` olayını üretir. Arayüz `turu_goster` ile girişleri, izleri ve süreyi yeniler.

Terminal `Oyun` modelini doğrudan kullanır. Denetleyici ve Tkinter değişiklikleri terminale otomatik uygulanmaz. Modeldeki değişiklikler her iki sürümü etkiler.

Geliştirici sürümü `SayiTahminOyunu` sınıfını genişletir. Puan, bölge ve zorluk komutları ortak oyun durumunu günceller. Panel pencere içinde açılır, F12 ile gizlenir ve gösterilir.

## Davranış ve veri notları

- Normal kayıt varsayılan olarak `LOCALAPPDATA/SayiTahminMacerasi/maceralar.sqlite3` altında tutulur. Geliştirici oturumu aynı dizinde `gelistirici.sqlite3` kullanır.
- Geliştirici denetleyicisi Zor seviye kilidini açar. Normal kilit ilk macera galibiyetiyle açılır.
- Uyarlanabilir zorluk normal Tkinter oluşturulurken etkinleştirilir. Terminalin varsayılan modeli bu seçeneği açmaz.
- İlk doğru tahmin ödülü 10, her ek geçerli tahminde ödül 1 azalır, taban ödül 1 ve Zor çarpanı 2'dir. Geçersiz ve yinelenen tahminler hak harcamaz.
- Bölge puan eşikleri Orman için 0, Buzul için 9, Volkan için 17 ve macera hedefi 25'tir. Sayısal değerler değişirse tabloyu güncelle.
- `sesler/ortam_orman.wav`, `ortam_buzul.wav`, `ortam_volkan.wav` bölge fonlarıdır. `tahmin.wav`, `dogru.wav`, `kalp.wav` efektlerdir.
- `_ses_yolu` önce mevcut `sesler/` dosyasını seçer. Dosya yoksa geçici üretim yoluna döner. Üretici fonksiyonu değiştirmek mevcut WAV dosyasının içeriğini değiştirmez.
- Windows'ta ortam ve efekt kendi `waveOut` aygıtlarını kullanır. Pygame mevcutsa ayrı mikser kanalları kullanılır. Ses düzeyi 0–100 arasında iki kanala uygulanır. Aynı bölgedeki tahmin ve ses düzeyi değişimi fonu baştan başlatmamalıdır.

## Hedefli doğrulama

| Değişiklik | Uygun başlangıç kontrolü |
|---|---|
| Ortak puanlama | `python -B -m unittest discover -s tests -p test_puanlama.py` içindeki model ve terminal sınıfları |
| Tkinter akışı, süre, kayıt, bölge | `tests/test_puanlama.py` içindeki `TkinterPuanlamaTesti` ve değişen giriş noktasının çalıştırılması |
| Ses kontrol akışı | `python -B -m unittest discover -s tests -p test_macera_sesi.py` |
| Ses kalitesi veya gerçek ses düzeyi | Gerçek ses aygıtında dinleme ve oynatma kontrolü. Taklit edilmiş ses testi algısal kaliteyi doğrulamaz. |
| Geliştirici paneli | Geliştirici başlatıcısında puan, bölge, zorluk, tur atlama ve F12 kontrolü. Ayrı kayıt dosyası kullanıldığını kontrol et. |
| Tam mevcut test takımı | `python -B -m unittest discover -s tests -q` |

## Sonraki görevlerde izlenecek yol

1. Görevi yukarıdaki tablodan ilgili dosya ve sembole eşleştir.
2. İlgili yollardaki yerel değişiklikleri kontrol et.
3. Ek bağımlılık gerekiyorsa Graphify'de dosya komşuluğu, sembol veya etki sorgusu kullan.
4. Grafik eksik, kısmi ya da güncelliğini kaybetmişse ilgili yerel kaynak bölümünü oku.
5. Taramayı görev ve gerçek bağımlılıklarıyla sınırla. Önbellek, ikili çıktı ve ilgisiz varlıkları ancak görev bunlarla ilgiliyse incele.
6. Etkilenen davranışları doğrula. Dosya sorumluluğu veya akış değiştiyse bu haritayı güncelle.
