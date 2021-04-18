import os
import sys


def main():
    from core.management import execute_from_command_line

    os.environ.setdefault("APP_SETTINGS_MODULE", "settings")
    os.environ.setdefault("PYTHONPATH", os.path.basename(__file__))
    return execute_from_command_line(sys.argv)


if __name__ == "__main__":
    exit_code = main()
    os._exit(exit_code)
