# Let PowerPoint itself author what pptxgenjs cannot: each slide's clip plays
# automatically when the slide opens, and slides change with a fade.
# Hand-written <p:timing> XML was refused by PowerPoint as corrupt (24 Sept 2026),
# so the timing is written by the app that has to read it.
#   pwsh -File postprocess-deck.ps1 <deck.pptx>
# Gate: exits 1 unless every slide ends with exactly one auto-starting media effect.
param([Parameter(Mandatory)][string]$Deck)
$path = (Resolve-Path $Deck).Path
$pp = New-Object -ComObject PowerPoint.Application
$bad = 0
try {
  $p = $pp.Presentations.Open($path, $false, $false, $false)
  foreach ($s in $p.Slides) {
    $media = @($s.Shapes | Where-Object { $_.Type -eq 16 })            # msoMedia
    if ($media.Count -ne 1) { "slide $($s.SlideIndex): $($media.Count) media shapes"; $bad++; continue }
    $seq = $s.TimeLine.MainSequence
    for ($i = $seq.Count; $i -ge 1; $i--) { $seq.Item($i).Delete() }
    $null = $seq.AddEffect($media[0], 83, 0, 2)                       # msoAnimEffectMediaPlay, with previous
    $s.SlideShowTransition.EntryEffect = 3849                          # ppEffectFadeSmoothly
    if ($seq.Count -ne 1 -or $seq.Item(1).Timing.TriggerType -ne 2) { "slide $($s.SlideIndex): effect not set"; $bad++ }
  }
  $p.Save()
  "autoplay + fade on $($p.Slides.Count - $bad) of $($p.Slides.Count) slide(s)"
  $p.Close()
} finally {
  $pp.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null; [GC]::Collect()
}
exit ([int]($bad -gt 0))
