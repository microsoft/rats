from rats import apps


class PipelineContainer(apps.AnnotatedContainer):
    """Specialized container for defining pipelines.

    Currently does nothing beyond being an AnnotationContainer, but we might want to add some
    pipeline specific functionality in the future.  Possibly, we'll change the way the
    implementations of the pipeline specific decorators work and we'll need to add functionality to
    this class to support this.
    """

    pass
