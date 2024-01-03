# Plugins
Protocols that can be implemented to attach behaviors and capabilities to OneML pipelines. For
example, `AppPlugin` objects are loaded as part of the creation of the main `App` object, and
are able to register new services and provide additional functionality to the user. More
specific interfaces like `OnemlIoPlugin` can be used to give plugin authors a more direct path
to enhancing a specific portion of the system. Implementing `OnemlIoPlugin` allows authors to
respond to node completion events in order to perform custom IO operations.
