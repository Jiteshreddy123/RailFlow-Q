$ErrorActionPreference = 'Stop'

Write-Host 'RailFlow-Q Phase 1' -ForegroundColor Cyan
Write-Host 'Installing Python dependencies...'
python -m pip install -r requirements.txt
Write-Host 'Running tests...'
python -m pytest -q
Write-Host 'Running mock dashboard...'
python -m mock.frontend.mock_dashboard
