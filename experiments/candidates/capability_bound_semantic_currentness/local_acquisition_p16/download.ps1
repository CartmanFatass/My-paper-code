param([string]$Url, [string]$Target, [long]$ExpectedBytes)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Net.Http
$handler = [System.Net.Http.HttpClientHandler]::new()
$handler.UseProxy = $false
$handler.UseDefaultCredentials = $false
$handler.Credentials = $null
$handler.UseCookies = $false
$handler.AllowAutoRedirect = $false
# No TLS callback/override, proxy, credentials, retries or range headers.
$client = [System.Net.Http.HttpClient]::new($handler)
$client.Timeout = [System.Threading.Timeout]::InfiniteTimeSpan
$response = $null
$stream = $null
$file = $null
try {
    $response = $client.GetAsync($Url, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
    if ([int]$response.StatusCode -ne 200) { throw "HTTP $([int]$response.StatusCode)" }
    $file = [System.IO.File]::Open($Target, [System.IO.FileMode]::CreateNew)
    $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
    $stream.CopyTo($file)
    $file.Flush()
    if ($file.Length -ne $ExpectedBytes) { throw "Incomplete body: $($file.Length) / $ExpectedBytes" }
    if ($null -ne $response.Content.Headers.ContentLength -and
        $response.Content.Headers.ContentLength -ne $ExpectedBytes) { throw 'Content-Length mismatch' }
} finally {
    if ($null -ne $file) { $file.Dispose() }
    if ($null -ne $stream) { $stream.Dispose() }
    if ($null -ne $response) { $response.Dispose() }
    $client.Dispose()
    $handler.Dispose()
}
