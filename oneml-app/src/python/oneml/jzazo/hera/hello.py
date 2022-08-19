#!/usr/bin/env python3
# # flake8: noqa
from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService

from .constants import NAMESPACE, TOKEN


def say(message: str) -> None:
    """
    This can be anything as long as the Docker image satisfies the dependencies.
    You can import anything Python that is in your container e.g torch, tensorflow, scipy,
    biopython, etc - just provide an image to the task!
    """
    print(message)


ws = WorkflowService(host="http://localhost:2746", token=TOKEN, namespace=NAMESPACE)
w = Workflow("my-workflow2", ws)
t = Task("say", say, [{"message": "Hello, world!"}])
t2 = Task("say", say, [{"message": "Hello, world2!"}])
w.add_task(t)
w.add_task(t2)
w.create(namespace=NAMESPACE)
