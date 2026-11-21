' Bu başlatıcı aynı klasördeki güncel Python kodunu konsol açmadan çalıştırır.
Set dosyaSistemi = CreateObject("Scripting.FileSystemObject")
klasor = dosyaSistemi.GetParentFolderName(WScript.ScriptFullName)
oyun = dosyaSistemi.BuildPath(klasor, "sayi_tahmin_tkinter.py")
Set kabuk = CreateObject("WScript.Shell")
kabuk.Run "pythonw.exe """ & oyun & """", 1, False
