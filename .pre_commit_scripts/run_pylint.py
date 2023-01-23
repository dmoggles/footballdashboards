import subprocess
import sys
import os


def main():
    """
    Run pylint with the same arguments as the pre-commit hook.


    """
    if sys.platform == "win32":
        cmd = (
            os.path.join(os.path.dirname(__file__), "..", "env", "Scripts", "pylint.exe"),
            *sys.argv[1:],
        )
        print(f"Running {' '.join(cmd)}")

    else:
        cmd = (os.path.join(os.path.dirname(__file__), "..", "env", "bin", "pylint"), *sys.argv[1:])
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
