# Design suggestion: Datasets, Batches, Processors

Author: elonp@microsoft.com

Date: 2022-04-05

## Introduction

Following discussions with javierzazo@microsoft.com, I believe he has pinpointed the source of the extra complexity in immunocam containers (V1.0 and V2.0).  That extra complexity stems from the attempt to incorporate two distinct concepts into the container.

These two concepts are:

* Batches: a *Batch* is a dictionary mapping property names to in-memory objects.  It is a simple data object, with no methods and no automatic properties.
* Datasets: a *Dataset* represents a set of samples, holds information that unqiuely defines it, but does not hold the data in memory.  *Dataset*s provide operations to
    slice themself, and to load the data into a *Batch*.

By decoupling these two functionalities of the current containers, we should be to avoid the need for lazy evaluation, which is responsible for most of the complexity of the container codebase.

The [next section](#data) defines these concepts in more detail.

[Processors](#processors) defines computation steps that operate on them.

## Data

### Batch

A batch is a dictionary mapping property names to property values.  All values should already be in memory.  The types used for values are TBD.  The batch should also provide access to metadata, such as names of dimensions, shape (=sizes of dimesions), dtypes, names of columns.

### Dataset

```python
class Dataset:
    def load() -> Batch:
        """Load the dataset."""

    def select(self, propety_names: List[str]) -> Dataset:
        """Get a view of this dataset narrowed down to the requested properties."""

    def slice(self, dimension_name: str, slice_operation: SliceOperation) -> Dataset:
        """Slices the dataset along a dimension.

        Slice operation TBD.  Should allow:
        1. slicing to a specific set of elements by key (e.g. sample name, bioidentity).
        1. slicing to exclude a specific set of elements by key.
        1. slicing by a providing a salt and a predicate.  A hash of the element key and the salt is passed to the predicate.
        """

    def get_slice_iterable(self, iteration_operation: IterationOperation) -> Iterable[Dataset]:
        """Breaks down `self` into an iteration of datasets.
        
        The returned datasets are non-intersecting and their union is this dataset.

        Iteration operation TBD.  Should allow:
        1. Slicing along a dimension, providing arbitrary slices of roughly requested size.
        1. Slicing along a dimension, using modulu of a hash of the key, defined using salt, N.
        1. Slicing along multiple dimensions.
        """

    def union_with(self, other: Dataset) -> Dataset:
        """Unions this dataset with `other`.

        TBD: dealing with overlaps.
        """

    @classmethod
    def from_batches(cls, Iterable[Batch], slice_dimensions: List[str]) -> Dataset:
        """Creates a dataset from an iterable of batches.

        Assumes:
        1. All batches have the same set of properties.
        1. Batches are distinct allong `slice_dimensions`.
        1. Properties that are not indexed by `slice_dimensions` are repeated in all batches.
        """

    # Metadata accessors:

    def get_dimensions(self) -> List[str]:
        """Get the list of dimension names for this dataset."""

    def get_dimension_size(self, dimension_name: str) -> Optional[int]:
        """Get the number of elements in the dimension.  Might be None if not known."""

    def get_dimension_size_estimate(self, dimension_name: str) -> int:
        """Get an estimation of the number of elements in the dimension."""

    def get_properties(self) -> List[str]:
        """Get the list of names of properties held in this dataset."""

    def get_property_dimensions(self, property_name: str) -> List[str]:
        """Get the list of dimention names for a property of this dataset."""
```

## Processors

Computation steps are defined as processors.

Processors need to declare what inputs they expect and what outputs they provide.  This is done usinga mapping from input/output name to the input/output dimensions.  TBD: declare dtypes and general schema?  A processor may declare that it accepts any dimension name and propagate that dimension name to the output.

Processors also declare what (if any) dimensions they are independent of (here independent means associative and commutative).

Most processors process *Batch*es, i.e. loaded data.

Some process *Datasets*.

### Batch level propcessors

Examples:

```python
class FET(BatchProcessor):
    independent_dimensions: List[str] = ["TCR"]
    input_properties: Dict[str, List[str]] = dict(indicators= ["repertoire", "TCR"])
    output_properties: Dict[str, List[str]] = dict(pvalues= ["TCR"])

    def process() -> None:
        ...
```

```python
class LinearRegression(BatchProcessor):
    independent_dimensions: List[str] = []
    input_properties: Dict[str, List[str]] = dict(features= ["*SAMPLE_DIMENSION*", "*FEATURE_DIMENSION*"], labels= ["*SAMPLE_DIMENSION*"])
    output_properties: Dict[str, List[str]] = dict(model= [])

    def process() -> None:
        ...
```

## Metadata
