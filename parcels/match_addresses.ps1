$ErrorActionPreference = 'Stop'

function Normalize-Address([string]$address, [switch]$NoSuffix) {
    if ([string]::IsNullOrWhiteSpace($address)) { return '' }
    $text = $address.ToUpperInvariant()
    $text = $text -replace '[^A-Z0-9 ]', ' '
    $text = $text -replace '\bNORTH\b', 'N'
    $text = $text -replace '\bSOUTH\b', 'S'
    $text = $text -replace '\bEAST\b', 'E'
    $text = $text -replace '\bWEST\b', 'W'
    $text = $text -replace '\bNORTHEAST\b', 'NE'
    $text = $text -replace '\bNORTHWEST\b', 'NW'
    $text = $text -replace '\bSOUTHEAST\b', 'SE'
    $text = $text -replace '\bSOUTHWEST\b', 'SW'
    $replacements = @{
        'STREET'='ST'; 'ROAD'='RD'; 'AVENUE'='AVE'; 'BOULEVARD'='BLVD'; 'DRIVE'='DR';
        'COURT'='CT'; 'LANE'='LN'; 'PLACE'='PL'; 'PARKWAY'='PKWY'; 'CIRCLE'='CIR';
        'TERRACE'='TER'; 'TRAIL'='TRL'; 'HIGHWAY'='HWY'; 'SQUARE'='SQ'; 'WAY'='WAY';
        'APARTMENT'='APT'; 'UNIT'='UNIT'; 'SUITE'='STE'
    }
    foreach ($key in $replacements.Keys) { $text = $text -replace ("\b{0}\b" -f $key), $replacements[$key] }
    $text = ($text -replace '\s+', ' ').Trim()
    if ($NoSuffix) { $text = $text -replace '\s+(ST|RD|AVE|BLVD|DR|CT|LN|PL|PKWY|CIR|TER|TRL|HWY|SQ|WAY)$', '' }
    return $text
}

function Get-UniqueAddressCandidate($items) {
    if (!$items -or $items.Count -eq 0) { return $null }
    $addresses = @($items | ForEach-Object { $_.PropAddress_Full } | Select-Object -Unique)
    if ($addresses.Count -eq 1) { return $items[0] }
    return $null
}

function Get-AddressCore([string]$address) {
    $text = Normalize-Address $address
    # Keep the civic number, street name, street type, and an optional trailing direction;
    # discard unit, guest-house, and other descriptive text that follows the street address.
    if ($text -match '^(.*?\s(?:ST|RD|AVE|BLVD|DR|CT|LN|PL|PKWY|CIR|TER|TRL|HWY|SQ|WAY))(?:\s+(N|S|E|W|NE|NW|SE|SW))?(?:\s+.*)?$') {
        return (($Matches[1] + $(if ($Matches[2]) { ' ' + $Matches[2] } else { '' })).Trim())
    }
    return $text
}

$parcelRows = Import-Csv -LiteralPath 'Parcel_Digest_abridged.csv'
$exact = @{}
$base = @{}
foreach ($row in $parcelRows) {
    $address = $row.PropAddress_Full
    $key = Normalize-Address $address
    $baseKey = Get-AddressCore $address
    if (!$exact.ContainsKey($key)) { $exact[$key] = [System.Collections.Generic.List[object]]::new() }
    $exact[$key].Add($row)
    if (!$base.ContainsKey($baseKey)) { $base[$baseKey] = [System.Collections.Generic.List[object]]::new() }
    $base[$baseKey].Add($row)
}

$renewals = Import-Csv -LiteralPath 'STR Renewal List.ChathamCounty.2026.csv'
$results = foreach ($renewal in $renewals) {
    $source = $renewal.DBA
    $key = Normalize-Address $source
    $baseKey = Get-AddressCore $source
    $candidate = $null
    $method = 'No unique match'
    if ($exact.ContainsKey($key)) {
        $candidate = Get-UniqueAddressCandidate $exact[$key]
        if ($candidate) { $method = 'Exact normalized' }
    }
    if (!$candidate -and $base.ContainsKey($baseKey)) {
        $candidate = Get-UniqueAddressCandidate $base[$baseKey]
        if ($candidate) { $method = 'Normalized address core' }
    }

    $out = [ordered]@{}
    foreach ($property in $renewal.PSObject.Properties) { $out[$property.Name] = $property.Value }
    $out['Parcel_Matched_Address'] = if ($candidate) { $candidate.PropAddress_Full } else { '' }
    $out['Parcel_PIN'] = if ($candidate) { $candidate.PIN } else { '' }
    $out['Parcel_Match_Method'] = $method
    [pscustomobject]$out
}

$results | Export-Csv -LiteralPath 'STR Renewal List.ChathamCounty.2026.matched.csv' -NoTypeInformation -Encoding utf8
$results | Group-Object Parcel_Match_Method | Sort-Object Name | Select-Object Name,Count | Format-Table -AutoSize
