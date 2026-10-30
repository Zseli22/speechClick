<#
.SYNOPSIS
	Builds speechClick into a distributable .nvda-addon archive.

.DESCRIPTION
	Packages manifest.ini, doc and globalPlugins into dist\<name>-<version>.nvda-addon.
	The version is read from manifest.ini so the archive name always matches the metadata.

.EXAMPLE
	.\build.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$manifestPath = Join-Path $root 'manifest.ini'

if (-not (Test-Path $manifestPath)) {
	throw "manifest.ini not found at $manifestPath"
}

$manifestText = Get-Content $manifestPath -Raw
$nameMatch = [regex]::Match($manifestText, '(?m)^\s*name\s*=\s*"([^"]+)"')
$versionMatch = [regex]::Match($manifestText, '(?m)^\s*version\s*=\s*"([^"]+)"')

if (-not $nameMatch.Success -or -not $versionMatch.Success) {
	throw 'manifest.ini must contain quoted name and version fields'
}

$name = $nameMatch.Groups[1].Value
$version = $versionMatch.Groups[1].Value

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$distDir = Join-Path $root 'dist'
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$outputPath = Join-Path $distDir "$name-$version.nvda-addon"

if (Test-Path $outputPath) {
	Remove-Item $outputPath -Force
}

$sources = @('manifest.ini', 'doc', 'globalPlugins')
$files = foreach ($item in $sources) {
	$path = Join-Path $root $item
	if (Test-Path $path -PathType Leaf) {
		Get-Item $path
	}
	elseif (Test-Path $path -PathType Container) {
		Get-ChildItem $path -Recurse -File
	}
	else {
		throw "Missing packaging source: $item"
	}
}

$files = $files | Where-Object {
	$_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.Extension -notin @('.pyc', '.pyo')
}

$archive = [System.IO.Compression.ZipFile]::Open($outputPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
	foreach ($file in $files) {
		# Zip entry names always use forward slashes, as NVDA's zip reader expects.
		$entryName = $file.FullName.Substring($root.Length).TrimStart('\', '/').Replace('\', '/')
		[void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
			$archive,
			$file.FullName,
			$entryName,
			[System.IO.Compression.CompressionLevel]::Optimal
		)
		Write-Verbose "added $entryName"
	}
}
finally {
	$archive.Dispose()
}

$hash = (Get-FileHash $outputPath -Algorithm SHA256).Hash
Write-Host "Built $outputPath"
Write-Host ("Entries: {0}" -f $files.Count)
Write-Host "SHA256: $hash"
