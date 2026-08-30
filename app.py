"""Sentinel-SRM launcher - fresh project per UPDATED_SIH26142_FULL_v2.md:10"""
from core.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config["SENTINEL_SETTINGS"].host,
        port=app.config["SENTINEL_SETTINGS"].port,
        debug=app.config["SENTINEL_SETTINGS"].debug,
    )
