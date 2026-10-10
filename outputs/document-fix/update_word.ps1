$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null
try {
 $file = (Resolve-Path 'outputs/document-fix/CapstoneCHAPTER1-5_Corrected.docx').Path
 $doc = $word.Documents.Open($file,$false,$false)
 for ($pass=0; $pass -lt 3; $pass++) { $doc.Repaginate(); $null=$doc.Fields.Update() }
 $doc.Save()
 $rows = @()
 foreach ($field in $doc.Fields) {
  if ($field.Code.Text -match 'PAGEREF\s+(\S+)') {
   $name=$Matches[1];$range=$doc.Bookmarks.Item($name).Range
   $rows += [PSCustomObject]@{Bookmark=$name; Display=$field.Result.Text; Page=$range.Information(1); PhysicalPage=$range.Information(3); Target=$range.Text}
  }
 }
 $rows | ConvertTo-Json -Depth 4 | Set-Content -Encoding utf8 'outputs/document-fix/word_page_audit.json'
 $pdf = Join-Path (Split-Path $file) 'qa_document.pdf'
 $doc.ExportAsFixedFormat($pdf,17)
 Write-Output ('Pages: ' + $doc.ComputeStatistics(2))
 Write-Output ('Updated page references: ' + $rows.Count)
 $doc.Close(0);$doc=$null
} finally { if ($null -ne $doc) { try {$doc.Close(0)} catch {} };try {$word.Quit()} catch {} }
