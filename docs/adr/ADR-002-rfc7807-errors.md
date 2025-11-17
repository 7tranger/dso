# ADR-002: Ошибки в формате RFC 7807 и correlation_id

## Status
Accepted

## Context
Детальные сообщения ошибок могут раскрывать внутреннюю архитектуру и конфиденциальную информацию. Требуется унифицированный, безопасный формат ошибок и трассировка запросов.

## Decision
- Переходим на `application/problem+json` (RFC 7807) во всех обработчиках ошибок.
- Поля ответа: `type`, `title`, `status`, `detail`, `correlation_id`.
- `correlation_id` берётся из заголовка `X-Correlation-Id` или генерируется (UUID v4) middleware и возвращается в ответе заголовком и в теле ошибки.
- Маскирование деталей: сообщения формируются контролируемо; внутренние исключения не выводятся как есть.
- Типы ошибок нормализуются в пространство `/problems/<code>`.

## Consequences
- Снижается риск утечки деталей (см. R004, R008). Улучшается трассировка инцидентов по `correlation_id`.

## Links
- NFR: `NFR-005` (Обработка ошибок)
- P04: `F#-Errors-Standard`, `R#-RFC7807` (идентификаторы требований курса)
- Tests: `tests/test_errors.py::test_not_found_item`, `tests/test_errors.py::test_validation_error`, `tests/test_health.py::test_correlation_id_header_present`
- RISKS: Закрывает меры по `R004` (Утечка внутренней информации) и `R008` (Утечка stack trace). Критерий закрытия: все ошибки возвращаются в RFC 7807 формате; тесты проверяют наличие `correlation_id` и тип/заголовок/статус/деталь.
