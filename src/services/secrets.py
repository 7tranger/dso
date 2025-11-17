import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretValue:
    name: str
    _value: str

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:  # pragma: no cover
        return f"<secret:{self.name}>"

    __repr__ = __str__


def get_secret(
    name: str,
    *,
    default: str | None = None,
    required: bool = True,
    min_length: int = 16,
) -> SecretValue:
    raw = os.getenv(name, default)
    if raw is None:
        if required:
            raise RuntimeError(f"Secret '{name}' is not configured")
        raise RuntimeError(f"Secret '{name}' is not configured and no default provided")

    raw = raw.strip()
    if len(raw) < min_length:
        raise RuntimeError(f"Secret '{name}' has insufficient length")

    return SecretValue(name=name, _value=raw)
