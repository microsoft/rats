#!/usr/bin/env python3
import uuid

from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService

from oneml.jzazo.hera.constants import NAMESPACE, TOKEN


def say(message: str) -> None:
    print(message)


ws = WorkflowService(host="http://localhost:2746", token=TOKEN, namespace=NAMESPACE)
w = Workflow("example3_" + str(uuid.uuid4()).split("-")[1], ws)
a = Task("stz_train", say, [{"message": "Standardization Train."}])
b = Task("stz_train_predict", say, [{"message": "Standardized Train Predictions."}])
c = Task("lr_train", say, [{"message": "Logistic Regression Train."}])
d = Task("lr_train_predictions", say, [{"message": "Logistic Regression Train Predictions."}])
e = Task("stz_eval_predictions", say, [{"message": "Standardization Eval Predictions."}])
f = Task("lr_eval_predictions", say, [{"message": "Logistic Regression Eval Predictions."}])

a >> b >> c >> d
a >> e >> f
c >> f

w.add_tasks(a, b, c, d, e, f)
w.create(namespace=NAMESPACE)
