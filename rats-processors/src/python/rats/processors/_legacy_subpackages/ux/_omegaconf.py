from typing import Any, Literal, cast

from omegaconf import DictConfig, OmegaConf


def is_interpolated_string(x: Any) -> bool:
    # This is only a necessary check -- not a sufficient one -- that `x` is a valid interpolated
    # string. We do not verify that it rigorously satisfies omegaconf's grammar.
    # https://github.com/mit-ll-responsible-ai/hydra-zen/blob/1a27a5e94d4b74e33f386fa77d6b614ff8d9b619/src/hydra_zen/structured_configs/_utils.py#L490
    return isinstance(x, str) and len(x) > 3 and x.startswith("${") and x.endswith("}")


def _parse_strs(level: Literal[0, 1], *keys: str, _parent_: DictConfig) -> None:
    parent = _parent_ if level == 0 else cast(DictConfig, _parent_._get_parent())
    for key in keys:
        if isinstance(parent[key], str) and not is_interpolated_string(parent[key]):
            parent[key] = "${" + parent[key] + "}"


def _parse_portpipeline(*, _parent_: DictConfig) -> None:
    if isinstance(_parent_.pipeline, str) and not is_interpolated_string(_parent_.pipeline):
        _parent_.pipeline = "${...." + _parent_.pipeline + "}"


def _parse_list(attrs: list[str]) -> None:
    for i, attr in enumerate(attrs):
        if isinstance(attr, str) and not is_interpolated_string(attr):
            attrs[i] = "${" + attr + "}"


def _parse_dict(key: str, _parent_: DictConfig) -> None:
    _parent_[key] = {
        k: "${" + v + "}" if isinstance(v, str) and not is_interpolated_string(v) else v
        for k, v in _parent_[key].items()
    }


DPTYPE: dict[str, str] = {
    "in_entry": "rats.processors._legacy_subpackages.ux._ops.EntryDependencyOp",
    "in_collection": "rats.processors._legacy_subpackages.ux._ops.CollectionDependencyOp",
    "in_pipeline": "rats.processors._legacy_subpackages.ux._ops.PipelineDependencyOp",
    "out_entry": "rats.processors._legacy_subpackages.ux._ops.EntryDependencyOp",
    "out_collection": "rats.processors._legacy_subpackages.ux._ops.CollectionDependencyOp",
    "out_pipeline": "rats.processors._legacy_subpackages.ux._ops.PipelineDependencyOp",
}


def _parse_dependencies(dependencies: DictConfig | None) -> None:
    for v in dependencies.values() if dependencies else {}:
        if "_target_" not in v:
            err_msg = "Only the following pairs of (input, output) attributes are recognized: "
            err_msg += "(in_entry, out_entry), (in_collection, out_collection), "
            err_msg += "(in_pipeline, out_pipeline)."
            if len(v) > 2:
                raise ValueError(err_msg)
            base_target = ""
            for attr_k, attr_v in v.items():
                if attr_k not in DPTYPE:
                    raise ValueError(f"Attribute not recognized: {attr_k}.")
                if base_target and base_target != DPTYPE[attr_k]:
                    raise ValueError(err_msg)
                else:
                    base_target = DPTYPE[attr_k]
                v._target_ = base_target
                attr_v._target_ = "rats.processors._legacy_subpackages.ux._ops.get_pipelineport"
                attr_v.pipeline = "${...." + attr_v.pipeline + "}"


def _get_parent_or_processor_name(*, _parent_: DictConfig) -> str:
    return _parent_._key() if _parent_._key() else _parent_.processor_type.split(".")[-1]


def register_resolvers() -> None:
    OmegaConf.register_new_resolver("parse_strs", _parse_strs)
    OmegaConf.register_new_resolver("parse_portpipeline", _parse_portpipeline)
    OmegaConf.register_new_resolver("parse_list", _parse_list)
    OmegaConf.register_new_resolver("parse_dict", _parse_dict)
    OmegaConf.register_new_resolver("parse_dependencies", _parse_dependencies)
    OmegaConf.register_new_resolver("parent_or_processor_name", _get_parent_or_processor_name)
