from functools import partial

from optuna.samplers import GridSampler

from oneml.jzazo.hpo import CategoricalDistribution, Objective, OptunaStep, SearchSpace
from oneml.lorenzo.pipelines import InMemoryStorage, TypeNamespaceClient
from oneml.lorenzo.pipelines._example_oneml._pipeline import StandardizedLogisticRegressionPipeline


def _test() -> None:
    storage = InMemoryStorage()
    namespace_client = TypeNamespaceClient()
    batch_size = CategoricalDistribution(params={"choices": [32, 64]})
    learning_rate = CategoricalDistribution(params={"choices": [1e-2, 1e-3]})
    search_space = SearchSpace({"batch_size": batch_size, "learning_rate": learning_rate})
    algorithm = GridSampler(
        search_space={
            "batch_size": batch_size.params["choices"],
            "learning_rate": learning_rate.params["choices"],
        },
    )
    pipeline_factory = partial(
        StandardizedLogisticRegressionPipeline, namespace_client=namespace_client
    )
    objective = Objective(
        pipeline_factory=pipeline_factory,
        metric=["foo"],
        storage=storage,
        namespace_client=namespace_client,
    )
    num_trials = 4

    pipeline = OptunaStep(
        num_trials=num_trials,
        search_space=search_space,
        algorithm=algorithm,
        objective=objective,
        storage=storage,
    )
    pipeline.execute()

    for k, v in storage._data.items():
        print(k)


if __name__ == "__main__":
    _test()
