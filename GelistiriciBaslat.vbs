' Geliştirici kontrolleriyle oyunu açar.
Set dosyaSistemi = CreateObject("Scripting.FileSystemObject")
klasor = dosyaSistemi.GetParentFolderName(WScript.ScriptFullName)
oyun = dosyaSistemi.BuildPath(klasor, "gelistirici_arayuzu.py")
Set kabuk = CreateObject("WScript.Shell")
kabuk.Run "pythonw.exe """ & oyun & """", 1, False
