#!/usr/bin/env python3
from hera.task import Task
from hera.workflow import Workflow
from hera.workflow_service import WorkflowService


def say(message: str):
    print(message)

TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkZfRU9TM185Q1c3RlBzX09zWmFUR0FvN2hBcVdhRldKd29oUVZmM2QzN1kifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tejc0cmgiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImUxNGRlY2I1LWYwNjktNDIwMS1hNWRhLTYwZTQ4NGQyMjMwZiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.yP7w_-APVI11s93y-mH8NSJPcjEviR70LFEE766o2yzAYQCiQE9F7O540d6U06b8y0NbhDyQ4E1ILwhD6ULr0kjCx812VDPA_EEdZ2u4JFF8ugXcnawO7gxXku9myyaFk8BoGRJS-jCETX60Jztts3HGhwdQ2cdByaiJ2qqycdLOTD_9vPf5kZj1TjDcfxMCydoxSXD1CcDcVCE_QUoMH5yeuw5syyGIN5AxUt1Ezal0FjKz1CEcVbLWmPCwp9BcJRWmlTBzgQu4QWdg-w-3if6rn2uf_f7qJjvFC5RXTCkDUi8CKJ8XxTbSpqXqxmJqbfBW8OJyTA7J4CNQDIGWYA"

NAMESPACE = "argo"


ws = WorkflowService(host="http://localhost:2746", token=TOKEN, namespace=NAMESPACE)
w = Workflow("diamond", ws)
a = Task("A", say, [{"message": "This is task A!"}])
b = Task("B", say, [{"message": "This is task B!"}])
c = Task("C", say, [{"message": "This is task C!"}])
d = Task("D", say, [{"message": "This is task D!"}])

a.next(b).next(d)  # a >> b >> d
a.next(c).next(d)  # a >> c >> d

w.add_tasks(a, b, c, d)
w.create(namespace=NAMESPACE)
