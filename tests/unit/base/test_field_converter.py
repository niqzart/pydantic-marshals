from typing import Any
from unittest.mock import Mock, PropertyMock, call

import pytest

from pydantic_marshals.base.fields.base import MarshalField
from pydantic_marshals.base.models import FieldConverter
from tests.unit.conftest import DummyFactory, MockStack


def test_field_types_empty() -> None:
    class Converter(FieldConverter):
        pass

    assert len(Converter.field_types) == 0


@pytest.mark.parametrize("static_count", [0, 1, 2])
def test_field_types_static(dummy_factory: DummyFactory, static_count: int) -> None:
    class Converter(FieldConverter):
        field_types = tuple(dummy_factory(f"static_{i}") for i in range(static_count))

    assert len(Converter.field_types) == static_count
    for i in range(static_count):
        assert Converter.field_types[i] is dummy_factory(f"static_{i}")


@pytest.mark.parametrize("static_count", [0, 1, 2])
@pytest.mark.parametrize("dynamic_count", [0, 1, 2])
def test_field_types_dynamic(
    dummy_factory: DummyFactory,
    static_count: int,
    dynamic_count: int,
) -> None:
    class Converter(FieldConverter):
        field_types = tuple(dummy_factory(f"static_{i}") for i in range(static_count))

        @classmethod
        def dynamic_field_types(cls) -> Any:
            yield from (dummy_factory(f"dynamic_{i}") for i in range(dynamic_count))

    assert len(Converter.field_types) == static_count + dynamic_count
    for i in range(static_count):
        assert Converter.field_types[i] is dummy_factory(f"static_{i}")
    for i in range(dynamic_count):
        assert Converter.field_types[static_count + i] is dummy_factory(f"dynamic_{i}")


def test_convert_converted_field() -> None:
    field_mock = MarshalField()
    assert FieldConverter.convert_field(field_mock) is field_mock


def create_field_convert_mock(convert_result: Any) -> Mock:
    result = Mock(MarshalField)
    result.convert.return_value = convert_result
    return result


@pytest.mark.parametrize("field_count", [0, 1, 2])
def test_fail_conversion(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    field_count: int,
) -> None:
    field_types = tuple(create_field_convert_mock(None) for _ in range(field_count))

    field_types_mock = mock_stack.enter_mock(
        FieldConverter, "field_types", mock=PropertyMock(return_value=field_types)
    )

    with pytest.raises(RuntimeError) as exc:
        FieldConverter.convert_field(dummy_factory("raw"))

    assert len(exc.value.args) == 1
    assert exc.value.args[0] == f"Couldn't convert field: {(dummy_factory('raw'),)}"

    field_types_mock.assert_called_once_with()


@pytest.mark.parametrize("before_count", [0, 1, 2])
@pytest.mark.parametrize("after_count", [0, 1, 2])
@pytest.mark.parametrize("input_len", [0, 1, 2])
def test_convert_field(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    before_count: int,
    after_count: int,
    input_len: int,
) -> None:
    field_types = (
        *tuple(create_field_convert_mock(None) for _ in range(before_count)),
        create_field_convert_mock(dummy_factory("return")),
        *tuple(create_field_convert_mock(dummy_factory(i)) for i in range(after_count)),
    )

    field_types_mock = mock_stack.enter_mock(
        FieldConverter, "field_types", mock=PropertyMock(return_value=field_types)
    )

    input_value: Any
    check_value: tuple[Any, ...]
    if input_len == 0:
        input_value = dummy_factory("raw")
        check_value = (dummy_factory("raw"),)
    else:
        input_value = tuple(dummy_factory(f"raw_{i}") for i in range(input_len))
        check_value = input_value

    real = FieldConverter.convert_field(input_value)
    assert real is dummy_factory("return")

    field_types_mock.assert_called_once_with()

    for i in range(before_count):
        field_types[i].convert.assert_called_once_with(*check_value)
    field_types[before_count].convert.assert_called_once_with(*check_value)
    for i in range(after_count):
        field_types[before_count + 1 + i].convert.assert_not_called()


def test_convert_aliased_field(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
) -> None:
    field_mock = MarshalField()
    convert_field_mock = mock_stack.enter_mock(
        FieldConverter, "convert_field", return_value=field_mock
    )

    real = FieldConverter.convert_aliased_field(
        dummy_factory("raw_field"), dummy_factory("alias")
    )
    assert real is field_mock
    assert real.alias is dummy_factory("alias")

    convert_field_mock.assert_called_once_with(dummy_factory("raw_field"))


@pytest.mark.parametrize("normal_count", [0, 1, 2])
@pytest.mark.parametrize("aliased_count", [0, 1, 2])
def test_convert_multiple_fields(
    dummy_factory: DummyFactory,
    mock_stack: MockStack,
    normal_count: int,
    aliased_count: int,
) -> None:
    convert_field_mock = mock_stack.enter_mock(
        FieldConverter, "convert_field", return_value=dummy_factory("field")
    )
    convert_aliased_field_mock = mock_stack.enter_mock(
        FieldConverter, "convert_aliased_field", return_value=dummy_factory("field")
    )

    real = list(
        FieldConverter.convert_fields(
            *(dummy_factory(f"normal_{i}") for i in range(normal_count)),
            **{str(i): dummy_factory(f"aliased_{i}") for i in range(aliased_count)},
        )
    )

    assert len(real) == normal_count + aliased_count

    assert convert_field_mock.call_count == normal_count
    convert_field_mock.assert_has_calls(
        [call(dummy_factory(f"normal_{i}")) for i in range(normal_count)]
    )
    assert convert_aliased_field_mock.call_count == aliased_count
    convert_aliased_field_mock.assert_has_calls(
        [call(dummy_factory(f"aliased_{i}"), str(i)) for i in range(aliased_count)]
    )
