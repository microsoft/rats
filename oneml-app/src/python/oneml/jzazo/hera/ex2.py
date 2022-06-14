#!/usr/bin/env python3
import uuid

from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService

from oneml.jzazo.hera.constants import NAMESPACE, TOKEN


def say(message: str) -> None:
    print(message)


ws = WorkflowService(host="http://localhost:2746", token=TOKEN, namespace=NAMESPACE)
w = Workflow("example2_" + str(uuid.uuid4()).split("-")[1], ws)
a = Task("stz_train", say, [{"message": "Standardization Train."}])
b = Task("stz_train_predict", say, [{"message": "Standardized Train Predictions."}])
c = Task("lr_train", say, [{"message": "Logistic Regression Train."}])
d = Task("lr_train_predictions", say, [{"message": "Logistic Regression Train Predictions."}])

a >> b >> c >> d

w.add_tasks(a, b, c, d)
w.create(namespace=NAMESPACE)
