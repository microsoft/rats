from abc import ABC
from functools import partial
from typing import Any, Dict, Generic, List, Type

from .step import Output


class Storage:
    def load(self, inputs: List[str]) -> Dict[str, Any]:
        pass

    def save(self, vars: Output) -> None:
        pass


class ILogger:
    def log(self, name: str, var: Any) -> None:
        pass


class Processor(ABC):

    _loggers: List[ILogger] = []

    def __init__(self) -> None:
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    def process(self, *args: Any, **kwargs: Any) -> Output:
        pass

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return super().__call__(*args, **kwds)

    def log(self, name: str, var: Any) -> None:
        for logger in self.loggers:
            logger.log(name, var)

    def log_dict(self, var_dict: Dict[str, Any]) -> None:
        for key, value in var_dict.items():
            for logger in self.loggers:
                logger.log(key, value)

    @property
    def loggers(self) -> List[ILogger]:
        return self._loggers


class Transformer(Processor):
    pass


class ProcessorProvider(Generic[Processor]):
    def __init__(self, type: Type[Processor], **params: Any) -> None:
        super().__init__()
        self._partial = partial(type, **params)

    def __call__(self, **kwargs: Any) -> Processor:
        return self.partial(**kwargs)

    @property
    def partial(self) -> partial[Processor]:
        return self._partial


class TransformerProvider(ProcessorProvider[Transformer]):
    pass


class Estimator(Processor):
    _transformer_provider: TransformerProvider

    def get_transformer(self, **kwargs: Any) -> Transformer:
        return self.transformer_provider(**kwargs)

    @property
    def transformer_provider(self) -> TransformerProvider:
        return self._transformer_provider

    # provider without arguments?
    # returns object -> need to dill
    # returns config -> needs to instantiate
    # placeholder in graph? whose responsibility?
