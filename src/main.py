import sys
from src.app import create_app


def main():
    # type: () -> None
    app, window = create_app()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
