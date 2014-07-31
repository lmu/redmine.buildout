#!/usr/local/Plone/Python-2.7/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path[0:0] = [
    '/usr/local/Plone/redmine.buildout/src/python-redmine',
    '/usr/local/Plone/redmine.buildout/src/python-redminecrm',
    '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ValidationError

import csv
import os.path

def import_projects(file_path):
    print file_path

    redmine = Redmine('http://localhost/spielwiese/', username='admin', password='admin')


    with open(file_path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        project = 0
        for row in reader:
            path = row[0]
            fiona_id = row[1]
            fiona_title = row[2]
            release_date = row[3]
            path_list = path.split('/')
            try:
                if len(path_list) == 2:
                    project = redmine.project.create(name=fiona_title, identifier=fiona_id, is_public=False, inherit_members=True)
                elif len(path_list) == 3:
                    parent_project = redmine.project.get(path_list[1])
                    redmine.project.create(name=fiona_title, identifier=fiona_id, is_public=False, inherit_members=True, parent_id=parent_project.id)
            except ValidationError, e:
                print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_projects(file_path)
