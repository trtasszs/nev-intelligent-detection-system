' ============================================================
'  Silent launcher for bridge-autostart.ps1
' ------------------------------------------------------------
'  Pure ASCII and self-locating (derives its own folder from
'  WScript.ScriptFullName), so no non-ASCII path literal and
'  no encoding problem.
'
'  Window style 0 = completely hidden, so nothing flashes at
'  login. Placed in the Startup folder (or linked from it).
' ============================================================

Dim fso, sh, dir, ps1
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

dir = fso.GetParentFolderName(WScript.ScriptFullName)
ps1 = dir & "\bridge-autostart.ps1"

If fso.FileExists(ps1) Then
    sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ps1 & """", 0, False
End If
