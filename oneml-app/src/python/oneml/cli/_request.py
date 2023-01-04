from dataclasses import dataclass
from typing import Dict, Mapping, Optional, Tuple


class CliEnv:
    _values: Dict[str, str]

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = {k: v for k, v in values.items()}

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self._values.get(name, default)

    def as_dict(self) -> Dict[str, str]:
        return self._values.copy()

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __repr__(self) -> str:
        return repr(self._values)


class CliArgs(Tuple[str, ...]):
    pass


@dataclass(frozen=True)
class CliRequest:
    entrypoint: str
    args: CliArgs
    env: CliEnv

    @property
    def entrypoint_basename(self) -> str:
        return self.entrypoint.split("/")[-1]


def clean_env(env: Mapping[str, str]) -> Mapping[str, str]:
    cleaned = {}
    allow_list = [
        "PATH",
        "USERNAME",
        "PWD",
        "SHELL",
        "USER",
        "HOME",
        "PYENV_VIRTUALENV_INIT",
        "IMMUNODATA_USER_EMAIL",
        "VIRTUAL_ENV",
        "PYTHONDONTWRITEBYTECODE",
        "POETRY_ACTIVE",
        "ONEML_REMOTE_INSTANCE",
        "IMMUNODATA_PARENT_PUUID",
        "IMMUNODATA_PUUID",
    ]
    for k, v in env.items():
        if k in allow_list:
            cleaned[k] = v

    return cleaned


def build_cli_request(
    entrypoint: str, args: Tuple[str, ...], env: Mapping[str, str]
) -> CliRequest:
    return CliRequest(
        entrypoint=entrypoint,
        args=CliArgs(tuple(args)),
        env=CliEnv(env),
    )
