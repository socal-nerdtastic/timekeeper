#!/usr/bin/env python3.9

import time
import json
from pathlib import Path
from threading import Thread
from datetime import datetime
from collections import defaultdict
import platform
from functools import cache
from bisect import bisect

from constants import TIMECLOCK_FILE, DAY_FMT, BACKUP_FOLDER, BACKUPS
from constants import OFF, REPORT_FRACTION, AUTOSAVE, RESET

@cache
def backup():
    if TIMECLOCK_FILE.exists():
        if BACKUPS:
            if not BACKUP_FOLDER.exists():
                BACKUP_FOLDER.mkdir()
            bkup_prefix = f"{time.strftime('%Y-%m-%d-%H-%M-%S')}_{platform.node()}_{platform.system()}"
            with open(BACKUP_FOLDER / f"{bkup_prefix}_{TIMECLOCK_FILE.name}", 'w') as f:
                f.write(TIMECLOCK_FILE.read_text())
            print("timeclock backed up")

def load_timeclock(fn=TIMECLOCK_FILE):
    try:
        with open(fn) as f:
            data = json.load(f)
        print('Loaded timedata file:', TIMECLOCK_FILE)
    except FileNotFoundError:
        print("times file not found; creating new one")
        data = {}
    return data

def save_timeclock(data, fn=TIMECLOCK_FILE):
    backup()
    with open(fn, 'w') as f:
        json.dump(data, f, indent=2)

class Timeclock:
    def __init__(self, callback=None):
        self.dirty = False
        self.callback = callback
        self.timedata = load_timeclock()
        self.clocked_in = OFF
        timer = Thread(target=self.minute_clock, daemon=True)
        timer.start()
        autosaver = Thread(target=self.autosave_clock, daemon=True)
        autosaver.start()

    def minute_clock(self):
        while True:
            self.tick()
            time.sleep(60)

    def autosave_clock(self):
        while True:
            print(time.strftime("%Y-%m-%d_%H:%M"), "Am i dirty?", self.dirty)
            if self.dirty:
                self.save()
                self.dirty = False
            time.sleep(60*AUTOSAVE)

    def save(self):
        save_timeclock(self.timedata)

    def monthreport(self):
        days = {datetime.strptime(key, DAY_FMT): value for key, value in self.timedata.items()}
        months = defaultdict(list)
        for day, times in days.items():
            months[datetime(day.year, day.month, 1)].append((day, times))

        result = []
        for month in sorted(months, reverse=True):
            result.append(month.strftime("%B %Y"))

            month_totals = defaultdict(int)
            day_totals = defaultdict(dict)
            all_times = months[month]
            for day, times in all_times:
                for project, minutes in times.items():
                    month_totals[project] += minutes
                    day_totals[project][day] = minutes

            for project in sorted(month_totals):
                result.append(f"{project} total: {convert_func(month_totals[project])}")
                result.append(month_percent(month_totals[project], month))
                dates = day_totals[project]
                for day in sorted(dates):
                    result.append(f"{day.strftime(DAY_FMT)}\t{convert_func(dates[day])}")

            result.append("")
        return '\n'.join(result)

    def taskreport(self, task):
        days = {}
        resets = []
        for key, value in self.timedata.items():
            key = datetime.strptime(key, DAY_FMT).date()
            if (minutes := value.get(task)):
                days[key] = minutes
            if (val := value.get(RESET.format(task))):
                resets.append(key)
        daylist = list(sorted(days))
        resets.sort()
        splitpoints = [bisect(daylist, billdate) for billdate in resets]
        sections = []
        for start, end in zip([None]+splitpoints, splitpoints+[None]):
            sections.append(daylist[start:end])
        carry = 0
        output = f"Times for {task}:\n(line) (Date) (day actual min) (day time rounded) (section sum) (carry min)\n\n"
        resets.append("TBD")

        for idx, section in enumerate(reversed(sections)):
            if not section:
                continue

            sec_out = [f"=== Billed {resets[~idx]} ==="]
            sec_sum = 0
            for linenum, day in enumerate(section,1):
                minutes_worked = days[day] + carry
                hours, minutes = divmod(minutes_worked, 60)
                quarterhours, carry = divmod(minutes, 15)
                sec_sum += (hours*60 + quarterhours*15)
                # ~ print(day, minutes_worked, hours, quarterhours, carry, sec_sum)
                sec_out.append(
                    f"{linenum:<3}\t"
                    f"{day.strftime(DAY_FMT)}\t{days[day]:<4}\t"
                    f"{hours:0>2}.{quarterhours*25:0>2}\t"
                    f"{min_to_human(sec_sum):<8}\t{carry}")
            output += "\n".join(sec_out)
            output += "\n\n"

        return output

    def clock_billpoint(self, job_name, event=None):
        today = time.strftime(DAY_FMT)
        if today not in self.timedata:
            self.timedata[today] = {}
        self.timedata[today][RESET.format(job_name)] = True
        self.dirty = True

    def tick(self):
        """adds 1 to the current clocked in job"""
        if self.clocked_in == OFF:
            return
        self.dirty = True

        today = time.strftime(DAY_FMT)
        if today not in self.timedata:
            self.timedata[today] = {}
        if self.clocked_in not in self.timedata[today]:
            self.timedata[today][self.clocked_in] = 0
        self.timedata[today][self.clocked_in] += 1

        if self.callback:
            self.callback(self.report())

    def report(self):
        today = time.strftime(DAY_FMT)
        if self.clocked_in == OFF:
            return "Clocked out"
        elif today in self.timedata and self.clocked_in in self.timedata[today]:
            return f"{today}: {self.clocked_in} for {min_to_human(self.timedata[today][self.clocked_in])}"
        else:
            return f"{today}: {self.clocked_in} for 0 minutes"

    def clock_in(self, job_name):
        self.clocked_in = job_name

        if job_name == OFF:
            print("clocked out")
        else:
            print("clocked in for", job_name)

    def clock_out(self):
        self.clocked_in = OFF

    def __del__(self):
        self.save()

def min_to_human(minutes):
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h, {minutes}m"

def min_to_fraction(minutes):
    hours, minutes = divmod(minutes, 60)
    minutes = round(minutes / 15) * 25
    if minutes == 100:
        minutes = 0
        hours += 1
    return f"{hours}.{minutes}"
convert_func = min_to_fraction if REPORT_FRACTION else min_to_human

MONTHDAYS = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
def month_percent(minutes, month, cap=32*60):
    today = datetime.today()
    if month.month == today.month and month.year == today.year:
        month_elapsed = today.day / MONTHDAYS[today.month]
    else:
        month_elapsed = 1.0
    billable_elapsed = minutes / cap
    return f"{billable_elapsed:.0%} hours at {month_elapsed:.0%} month"

def main():
    t = Timeclock()
    print(t.taskreport("JMOORE"))
    # ~ print(t.monthreport())
    input("press enter to exit")

if __name__ == "__main__":
    main()
