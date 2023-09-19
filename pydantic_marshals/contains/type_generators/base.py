from typing import Annotated, Any

from pydantic import AfterValidator

from pydantic_marshals.base.type_aliases import TypeHint


class BaseTypeGenerator:
    """
    Helper interface to make creating custom types for pydantic easier
    Subclasses must override :py:attr:`data_type` and :py:meth:`_validate`

    See also: https://docs.pydantic.dev/2.0/usage/types/custom
    """

    data_type: TypeHint

    def _validate(self, data: Any) -> None:
        """
        Method to validate `data`. Should throw errors on fails, same as validators in
        pydantic: https://docs.pydantic.dev/2.0/usage/validators/
        """
        raise NotImplementedError

    def validate(self, data: Any) -> Any | None:
        self._validate(data)
        return data

    def to_typehint(self) -> TypeHint:
        """
        Converts type generator into a type hint, usable as a custom type with pydantic
        https://docs.pydantic.dev/2.0/usage/types/custom
        """
        return Annotated[self.data_type, AfterValidator(self.validate)]
