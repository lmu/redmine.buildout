# -*- coding: utf-8 -*-
#!/usr/bin/env python

from redmine import Redmine
from redmine.exceptions import ValidationError

import csv
import os.path
import sys

def import_projects(file_path):
    print file_path

    redmine = Redmine('http://localhost:3000', username='admin', password='admin')


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
                print "Error on " + fiona_id



if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_projects(file_path)







