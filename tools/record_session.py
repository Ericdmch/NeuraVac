"""Record an application showcase; use rosbag2 script for actual ROS sensor topics."""

import sys

from neuravac_core.cli import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "demo", "--record", "artifacts/session.jsonl", *sys.argv[1:]]
    main()
