from contextvars import ContextVar

correlation_id_var = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str | None):
    correlation_id_var.set(value)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()
