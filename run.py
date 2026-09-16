from app.app import run
from app.setup import setup, shutdown_mcp_server


def main():
    try:
        setup()
    except Exception:
        shutdown_mcp_server()
        raise
    run()


if __name__ == "__main__":
    main()