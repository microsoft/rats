#
# class ExecutionContextClient:
#     def request_context(self, request: CliRequest) -> Generator[None, None, None]:
#         raise NotImplementedError()
#
#
# class CliClient:
#
#     _execution_context_client: ExecutionContextClient
#
#     def execute(self, request: CliRequest) -> None:
#         with self._execution_context_client.request_context(request):
#             pass
#
#
# class SubRequestFactory:
#
#     _original: CliRequest
#
#     def get_instance(self, entrypoint: str, args: Tuple[str, ...]) -> CliRequest:
#         return CliRequest(
#             entrypoint=entrypoint,
#             args=CliArgs(args),
#             env=self._original.env,
#         )
#
#
# class DemoApp:
#
#     _cli_client: CliClient
#     _request_factory: SubRequestFactory
#
#     def execute(self) -> None:
#         req = self._request_factory.get_instance("demo1", ())
#         self._cli_client.execute(req)
