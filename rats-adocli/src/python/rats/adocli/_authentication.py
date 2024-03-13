import json
import subprocess


class AdoOauthToken:

    def get_token(self) -> str:
        response = subprocess.run(
            ["az", "account", "get-access-token"],
            check=True,
            capture_output=True,
        )

        data = json.loads(response.stdout)
        return data["accessToken"]
