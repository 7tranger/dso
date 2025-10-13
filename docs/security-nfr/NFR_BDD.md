# NFR Behavior-Driven Development (BDD) Scenarios

## NFR-001: Время ответа API

### Позитивный сценарий: Быстрый ответ на health check
```gherkin
Feature: API Response Time
  As a client application
  I want API endpoints to respond quickly
  So that my application remains responsive

Scenario: Health check responds within acceptable time
  Given the API server is running
  When I send a GET request to "/health"
  Then the response should be received within 200ms
  And the response status should be 200
  And the response body should contain {"status": "ok"}
```

### Позитивный сценарий: Создание элемента в пределах времени
```gherkin
Scenario: Create item responds within acceptable time
  Given the API server is running
  And no items exist in the system
  When I send a POST request to "/items" with name "test item"
  Then the response should be received within 200ms
  And the response status should be 200
  And the response should contain the created item
```

### Негативный сценарий: Медленный ответ при высокой нагрузке
```gherkin
Scenario: API degrades gracefully under load
  Given the API server is running
  And 100 concurrent requests are being processed
  When I send a GET request to "/health"
  Then the response should be received within 500ms
  And the response status should be 200
```

## NFR-005: Обработка ошибок

### Позитивный сценарий: Консистентный формат ошибок
```gherkin
Feature: Error Handling
  As a client application
  I want consistent error responses
  So that I can handle errors uniformly

Scenario: Validation error returns proper format
  Given the API server is running
  When I send a POST request to "/items" with empty name
  Then the response status should be 422
  And the response should be valid JSON
  And the response should contain:
    """
    {
      "error": {
        "code": "validation_error",
        "message": "name cannot be empty"
      }
    }
    """
```

### Позитивный сценарий: Not found error format
```gherkin
Scenario: Not found error returns proper format
  Given the API server is running
  And no items exist in the system
  When I send a GET request to "/items/999"
  Then the response status should be 404
  And the response should be valid JSON
  And the response should contain:
    """
    {
      "error": {
        "code": "not_found",
        "message": "item not found"
      }
    }
    """
```

### Негативный сценарий: Обработка неожиданных ошибок
```gherkin
Scenario: Unexpected error is handled gracefully
  Given the API server is running
  And the database is unavailable
  When I send a GET request to "/items/1"
  Then the response status should be 500
  And the response should be valid JSON
  And the response should contain an error object
  And the error should not expose internal details
```

## NFR-008: Валидация входных данных

### Позитивный сценарий: Валидные данные принимаются
```gherkin
Feature: Input Validation
  As a client application
  I want input validation to prevent invalid data
  So that the system remains secure and stable

Scenario: Valid input is accepted
  Given the API server is running
  When I send a POST request to "/items" with name "valid item name"
  Then the response status should be 200
  And the response should contain the created item
  And the item name should be "valid item name"
```

### Позитивный сценарий: Пустые строки отклоняются
```gherkin
Scenario: Empty string is rejected
  Given the API server is running
  When I send a POST request to "/items" with name ""
  Then the response status should be 422
  And the response should contain validation error
```

### Негативный сценарий: Слишком длинные строки отклоняются
```gherkin
Scenario: Long string is rejected
  Given the API server is running
  When I send a POST request to "/items" with name longer than 100 characters
  Then the response status should be 422
  And the response should contain validation error
  And the error message should indicate "name too long"
```

### Негативный сценарий: SQL injection попытки блокируются
```gherkin
Scenario: SQL injection attempts are blocked
  Given the API server is running
  When I send a POST request to "/items" with name "'; DROP TABLE items; --"
  Then the response status should be 422
  And the response should contain validation error
  And the malicious input should not be processed
```

## NFR-012: Покрытие тестами

### Позитивный сценарий: Критические пути покрыты тестами
```gherkin
Feature: Test Coverage
  As a developer
  I want comprehensive test coverage
  So that the system is reliable

Scenario: Critical paths have test coverage
  Given the test suite is configured
  When I run the test coverage analysis
  Then the overall coverage should be at least 80%
  And all API endpoints should have test coverage
  And all error handling paths should have test coverage
  And all validation functions should have test coverage
```

### Негативный сценарий: Недостаточное покрытие тестами
```gherkin
Scenario: Insufficient test coverage is detected
  Given the test suite is configured
  And some critical functions lack tests
  When I run the test coverage analysis
  Then the coverage should be below 80%
  And the CI pipeline should fail
  And a detailed coverage report should be generated
```

## NFR-004: Доступность системы

### Позитивный сценарий: Система доступна
```gherkin
Feature: System Availability
  As a user
  I want the system to be available
  So that I can use the service when needed

Scenario: System is available and responding
  Given the API server is running
  When I check the system status
  Then the health endpoint should return 200
  And the system should be accessible
  And the uptime should be at least 99.5%
```

### Негативный сценарий: Восстановление после сбоя
```gherkin
Scenario: System recovers after failure
  Given the API server is running
  And the system experiences a failure
  When the system restarts
  Then it should be available within 30 seconds
  And the health endpoint should return 200
  And all functionality should be restored
```
