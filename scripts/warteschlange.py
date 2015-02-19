#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.2-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]

elif hostname.startswith('Pumukel-MacBook'):
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.2-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.5.1-py2.7.egg',
    ]
elif hostname.startswith('redmine'):
    sys.path[0:0] = [
        '/data/buildout-cache/eggs/python_redmine-1.0.2-py2.6.egg',
        '/data/buildout-cache/eggs/ipython-1.2.1-py2.6.egg',
        #'/data/buildout-cache/eggs/ipdb-0.8-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

from redmine import Redmine

import datetime
import logging


log = logging.getLogger('Redmine-Warteschlange-Handler')
my_formatter = logging.Formatter(
    fmt='%(name)s: %(asctime)s - %(levelname)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)
stdout_hanlder = logging.StreamHandler(sys.stdout)
stdout_hanlder.setFormatter(my_formatter)
log.addHandler(stdout_hanlder)
file_handler = logging.FileHandler(
    'warteschlange.log',
    mode='a',
    encoding='utf-8')
file_handler.setFormatter(my_formatter)
log.addHandler(file_handler)
# Set Basic Log-Level for this
log.setLevel(logging.DEBUG)

# Timestamp for reporting
datefmt = '%Y-%m-%d %H:%M'  # user timestamp.strf(datefmt) for output
today = datetime.date.today()

# Setup Redmine-Connector:
redmine = Redmine(
    #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
    'https://localhost/internetdienste/',
    #'http://localhost/internetdienste/',
    #username='admin',
    #password='admin',
    key='6824fa6b6ad10fa4828e003faf793a2260688486',
    requests={'verify': False})

log.info("Connecting to Redmine Instance %s ", redmine.url)

statuses = redmine.issue_status.all()

todo_id = 0
warteschlange_id = 0
for status in statuses:
    if status.name == 'To Do':
        todo_id = status.id
    elif status.name == 'Warteschlange':
        warteschlange_id = status.id

issues = redmine.issue.filter(
    status_id=todo_id,
    start_date=">={date}".format(date=(today+datetime.timedelta(days=1)).isoformat())  # could not check only greater so do tomorrow
)

for issue in issues:
    if issue.start_date != today.isoformat():
        log.info('Move Issue "%s" to Warteschlange', issue.id)
        issue.status_id = warteschlange_id
        issue.save()

issues = redmine.issue.filter(
    status_id=warteschlange_id,
    start_date="<={date}".format(date=today.isoformat())
)

for issue in issues:
    log.info('Move Issue "%s" to Todo', issue.id)
    issue.status_id = todo_id
    issue.save()
