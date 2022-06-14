#!/usr/bin/env python3
import uuid

from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService

from oneml.jzazo.hera.constants import NAMESPACE, TOKEN


def say(message: str) -> None:
    print(message)


ws = WorkflowService(host="http://localhost:2746", token=TOKEN, namespace=NAMESPACE)
w = Workflow("example1_" + str(uuid.uuid4()).split("-")[1], ws)
a = Task("stz_lr", say, [{"message": "Standardized Logistic Regression."}])

w.add_tasks(a)
w.create(namespace=NAMESPACE)
