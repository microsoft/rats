from collections.abc import Mapping
from typing import TypedDict

import hydra
import pytest
from hydra_zen import instantiate
from omegaconf import OmegaConf

from rats.processors._legacy.ux import (
    CombinedConf,
    CombinedPipeline,
    EntryDependencyOpConf,
    PipelinePortConf,
    Task,
    TaskConf,
)


class IdentityArrays:
    def process(self, **floats: float) -> Mapping[str, float]:
        return floats


def test_task_conf(register_resolvers_and_configs: None) -> None:
    # tests instantiating a processor with no other arguments
    processor_type = "rats_test.processors._legacy.test_ux_estimators.StandardizeTrain"
    cfg = OmegaConf.structured(TaskConf(processor_type=processor_type))
    task = instantiate(cfg)
    assert isinstance(task, Task)
    assert len(task._dag) == 1

    # tests that the input and return annotations are processed if given
    processor_type = "rats_test.processors._legacy.test_schema.IdentityArrays"
    input_annotation = {"floats": "float"}
    return_annotation = {"one": "float"}
    task = instantiate(
        TaskConf(
            processor_type=processor_type,
            input_annotation=input_annotation,
            return_annotation=return_annotation,
        )
    )
    assert isinstance(task, Task)
    assert len(task._dag) == 1

    # tests that instantiating a class with no var keyword argument fails if given input_annotation
    processor_type = "rats_test.processors._legacy.test_ux_arrays.SumArrays"
    input_annotation = {"floats": "float"}
    with pytest.raises(hydra.errors.InstantiationException):  # pyright: ignore
        # ValueError('`input_annotation` provided; processor does not have keyword vars.')
        instantiate(TaskConf(processor_type=processor_type, input_annotation=input_annotation))


class AOutput(TypedDict):
    z: int


class A:
    def process(self) -> AOutput:
        return {"z": 1}


class B:
    def process(self, x: int) -> None:
        pass


def test_combined_conf(register_resolvers_and_configs: None) -> None:
    Acfg = TaskConf(processor_type="rats_test.processors._legacy.test_schema.A")
    Bcfg = TaskConf(processor_type="rats_test.processors._legacy.test_schema.B")
    Ccfg = CombinedConf(pipelines={"A": Acfg, "B": Bcfg}, name="combined")
    cfg = OmegaConf.create({"C": Ccfg})
    combined = instantiate(cfg.C)
    assert isinstance(combined, CombinedPipeline)
    assert len(combined._dag) == 2

    dp = EntryDependencyOpConf(
        in_entry=PipelinePortConf(pipeline="pipelines.B", port="inputs.x"),
        out_entry=PipelinePortConf(pipeline="pipelines.A", port="outputs.z"),
    )
    Ccfg = CombinedConf(pipelines={"A": Acfg, "B": Bcfg}, name="combined", dependencies={"d0": dp})
    cfg = OmegaConf.create({"C": Ccfg})
    combined = instantiate(cfg.C)
    assert isinstance(combined, CombinedPipeline)
    assert len(combined._dag) == 2
