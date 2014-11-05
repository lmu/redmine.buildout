#!/usr/bin/env python

import sys
import socket

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/redmine.buildout/src/python-redmine',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]
elif hostname == 'redmine1':
    sys.path[0:0] = [
        '/data/redmine.buildout/src/python-redmine',
        '/data/redmine.buildout/eggs/ipython-1.2.1-py2.6.egg',
        '/data/redmine.buildout/eggs/ipdb-0.8-py2.6.egg',
        '/data/redmine.buildout/eggs/requests-2.3.0-py2.6.egg',
    ]

from redmine import Redmine

import ipdb


def update_projects():

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    custom_fields = redmine.custom_field.all()
    cf_host_id = None
    cf_hostname_id = None

    for cf in custom_fields:
        if cf.name == "Host":
            cf_host_id = cf.id
        elif cf.name == "Hostname":
            cf_hostname_id = cf.id

    _all_projects = redmine.project.all()

    for project in _all_projects:
        fields = project.custom_fields

        new_fields = []

        for field in fields:
            if field.name == 'Host':
                fval = field.value
                if fval == 'intern':
                    new_fields.append(
                        {'id': cf_hostname_id,
                         'value': 'lmu-.verwaltung.uni-muenchen.de'})
                elif fval == 'extern':
                    new_fields.append(
                        {'id': cf_hostname_id,
                         'value': 'extern'})

            new_fields.append({'id': field.id, 'value': fval})

        project.custom_fields = new_fields
        project.save()
        print 'Update Project: {id}'.format(id=project.identifier)

if __name__ == "__main__":
    update_projects()
