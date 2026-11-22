import unittest
from unittest.mock import Mock, patch

import macera_sesi


class MaceraSesiTesti(unittest.TestCase):
    def test_windows_efektleri_ortam_dongusunu_yeniden_baslatmaz(self):
        windows = Mock(SND_FILENAME=1, SND_ASYNC=2, SND_NODEFAULT=4, SND_LOOP=8)
        with patch.multiple(macera_sesi, mixer=None, winsound=windows), patch.object(
            macera_sesi, "WindowsEfektSesi",
        ):
            ses = macera_sesi.MaceraSesi()
            self.addCleanup(ses.kapat)
            with patch.object(ses, "_windows_efekti") as efekt_sesi:
                ortam_sesi = ses._windows_ortami
                ses.ortam_degistir("Orman")
                for efekt in ("tahmin", "tahmin", "kalp", "dogru"):
                    ses.ortam_degistir("Orman")
                    ses.cal(efekt)
                self.assertEqual(ortam_sesi.cal.call_count, 1)
                self.assertEqual(ortam_sesi.cal.call_args.args[0].name, "ortam_orman.wav")
                self.assertEqual(ortam_sesi.cal.call_args.kwargs, {"dongu": True})
                self.assertEqual(efekt_sesi.cal.call_count, 4)
                ses.ses_duzeyini_ayarla(35)
                ortam_sesi.ses_duzeyini_ayarla.assert_called_with(35)
                efekt_sesi.ses_duzeyini_ayarla.assert_called_with(35)
                self.assertEqual(ortam_sesi.cal.call_count, 1)

                ses.ortam_degistir("Buzul")
                self.assertEqual(ortam_sesi.cal.call_count, 2)
                self.assertEqual(ortam_sesi.cal.call_args.args[0].name, "ortam_buzul.wav")
                ses.sustur()
                ortam_sesi.durdur.assert_called_once()
                efekt_sesi.durdur.assert_called_once()
