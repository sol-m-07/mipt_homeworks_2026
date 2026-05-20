import json
from datetime import UTC, datetime, timedelta
from typing import Any, ParamSpec, Protocol, TypeVar, cast
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


def _is_positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _collect_validation_errors(
    critical_count: int,
    time_to_recover: int,
) -> list[ValueError]:
    checks = (
        (critical_count, INVALID_CRITICAL_COUNT),
        (time_to_recover, INVALID_RECOVERY_TIME),
    )
    return [ValueError(message) for value, message in checks if not _is_positive_integer(value)]


def _in_block_window(blocked_at: datetime, time_to_recover: int) -> bool:
    recover_after = blocked_at + timedelta(seconds=time_to_recover)
    return datetime.now(UTC) < recover_after


def _handle_failure(
    err: Exception,
    failed_calls: int,
    critical_count: int,
    triggers_on: type[Exception],
) -> tuple[int, datetime | None]:
    if not isinstance(err, triggers_on):
        return failed_calls, None

    next_failed_calls = failed_calls + 1
    if next_failed_calls < critical_count:
        return next_failed_calls, None

    return next_failed_calls, datetime.now(UTC)


def _is_recovered_or_raise(
    blocked_at: datetime | None,
    time_to_recover: int,
    func_name: str,
) -> bool:
    if blocked_at is None:
        return False
    if _in_block_window(blocked_at, time_to_recover):
        raise BreakerError(func_name=func_name, block_time=blocked_at)
    return True


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime):
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class _WrappedFunction:
    __name__: str
    __module__: str
    __doc__: str | None

    def __init__(
        self,
        func: Any,
        critical_count: int,
        time_to_recover: int,
        triggers_on: type[Exception],
    ):
        self._func = func
        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on
        self._failed_calls = 0
        self._blocked_at: datetime | None = None
        self._func_name = f"{func.__module__}.{func.__name__}"

        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if _is_recovered_or_raise(self._blocked_at, self._time_to_recover, self._func_name):
            self._blocked_at = None
            self._failed_calls = 0
        return self._invoke(*args, **kwargs)

    def _invoke(self, *args: Any, **kwargs: Any) -> Any:
        try:
            result = self._func(*args, **kwargs)
        except Exception as err:
            self._failed_calls, self._blocked_at = _handle_failure(
                err,
                self._failed_calls,
                self._critical_count,
                self._triggers_on,
            )
            if self._blocked_at is not None:
                raise BreakerError(func_name=self._func_name, block_time=self._blocked_at) from err
            raise

        self._failed_calls = 0
        return result


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors = _collect_validation_errors(critical_count, time_to_recover)
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        return cast(
            "CallableWithMeta[P, R_co]",
            _WrappedFunction(
                func=func,
                critical_count=self._critical_count,
                time_to_recover=self._time_to_recover,
                triggers_on=self._triggers_on,
            ),
        )


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
