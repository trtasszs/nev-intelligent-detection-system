Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$targetPid = 17528
$out = Join-Path $env:TEMP 'uia_dump.txt'
$lines = New-Object System.Collections.Generic.List[string]

$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $targetPid)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)

$lines.Add("== top-level windows: " + $wins.Count + " ==")
foreach ($w in $wins) {
    $lines.Add("")
    $lines.Add("--- window: [" + $w.Current.Name + "] class=" + $w.Current.ClassName + " ---")
    $all = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                      [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($e in $all) {
        $n = $e.Current.Name
        $ct = $e.Current.ControlType.ProgrammaticName
        if ($n -and $n.Trim().Length -gt 0) {
            $lines.Add("   " + $ct + " | " + $n)
        }
    }
}
[System.IO.File]::WriteAllLines($out, $lines, [System.Text.Encoding]::UTF8)
Write-Output ("written: " + $out + " lines=" + $lines.Count)
