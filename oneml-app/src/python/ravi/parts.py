from abc import abstractmethod
import numpy as np
from munch import Munch
from sklearn.classification import LogisticRegression as SkLearnLR
from typing import Dict, Any

# stubs for type declarations


class In:
    pass


class Out:
    pass


class InOut:
    pass


class Schema:
    pass


class Alias:
    pass


"""
Some initial sketches of parts of the framework around this
- fundamental model is a tree of nested objects - Steps, Data, and values (scalars, lists, etc.)
- these should be  the specific data objects used - pandas, Spark, containers, xarray, ...
- uses a functional pattern, so assign(key=value, ..) returns a copy with modified attributes
  - could automatically nest with key__key__key path

Future ideas
- can be roundtripped into a json-ish description via describe()/create()
- can be roundtripped into persistent storage with save()/load()
"""


class Part:
    """
    - common base class of Data & Step objects
    - captures schema & names from attributes
    - immutable - directly assigning attributes is not allowed, must use 'assign'
      to return a modified copy
    - todo: validation to avoid mutable values
    """

    @property
    def _schema(self) -> Dict[str, Schema]:
        # get all attributes and their schemas
        pass

    def _assign(self, **kwargs: Dict) -> 'Part':
        """return a copy with updated attributes
        can specify nested attribute keys separated by '.', '__', or '/' (only '.' implemented)"""
        # todo: aliasing
        result = self.shallowCopy()
        for k, v in kwargs:
            if '.' in k:
                k0, kn = k.split('.', 1)
                result[k0] = self[k0].assign(kn, v)
            else:
                result[k] = v
        return result

    def __getitem__(self, *keys):
        """get one or more named values"""
        # p[k0] = p.k0
        # p[k0, k1, ...] = (p.k0, p.k1, ...)
        # keys can have '.' or '__' or '/' to delimit nested lookups
        pass


class Step(Part):
    """
    - primitive code execution step
    - running a Step returns a new Step object with outputs assigned
    - `_runner` gets execution context to spawn other Step
    """

    @property
    def _runner(self) -> Runner:
        pass

    @abstractmethod
    def _validate_inputs()
        """validate schema and input values"""
        # autogenerated
        pass

    @abstractmethod
    def _validate_outputs(self) -> None:
        """validate schema and output values"""
        # autogenerated
        pass

    # actual implementation of the processor's algorithm
    # should only be called from Runner(), don't actually call directly
    # get inputs from self.* attributes, return outputs by assigning to result
    # todo: could autogenerate custom Result class with exact output attribute names, type checking
    @abstractmethod
    def _run(self, result: Result) -> None:
        pass


class Result(Munch):
    """
    for now this is just a Munch dict, can add more later
    could be an autogenerated private class with just Out attributes & types
    """
    pass


class SimpleStep(Step):
    """
    simplest step defined like a dataclass
    - parameters, inputs, and outputs declared as typed attributes
    - schema and in/out attributes are learned by introspection
    """
    pass


class Runner:
    """
    context object that runs compute steps
    """

    def run(self, step: Step, **kwargs: Dict[str, Any]) -> Step:
        """schedule and run a step, returning a copy with outputs assigned"""
        # assign additional params/inputs
        # todo: this is 
        step_out = step._assign(**kwargs)
        # validate input types etc.
        step_out._validate_inputs()
        # run computation and gather result values
        result = Result()
        step_out._run(result)
        # assign result values to step object
        step_out = step_out._assign(**result)
        # validate output schemas etc.
        self._validate_outputs(step_out)
        # return updated step object
        return step_out

    def schedule(self, step: Step, **kwargs) -> Step:
        """
        schedules a step to run asynchronously when its inputs and compute resources are available
        immediately returns Step with input and output types T changed to Future[T]
        these can then be used to assign inputs of subsequently scheduled steps without waiting for completion
        """
        pass


class Standardizer(SimpleStep):

    # parameters
    offset: float = 0

    # inputs / outputs
    features: InOut[np.array]

    # output
    fitted: Out[Step]  # trained model

    def _run(self, result: Result) -> None:
        offset = -self.features.mean(axis=0)
        scale = 1. / self.features.std(axis=0)
        f = FittedStandardizer(offset=offset, scale=scale)
        result.fitted = self._runner.run(f, features=self.features)
        result.features = result.fitted.features


class FittedStandardizer(SimpleStep):

    # parameters
    offset: np.array
    scale: np.array

    # inputs / outputs
    features: InOut[np.array]

    def _run(self, result: Result) -> None:
        result.features = self.features * self.scale + self.offset


class LogisticRegression(SimpleStep):

    # inputs
    labels: In[np.array]

    # inputs / outputs
    features: InOut[np.array]

    # outputs
    fitted: Out[Step]  # trained model
    predictions: Out[np.array]

    # output artifacts
    weights: Out[np.array]
    bias: Out[float]

    def _run(self, result: Result) -> None:
        lr = SkLearnLR()
        lr.fit(self.features, self.labels)
        result.weights = lr.weights_
        result.bias = lr.bias_
        f = FittedLogisticRegression(lr=lr)
        result.fitted = self._runner.run(f, features=self.features)
        result.predictions = result.fitted.predictions


class FittedLogisticRegression(SimpleStep):

    # parameters
    lr: SkLearnLR

    # inputs / outputs
    features: InOut[np.array]

    # outputs
    predictions: Out[np.array]

    def _run(self, result: Result) -> None:
        result.predictions = self.lr.transform(self.features)


class StandardizedLogisticRegression(SimpleStep):

    # parameters
    offset: Alias['stz.offset']

    # pseudo-parameters, these would be list of generic steps in generic pipeline
    stz: Standardizer
    lr: LogisticRegression

    # inputs
    labels: In[np.array]

    # inputs/outputs
    features: InOut[np.array]

    # outputs
    fitted: Out[Step]  # trained model
    predictions: Out[np.array]

    def _run(self, result: Result) -> None:
        # import my inputs, run steps, and replace each step with result of run
        result.stz = self.runner.run(self.stz, features=self.features)
        # supply inputs of step from nearest preceding output of same name
        result.lr = self.runner.run(self.lr, features=result.stz.features, labels=self.labels)
        # fitted pipeline has estimators replaced with their fitted outputs
        result.fitted = FittedStandardizedLogisticRegression(stz=result.stz.fitted, lr=result.lr.fitted)
        # export step outputs that were not consumed by later inputs
        result.features = result.lr.features
        result.predictions = result.lr.predictions


class FittedStandardizedLogisticRegression(SimpleStep):

    # pseudo-parameters, these would be list of generic steps in generic pipeline
    stz: FittedStandardizer
    lr: FittedLogisticRegression

    # inputs/outputs
    features: InOut[np.array]

    # outputs
    predictions: Out[np.array]

    def _run(self, result: Result) -> None:
        # import my inputs, run steps, and replace each step with result of run
        result.stz = self.runner.run(self.stz, features=self.features)
        result.lr = self.runner.run(self.lr, features=result.stz.features)
        # export step outputs that were not consumed by later inputs
        result.features = result.stz.features
        result.predictions = result.lr.predictions
