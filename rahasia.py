import os
from typing import cast
from dataclasses import dataclass
from infisical_sdk import InfisicalSDKClient  # type: ignore[reportMissingTypeStubs]

try:
    from rahasia_buildinfo import (  # type: ignore[import-not-found]
        env_host,  # type: ignore[reportUnknownVariableType]
        env_project_id,  # type: ignore[reportUnknownVariableType]
        env_client_id,  # type: ignore[reportUnknownVariableType]
        env_client_secret,  # type: ignore[reportUnknownVariableType]
    )
except ImportError:
    # fallback ke lokal development
    from dotenv import load_dotenv

    load_dotenv()
    env_mode = os.getenv("ENV_MODE")
    env_host = os.getenv("ENV_HOST")
    env_project_id = os.getenv("ENV_PROJECT_ID")
    env_client_id = os.getenv("ENV_CLIENT_ID")
    env_client_secret = os.getenv("ENV_CLIENT_SECRET")


@dataclass
class ParamRahasia:
    url: str
    id_perusahaan: list[int]


class Rahasia:
    def __init__(self):
        try:
            klien_env = InfisicalSDKClient(cast(str, env_host))
            klien_env.auth.universal_auth.login(
                cast(str, env_client_id), cast(str, env_client_secret)
            )
            list_rahasia = klien_env.secrets.list_secrets(
                project_id=cast(str, env_project_id),
                environment_slug="dev" if env_mode == "dev" else "prod",
                secret_path="/",
                expand_secret_references=True,
            ).secrets

            if list_rahasia:
                for rahasia in list_rahasia:
                    os.environ[rahasia.secretKey] = rahasia.secretValue

            self.param = ParamRahasia(
                url=cast(str, os.getenv("URL")),
                id_perusahaan=[
                    int(x) for x in cast(str, os.getenv("ID_PERUSAHAAN")).split(",")
                ],
            )
        except Exception as e:
            raise RuntimeError(f"Gagal memuat rahasia: {e}")
