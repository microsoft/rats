# class RatsPycharmCommands(devtools.ClickCommandRegistry):
#     @devtools.command
#     @click.argument("filename", type=click.Path(exists=True, file_okay=True, dir_okay=False))
#     def pycharm_actions_on_save(self, filename: str) -> None:
#         """Build the python wheel for one of the components in this project."""
#         component_path = Path(filename.split("/")[0])
#         relative_file = "/".join(filename.split("/")[1:])
#         pyproject_path = Path(f"{component_path}/pyproject.toml")
#
#         if not pyproject_path.is_file():
#             raise ValueError("does not seem to be running within repo root")
#
#         poetry_commands = [
#             ["ruff", "check", "--fix", "--unsafe-fixes", str(relative_file)],
#             ["ruff", "format", str(relative_file)],
#         ]
#
#         try:
#             for cmd in poetry_commands:
#                 subprocess.run(
#                     ["poetry", "run", *cmd],
#                     check=True,
#                     cwd=component_path,
#                 )
#         except subprocess.CalledProcessError:
#             # We exit successfully so pycharm doesn't auto-disable our hook :(
#             sys.exit(0)
#
#     @devtools.command
#     def ping(self) -> None:
#         """No-op used for testing."""
#         print("pong")
