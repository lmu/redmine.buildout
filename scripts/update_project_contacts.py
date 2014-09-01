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


def connect_projects_with_user(file_path):
    print file_path

    redmine = Redmine('http://localhost/spielwiese/', username='admin', password='admin')

    custom_fields = redmine.custom_field.all()
    cf_fiona_gruppe_id = None

    for cf in custom_fields:
        if cf.name == "Fionagruppen":
            cf_fiona_gruppe_id = cf.id

    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;

        project = 0
        for row in reader:

            fiona_id = row.get('Fiona-Name')
            user_data = row.get('Fionagruppe')

            groups = user_data.split('#')

            

            try:
                
            except ValidationError, e:
                print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)
        

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_projects(file_path)
