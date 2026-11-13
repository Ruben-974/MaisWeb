param([Parameter(Mandatory=$true)][string]$QueuePath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$taskAsyncMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Wait-ArchiveOperation($Operation, $ResultType) {
    $taskNet = $taskAsyncMethod.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $taskNet.Wait()
    $taskNet.Result
}
$taskLanguage = New-Object Windows.Globalization.Language('pt-BR')
$taskEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($taskLanguage)
if ($null -eq $taskEngine) { throw 'OCR de Português (Brasil) indisponível.' }
$taskQueue = Get-Content -LiteralPath $QueuePath -Raw -Encoding UTF8 | ConvertFrom-Json
$taskDone = 0
foreach ($taskItem in $taskQueue) {
    $taskDone++
    if (Test-Path -LiteralPath $taskItem.saida) { continue }
    try {
        $taskFile = Wait-ArchiveOperation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($taskItem.imagem)) ([Windows.Storage.StorageFile])
        $taskStream = Wait-ArchiveOperation ($taskFile.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $taskDecoder = Wait-ArchiveOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($taskStream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $taskBitmap = Wait-ArchiveOperation ($taskDecoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $taskResult = Wait-ArchiveOperation ($taskEngine.RecognizeAsync($taskBitmap)) ([Windows.Media.Ocr.OcrResult])
        $taskLines = @($taskResult.Lines | ForEach-Object { $_.Text })
        $taskOutput = @{ documento=$taskItem.documento; pagina=$taskItem.pagina; metodo='OCR Windows pt-BR'; texto=($taskLines -join "`n"); estado='ok' }
        $taskBitmap.Dispose(); $taskStream.Dispose()
    } catch {
        $taskOutput = @{ documento=$taskItem.documento; pagina=$taskItem.pagina; metodo='OCR Windows pt-BR'; texto=''; estado='erro'; erro=$_.Exception.Message }
    }
    $taskOutput | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskItem.saida -Encoding UTF8
    Write-Output "OCR $taskDone/$($taskQueue.Count): $($taskItem.documento) pagina $($taskItem.pagina) - $($taskOutput.estado)"
}
