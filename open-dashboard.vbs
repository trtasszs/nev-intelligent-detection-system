' ============================================================
'  open-dashboard.vbs
' ------------------------------------------------------------
'  One-click entry point for the inspection dashboard:
'    1) start the data bridges (ROS 8770 / CAN 8780) silently
'    2) wait briefly for them to come up
'    3) open the dashboard page in the default browser
'
'  Pure ASCII and self-locating (WScript.ScriptFullName), so no
'  non-ASCII path literal is needed and no encoding problem can
'  occur. The page to open is passed in as argument 0 by the
'  shortcut (shortcuts are Unicode, so the Chinese path is safe
'  there); if omitted, the newest .html beside this script wins.
' ============================================================

Option Explicit

Dim fso, sh, dir, sub_, ps1, html, arg, f, newest, newestTime
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

dir = fso.GetParentFolderName(WScript.ScriptFullName)

' ---- 1. locate bridge-autostart.ps1 (this folder, else a subfolder) ----
ps1 = ""
If fso.FileExists(dir & "\bridge-autostart.ps1") Then
    ps1 = dir & "\bridge-autostart.ps1"
Else
    For Each sub_ In fso.GetFolder(dir).SubFolders
        If fso.FileExists(sub_.Path & "\bridge-autostart.ps1") Then
            ps1 = sub_.Path & "\bridge-autostart.ps1"
            Exit For
        End If
    Next
End If

' window style 0 = hidden, bWaitOnReturn = True so the check finishes first
If ps1 <> "" Then
    sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & ps1 & """", 0, True
End If

' ---- 2. resolve which page to open ----
html = ""
If WScript.Arguments.Count > 0 Then
    arg = WScript.Arguments(0)
    If fso.FileExists(arg) Then html = arg
End If

If html = "" Then
    newest = ""
    newestTime = 0
    For Each f In fso.GetFolder(dir).Files
        If LCase(fso.GetExtensionName(f.Name)) = "html" Then
            If f.DateLastModified > newestTime Then
                newestTime = f.DateLastModified
                newest = f.Path
            End If
        End If
    Next
    html = newest
End If

' ---- 3. give the bridges a moment, then open the page ----
WScript.Sleep 2500

If html <> "" Then
    sh.Run """" & html & """", 1, False
End If
