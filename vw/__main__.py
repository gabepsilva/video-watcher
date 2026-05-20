"""python -m vw entrypoint."""

import sys

print("video-watcher: starting …", file=sys.stderr, flush=True)

from vw.cli import main

raise SystemExit(main())
