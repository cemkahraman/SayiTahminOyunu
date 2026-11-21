"""Windows'ta çalınan kısa, uygulamaya özgü oyun sesleri."""

import math
import tempfile
import wave
from array import array
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None


SES_NOTALARI = {
    "tahmin": ((220, 0.045),),
    "dogru": ((523, 0.075), (659, 0.075), (784, 0.14)),
    "kalp": ((100, 0.065), (0, 0.045), (80, 0.09)),
}


class MaceraSesi:
    def __init__(self):
        self.destekleniyor = winsound is not None
        self.acik = self.destekleniyor
        self.klasor = None

    def cal(self, ad):
        if not self.acik or not self.destekleniyor:
            return
        try:
            if self.klasor is None:
                self.klasor = tempfile.TemporaryDirectory(prefix="sayi_macera_")
            yol = Path(self.klasor.name) / f"{ad}.wav"
            if not yol.exists():
                self.ses_yaz(yol, SES_NOTALARI[ad])
            winsound.PlaySound(str(yol), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except (OSError, RuntimeError):
            self.acik = False

    @staticmethod
    def ses_yaz(yol, notalar):
        ornek_hizi = 22050
        ornekler = array("h")
        for frekans, sure in notalar:
            uzunluk = int(ornek_hizi * sure)
            ornekler.extend(
                int(3000 * math.sin(math.tau * frekans * i / ornek_hizi)
                    * min(1, i / 100, (uzunluk - i) / 240))
                for i in range(uzunluk)
            )
        with wave.open(str(yol), "wb") as dosya:
            dosya.setparams((1, 2, ornek_hizi, 0, "NONE", "not compressed"))
            dosya.writeframes(ornekler.tobytes())

    def sustur(self):
        if winsound is not None and self.klasor is not None:
            winsound.PlaySound(None, 0)

    def kapat(self):
        self.sustur()
        if self.klasor is not None:
            self.klasor.cleanup()
