from collections.abc import Callable
from typing import Final

from mypy.mro import calculate_mro
from mypy.nodes import (
    GDEF,
    Block,
    ClassDef,
    MypyFile,
    SymbolTable,
    SymbolTableNode,
    TypeInfo,
)
from mypy.plugin import DynamicClassDefContext, Plugin

# TODO redo and generalize
base_model_qualname: Final = "pydantic_marshals.sqlalchemy.models.MappedModel"
type_matrix = {base_model_qualname}
methods = {"extend", "create"}

pydantic_base_model_qualname: Final = "pydantic_marshals.base.models.MarshalBaseModel"
stub_module_name: Final = "pydantic_marshals.mypy.magic"
stub_class_name: Final = f"{stub_module_name}.MappedModelStub"


class MarshalsPlugin(Plugin):
    def get_dynamic_class_hook(
        self,
        fullname: str,
    ) -> Callable[[DynamicClassDefContext], None] | None:
        class_fullname, method_name = fullname.rpartition(".")[::2]
        if (
            fullname == base_model_qualname
            or class_fullname in type_matrix
            and method_name in methods
        ):
            return add_info_hook
        return None

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        return [(10, stub_module_name, -1)]


def add_info_hook(ctx: DynamicClassDefContext) -> None:
    class_def = ClassDef(ctx.name, Block([]))
    class_def.fullname = ctx.api.qualified_name(ctx.name)
    info = TypeInfo(SymbolTable(), class_def, ctx.api.cur_mod_id)
    class_def.info = info
    bm = ctx.api.named_type(pydantic_base_model_qualname)
    pm = ctx.api.named_type(stub_class_name)
    info.bases = [bm, pm]
    calculate_mro(info)

    ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))
    type_matrix.add(class_def.fullname)


def plugin(_: str) -> type[Plugin]:
    return MarshalsPlugin
