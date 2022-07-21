from datetime import datetime, timedelta
from pathlib import Path
import os, csv, math
from typing import List

import yaml
from PyInquirer import prompt
from examples import custom_style_2
from rich.console import Console
from rich.table import Column, Table
from colorama import Fore

headers = ['start_time', 'end_time', 'hours', 'project', 'description' ]
path = os.path.join('.', 'worktimes.csv')
dateformat = '%Y-%m-%d %H:%M'

class Database:
    def __init__(self):
        if not Path(path).exists():
            Path(path).touch()
            print('No database found. New database created...')

    def read(self):
        worktimes: List[Worktime] = []

        with open(path, 'r') as f:
            reader = csv.reader(f)
            try:
                next(reader)
            except:
                pass
            for row in reader:
                if len(row) > 0:
                    start_time: datetime = datetime.strptime(row[0], dateformat)
                    end_time: datetime = len(row[1]) > 0 and datetime.strptime(row[1], dateformat) or None
                    project: str = row[3]
                    desc: str = row[4]
                    if end_time is not None:
                        hours = end_time - start_time
                    else:
                        hours = None

                    wkt = Worktime(start_time=start_time,
                                   end_time=end_time,
                                   hours=hours,
                                   project=project,
                                   description=desc)
                    worktimes.append(wkt)
            print(f'Read all worktimes, found {reader.line_num -1}')
        return worktimes

    def write(self, worktimes):
        with open(path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for worktime in worktimes:
                row = worktime.get_tuple()
                writer.writerow(row)

# Controller
class WorktimeController:
    def __init__(self):
        self.db = Database()
        with open(os.path.join('.', 'cfg.yaml')) as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)

        self.worktimes = self.db.read()

    def add_worktime(self, project: str, desc: str):
        wkt = Worktime(start_time=datetime.now(), project=project, description=desc)
        self.worktimes.append(wkt)
        self.db.write(self.worktimes)

    def finish_worktime(self):
        self.worktimes[-1].end_time = datetime.now()
        self.worktimes[-1].hours = self.worktimes[-1].end_time - self.worktimes[-1].start_time
        self.db.write(self.worktimes)

# Model
class Worktime:
    start_time: datetime
    end_time: datetime
    project: str
    description: str
    hours: timedelta

    def __init__(self, start_time: datetime, project: str, description: str, end_time: datetime = None, hours: timedelta = None):
        self.start_time = start_time
        self.project = project
        self.description = description
        self.end_time = end_time
        self.hours = hours

    def get_tuple(self):
        return (self.start_time.strftime(dateformat),
                self.end_time is not None and self.end_time.strftime(dateformat) or '',
                self.hours is not None and self.hours or '',
                self.project,
                self.description)


wkt_ctr = WorktimeController()
questions = [
    {
        'type': 'list',
        'name': 'modus',
        'message': 'Select modus',
        'choices': ['start', 'finish', 'list']
    },
    {
        'type': 'list',
        'name': 'project',
        'message': 'Select project',
        'choices': wkt_ctr.cfg['projects'],
        'when': lambda answers: answers['modus'] == 'start'
    },
    {
        'type': 'input',
        'name': 'description',
        'message': 'Insert a description',
        'when': lambda answers: answers['modus'] == 'start'
    },
    {
        'type': 'list',
        'name': 'filter',
        'message': 'Which range',
        'choices': ['this week', 'this month', 'all'],
        'when': lambda answers: answers['modus'] == 'list'
    }
]
answers = prompt(questions)

def list_times():
    global end_time, hours, project
    print(F'Listing worktimes {len(wkt_ctr.worktimes)}')
    print('Startime\t\t| Endtime\t\t| Hours\t| Project\t| Description')
    print('-' * 90)
    for worktime in wkt_ctr.worktimes:
        end_time = worktime.end_time is not None and worktime.end_time or '\t\t'
        # hours = worktime.hours is not None and worktime.hours or ''
        hours = worktime.end_time is not None and worktime.end_time - worktime.start_time or ''
        project = len(worktime.project) > 5 and f'{worktime.project}\t' or f'{worktime.project}\t\t'
        print(f'{worktime.start_time}\t| '
              f'{end_time}\t| '
              f'{hours}\t| '
              f'{project}| '
              f'{worktime.description}'
              )


def list_table(worktimes):
    table = Table(title='Worktimes', show_footer=True)
    for header in headers:
        table.add_column(header, justify='left', no_wrap=True)
    for worktime in worktimes:
        table.add_row(str(worktime.start_time), str(worktime.end_time), str(worktime.hours), worktime.project,
                      worktime.description)
    console = Console()
    console.print(table)


if answers['modus'] == 'start':
    if len(wkt_ctr.worktimes) > 0 and wkt_ctr.worktimes[-1].end_time is None:
        wkt_ctr.finish_worktime()
    wkt_ctr.add_worktime(answers['project'], answers['description'])
    print()
elif answers['modus'] == 'finish':
    wkt_ctr.finish_worktime()
elif answers['modus'] == 'list':
    # list_times()
    if answers['filter'] == 'this week':
        wkts = [wkt for wkt in wkt_ctr.worktimes if math.fabs(datetime.now().day - wkt.start_time.day) <= 7 and math.fabs(datetime.now().month - wkt.start_time.month) == 0]
    elif answers['filter'] == 'this month':
        wkts = [wkt for wkt in wkt_ctr.worktimes if math.fabs(datetime.now().month - wkt.start_time.month) == 0]
    else:
        wkts = wkt_ctr.worktimes
    list_table(wkts)
