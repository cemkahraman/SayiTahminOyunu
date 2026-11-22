"""Kısa oyun sesleri ve bölgelere özgü ortam döngüleri."""

import math
import tempfile
import wave
from array import array
from ctypes import (
    Structure, addressof, byref, c_size_t, c_uint, c_uint16, c_uint32,
    c_void_p, create_string_buffer, sizeof,
)
from pathlib import Path
from random import Random

try:
    from pygame import mixer
except ImportError:
    mixer = None

try:
    import winsound
except ImportError:
    winsound = None
else:
    from ctypes import windll


SES_NOTALARI = {
    "tahmin": ((220, 0.045),),
    "dogru": ((523, 0.075), (659, 0.075), (784, 0.14)),
    "kalp": ((100, 0.065), (0, 0.045), (80, 0.09)),
}
ORTAMLAR = {"Orman": "orman", "Buzul": "buzul", "Volkan": "volkan"}
ORNEK_HIZI = 22050
SES_KLASORU = Path(__file__).resolve().with_name("sesler")


class DalgaFormati(Structure):
    _pack_ = 1
    _fields_ = [
        ("bicim", c_uint16), ("kanal", c_uint16), ("ornek_hizi", c_uint32),
        ("bayt_hizi", c_uint32), ("blok_boyutu", c_uint16), ("bit", c_uint16),
        ("ek_boyut", c_uint16),
    ]


class DalgaTamponu(Structure):
    _fields_ = [
        ("veri", c_void_p), ("uzunluk", c_uint32), ("kaydedilen_bayt", c_uint32),
        ("kullanici", c_size_t), ("bayraklar", c_uint32), ("donguler", c_uint32),
        ("sonraki", c_void_p), ("ayrilan", c_size_t),
    ]


class WindowsEfektSesi:
    """PCM sesini kendi Windows aygıtıyla ve bağımsız ses düzeyiyle çalar."""

    def __init__(self) -> None:
        self.aygit = c_void_p()
        self.tampon = None
        self.veri = None
        self.duzey = 100

    @staticmethod
    def sonucu_denetle(sonuc: int) -> None:
        if sonuc:
            raise OSError(f"Windows ses aygıtı hata kodu: {sonuc}")

    def cal(self, yol: Path, *, dongu: bool = False) -> None:
        self.durdur()
        with wave.open(str(yol), "rb") as dosya:
            veri = dosya.readframes(dosya.getnframes())
        ses = windll.winmm
        if not self.aygit:
            bicim = DalgaFormati(1, 1, ORNEK_HIZI, 2 * ORNEK_HIZI, 2, 16, 0)
            # PCM, varsayılan aygıt ve geri çağrı kullanmayan oynatma.
            self.sonucu_denetle(ses.waveOutOpen(byref(self.aygit), c_uint(-1), byref(bicim), None, None, 0))
            self.ses_duzeyini_ayarla(self.duzey)
        tampon_verisi = create_string_buffer(veri, len(veri))
        tampon = DalgaTamponu(addressof(tampon_verisi), len(veri))
        if dongu:
            tampon.bayraklar = 0x04 | 0x08  # WHDR_BEGINLOOP | WHDR_ENDLOOP
            tampon.donguler = 0xFFFFFFFF
        self.sonucu_denetle(ses.waveOutPrepareHeader(self.aygit, byref(tampon), sizeof(tampon)))
        self.veri = tampon_verisi
        self.tampon = tampon
        self.sonucu_denetle(ses.waveOutWrite(self.aygit, byref(tampon), sizeof(tampon)))

    def ses_duzeyini_ayarla(self, duzey: int) -> None:
        self.duzey = duzey
        if self.aygit:
            kanal = round(0xFFFF * duzey / 100)
            self.sonucu_denetle(windll.winmm.waveOutSetVolume(self.aygit, c_uint32(kanal | kanal << 16)))

    def durdur(self) -> None:
        if self.tampon is not None:
            ses = windll.winmm
            self.sonucu_denetle(ses.waveOutReset(self.aygit))
            self.sonucu_denetle(ses.waveOutUnprepareHeader(
                self.aygit, byref(self.tampon), sizeof(self.tampon),
            ))
            self.tampon = self.veri = None

    def kapat(self) -> None:
        self.durdur()
        if self.aygit:
            self.sonucu_denetle(windll.winmm.waveOutClose(self.aygit))
            self.aygit = c_void_p()


class MaceraSesi:
    def __init__(self) -> None:
        self._efekt_kanali = None
        self._ortam_kanali = None
        if mixer is not None:
            try:
                if not mixer.get_init():
                    mixer.init(frequency=ORNEK_HIZI, channels=1)
                self._ortam_kanali = mixer.Channel(0)
                self._efekt_kanali = mixer.Channel(1)
            except (RuntimeError, IndexError):
                self._ortam_kanali = None
        self.destekleniyor = self._ortam_kanali is not None or winsound is not None
        self.acik = self.destekleniyor
        self.klasor: tempfile.TemporaryDirectory | None = None
        self._ortam: str | None = None
        self._ortam_caliyor = False
        self._windows_efekti = WindowsEfektSesi() if winsound is not None and self._efekt_kanali is None else None
        self._windows_ortami = WindowsEfektSesi() if self._windows_efekti is not None else None
        self.duzey = 100

    def ses_duzeyini_ayarla(self, duzey: int) -> None:
        self.duzey = max(0, min(100, int(duzey)))
        for kanal in (self._ortam_kanali, self._efekt_kanali):
            if kanal is not None:
                kanal.set_volume(self.duzey / 100)
        for kanal in (self._windows_ortami, self._windows_efekti):
            if kanal is not None:
                kanal.ses_duzeyini_ayarla(self.duzey)

    def cal(self, ad: str) -> None:
        if not self.acik or not self.destekleniyor or ad not in SES_NOTALARI:
            return
        try:
            yol = self._ses_yolu(ad)
            if not yol.exists():
                self.ses_yaz(yol, SES_NOTALARI[ad])
            if self._efekt_kanali is not None:
                self._efekt_kanali.play(mixer.Sound(str(yol)))
            elif self._windows_efekti is not None:
                self._windows_efekti.cal(yol)
        except (OSError, RuntimeError):
            return

    def ortam_degistir(self, bolge: str | None) -> None:
        onceki = self._ortam
        self._ortam = ORTAMLAR.get(bolge) if bolge is not None else None
        if self._ortam is None or not self.acik:
            self._ortami_durdur()
        elif self._ortam != onceki or not self._ortam_caliyor:
            self._ortami_cal()

    def _ortami_cal(self) -> None:
        if self._ortam is None or not self.acik or not self.destekleniyor:
            return
        try:
            yol = self._ses_yolu(f"ortam_{self._ortam}")
            if not yol.exists():
                self._ortam_sesi_yaz(yol, self._ortam)
            if self._ortam_kanali is not None:
                self._ortam_kanali.play(mixer.Sound(str(yol)), loops=-1)
            elif self._windows_ortami is not None:
                self._windows_ortami.cal(yol, dongu=True)
            self._ortam_caliyor = True
        except (OSError, RuntimeError):
            self._ortam_caliyor = False

    def _ortami_durdur(self) -> None:
        if self._ortam_kanali is not None:
            self._ortam_kanali.stop()
        elif self._windows_ortami is not None:
            self._windows_ortami.durdur()
        self._ortam_caliyor = False

    def _ses_yolu(self, ad: str) -> Path:
        dosya_adi = f"{ad}.wav"
        kayitli_ses = SES_KLASORU / dosya_adi
        if kayitli_ses.is_file():
            return kayitli_ses
        if self.klasor is None:
            self.klasor = tempfile.TemporaryDirectory(prefix="sayi_macera_")
        return Path(self.klasor.name) / dosya_adi

    @staticmethod
    def ses_yaz(yol: Path, notalar: tuple[tuple[int, float], ...]) -> None:
        ornekler = array("h")
        for frekans, sure in notalar:
            uzunluk = int(ORNEK_HIZI * sure)
            ornekler.extend(
                int(3000 * math.sin(math.tau * frekans * i / ORNEK_HIZI)
                    * min(1, i / 100, (uzunluk - i) / 240))
                for i in range(uzunluk)
            )
        MaceraSesi._wav_yaz(yol, ornekler)

    @staticmethod
    def _ortam_sesi_yaz(yol: Path, ortam: str) -> None:
        if ortam == "orman":
            MaceraSesi._orman_fonu_yaz(yol)
            return
        ornekler = array("h")
        for i in range(4 * ORNEK_HIZI):
            saniye = i / ORNEK_HIZI
            aci = math.tau * saniye
            if ortam == "buzul":
                ruzgar = 0.55 + 0.45 * math.sin(0.25 * aci)
                ses = ruzgar * (170 * math.sin(181 * aci) + 120 * math.sin(247 * aci)
                                + 70 * math.sin(401 * aci))
            else:
                ugultu = 0.7 + 0.3 * math.sin(0.5 * aci)
                ses = ugultu * (450 * math.sin(55 * aci) + 200 * math.sin(73 * aci)
                                + 100 * math.sin(109 * aci))
            ornekler.append(int(ses))
        MaceraSesi._wav_yaz(yol, ornekler)

    @staticmethod
    def _orman_fonu_yaz(yol: Path) -> None:
        uzunluk = 56 * ORNEK_HIZI
        gecis = ORNEK_HIZI // 2
        rastgele = Random(503)
        ornekler = array("h")
        fisilti = esinti_filtresi = ruzgar = 0.0
        for i in range(uzunluk + gecis):
            gurultu = 2 * rastgele.random() - 1
            # Üç kademeli süzme, ince statik hışırtısını yumuşatır.
            fisilti += 0.07 * (gurultu - fisilti)
            esinti_filtresi += 0.07 * (fisilti - esinti_filtresi)
            ruzgar += 0.012 * (esinti_filtresi - ruzgar)
            aci = math.tau * i / uzunluk
            esinti = (0.5 + 0.5 * math.sin(3 * aci + 0.8)) ** 2
            yapraklar = (esinti_filtresi - ruzgar) * (45 + 95 * esinti)
            ornekler.append(int(yapraklar + 70 * ruzgar))

        # Aralarında sessiz alan bırakan, farklı yön ve perdelerde kısa kuş çağrıları.
        for baslangic, sure, perde, degisim, genlik in (
            (5.3, 0.36, 1460, 510, 115), (5.86, 0.25, 1830, -310, 80),
            (18.6, 0.44, 1180, 370, 90),
            (32.4, 0.28, 1960, 460, 100), (33.1, 0.34, 1710, -420, 75),
            (47.2, 0.40, 1390, 520, 105), (47.94, 0.22, 1660, -270, 65),
        ):
            ilk = int(baslangic * ORNEK_HIZI)
            kare_sayisi = int(sure * ORNEK_HIZI)
            for kare in range(kare_sayisi):
                ilerleme = kare / kare_sayisi
                zaman = kare / ORNEK_HIZI
                faz = math.tau * zaman * (perde + 0.5 * degisim * ilerleme)
                zarf = math.sin(math.pi * ilerleme) ** 2
                ornekler[ilk + kare] += int(genlik * zarf * (math.sin(faz) + 0.04 * math.sin(2 * faz)))

        # Son yarım saniyeyi başlangıca karıştırarak döngü birleşimini yumuşat.
        for i in range(gecis):
            oran = 0.5 - 0.5 * math.cos(math.pi * i / (gecis - 1))
            ornekler[uzunluk + i] = int((1 - oran) * ornekler[uzunluk + i] + oran * ornekler[i])
        MaceraSesi._wav_yaz(yol, ornekler[gecis:])

    @staticmethod
    def _wav_yaz(yol: Path, ornekler: array) -> None:
        with wave.open(str(yol), "wb") as dosya:
            dosya.setparams((1, 2, ORNEK_HIZI, 0, "NONE", "not compressed"))
            dosya.writeframes(ornekler.tobytes())

    def sustur(self) -> None:
        self._ortami_durdur()
        if self._efekt_kanali is not None:
            self._efekt_kanali.stop()
        elif self._windows_efekti is not None:
            try:
                self._windows_efekti.durdur()
            except OSError:
                pass

    def kapat(self) -> None:
        self.acik = False
        self.sustur()
        if self._windows_efekti is not None:
            try:
                self._windows_efekti.kapat()
            except OSError:
                pass
        if self._windows_ortami is not None:
            try:
                self._windows_ortami.kapat()
            except OSError:
                pass
        if self.klasor is not None:
            self.klasor.cleanup()
            self.klasor = None
