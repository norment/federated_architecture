import os
from pathlib import Path
os.environ["REGENIE_TSD_CONFIG"] = "/home/zrahman/nvflare/tsd1/test2/tsd_wrapper_config.yml"
from tre_wrappers.tsd import TSDSettings, _fetch_hpc_token
settings = TSDSettings.from_config(
    config_path=Path(os.environ["REGENIE_TSD_CONFIG"]),
    env_prefix="REGENIE_TSD_",
)
token = _fetch_hpc_token(settings)
print(f"Token cached at: {settings.hpc_token_path}")
