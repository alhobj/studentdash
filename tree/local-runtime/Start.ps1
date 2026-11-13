# Read-only loopback server using built-in .NET; never changes execution policy.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$port = 8765
$origin = "http://127.0.0.1:$port"
$paths = @{'/'='app/index.html'; '/package.json'='package.json'; '/results.json'='results.json'}
$assets = Get-Content -LiteralPath (Join-Path $root 'assets-manifest.json') -Raw | ConvertFrom-Json
foreach ($asset in $assets) {
    if ($asset -notmatch '^assets/[A-Za-z0-9_.-]+\.(js|css)$') { throw 'Invalid asset manifest.' }
    $paths['/' + $asset] = 'app/' + $asset
}
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
try { $listener.Start() } catch { throw 'Port 8765 is in use. Close the other local viewer and try again. Keep the same port to retain confidence.' }
Write-Host "Local student viewer: $origin/"
Write-Host 'Keep this window open. Close it to stop the viewer.'
Start-Process "$origin/"
try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $stream.ReadTimeout = 3000
            $stream.WriteTimeout = 3000
            $requestBytes = New-Object System.Collections.Generic.List[byte]
            $complete = $false
            while ($requestBytes.Count -lt 16384) {
                $value = $stream.ReadByte()
                if ($value -lt 0) { break }
                $requestBytes.Add([byte]$value)
                $n = $requestBytes.Count
                if ($n -ge 4 -and $requestBytes[$n-4] -eq 13 -and $requestBytes[$n-3] -eq 10 -and $requestBytes[$n-2] -eq 13 -and $requestBytes[$n-1] -eq 10) { $complete = $true; break }
            }
            if (-not $complete) { continue }
            $request = [Text.Encoding]::ASCII.GetString($requestBytes.ToArray())
            $lines = $request -split "`r`n"
            $first = $lines[0] -split ' '
            $headers = @{}
            foreach ($line in $lines | Select-Object -Skip 1) {
                $colon = $line.IndexOf(':')
                if ($colon -gt 0) { $headers[$line.Substring(0,$colon).ToLowerInvariant()] = $line.Substring($colon+1).Trim() }
            }
            $code = 200; $message = 'OK'; $type = 'text/plain'; $content = [byte[]]@()
            if ($first.Length -ne 3 -or $first[0] -notin @('GET','HEAD')) { $code = 405; $message = 'Method not allowed' }
            elseif ($headers['host'] -ne "127.0.0.1:$port" -or $headers['sec-fetch-site'] -eq 'cross-site' -or ($headers.ContainsKey('origin') -and $headers['origin'] -ne $origin)) { $code = 403; $message = 'Forbidden' }
            else {
                $route = ($first[1] -split '\?')[0]
                if (-not $paths.ContainsKey($route)) { $code = 404; $message = 'Not found' }
                else {
                    try {
                        $file = Join-Path $root $paths[$route]
                        # Reject actual links; OneDrive cloud placeholders may themselves be reparse points.
                        $item = Get-Item -LiteralPath $file
                        $check = $item
                        while ($null -ne $check -and $check.FullName -ne $root) {
                            if ($check.LinkType -in @('SymbolicLink','Junction')) { throw 'Linked file refused' }
                            if ($check -is [IO.FileInfo]) { $check = $check.Directory } else { $check = $check.Parent }
                        }
                        $limit = if ($route -eq '/results.json') { 2097152 } else { 8388608 }
                        if ($item.Length -gt $limit) { throw 'File too large' }
                        $content = [IO.File]::ReadAllBytes($file)
                        if ($content.Length -gt $limit) { throw 'File too large' }
                        $type = switch ([IO.Path]::GetExtension($file)) { '.html' {'text/html'} '.js' {'application/javascript'} '.css' {'text/css'} '.json' {'application/json'} default {'application/octet-stream'} }
                    } catch { $code = 503; $message = 'Local file unavailable; wait for OneDrive to download it' }
                }
            }
            if ($code -ne 200) { $content = [Text.Encoding]::UTF8.GetBytes($message) }
            $csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            $reply = "HTTP/1.1 $code $message`r`nContent-Type: $type`r`nContent-Length: $($content.Length)`r`nCache-Control: no-store`r`nContent-Security-Policy: $csp`r`nX-Content-Type-Options: nosniff`r`nReferrer-Policy: no-referrer`r`nConnection: close`r`n`r`n"
            $bytes = [Text.Encoding]::ASCII.GetBytes($reply)
            $stream.Write($bytes,0,$bytes.Length)
            if ($first[0] -ne 'HEAD') { $stream.Write($content,0,$content.Length) }
        } catch {
            # A timed-out or incomplete client cannot stop subsequent file updates.
        } finally { $client.Close() }
    }
} finally { $listener.Stop() }
