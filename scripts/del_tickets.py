#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]
elif hostname == 'redmine1':
    sys.path[0:0] = [
        '/data/buildout-cache/eggs/python_redmine-1.0.1-py2.6.egg',
        '/data/buildout-cache/eggs/ipython-1.2.1-py2.6.egg',
        '/data/buildout-cache/eggs/ipdb-0.8-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError

import csv
import json
import datetime
import os.path

import ipdb
from pprint import pprint  # NOQA


def del_tickets():

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'https://localhost/internetdienste/',
        #'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    master_project = 'webprojekte'
    rmaster_project = redmine.project.get(master_project)

    all_support_issues = redmine.issue.filter(project_id='support',tracker_id=3)

    for issue in all_support_issues:
        print u'Ticket {id}: "{subject}" processed'.format(id=issue.id, subject=issue.subject) 
        if issue.subject == "Delivery Status Notification (Failure)":
            print u'Ticket {id}: "{subject}" will be deleted'.format(id=issue.id, subject=issue.subject)
            redmine.issue.delete(issue.id)

if __name__ == "__main__":
    del_tickets()
