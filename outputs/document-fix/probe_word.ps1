$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try { $doc = $word.Documents.Open((Resolve-Path 'outputs/document-fix/source.docx').Path,$false,$true); $doc.Repaginate(); Write-Output ('Pages: ' + $doc.ComputeStatistics(2)); $doc.Close(0) } finally { $word.Quit() }
