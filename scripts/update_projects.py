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


def update_projects(group_file_path, structure_file_path):

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'https://localhost/internetdienste/',
        #'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    master_project = 'webprojekte'
    rmaster_project = redmine.project.get(master_project)

    custom_fields = redmine.custom_field.all()
    cf_lang_id = None
    cf_status_id = None
    cf_host_id = None
    cf_hostname_id = None
    cf_analytic_tool_id = None
    cf_analytic_url_id = None

    for cf in custom_fields:
        if cf.name == 'Sprache':
            cf_lang_id = cf.id
        elif cf.name == 'Status':
            cf_status_id = cf.id
        elif cf.name == 'Host':
            cf_host_id = cf.id
        elif cf.name == 'Hostname':
            cf_hostname_id = cf.id
        elif cf.name == 'Analytic-Tool':
            cf_analytic_tool_id = cf.id
        elif cf.name == 'Analytic-URL':
            cf_analytic_url_id = cf.id


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

    error_store = {}
    diff_store = {}

    # read Fionagruppen+Mitglieder aus JSOn-Wiki-Page

    wiki_fgm = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Mitglieder',
        project_id=rmaster_project.id)

    wiki_text = wiki_fgm.text

    old_fgm_data = {}  # json.loads(wiki_text)
    new_fgm_data = {}

    with open(group_file_path, 'rb') as csvfile_groups:
        reader = csv.DictReader(csvfile_groups, delimiter=';', quotechar='"')

        for row in reader:
            gruppenname = row.get('Gruppenname')
            _gruppenmitglieder = row.get('Mitglieder', '')
            gruppenmitglieder = _gruppenmitglieder.split(',')

            members = []

            if gruppenmitglieder is not None and gruppenmitglieder != '':
                for mitglied in gruppenmitglieder:
                    user = mitglied.lower()
                    #contact_mitglied = all_contacts.get(mitglied.lower())
                    members.append(user)
                    if mitglied.lower() not in all_contacts:
                        error_message = error_store.get(user, {})
                        e_webauftritt = error_message.get('Webauftritt', [])
                        #e_webauftritt.append(project.identifier)
                        e_group = error_message.get('Group', [])
                        #e_group.append(group_name)

                        error_store[user] = {
                            'Webauftritt': e_webauftritt,
                            'Group': e_group
                        }

            new_fgm_data[gruppenname] = {'projects': [], 'members': members}

    # 2. Compare old and new Fiona Group Data

    for entry in new_fgm_data:
        if entry in old_fgm_data:
            differences = new_fgm_data[entry]['members'] - old_fgm_data[entry]['members']  # NOQA
            if differences:
                pprint(differences)
            # diff_store_member
        else:
            # diff_store_groups
            print(entry + "not knowen till today")

        # 3. Import Stucture

    with open(structure_file_path, 'rb') as csvfile_strcuture:
        reader = csv.DictReader(csvfile_strcuture, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;  # NOQA

        #all_projects = redmine.project.all()

        for row in reader:
            #import ipdb; ipdb.set_trace()
            fiona_id = row.get('Fiona-Name')
            fiona_title = row.get('Playland-Titel')

            path = row.get('Fiona-Pfad')
            url = row.get('URL')

            path_list = path.split('/')

            user_data = row.get('Fionagruppe')

            print "update Project: " + fiona_id

            myproject = None

            try:
                myproject = redmine.project.get(fiona_id)
                myproject.refresh()
                myproject.homepage = url
                myproject.name = fiona_title
                cfs = myproject.custom_fields
                new_fields = []

                for field in cfs:
                    fval = field.value if 'value' in field else ''
                    if field.name == 'Status':
                        fval = row.get('Status', '')
                    elif field.name == 'Sprache':
                        fval = row.get('Sprache', '')
                    #if fval == '0' or fval == 0:
                    #    fval = ''
                    new_fields.append({'id': field.id, 'value': fval})

                #ipdb.set_trace()
                myproject.custom_fields = new_fields
                myproject.save()

            except ResourceNotFoundError as e:
                if len(path_list) == 2:
                    myproject = redmine.project.create(
                        name=fiona_title,
                        identifier=fiona_id,
                        homepage=url,
                        is_public=False,
                        inherit_members=True,
                        parent_id=rmaster_project.id,
                        # Custom Fields
                        custom_fields=[
                            {'id': cf_status_id, 'value': row.get('Status', '')},  # NOQA
                            {'id': cf_lang_id, 'value': row.get('Sprache', '')},
                            {'id': cf_host_id, 'value': ''},
                            {'id': cf_hostname_id, 'value': ''},
                            {'id': cf_analytic_tool_id, 'value': ''},
                            {'id': cf_analytic_url_id, 'value': ''},
                        ])
                elif len(path_list) == 3:
                    parent_project = redmine.project.get(path_list[1])
                    myproject = redmine.project.create(
                        name=fiona_title,
                        identifier=fiona_id,
                        homepage=url,
                        is_public=False,
                        inherit_members=True,
                        parent_id=parent_project.id,
                        # Custom Fields
                        custom_fields=[
                            {'id': cf_status_id, 'value': row.get('Status', '')},  # NOQA
                            {'id': cf_lang_id, 'value': row.get('Sprache', '')},
                            {'id': cf_host_id, 'value': ''},
                            {'id': cf_hostname_id, 'value': ''},
                            {'id': cf_analytic_tool_id, 'value': ''},
                            {'id': cf_analytic_url_id, 'value': ''},
                        ])

            if user_data:
                try:
                    #myproject = redmine.project.get(fiona_id)
                    content = """
h1. Fionagruppen


"""

                    groups = user_data.split('#')

                    for group in groups:
                        if group != '' and group != 'all_users':
                            group_data = group.split(':')
                            group_name = group_data[0]
                            user_ids = group_data[1].split(' ')

                            content += "\n\nh2. " + group_name + "\n\n"
                            for user in user_ids:
                                #contact = redmine.contact.get()
                                if user != '':
                                    contact = all_contacts.get(user.lower())

                                    if contact:

                                        content += "* {{contact(%s)}}: %s \n" % (contact.id, user)  # NOQA

                                        contact.project.add(myproject.id)

                                    else:
                                        content += "* " + user + "\n"
                                        error_message = error_store.get(user, {})
                                        e_webauftritt = error_message.get('Webauftritt', [])
                                        e_webauftritt.append(myproject.identifier)
                                        e_group = error_message.get('Group',[])
                                        e_group.append(group_name)

                                        error_store[user] = {'Webauftritt': e_webauftritt, 'Group': e_group}

                    try:
                        page = redmine.wiki_page.get('Fionagruppen',project_id=myproject.id)
                        redmine.wiki_page.update('Fionagruppen',
                                                 project_id=myproject.id,
                                                 title='Fionagruppen',
                                                 text=content)
                    except ResourceNotFoundError, e:
                        redmine.wiki_page.create(project_id=myproject.id,
                                                 title='Fionagruppen',
                                                 text=content)

                except ValidationError as e:
                    print "Error on {id} with error: {message}".format(id=fiona_id, message=e.message)
                except ResourceNotFoundError, e:
                    pass

    # Timestamp for reporting
    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),

    ipdb.set_trace()
    # 4. Fehlerprotokolle
    wiki_fgm.text = json.dumps(new_fgm_data)
    wiki_fgm.comment = 'Import from ' + str(time_stamp)
    wiki_fgm.save()

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
            subject='Unbekannte Nutzer bei Import ' + str(time_stamp),
            description=error_message,
            assigned_to_id=support_team.id)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        group_file_param = sys.argv[1]
        group_file_path = os.path.abspath(group_file_param)
        structure_file_param = sys.argv[2]
        structure_file_path = os.path.abspath(structure_file_param)

        update_projects(group_file_path, structure_file_path)
