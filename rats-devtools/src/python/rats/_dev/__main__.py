"""rats-devtools provides tooling for building commands that help us develop the rats libraries."""

from rats import devtools

if __name__ == "__main__":
    devtools.run(
        "rats.local.plugins",
    )
