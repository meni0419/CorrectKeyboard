from config import ENV_PATH


def read_env(key, default=None, cast=str, env_path=ENV_PATH):
    try:
        with open(env_path, "r") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#"):  # Skip comments and empty lines
                    continue
                env_key, value = line.split("=", 1)  # Split on the first '='
                if env_key.strip() == key:  # Find the key
                    value = value.strip(' "\'')  # Clean quotes
                    # Apply the cast function if provided (e.g., bool, int)
                    return cast(value)
    except FileNotFoundError:
        pass  # If .env is not found, just return the default
    return default
