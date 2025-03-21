# Install-HaiperService.ps1
# Script to install the Haiper API as a Windows service

# Ensure the script is run as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script requires administrator privileges. Please run as administrator."
    exit 1
}

# Define service properties
$serviceName = "HaiperAPI"
$serviceDisplayName = "Haiper API Service"
$serviceDescription = "FastAPI-based service for workflow management with PostgreSQL backend"
$exePath = "D:\Projects\haiper_api"
$nssm = "C:\Tools\nssm\win64\nssm.exe"

# Check if NSSM (Non-Sucking Service Manager) is installed
if (-not (Test-Path $nssm)) {
    Write-Host "NSSM is not installed at the expected location. Please install NSSM and try again."
    Write-Host "You can download NSSM from https://nssm.cc/download"
    exit 1
}

# Check if the service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "Service '$serviceName' already exists. Removing existing service..."
    
    # Stop the service if it's running
    if ($existingService.Status -eq "Running") {
        Write-Host "Stopping service '$serviceName'..."
        Stop-Service -Name $serviceName
        Start-Sleep -Seconds 5
    }
    
    # Use NSSM to remove the service
    & $nssm remove $serviceName confirm
    
    Write-Host "Service '$serviceName' has been removed."
}

# Verify that the path to the application exists
if (-not (Test-Path $exePath)) {
    Write-Host "Path '$exePath' does not exist. Please check the path and try again."
    exit 1
}

# Create Python virtual environment if needed (uncomment if required)
# $venvPath = Join-Path $exePath "venv"
# if (-not (Test-Path $venvPath)) {
#     Write-Host "Creating Python virtual environment..."
#     Set-Location $exePath
#     & python -m venv venv
# }

# Install the service using NSSM
Write-Host "Installing '$serviceName' service..."

# Create an activation script that will be called by the service
$activationScript = @"
@echo off
echo Activating conda environment...
call conda activate haiper_api
echo Setting Tesseract Path...
SET TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
cd /d $exePath
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
"@

# Save the activation script
$scriptPath = Join-Path $exePath "start_service.bat"
$activationScript | Out-File -FilePath $scriptPath -Encoding ASCII

# Basic service installation
& $nssm install $serviceName $env:ComSpec "/c $scriptPath"
& $nssm set $serviceName DisplayName $serviceDisplayName
& $nssm set $serviceName Description $serviceDescription

# Set the working directory
& $nssm set $serviceName AppDirectory $exePath

# Set the startup type to automatic
& $nssm set $serviceName Start SERVICE_AUTO_START

# Set the service to restart if it fails
& $nssm set $serviceName AppExit Default Restart
& $nssm set $serviceName AppRestartDelay 5000  # 5 seconds delay before restart

# Configure stdout and stderr logging
$logPath = Join-Path $exePath "logs"
if (-not (Test-Path $logPath)) {
    New-Item -Path $logPath -ItemType Directory | Out-Null
}
& $nssm set $serviceName AppStdout (Join-Path $logPath "service_stdout.log")
& $nssm set $serviceName AppStderr (Join-Path $logPath "service_stderr.log")
& $nssm set $serviceName AppRotateFiles 1
& $nssm set $serviceName AppRotateOnline 1
& $nssm set $serviceName AppRotateSeconds 86400  # Rotate logs daily
& $nssm set $serviceName AppRotateBytes 10485760  # Rotate logs when they reach ~10MB

# Configure environment variables
& $nssm set $serviceName AppEnvironmentExtra "TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe"

# Start the service
Write-Host "Starting service '$serviceName'..."
Start-Service -Name $serviceName

# Check the service status
$service = Get-Service -Name $serviceName
Write-Host "Service status: $($service.Status)"

if ($service.Status -eq "Running") {
    Write-Host "Service '$serviceName' has been successfully installed and started."
} else {
    Write-Host "Service was installed but failed to start. Check the logs for details."
}

Write-Host "Done."