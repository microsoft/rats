# syntax = docker/dockerfile:1.0-experimental
ARG REGISTRY=immunodata.azurecr.io
FROM ${REGISTRY}/ubuntu-22.04-python-3:2022-10-11.21-01-00

ARG SECRET_DIR_PREFIX=""

ENV PROJECT_NAME="oneml"
ENV APP_NAME="oneml-app"

ENV PROJECT_PATH="/opt/oneml"
ENV APP_PATH="$PROJECT_PATH/$APP_NAME"

RUN mkdir -p $PROJECT_PATH/.tmp
RUN mkdir -p $APP_PATH/.tmp

WORKDIR $APP_PATH

# Copy just the pyproject.toml files required to be able to install local python packages
COPY oneml-devtools/pyproject.toml $PROJECT_PATH/oneml-devtools/pyproject.toml
COPY oneml-habitats/pyproject.toml $PROJECT_PATH/oneml-habitats/pyproject.toml
COPY oneml-pipelines/pyproject.toml $PROJECT_PATH/oneml-pipelines/pyproject.toml
COPY oneml-processors/pyproject.toml $PROJECT_PATH/oneml-processors/pyproject.toml
COPY $APP_NAME/pyproject.toml $APP_PATH/pyproject.toml

# Create src dirs of local packages, the bare minimum needed to install local packages
RUN \
    mkdir -p $PROJECT_PATH/oneml-devtools/src/python/$PROJECT_NAME/devtools && \
    mkdir -p $PROJECT_PATH/oneml-habitats/src/python/$PROJECT_NAME/habitats && \
    mkdir -p $PROJECT_PATH/oneml-pipelines/src/python/$PROJECT_NAME/pipelines && \
    mkdir -p $PROJECT_PATH/oneml-processors/src/python/$PROJECT_NAME/processors && \
    mkdir -p $PROJECT_PATH/$APP_NAME/src/python/$PROJECT_NAME/app && \
    # Poetry, unlike pipenv, needs these to be valid python packages so we stub out empty ones.
    touch $PROJECT_PATH/oneml-devtools/src/python/$PROJECT_NAME/devtools/__init__.py && \
    touch $PROJECT_PATH/oneml-habitats/src/python/$PROJECT_NAME/habitats/__init__.py && \
    touch $PROJECT_PATH/oneml-pipelines/src/python/$PROJECT_NAME/pipelines/__init__.py && \
    touch $PROJECT_PATH/oneml-processors/src/python/$PROJECT_NAME/processors/__init__.py && \
    touch $PROJECT_PATH/$APP_NAME/src/python/$PROJECT_NAME/app/__init__.py

# From the app we just need the poetry.lock
COPY $APP_NAME/poetry.lock $APP_PATH/poetry.lock

# Then install all dependencies
RUN --mount=type=secret,id=build-envs \
    . ${SECRET_DIR_PREFIX}/run/secrets/build-envs \
    && export POETRY_DYNAMIC_VERSIONING_BYPASS=0.0.0 \
    && poetry config virtualenvs.in-project true \
    && poetry run pip install -U pip \
    && poetry install \
    && rm -rf /root/.cache

# Copy in the full contents of local packages (after `poetry install`,
# to not invalidate that slow step when local contents change)
COPY oneml-pipelines $PROJECT_PATH/oneml-pipelines

COPY immunoproject.yaml $PROJECT_PATH/immunoproject.yaml

# Copy in runtime configuration
ARG IMMUNOCLI_HABITAT=msft
COPY .habitats $PROJECT_PATH/.habitats
RUN set -ex \
    && mkdir -p $HOME/.immunocli/habitats \
    && echo ${IMMUNOCLI_HABITAT} >> $HOME/.immunocli/habitats/default-habitat

# Copy in the full contents of the app itself (after `poetry install`,
# to not invalidate that slow step when local contents change)
COPY $APP_NAME $APP_PATH

ENV PATH $APP_PATH/.venv/bin:$PATH
