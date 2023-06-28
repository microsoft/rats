from abc import abstractmethod
from collections import ChainMap
from typing import Protocol, TypedDict

from ..io import IReadFromUrlPipelineBuilder, IWriteToNodeBasedUriPipelineBuilder
from ..ux import Pipeline, PipelineBuilder
from ._train_and_eval import TrainAndEvalBuilders


class IPersistFittedEvalPipeline(Protocol):
    @abstractmethod
    def with_persistance(
        self,
        train_and_eval_pl: Pipeline,
    ) -> Pipeline:
        ...


class PersistFittedEvalPipeline(IPersistFittedEvalPipeline):
    _read_pb: IReadFromUrlPipelineBuilder
    _write_pb: IWriteToNodeBasedUriPipelineBuilder

    def __init__(
        self,
        read_pb: IReadFromUrlPipelineBuilder,
        write_pb: IWriteToNodeBasedUriPipelineBuilder,
    ) -> None:
        self._read_pb = read_pb
        self._write_pb = write_pb

    def _get_types_of_fitted_params(self, train_pl: Pipeline) -> dict[str, type]:
        return {
            fitted_name: tuple(entry)[0].param.annotation
            for fitted_name, entry in train_pl.out_collections.fitted.items()
        }

    def _get_write_fitted_pl(
        self,
        fitted_to_types: dict[str, type],
    ) -> Pipeline:
        write_fitted_pl = PipelineBuilder.combine(
            name="write_fitted",
            pipelines=[
                (
                    self._write_pb.build(data_type=param_type, node_name=fitted_name)
                    .rename_inputs({"data": f"fitted.{fitted_name}"})
                    .rename_outputs({"uri": f"uris.{fitted_name}"})
                )
                for fitted_name, param_type in fitted_to_types.items()
            ],
        )
        return write_fitted_pl

    def _get_read_fitted_pl(
        self,
        fitted_to_types: dict[str, type],
    ) -> Pipeline:
        read_fitted_pl = PipelineBuilder.combine(
            name="read_fitted",
            pipelines=[
                (
                    self._read_pb.build(data_type=param_type)
                    .decorate(fitted_name)
                    .rename_inputs({"uri": f"uris.{fitted_name}"})
                    .rename_outputs({"data": f"fitted.{fitted_name}"})
                )
                for fitted_name, param_type in fitted_to_types.items()
            ],
        )
        return read_fitted_pl

    def _get_eval_using_persistance_pl(
        self, read_fitted_pl: Pipeline, eval_pl: Pipeline
    ) -> Pipeline:
        p = PipelineBuilder.combine(
            name="eval_using_persistance",
            pipelines=[read_fitted_pl, eval_pl],
            dependencies=(read_fitted_pl.out_collections.fitted >> eval_pl.in_collections.fitted,),
        )
        return p

    def _get_create_fitted_eval_pipeline_pl(
        self, fitted_to_types: dict[str, type], eval_pl: Pipeline
    ) -> Pipeline:
        read_fitted_pl = self._get_read_fitted_pl(fitted_to_types)
        eval_using_persistance_pl = self._get_eval_using_persistance_pl(read_fitted_pl, eval_pl)
        create_fitted_eval_pipeline = PipelineBuilder.task(
            name="create_fitted_eval_pipeline",
            processor_type=CreateFittedEvalPipelineProcessor,
            config=dict(
                eval_using_persistance_pl=eval_using_persistance_pl,
            ),
            input_annotation={
                fitted_name: str for fitted_name in read_fitted_pl.in_collections.uris
            },
        ).rename_inputs(
            {
                fitted_name: f"uris.{fitted_name}"
                for fitted_name in read_fitted_pl.in_collections.uris
            }
        )
        return create_fitted_eval_pipeline

    def _get_write_fitted_eval_pipeline_pl(self) -> Pipeline:
        return (
            self._write_pb.build(data_type=Pipeline, node_name="fitted_eval_pipeline")
            .rename_inputs({"data": "fitted_eval_pipeline"})
            .rename_outputs({"uri": "uris.fitted_eval_pipeline"})
        )

    def with_persistance(
        self,
        train_and_eval_pl: Pipeline,
    ) -> Pipeline:
        train_pl, eval_pl = TrainAndEvalBuilders.split_pipeline(train_and_eval_pl)
        fitted_to_types = self._get_types_of_fitted_params(train_pl)
        write_fitted_pl = self._get_write_fitted_pl(fitted_to_types)
        create_fitted_eval_pipeline_pl = self._get_create_fitted_eval_pipeline_pl(
            fitted_to_types, eval_pl
        )
        write_fitted_eval_pipeline_pl = self._get_write_fitted_eval_pipeline_pl()
        p = PipelineBuilder.combine(
            name=train_and_eval_pl.name,
            pipelines=[
                train_pl,
                eval_pl,
                write_fitted_pl,
                create_fitted_eval_pipeline_pl,
                write_fitted_eval_pipeline_pl,
            ],
            dependencies=(
                train_pl.out_collections.fitted >> eval_pl.in_collections.fitted,
                train_pl.out_collections.fitted >> write_fitted_pl.in_collections.fitted,
                write_fitted_pl.out_collections.uris
                >> create_fitted_eval_pipeline_pl.in_collections.uris,
                create_fitted_eval_pipeline_pl.outputs.fitted_eval_pipeline
                >> write_fitted_eval_pipeline_pl.inputs.fitted_eval_pipeline,
            ),
            outputs=ChainMap(
                dict(train_pl.outputs),
                dict(eval_pl.outputs),
                dict(create_fitted_eval_pipeline_pl.outputs),
                {
                    f"{col}.{entry}": train_pl.out_collections[col][entry]
                    for col in train_pl.out_collections
                    if col != "fitted"
                    for entry in train_pl.out_collections[col]
                },
                {
                    f"{col}.{entry}": eval_pl.out_collections[col][entry]
                    for col in eval_pl.out_collections
                    for entry in eval_pl.out_collections[col]
                },
                {
                    f"uris.{entry_name}": write_fitted_pl.out_collections.uris[entry_name]
                    for entry_name in write_fitted_pl.out_collections.uris
                },
                {
                    "uris.fitted_eval_pipeline": (
                        write_fitted_eval_pipeline_pl.out_collections.uris.fitted_eval_pipeline
                    )
                },
            ),
        )
        return p


ProvideFixedUriProcessorOutputs = TypedDict("ProvideFixedUriProcessorOutputs", {"uri": str})


class ProvideFixedUriProcessor:
    _uri: str

    def __init__(self, uri: str) -> None:
        self._uri = uri

    def process(self) -> ProvideFixedUriProcessorOutputs:
        return ProvideFixedUriProcessorOutputs(uri=self._uri)


CreateFittedEvalPipelineProcessorOutputs = TypedDict(
    "CreateFittedEvalPipelineProcessorOutputs", {"fitted_eval_pipeline": Pipeline}
)


class CreateFittedEvalPipelineProcessor:
    """A processor that attached LoadPersisted nodes to an eval pipeline."""

    _eval_using_persistance_pl: Pipeline

    def __init__(
        self,
        eval_using_persistance_pl: Pipeline,
    ):
        self._eval_using_persistance_pl = eval_using_persistance_pl

    def process(self, **uris: str) -> CreateFittedEvalPipelineProcessorOutputs:
        if frozenset(uris) != frozenset(self._eval_using_persistance_pl.in_collections.uris):
            missing = frozenset(self._eval_using_persistance_pl.in_collections.uris) - frozenset(
                uris
            )
            spurious = frozenset(uris) - frozenset(
                self._eval_using_persistance_pl.in_collections.uris
            )
            raise ValueError(f"Expected uris to contain {missing} and not contain {spurious}")
        provide_uris_pl = PipelineBuilder.combine(
            name="uris",
            pipelines=[
                PipelineBuilder.task(
                    name=fitted_name,
                    processor_type=ProvideFixedUriProcessor,
                    config=dict(
                        uri=uris[fitted_name],
                    ),
                ).rename_outputs({"uri": f"uris.{fitted_name}"})
                for fitted_name in uris
            ],
        )
        fitted_eval_pl = PipelineBuilder.combine(
            name="fitted_eval",
            pipelines=[provide_uris_pl, self._eval_using_persistance_pl],
            dependencies=(
                provide_uris_pl.out_collections.uris
                >> self._eval_using_persistance_pl.in_collections.uris,
            ),
        )
        return CreateFittedEvalPipelineProcessorOutputs(fitted_eval_pipeline=fitted_eval_pl)
