#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError

import csv
import datetime
import os.path

import ipdb


def connect_projects_with_user(file_path):
    print file_path

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/spielwiese/',
        'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    _all_contacts = redmine.contact.all()
    all_contacts = {}
    for contact in _all_contacts:
        fields = contact.custom_fields
        ck = 'keine_'+contact.last_name.lower()
        for field in fields:
            if field.name == 'Campus-Kennung':
                ck = field.value.strip().lower()
        print "add {user} to all_contacts".format(user=ck)
        all_contacts[ck] = contact

    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')

        error_store = {}

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;

        project = 0
        for row in reader:
            #import ipdb; ipdb.set_trace()
            fiona_id = row.get('Fiona-Name')
            user_data = row.get('Fionagruppe')

            print "update Project: " + fiona_id

            if user_data:
                try:
                    project = redmine.project.get(fiona_id)
                    content = """
h1. Fionagruppen


"""

                    groups = user_data.split('#')

                    for group in groups:
                        if group != '':
                            group_data = group.split(':')
                            group_name = group_data[0]
                            user_ids = group_data[1].split(' ')

                            content += "\n\nh2. " + group_name + "\n\n"
                            for user in user_ids:
                                #contact = redmine.contact.get()
                                if user != '':
                                    contact = all_contacts.get(user.lower())

                                    if contact:

                                        content += "* {{contact(%s)}}: %s \n" % (contact.id, user)
                                        try:
                                            redmine.contact_projects.create(
                                                contact_id=contact.id,
                                                id=project.id)
                                        except ValidationError, e:
                                            #print "Error on {id} with error: {message}".format(id=contact.id, message=e.message)
                                            print "Contact: {cid} already exists on Project: {pid}".format(cid=contact.id, pid=project.id)

                                    else:
                                        content += "* " + user + "\n"
                                        error_message = error_store.get(user, {})
                                        e_webauftritt = error_message.get('Webauftritt', [])
                                        e_webauftritt.append(project.identifier)
                                        e_group = error_message.get('Group',[])
                                        e_group.append(group_name)

                                        error_store[user] = {'Webauftritt': e_webauftritt, 'Group': e_group}

                    try:
                        page = redmine.wiki_page.get('Fionagruppen',project_id=project.id)
                        redmine.wiki_page.update('Fionagruppen',
                                                 project_id=project.id,
                                                 title='Fionagruppen',
                                                 text=content)
                    except ResourceNotFoundError, e:
                        redmine.wiki_page.create(project_id=project.id,
                                                 title='Fionagruppen',
                                                 text=content)


                except ValidationError, e:
                    print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)
                except ResourceNotFoundError, e:
                    pass
        if error_store:
            error_message = """Folgende User sind unbekannt:

|_.Campus-Kennung |_.Fionagruppen |_.Projekte |
"""
            for message in error_store:
                error_message += '| {ck} | {groups} | {projects} |\n'.format(
                    ck=message,
                    groups=', '.join(set(error_store[message]['Group'])),
                    projects=', '.join(set(error_store[message]['Webauftritt'])))
            support_project = redmine.project.get('support')
            teams = redmine.group.all()
            support_team = None
            for team in teams:
                if team.name == 'Support':
                    support_team = team
                    break
            redmine.issue.create(
                project_id=support_project.id,
                subject="Unbekannte Nutzer bei Import " +
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                description=error_message,
                assigned_to_id=support_team.id)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        connect_projects_with_user(file_path)
