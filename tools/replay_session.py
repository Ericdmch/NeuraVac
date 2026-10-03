import sys

from neuravac_core.cli import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "replay", *sys.argv[1:]]
    main()
