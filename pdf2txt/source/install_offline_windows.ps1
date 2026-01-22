# Install the project on an offline Windows machine with Anaconda 3
# Run this script in PowerShell on the target machine without internet access

param(
    [string]$EnvName = "pdf2txt",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Get script and project directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Check if we're running from offline_packages_windows/source
if (Test-Path (Join-Path $ScriptDir "extractors")) {
    # Script is in source directory
    $OfflineDir = Split-Path -Parent $ScriptDir
    $ProjectDir = $ScriptDir
} else {
    # Script is in scripts directory
    $OfflineDir = Join-Path $ProjectDir "offline_packages_windows"
}

$PythonDir = Join-Path $OfflineDir "python"
$RequirementsFile = Join-Path $OfflineDir "requirements.txt"

Write-Host "=== Windows Offline Installation Script ===" -ForegroundColor Cyan
Write-Host "Project directory: $ProjectDir"
Write-Host "Offline packages: $OfflineDir"
Write-Host "Environment name: $EnvName"
Write-Host ""

# Check if offline_packages directory exists
if (-not (Test-Path $OfflineDir)) {
    Write-Host "Error: offline_packages_windows directory not found!" -ForegroundColor Red
    Write-Host "Please ensure you have copied the offline_packages_windows directory."
    exit 1
}

# Check if Python packages exist
if (-not (Test-Path $PythonDir) -or (Get-ChildItem $PythonDir -Filter "*.whl" | Measure-Object).Count -eq 0) {
    Write-Host "Error: No Python wheel packages found in $PythonDir" -ForegroundColor Red
    exit 1
}

$WheelCount = (Get-ChildItem $PythonDir -Filter "*.whl" | Measure-Object).Count
Write-Host "Found $WheelCount wheel packages in $PythonDir"
Write-Host ""

# Check for Anaconda/Miniconda
Write-Host "=== Checking for Anaconda ===" -ForegroundColor Cyan
$CondaPath = $null

# Try to find conda in common locations
$CondaLocations = @(
    "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
    "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
    "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe",
    "$env:LOCALAPPDATA\miniconda3\Scripts\conda.exe",
    "C:\ProgramData\anaconda3\Scripts\conda.exe",
    "C:\ProgramData\miniconda3\Scripts\conda.exe",
    "C:\anaconda3\Scripts\conda.exe",
    "C:\miniconda3\Scripts\conda.exe"
)

foreach ($loc in $CondaLocations) {
    if (Test-Path $loc) {
        $CondaPath = $loc
        break
    }
}

# Also check if conda is in PATH
if (-not $CondaPath) {
    try {
        $CondaPath = (Get-Command conda -ErrorAction SilentlyContinue).Source
    } catch {
        # conda not found in PATH
    }
}

if (-not $CondaPath) {
    Write-Host "Error: Anaconda/Miniconda not found!" -ForegroundColor Red
    Write-Host "Please ensure Anaconda 3 is installed."
    exit 1
}

Write-Host "Found conda at: $CondaPath"
$CondaDir = Split-Path -Parent (Split-Path -Parent $CondaPath)
Write-Host "Anaconda directory: $CondaDir"
Write-Host ""

# Initialize conda for PowerShell if needed
Write-Host "=== Initializing Conda ===" -ForegroundColor Cyan
$CondaHook = Join-Path $CondaDir "shell\condabin\conda-hook.ps1"
if (Test-Path $CondaHook) {
    . $CondaHook
    Write-Host "Conda initialized."
} else {
    # Try alternative initialization
    $env:PATH = "$CondaDir;$CondaDir\Scripts;$CondaDir\Library\bin;$env:PATH"
    Write-Host "Conda added to PATH."
}
Write-Host ""

# Check if environment already exists
Write-Host "=== Setting Up Conda Environment ===" -ForegroundColor Cyan
$EnvExists = & $CondaPath env list | Select-String -Pattern "^$EnvName\s"

if ($EnvExists) {
    if ($Force) {
        Write-Host "Removing existing environment '$EnvName'..."
        & $CondaPath env remove -n $EnvName -y
    } else {
        Write-Host "Environment '$EnvName' already exists." -ForegroundColor Yellow
        $Response = Read-Host "Do you want to recreate it? [y/N]"
        if ($Response -match "^[Yy]") {
            Write-Host "Removing existing environment..."
            & $CondaPath env remove -n $EnvName -y
        } else {
            Write-Host "Using existing environment."
        }
    }
}

# Create conda environment with Python 3.11
$EnvDir = Join-Path $CondaDir "envs\$EnvName"

if (-not (& $CondaPath env list | Select-String -Pattern "^$EnvName\s")) {
    Write-Host "Creating conda environment '$EnvName' with Python 3.11..."
    
    # Create environment (use --offline flag if conda packages are cached)
    & $CondaPath create -n $EnvName python=3.11 pip -y --offline
    
    # If offline fails, try without --offline flag
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Offline creation failed, trying online..." -ForegroundColor Yellow
        & $CondaPath create -n $EnvName python=3.11 pip -y
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating environment." -ForegroundColor Red
        Write-Host ""
        Write-Host "Please run the following command manually:" -ForegroundColor Yellow
        Write-Host "  conda create -n $EnvName python=3.11 pip -y" -ForegroundColor Yellow
        Write-Host "Then re-run this script." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Environment created."
}

# Verify environment was created
if (-not (Test-Path $EnvDir)) {
    Write-Host "Error: Environment directory not found at $EnvDir" -ForegroundColor Red
    Write-Host "Please create the environment manually:" -ForegroundColor Yellow
    Write-Host "  conda create -n $EnvName python=3.11 pip -y" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Set up paths directly (don't rely on conda activate)
Write-Host "=== Setting Up Environment Paths ===" -ForegroundColor Cyan
$PipPath = Join-Path $EnvDir "Scripts\pip.exe"
$PythonPath = Join-Path $EnvDir "python.exe"

# Verify pip exists
if (-not (Test-Path $PipPath)) {
    Write-Host "Error: pip not found at $PipPath" -ForegroundColor Red
    Write-Host "The environment may not have been created correctly." -ForegroundColor Yellow
    exit 1
}

Write-Host "Environment directory: $EnvDir"
Write-Host "Using pip: $PipPath"
Write-Host ""

# Upgrade pip first if wheel available
Write-Host "=== Upgrading pip ===" -ForegroundColor Cyan
$PipWheel = Get-ChildItem $PythonDir -Filter "pip-*.whl" | Select-Object -First 1
if ($PipWheel) {
    & $PipPath install --no-index --find-links="$PythonDir" pip
    Write-Host "pip upgraded."
} else {
    Write-Host "No pip wheel found, using existing pip."
}
Write-Host ""

# Install Python packages from local wheels
Write-Host "=== Installing Python Packages ===" -ForegroundColor Cyan
if (Test-Path $RequirementsFile) {
    Write-Host "Installing from requirements.txt..."
    & $PipPath install --no-index --find-links="$PythonDir" -r $RequirementsFile
} else {
    Write-Host "No requirements.txt found. Installing all wheels..."
    & $PipPath install --no-index --find-links="$PythonDir" (Get-ChildItem $PythonDir -Filter "*.whl" | ForEach-Object { $_.FullName })
}
Write-Host ""

# Verify installation
Write-Host "=== Verifying Installation ===" -ForegroundColor Cyan
Write-Host "Checking key packages..."

$Packages = @("pymupdf", "pdfminer", "pdfplumber", "pypdf")
foreach ($pkg in $Packages) {
    try {
        & $PythonPath -c "import $pkg" 2>$null
        Write-Host "  [OK] $pkg" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $pkg (not installed or import failed)" -ForegroundColor Red
    }
}
Write-Host ""

# Copy source files if needed
Write-Host "=== Setting Up Project Source ===" -ForegroundColor Cyan
$SourceDir = Join-Path $OfflineDir "source"
if (Test-Path $SourceDir) {
    $FilesToCopy = @("pyproject.toml", "compare.py", "README.md")
    foreach ($file in $FilesToCopy) {
        $SourceFile = Join-Path $SourceDir $file
        $DestFile = Join-Path $ProjectDir $file
        if ((Test-Path $SourceFile) -and -not (Test-Path $DestFile)) {
            Copy-Item $SourceFile $DestFile
            Write-Host "Copied $file"
        }
    }
    
    $ExtractorsSource = Join-Path $SourceDir "extractors"
    $ExtractorsDest = Join-Path $ProjectDir "extractors"
    if ((Test-Path $ExtractorsSource) -and -not (Test-Path $ExtractorsDest)) {
        Copy-Item $ExtractorsSource $ExtractorsDest -Recurse
        Write-Host "Copied extractors/"
    }
}
Write-Host ""

Write-Host "=== Installation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To use the project:"
Write-Host "  1. Activate the conda environment:"
Write-Host "     conda activate $EnvName" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Run the comparison script:"
Write-Host "     python compare.py samples\1.pdf" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: The following extractors are NOT available in this offline installation:"
Write-Host "  - marker-pdf, docling (AI/ML packages - excluded for size)"
Write-Host "  - pytesseract (requires Tesseract OCR)"
Write-Host "  - pdf2image (requires Poppler)"
Write-Host "  - tika (requires Java)"

