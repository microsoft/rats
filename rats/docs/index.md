---
title: about
---
# rats
The `rats` package is used as a meta-package that helps install the more specific `rats-*` packages
with the guarantee of all the versions matching. Each specific package is defined as an extra when
installing `rats`, like `rats[apps]` and `rats[devtools]`.

!!! warning
    this package is not yet being published to pypi, so you must install the individual
    packages for now.
