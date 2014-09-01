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

    #master-Project
    master_project = 'webauftritte'

    custom_fields = redmine.custom_field.all()
    cf_lang_id = None
    cf_status_id = None
    cf_fiona_gruppe_id = None

    for cf in custom_fields:
        if cf.name == "Sprache":
            cf_lang_id = cf.id
        elif cf.name == "Status":
            cf_status_id = cf.id
        elif cf.name == "Fionagruppen":
            cf_fiona_gruppe_id = cf.id

    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;

        project = 0
        for row in reader:

            fiona_id = row.get('Fiona-Name')
            path = row.get('Fiona-Pfad')
            fiona_title = row.get('Playland-Titel')
            url = row.get('URL')
            # Custom Fields
            status = row.get('Status')
            lang = row.get('Sprache')

            path_list = path.split('/')
            try:
                if redmine.project.get(fiona_id):
                    myproject = redmine.project.get(fiona_id)
                    redmine.project.update(myproject.id,
                                           name=fiona_title
                                           homepage=url,
                                           is_public=False, 
                                           inherit_members=True, 
                                           # Custom Fields
                                           custom_fields  = [
                                               { 'id': cf_status_id, 'value' : row.get('Status', '') },
                                               { 'id': cf_lang_id,   'value' : row.get('Sprache', '') }
                                           ], 
                                          )
                elif and len(path_list) == 2:
                    project = redmine.project.create(name=fiona_title, 
                                                     identifier=fiona_id, 
                                                     homepage=url,
                                                     is_public=False, 
                                                     inherit_members=True, 
                                                     parent_id=redmine.project.get(master_project),
                                                     # Custom Fields
                                                     custom_fields  = [
                                                         { 'id': cf_status_id, 'value' : row.get('Status', '') },
                                                         { 'id': cf_lang_id,   'value' : row.get('Sprache', '') }
                                                     ], 
                                                    )
                elif len(path_list) == 3:
                    parent_project = redmine.project.get(path_list[1])
                    redmine.project.create(name=fiona_title, 
                                           identifier=fiona_id, 
                                           homepage=url,
                                           is_public=False, 
                                           inherit_members=True, 
                                           parent_id=parent_project.id,
                                           # Custom Fields
                                           custom_fields  = [
                                               { 'id': cf_status_id, 'value' : row.get('Status', '') },
                                               { 'id': cf_lang_id,   'value' : row.get('Sprache', '') }
                                           ], 
                                          )


            except ValidationError, e:
                print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)
        

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_projects(file_path)
