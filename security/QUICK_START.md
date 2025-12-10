# Quick Start Guide - Security Scanning

Быстрый анализ

#### Semgrep (Windows PowerShell)
```powershell
Get-Content EVIDENCE/P10/semgrep.sarif | jq '.runs[0].results | length'
```

#### Gitleaks (Windows PowerShell)
```powershell
(Get-Content EVIDENCE/P10/gitleaks.json | ConvertFrom-Json).Count
```

## Локальный запуск (опционально)

### Semgrep (быстрая проверка)
```bash
pip install semgrep

semgrep --config=auto src/
```

### Gitleaks (полное сканирование)
```bash
docker run --rm -v ${PWD}:/repo zricethezav/gitleaks:latest \
  detect --no-banner --config=/repo/security/.gitleaks.toml \
  --source=/repo --report-format=json \
  --report-path=/repo/EVIDENCE/P10/gitleaks.json
```
