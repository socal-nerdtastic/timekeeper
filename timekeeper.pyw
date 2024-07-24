#!/usr/bin/env python3

import sys
from pathlib import Path

# dirty hack to avoid dealing with package imports
sys.path.append(str(Path(__file__).parent/'core'))

from core.timekeeper_main import main
main()
