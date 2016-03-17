#!/usr/bin/env python
from __future__ import print_function

from datetime import date
from datetime import timedelta
from os import listdir

import os.path
import time


# File Pattern "redmine_{orgtype}-{orgnum}_{filetype:db|files}_{DATE}.{fileending:sql|tar.gz}" 
base_dir = os.path.join('/', 'data', 'redmine.buildout', 'backup')

base_names_db = ['redmine_ref-vi.3_db_', 'redmine_ref-vi.4_db_', 'redmine_ref-vi.5_db_']
base_names_files = ['redmine_ref-vi.3_files_', 'redmine_ref-vi.4_files_', 'redmine_ref-vi.5_files_']
strip_pattern = base_names_db + base_names_files + ['.sql', '.tar.gz']

def cleanup_backups():
    last_7_days = date.today() - timedelta(days=7)
    last_4_weeks = date.today() - timedelta(days=30)

    for backupfile in listdir(base_dir):
        if os.path.isfile(os.path.join(base_dir, backupfile)):
            file_date = backupfile
            for pattern in strip_pattern:
                file_date = file_date.replace(pattern, '')
            file_date = time.strptime(file_date, '%Y-%m-%d')
            file_date = date(year=file_date[0], month=file_date[1], day=file_date[2])
            if file_date < last_4_weeks and file_date.day != 1:
                print("delete file: {file}".format(file=backupfile))
                os.remove(os.path.join(base_dir, backupfile))
            elif file_date > last_4_weeks and file_date < last_7_days and file_date.day != 1 and file_date.isoweekday() != 1:
                print("delete file: {file}".format(file=backupfile))
                os.remove(os.path.join(base_dir, backupfile))
            else:
                print("keep file: {file}".format(file=backupfile))

if __name__ == "__main__":
    cleanup_backups()

