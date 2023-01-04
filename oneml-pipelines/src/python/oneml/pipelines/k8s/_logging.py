import logging
import threading

from kubernetes.client import CoreV1Api, V1Pod
from kubernetes.watch import watch
from urllib3.exceptions import ReadTimeoutError

logger = logging.getLogger(__name__)


class LogTailerThread(threading.Thread):
    _should_terminate: threading.Event

    _pod: V1Pod  # type: ignore
    _core_api: CoreV1Api  # type: ignore

    def __init__(self, pod: V1Pod, core_api: CoreV1Api):  # type: ignore
        super().__init__()
        self._should_terminate = threading.Event()
        self._pod = pod
        self._core_api = core_api

    def run(self) -> None:
        while not self._should_terminate.is_set():
            try:
                w = watch.Watch()
                logs = w.stream(
                    self._core_api.read_namespaced_pod_log,
                    name=self._pod.metadata.name,
                    namespace=self._pod.metadata.namespace,
                    _request_timeout=60,  # timeout after 60 seconds of no response
                    since_seconds=60,  # only get the latest 60 seconds of logs
                )

                for line in logs:
                    if self._should_terminate.is_set():
                        logger.info("stopping log tailer")
                        return
                    # TODO: this is probably not the best way to handle multi-process logs
                    # We print here to let the remote process handle formatting logs
                    print(line)
                logger.info("pod logs completed")
                return
            except ReadTimeoutError:
                logger.warning("Timed out fetching pod logs. Attempting to resume tailing logs…")
            except Exception as e:
                logger.error(f"Exceptions when reading logs: {str(e)}")

    def terminate(self) -> None:
        logger.info("log tailing requested to terminate")
        self._should_terminate.set()
