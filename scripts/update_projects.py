#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]
elif hostname == 'redmine1':
    sys.path[0:0] = [
        '/data/buildout-cache/eggs/python_redmine-1.0.1-py2.6.egg',
        '/data/buildout-cache/eggs/ipython-1.2.1-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

from ConfigParser import SafeConfigParser

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError

import csv
import json
import datetime
import os.path
import time

import logging


logging.basicConfig(
    filename="import.log",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:S"
)


def update_projects(group_file_path, structure_file_path):

    log = logging.getLogger(__name__)  # "Redmine Fiona Import Logger"
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.DEBUG)

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'https://localhost/internetdienste/',
        #'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

    log.debug("Connecting to Redmine Instance %s ", redmine.url)

    master_project = 'webprojekte'
    rmaster_project = redmine.project.get(master_project)

    log.debug(u"Base Projekt für Webprojekte: [%s] %s - %s", rmaster_project.id, rmaster_project.identifier, rmaster_project.name)

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
        log.debug("add %s to all_contacts", ck)
        all_contacts[ck] = contact

    log.info(u"Anzahl an bekannten Kontakten: %s", str(len(all_contacts)))

    error_store = {}
    diff_store = {}

    # 1. read Fionagruppen + Mitglieder aus JSON-Wiki-Page
    log.info(u'Begin: AUTO-Fiona-Gruppen-Mitglieder Step')

    wiki_fgm = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Mitglieder',
        project_id=rmaster_project.id)

    wiki_text = wiki_fgm.text

    wiki_text = wiki_text.replace('{{fnlist}}','')
    wiki_text = wiki_text.replace('<div id="wiki_extentions_footer">','')
    wiki_text = wiki_text.replace('---','')
    wiki_text = wiki_text.replace('{{lastupdated_at}} von {{lastupdated_by}}','')
    wiki_text = wiki_text.replace('</div>','')


    log.info(u"Content of Auto-Fiona-Gruppen-Mitglieder Wiki Seite:\n%s", wiki_text)

    time.sleep(60)

    old_fgm_data = json.loads(wiki_text.strip())
    new_fgm_data = {}

    log.debug("Try to open file: %s", group_file_path)
    with open(group_file_path, 'r') as csvfile_groups:
        reader = csv.DictReader(csvfile_groups, delimiter=';', quotechar='"')

        for row in reader:
            log.debug("read row: %s", row)
            gruppenname = row.get('Gruppenname')
            _gruppenmitglieder = row.get('Mitglieder', '')
            gruppenmitglieder = _gruppenmitglieder.split(',')

            members = []

            if gruppenmitglieder is not None and gruppenmitglieder != '':
                for mitglied in gruppenmitglieder:
                    user = mitglied.strip().lower()
                    if user != "":
                        #contact_mitglied = all_contacts.get(mitglied.lower())
                        members.append(user)
                        if user not in all_contacts:
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

    log.info(u'Finish: AUTO-Fiona-Gruppen-Mitglieder Step')

    log.info('Begin: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')
    # 2. Process prefix-Data
    wiki_prefix = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Prefix-Zuordnung',
        project_id=rmaster_project.id)

    wiki_prefix_text = wiki_prefix.text

    log.info(u"Content of 'Auto-Fiona-Gruppen-Prefix-Zuordnung' Wiki Seite:\n%s", wiki_prefix_text)

    for row in wiki_prefix_text.splitlines():
        log.debug("read row: %s", row)
        if row.startswith('*'):
            line = row[2:].split(':')
            group_name = line[0]
            prefix_projects = line[1].split(',')
            if group_name.endswith('*'):
                for c_group_name in new_fgm_data.keys():
                    if c_group_name.startswith(group_name[:-1]):
                        for prefix_project in prefix_projects:
                            try:
                                project = redmine.project.get(prefix_project.strip())
                                new_fgm_data[c_group_name]['projects'].append({'id': project.id, 'fiona_id': project.identifier})
                            except ResourceNotFoundError as e:
                                log.error(u'No Project with id "%s" found', prefix_project)

            else:
                for prefix_project in prefix_projects:
                    try:
                        project = redmine.project.get(prefix_project.strip())
                        new_fgm_data[group_name]['projects'].append({'id': project.id, 'fiona_id': project.identifier})
                    except ResourceNotFoundError as e:
                        log.error(u'No Project with id "%s" found', prefix_project)
                    except KeyError as e:
                        log.error(u'A Group provided that is unknown: %s', group_name)

    log.info('Finished: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')


    # 3. Import Stucture

    log.info('Begin: Import Step of Fiona Structure File')

    with open(structure_file_path, 'r') as csvfile_structure:
        reader = csv.DictReader(csvfile_structure, delimiter=';', quotechar='"')

        #Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;  # NOQA

        #all_projects = redmine.project.all()

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
                myproject.homepage = url
                myproject.name = fiona_title
                cfs = myproject.custom_fields
                new_fields = []

                for field in cfs:
                    #fval = field.value if hasattr(field, 'value') else ''
                    fval = getattr(field, 'value', '')
                    if field.name == 'Status':
                        fval = row.get('Status', '')
                    elif field.name == 'Sprache':
                        fval = row.get('Sprache', '')
                    #if fval == '0' or fval == 0:
                    #    fval = ''
                    new_fields.append({'id': field.id, 'value': fval})

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

    # Timestamp for reporting
    time_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # 2. Compare old and new Fiona Group Data

    for entry in new_fgm_data:
        if entry in old_fgm_data:
            differences = set(new_fgm_data[entry]['members']) - set(old_fgm_data[entry]['members'])  # NOQA
            if differences:
                log.warn(differences)
            # diff_store_member
        else:
            # diff_store_groups
            log.warn("%s not known till today", entry)


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
