#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path[0:0] = [
    '/data/redmine.buildout/src/python-redmine',
    '/data/redmine.buildout/eggs/ipython-1.2.1-py2.6.egg',
    '/data/redmine.buildout/eggs/ipdb-0.8-py2.6.egg',
    '/data/redmine.buildout/eggs/requests-2.3.0-py2.6.egg',
]

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError

import csv
import os.path


def import_projects(file_path):
    print file_path

    redmine = Redmine(
        'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        #'http://localhost/internetdienste/'
        username='admin',
        password='admin',
        requests={'verify': False})

    master_project = 'webprojekte'

    custom_fields = redmine.custom_field.all()
    cf_lang_id = None
    cf_status_id = None

    for cf in custom_fields:
        if cf.name == "Sprache":
            cf_lang_id = cf.id
        elif cf.name == "Status":
            cf_status_id = cf.id

    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;  # NOQA

        project = 0
        #all_projects = redmine.project.all()
        rmaster_project = redmine.project.get(master_project)

        #import ipdb; ipdb.set_trace()
        for row in reader:

            fiona_id = row.get('Fiona-Name')

            print "Write Project: " + fiona_id

            path = row.get('Fiona-Pfad')
            fiona_title = row.get('Playland-Titel')
            url = row.get('URL')

            path_list = path.split('/')
            try:
                try:
                    myproject = redmine.project.get(fiona_id)
                    redmine.project.update(myproject.id,
                                           name=fiona_title,
                                           homepage=url,
                                           is_public=False,
                                           inherit_members=True,
                                           # Custom Fields
                                           custom_fields=[
                                               {'id': cf_status_id,
                                                'value': row.get('Status', '')},
                                               {'id': cf_lang_id,
                                                'value': row.get('Sprache', '')}
                                           ],)

                except ResourceNotFoundError, e:
                    if len(path_list) == 2:
                        project = redmine.project.create(name=fiona_title,
                                                         identifier=fiona_id,
                                                         homepage=url,
                                                         is_public=False,
                                                         inherit_members=True,
                                                         parent_id=rmaster_project.id,
                                                         # Custom Fields
                                                         custom_fields=[
                                                             {'id': cf_status_id, 'value': row.get('Status', '')},
                                                             {'id': cf_lang_id,   'value': row.get('Sprache', '')},
                                                         ])
                    elif len(path_list) == 3:
                        parent_project = redmine.project.get(path_list[1])
                        redmine.project.create(name=fiona_title,
                                               identifier=fiona_id,
                                               homepage=url,
                                               is_public=False,
                                               inherit_members=True,
                                               parent_id=parent_project.id,
                                               # Custom Fields
                                               custom_fields=[
                                                   {'id': cf_status_id, 'value': row.get('Status', '')},
                                                   {'id': cf_lang_id, 'value': row.get('Sprache', '')}
                                               ])

            except ValidationError, e:
                print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_projects(file_path)
