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
        #'/data/buildout-cache/eggs/ipdb-0.8-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

from ConfigParser import SafeConfigParser

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError
from pprint import pformat

import csv
import json
import datetime
import os.path
import pprint
import time

import logging


def update_projects(group_file_path, structure_file_path):

    # Set up log handler for Fiona Redmine Import:
    log = logging.getLogger('Redmine-Fiona-Import-Logger')
    my_formatter = logging.Formatter(
        fmt='%(name)s: %(asctime)s - %(levelname)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:S"
    )
    stdout_hanlder = logging.StreamHandler(sys.stdout)
    stdout_hanlder.setFormatter(my_formatter)
    log.addHandler(stdout_hanlder)
    file_handler = logging.FileHandler(
        'fione_import.log',
        mode='w',
        encoding='utf-8')
    file_handler.setFormatter(my_formatter)
    log.addHandler(file_handler)
    # Set Basic Log-Level for this
    log.setLevel(logging.DEBUG)

    # Timestamp for reporting
    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # Setup Internal Storage Variables for later Messaging trough Redmine
    store_new_projects = {}
    store_updated_projects = {}
    store_new_users = {}
    store_users_without_campus_kennung = {}
    store_prefix_nonexisting_project = {}
    store_new_group = {}
    store_diff = {}
    #error_store = {}
    #diff_store = {}

    # Setup Redmine-Connector:
    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'https://localhost/internetdienste/',
        #'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    log.info("Connecting to Redmine Instance %s ", redmine.url)

    # Setup Reference for Master Project: 'Webprojekte':
    master_project = 'webprojekte'
    rmaster_project = redmine.project.get(master_project)

    log.debug(u"Base Projekt für Webprojekte: [%s] %s - %s",
              rmaster_project.id,
              rmaster_project.identifier,
              rmaster_project.name)

    # Setup Reference for Custom Fields:
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

    log.debug(u"Custom Field ID für Sprache: %s", cf_lang_id)
    log.debug(u"Custom Field ID für Status: %s", cf_status_id)
    log.debug(u"Custom Field ID für Host: %s", cf_host_id)
    log.debug(u"Custom Field ID für Hostename: %s", cf_hostname_id)
    log.debug(u"Custom Field ID für Analytic-Tool: %s", cf_analytic_tool_id)
    log.debug(u"Custom Field ID für Analytic-URL: %s", cf_analytic_url_id)

    # get all existing Contacts from Redmine Instance:
    _all_contacts = redmine.contact.all()
    all_contacts = {}
    for contact in _all_contacts:
        fields = contact.custom_fields
        ck = 'keine_'+contact.last_name.lower()
        for field in fields:
            if field.name == 'Campus-Kennung':
                ck_n = field.value.strip().lower()
                if ck_n:
                    ck = ck_n
                else:
                    log.debug('Contact [%s] found, has no Campus-Kennung')
                    store_users_without_campus_kennung[contact.id] = {
                        'name': contact.name,
                        'email': contact.email,
                        'projects': contact.projects
                    }
        log.debug("add %s to all_contacts", ck)
        all_contacts[ck] = contact

    log.info(u"Anzahl an bekannten Kontakten: %s", str(len(all_contacts)))

    # Proceed Import Steps:
    # 1. Read Fionagruppen and group membership
    # 1.1. Read OLD Fionagruppen and group membership data from JSON-Wiki-Page
    # 1.2. Read NEW Fionagruppen and group membership data from input file
    # 1.3. Assign special Fiona groups to projects
    # 2.
    # 3.

    # 1. Read Fionagruppen and group membership:
    # 1.1. Read OLD Fionagruppen and group membership data from JSON-Wiki-Page
    log.info(u'Begin: AUTO-Fiona-Gruppen-Mitglieder Step')

    # Internal Dictionaries for Groups with Projects and Members
    # (old, new for comparison reasons)
    old_fgm_data = {}
    new_fgm_data = {}

    wiki_fgm = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Mitglieder',
        project_id=rmaster_project.id)

    wiki_text = wiki_fgm.text

    # strip all additional Redmine markup (Redmine-Tweaks) from wiki-page
    # so that we have only JSON data
    wiki_text = wiki_text.replace('{{fnlist}}', '')
    wiki_text = wiki_text.replace('<div id="wiki_extentions_footer">', '')
    wiki_text = wiki_text.replace('---', '')
    wiki_text = wiki_text.replace('{{lastupdated_at}} von {{lastupdated_by}}', '')
    wiki_text = wiki_text.replace('</div>', '')
    wiki_text = wiki_text.strip()

    log.debug(u"Content of Auto-Fiona-Gruppen-Mitglieder Wiki Seite:\n%s", pformat(wiki_text))

    if log.getEffectiveLevel() == logging.DEBUG:
        time.sleep(60)

    old_fgm_data = json.loads(wiki_text)

    # 1.2. Read NEW Fionagruppen and group membership data from input file
    log.debug("Try to open file: %s", group_file_path)
    with open(group_file_path, 'r') as csvfile_groups:
        reader = csv.DictReader(csvfile_groups, delimiter=';', quotechar='"')

        for row in reader:
            log.debug(u"read row: %s", row)
            gruppenname = row.get(u'Gruppenname')
            _gruppenmitglieder = row.get(u'Mitglieder', '')
            gruppenmitglieder = _gruppenmitglieder.split(',')

            members = []

            if gruppenmitglieder is not None and gruppenmitglieder != '':
                for mitglied in gruppenmitglieder:
                    user = mitglied.strip().lower()
                    if user != "":
                        #contact_mitglied = all_contacts.get(mitglied.lower())
                        members.append(user)
                        if user not in all_contacts:
                            l_group = store_new_users.get(user, {})
                            e_webauftritt = l_group.get('projects', [])
                            #e_webauftritt.append(project.identifier)
                            e_group = l_group.get('groups', [])
                            e_group.append(gruppenname)

                            store_new_users[user] = {
                                'projects': e_webauftritt,
                                'groups': e_group
                            }
            log.debug('Found Group "%s", with Members: %s', gruppenname, ', '.join(members))
            new_fgm_data[gruppenname] = {'projects': [], 'members': members}

    log.info(u'Finish: AUTO-Fiona-Gruppen-Mitglieder Step')

    # 1.3. Assign special Fiona groups to projects
    log.info('Begin: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')
    # Process prefix-Data
    wiki_prefix = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Prefix-Zuordnung',
        project_id=rmaster_project.id)

    wiki_prefix_text = wiki_prefix.text

    log.debug(u"Content of 'Auto-Fiona-Gruppen-Prefix-Zuordnung' Wiki Seite:\n%s", pformat(wiki_prefix_text))

    for row in wiki_prefix_text.splitlines():
        if row.startswith('* '):
            log.debug("read prefix row: %s", row)
            line = row[2:].split(':')
            group_name = line[0].strip()
            prefix_projects = line[1].split(',')
            if group_name.endswith('*'):
                wildcard_group_name = group_name[:-1]
                for c_group_name in new_fgm_data.keys():
                    if c_group_name.startswith(wildcard_group_name):
                        for prefix_project in prefix_projects:
                            try:
                                project = redmine.project.get(prefix_project.strip())
                                new_fgm_data[c_group_name]['projects'].append(
                                    {'id': project.id,
                                     'fiona_id': project.identifier})
                                log.debug('Add project: "%s" to group: "%s"', project.identifier, c_group_name)
                            except ResourceNotFoundError as e:
                                log.error(u'No Project with id "%s" found', prefix_project)
                                store_prefix_nonexisting_project.append(prefix_project)

            else:
                for prefix_project in prefix_projects:
                    try:
                        project = redmine.project.get(prefix_project.strip())
                        new_fgm_data[group_name]['projects'].append(
                            {'id': project.id, 'fiona_id': project.identifier})
                        log.debug('Add project: "%s" to group: "%s"', project.identifier, group_name)
                    except ResourceNotFoundError as e:
                        log.error(u'No Project with id "%s" found', prefix_project)
                        store_prefix_nonexisting_project.append(prefix_project)
                    except KeyError as e:
                        log.error(u'A Group provided that is unknown: %s', group_name)
                        store_prefix_nonexisting_group.append(group_name)

    log.info('Finished: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')

    # 2. Import Fiona Stucture
    log.info('Begin: Import Step of Fiona Structure File')
    with open(structure_file_path, 'r') as csvfile_structure:
        reader = csv.DictReader(csvfile_structure, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;  # NOQA
        for row in reader:
            fiona_id = row.get('Fiona-Name')
            fiona_title = row.get('Playland-Titel')
            path = row.get('Fiona-Pfad')
            url = row.get('URL')
            path_list = path.split('/')
            user_data = row.get('Fionagruppe')

            log.info("update Project: %s", fiona_id)
            myproject = None
            try:
                myproject = redmine.project.get(fiona_id)
                myproject.refresh()
                l_message = {}
                if myproject.name != fiona_title:
                    log.debug('Update project: "%s" with new Title: "%s"', myproject.identifier, fiona_title)
                    l_message['title_old'] = myproject.name
                    l_message['title_new'] = fiona_title
                    myproject.name = fiona_title

                if myproject.homepage != url:
                    log.debug('Update project: "%s" with new homepage URL: "%s"', myproject.identifier, url)
                    l_message['homepage_old'] = myproject.name
                    l_message['homepage_new'] = fiona_title
                    myproject.homepage = url
                cfs = myproject.custom_fields
                new_fields = []

                for field in cfs:
                    fval = getattr(field, 'value', '')
                    if field.name == 'Status':
                        nfval = row.get('Status', '')
                        if nfval != fval:
                            log.debug('Update project: "%s" with new Status: "%s"', myproject.identifier, url)
                            l_message['status_old'] = fval
                            l_message['status_new'] = nfval
                            fval = nfval
                    elif field.name == 'Sprache':
                        nfval = row.get('Sprache', '')
                        if nfval != fval:
                            log.debug('Update project: "%s" with new Language: "%s"', myproject.identifier, url)
                            l_message['lang_old'] = fval
                            l_message['lang_new'] = nfval
                            fval = nfval
                    new_fields.append({'id': field.id, 'value': fval})

                myproject.custom_fields = new_fields
                myproject.save()
                if l_message:
                    store_updated_projects[myproject.identifier] = l_message

            except ResourceNotFoundError as e:
                log.info('No Project with identifier: "%s" found, will be created', fiona_id)
                store_new_projects.append(fiona_id)
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

            # Add project to group list
            if user_data:
                groups = user_data.split('#')
                for group in groups:
                    group = group.strip()
                    if group != '' and group != 'all_users':
                        new_fgm_data[group]['projects'].append(
                            {'id': myproject.id,
                             'identifier': myproject.identifier})

    # 3. Compare and handle difference on Fiona Data:

    # 3.1. Remove Ignored Groups from New Fiona Group Data:
    log.info('Begin: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')

    wiki_group_ignore = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Prefix-Zuordnung',
        project_id=rmaster_project.id)

    wiki_group_ignore_text = wiki_group_ignore.text

    for line in wiki_group_ignore_text:
        if line.startswith('* '):
            l_group = line[2:]
            if l_group in new_fgm_data:
                del new_fgm_data[l_group]

    wiki_group_temp_ignore = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Prefix-Zuordnung',
        project_id=rmaster_project.id)

    wiki_group_temp_ignore_text = wiki_group_temp_ignore.text

    for line in wiki_group_temp_ignore_text:
        if line.startswith('* '):
            l_group = line[2:]
            if l_group in new_fgm_data:
                del new_fgm_data[l_group]

    # Transform new_fgm_data into project_group-mapping
    for l_group_key, l_group_value in new_fgm_data.iteritems():
        if not l_group_value['projects']:
            store_group_with_no_projects.append(l_group_key)
        if not l_group_value['members']:
            store_group_with_no_members.append(l_group_key)
        if l_group_value['projects'] and l_group_value['members']:
            for project in l_group_value['projects']:
                store_project_data[project] = store_project_data.get(project, []).append(project)  # NOQA

    # 3.1. Compare old and new Fiona Group Data
    for entry in new_fgm_data:
        if entry in old_fgm_data:
            differences = set(new_fgm_data[entry]['members']) - set(old_fgm_data[entry]['members'])  # NOQA
            if differences:
                log.warn(differences)
            # diff_store_member
        else:
            # diff_store_groups
            log.warn("%s not known till today", entry)

    # 3.2.
    for project_key, groups in store_project_data.iteritems():
        l_project = redmine.project.get(project_key)

































                try:
                    #myproject = redmine.project.get(fiona_id)
                    content = """
h1. Fionagruppen


"""

                    groups = user_data.split('#')

                    for group in groups:
                        if group != '' and group != 'all_users':
                            new_fgm_data[group]['projects'].append({'id':myproject.id, 'identifier': myproject.identifier})



                            #
                            #for c_group in new_fgm_data.keys():
                            #
                            #    c_members = new_fgm_data[c_group]
                            #content += "\n\nh2. " + group_name + "\n\n"
                            #for user in user_ids:
                            #    #contact = redmine.contact.get()
                            #    if user != '':
                            #        contact = all_contacts.get(user.lower())
#
#                                    if contact:
#
#                                        content += "* {{contact(%s)}}: %s \n" % (contact.id, user)  # NOQA#
#
#                                        contact.project.add(myproject.id)
#
#                                    else:
#                                        content += "* " + user + "\n"
#                                        error_message = error_store.get(user, {})
#                                        e_webauftritt = error_message.get('Webauftritt', [])
#                                        e_webauftritt.append(myproject.identifier)
#                                        e_group = error_message.get('Group',[])
#                                        e_group.append(group_name)
#
#                                        error_store[user] = {'Webauftritt': e_webauftritt, 'Group': e_group}

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
                    log.error("Error on %s with error: %s", fiona_id, e.message)
                except ResourceNotFoundError, e:
                    pass


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
