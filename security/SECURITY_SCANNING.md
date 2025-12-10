# Security Scanning Setup - SAST & Secrets

Запуск локально

#### Semgrep
```bash
pip install semgrep

semgrep ci --config p/ci --config security/semgrep/rules.yml \
  --sarif --output EVIDENCE/P10/semgrep.sarif
```

#### Gitleaks
```bash
docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest \
  detect --no-banner --config=/repo/security/.gitleaks.toml \
  --source=/repo --report-format=json \
  --report-path=/repo/EVIDENCE/P10/gitleaks.json
```

### Semgrep Rules

Файл: `security/semgrep/rules.yml`

**Текущие кастомные правила:**

1. **hardcoded-password** (WARNING)
   - Обнаруживает хардкоженные пароли в коде
   - Игнорирует пустые строки

2. **sql-injection-risk** (ERROR)
   - Обнаруживает потенциальные SQL injection через конкатенацию строк
   - Проверяет f-strings с переменными в SQL запросах

3. **flask-debug-enabled** (WARNING)
   - Обнаруживает включенный debug режим Flask
   - Не должен быть включен в production
