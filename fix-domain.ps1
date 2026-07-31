$repo = "D:\projects\wordfeather"   # adjust if needed
$files = Get-ChildItem -Path $repo -Recurse -Include *.html,*.js,*.json

$replacements = @{
    'https://abdullahbutt.github.io/deutsch-lernen-goethe-a1-c2/' = 'https://wordfeather.com/'
    '/deutsch-lernen-goethe-a1-c2/icons/'                          = '/icons/'
    '/deutsch-lernen-goethe-a1-c2/manifest.json'                   = '/manifest.json'
    "/deutsch-lernen-goethe-a1-c2/sw.js"                           = '/sw.js'
    'content="Deutsch Lernen"'                                     = 'content="WordFeather"'
    '🇩🇪 Deutsch Lernen</a>'                                        = '🪶 WordFeather</a>'
    '🇩🇪 Deutsch Lernen — Goethe-Zertifikat A1 to C2'               = '🪶 WordFeather — Goethe-Zertifikat A1 to C2'
    'github.com/abdullahbutt/deutsch-lernen-goethe-a1-c2'          = 'github.com/abdullahbutt/wordfeather'
    '3,000+ words'                                                 = '5,200+ words'
    'Deutsch Learning Hub'                                         = 'WordFeather'
}

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $original = $content
    foreach ($old in $replacements.Keys) {
        $content = $content -replace [regex]::Escape($old), $replacements[$old]
    }
    if ($content -ne $original) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        Write-Host "Fixed: $($file.Name)"
    }
}