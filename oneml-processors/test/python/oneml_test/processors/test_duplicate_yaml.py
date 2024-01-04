from pathlib import Path

from hydra import compose, initialize_config_dir
from hydra_zen import instantiate

from oneml.processors.ux import CombinedPipeline

CONF_PATH = Path("src/resources/pipelines")


def test_three_diamond_config(register_resolvers_and_configs: None) -> None:
    with initialize_config_dir(
        config_dir=str(CONF_PATH.absolute()), job_name="test", version_base=None
    ):
        cfg = compose(
            config_name="pipeline_config", overrides=["+combined@pipeline=three_diamonds"]
        )
        p = instantiate(cfg.pipeline)
        assert isinstance(p, CombinedPipeline)
