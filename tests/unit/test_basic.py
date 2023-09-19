from unittest.mock import patch

import pytest

from pydantic_marshals.base.fields.base import MarshalField


@pytest.mark.parametrize("alias", [None, "something"])
def test_base_field_alias(alias: str | None) -> None:
    chosen_type = int
    expected = {}
    if alias is not None:
        expected["alias"] = alias

    with patch.object(MarshalField, "generate_type") as mock_generate_type:
        mock_generate_type.return_value = chosen_type
        field = MarshalField(alias=alias)

        assert dict(field.generate_field_data()) == expected

        annotation, field_info = field.generate_field()
        assert annotation is chosen_type
        assert field_info.alias == alias

        mock_generate_type.assert_called_once_with()
