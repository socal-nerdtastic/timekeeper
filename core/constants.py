#!/usr/bin/env python3

from pathlib import Path

p = Path(__file__).parent # for resource files

# todo: make these user-settable
TIMECLOCK_FILE = p.parent / "timedata.json"
BACKUP_FOLDER = p.parent / "timedatabackups"
BACKUPS = True # make backups of the datafiles?
SETTING_FILE = p.parent / "timekeeper_settings.json"
SENTINEL_FILE = p.parent / "donttouch.txt"

assets = p / "assets"
LOGO_FILE = assets / "clock.png"
XMARK_IMG = assets / "xmark.png"
STAY_ON_TOP = False
SETTING_DEFAULT = dict(
    position=(30,30),
    tasks = ["TASK 1", "TASK 2"])

DAY_FMT = "%Y-%m-%d"

OFF = "OFF" # special clocked in value that does not log
REPORT_FRACTION = True # use a fraction of hours in the report window (2.25 instead of 2h 15m)
AUTOSAVE = 15 # autosave every 15 minutes
RESET = "{}_RESET" # flag used to set internal billing reset. Bill INCLUDES this day

