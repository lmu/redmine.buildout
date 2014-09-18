#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path[0:0] = [
    '/usr/local/Plone/redmine.buildout/src/python-redmine',
    '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
]

import ipdb

from redmine import Redmine
#from redmine.exceptions import ResourceNotFoundError
#from redmine.exceptions import ResourceAttrError
from redmine.exceptions import UnknownError
from redmine.exceptions import ValidationError


redmine = Redmine(
    #'https://www.scm.verwaltung.uni-muenchen.de/spielwiese/',
    'http://localhost/spielwiese/',
    username='admin',
    password='admin',
    requests={'verify': False},
    raise_attr_exception=False
)

#iredmine = Redmine(
#    #'https://www.scm.verwaltung.uni-muenchen.de/spielwiese/',
#    'http://localhost/spielwiese/',
#    username='admin',
#    password='admin',
#    impersonate='Alexander.Loechel',
#    requests={'verify': False},
#    raise_attr_exception=False
#)

master_project = 'webprojekte'
master_project = 'webauftritte'
rmaster_project_id = redmine.project.get(master_project).id


def generate_wiki_wegweiser():

    all_projects = [(project.id,
                     project,
                     project.identifier,
                     project.name)
                    for project in redmine.project.all()]

    for project_id, project, project_identifier, project_name in all_projects:
        try:
            content = '[[Fionagruppen]]' if isWebproject(project) \
                else 'Bitte [[wegweiser]] aufbauen'
            print u"Try to update Project: [{id}] {identifier}: {name} - write {content}".format(
                id=project_id,
                identifier=project_identifier,
                name=project_name,
                content=content)
            redmine.wiki_page.create(project_id=project_id,
                                     title='wegweiser',
                                     text=content)
        except ValidationError:
            pass
        #except UnknownError:
        #    ipdb.set_trace()


def isWebproject(project):
    return '_' in project.identifier
    #try:
    #    parent = project.parent
    #    if parent:
    #    #ipdb.set_trace()
    #        if parent.id == rmaster_project_id:
    #            return True
    #        else:
    #            return isWebproject(parent)
    #    return False
    #except ResourceAttrError:
    #    return False

if __name__ == "__main__":
    generate_wiki_wegweiser()
