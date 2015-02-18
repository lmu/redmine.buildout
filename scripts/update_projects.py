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

# from ConfigParser import SafeConfigParser
from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from redmine.exceptions import ValidationError
from pprint import pformat

import csv
import json
import datetime
import os.path
# import pprint
import time

import logging


def update_projects(group_file_path, structure_file_path):

    # Set up log handler for Fiona Redmine Import:
    log = logging.getLogger('Redmine-Fiona-Import-Logger')
    my_formatter = logging.Formatter(
        fmt='%(name)s: %(asctime)s - %(levelname)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
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
    datefmt = '%Y-%m-%d %H:%M'  # user timestamp.strf(datefmt) for output
    today = datetime.date.today()
    begin_time_stamp = datetime.datetime.now()

    # Setup Internal Storage Variables for later Messaging trough Redmine - error-logs
    store_new_projects = []  # [project_identifiers] <-- from Fiona structure file
    store_removed_projects = []  # [project_identfier]
    store_updated_projects = {}  # { project_identifiers : { change_field_old/new: changed_value_old/new } }
    store_new_users = {}  # {campus_kennung : {'projects': [], 'groups': []}] <-- from Fiona group file
    store_users_without_campus_kennung = {}  # from all_contacts --> { contact_id : { name: _, email: -, projects: [] }
    store_prefix_nonexisting_project = []  # [project_identifiers]
    store_prefix_nonexisting_group = []  # [group_names]
    store_group_with_no_projects = []  # [group_names]
    store_group_with_no_members = []  # [group_names]
    store_new_groups = []  # [group_names]
    store_removed_groups = []  # [group_names]
    store_new_members_in_group = {}  # {group_name: [members]}
    store_removed_members_in_group = {}  # {group_name: [members]}
    store_project_added_groups = {}  # {project_identifier: [group]}
    store_project_removed_groups = {}  # {project_identifier: [group]}
    store_project_added_members = {}  # {project_identifier: [campus-kennung]}
    store_project_removed_members = {}  # {project_identifier: [campus-kennung]}
    store_no_fiona_contacts = []  # [campus-kennung]
    store_no_fiona_projects = []  # [project_identifier]
    store_no_webproject_projects = []  # [project_identifier]
    # special stores - no error log
    store_project_data = {}  # {project_idetifier : [group_names]}

    # Special Wiki-Pages from Redmine for processing:
    # 1. Auto-Fiona-Gruppen-Mitglieder
    # 2. Auto-Fiona-Gruppen-Prefix-Zuordnung
    # 3. Auto-Fiona-Gruppen-Ignore
    # 4. Auto-Fiona-Gruppen-Temp-Ignore
    # Special Wiki-Pages for Wegweiser
    # 1. Auto-Webprojekt_Wegweiser_new
    # 2. Auto-Webprojekt-Wegweiser_old
    # 3. AUto-Projekt_Wegweiser
    # Special Wiki-Pages for Logging
    # 1. FionaImportLogs <-- Master page / parent for all Logs
    # 2. Fiona-Import-Log-ISODate for each Import

    # Setup Redmine-Connector:
    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'https://localhost/internetdienste/',
        #'http://localhost/internetdienste/',
        #username='admin',
        #password='admin',
        key='6824fa6b6ad10fa4828e003faf793a2260688486',
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
    log.debug(u"Custom Field ID für Hostname: %s", cf_hostname_id)
    log.debug(u"Custom Field ID für Analytic-Tool: %s", cf_analytic_tool_id)
    log.debug(u"Custom Field ID für Analytic-URL: %s", cf_analytic_url_id)

    # get all existing Contacts from Redmine Instance:
    _all_contacts = redmine.contact.all()
    all_contacts = {}
    for contact in _all_contacts:
        if not contact.is_company:
            fields = contact.custom_fields
            ck = 'keine_'+contact.last_name.strip().lower()
            for field in fields:
                if field.name == 'Campus-Kennung':
                    ck_n = field.value.strip().lower()
                    if ck_n and ck_n == ck:
                        log.debug('Contact [%s] found, has no formal Camus-Kennung but informal placeholder "%s"', contact.id, ck)
                    elif ck_n:
                        ck = ck_n
                    else:
                        log.debug('Contact [%s] found, has no Campus-Kennung', contact.id)
                        store_users_without_campus_kennung[contact.id] = {
                            'name': contact.last_name,
                            'email': contact.emails,
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
    old_fgm_data = {}  # later directly overwritten by json data from wiki page
    new_fgm_data = {}

    wiki_fgm = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Mitglieder',
        project_id=rmaster_project.id)

    wiki_text = wiki_fgm.text

    # strip all additional Redmine markup (Redmine-Tweaks) from wiki-page
    # so that we have only JSON data
    wiki_common_footer_elems = ['{{fnlist}}',
                                '<div id="wiki_extentions_footer">',
                                '---',
                                '{{lastupdated_at}} von {{lastupdated_by}}'
                                '</div>',
                                '<pre><code class="json">',
                                '</code></pre>']
    for elem in wiki_common_footer_elems:
        wiki_text = wiki_text.replace(elem, '')
    wiki_text = wiki_text.strip()
    old_fgm_data = json.loads(wiki_text)

    log.debug(u"Content of Auto-Fiona-Gruppen-Mitglieder Wiki Seite read into JSON:\n%s", pformat(old_fgm_data))

    if log.getEffectiveLevel() == logging.DEBUG: # make it possible to read debug message of wiki_text
        time.sleep(60)

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
                                new_fgm_data[c_group_name]['projects'] = new_fgm_data[c_group_name].get('projects', []).append(project.identifier)
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
        'Auto-Fiona-Gruppen-Ignore',
        project_id=rmaster_project.id)

    wiki_group_ignore_text = wiki_group_ignore.text

    for line in wiki_group_ignore_text:
        if line.startswith('* '):
            l_group = line[2:]
            if l_group in new_fgm_data:
                del new_fgm_data[l_group]

    wiki_group_temp_ignore = redmine.wiki_page.get(
        'Auto-Fiona-Gruppen-Temp-Ignore',
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
                store_project_data[project] = store_project_data.get(project, []).append(l_group_key)  # NOQA

    # 3.1. Compare old and new Fiona Group Data
    for group_entry in new_fgm_data:
        if group_entry in old_fgm_data:
            new_members = set(new_fgm_data[group_entry]['members']) - set(old_fgm_data[group_entry]['members'])  # NOQA
            removed_members = set(old_fgm_data[group_entry]['members']) - set(new_fgm_data[group_entry]['members'])  # NOQA
            if new_members:
                store_new_members_in_group[group_entry] = new_members
                log.warn('Found new members in group "%s": ', group_entry, ', '.join(new_members))
            if removed_members:
                store_removed_members_in_group[group_entry] = new_members
                log.warn('Found removed members in group "%s": ', group_entry, ', '.join(removed_members))
        else:
            # diff_store_groups
            log.warn('group "%s" not known till today', group_entry)
            store_new_groups.append(group_entry)
    store_new_groups = set(new_fgm_data.keys()) - set(old_fgm_data.keys())
    store_removed_groups = set(old_fgm_data.keys()) - set(new_fgm_data.keys())
    if store_new_groups:
        log.warn('Found new groups: %s', ', '.join(store_new_groups))
    if store_removed_groups:
        log.warn('Found removed groups: %s', ', '.join(store_removed_groups))


    # 3.2. Write Fionagroup Information into Webproject
    for project_key, groups in store_project_data.iteritems():
        l_project = redmine.project.get(project_key)
        l_project_contacts = l_project.contacts
        l_project_contacts_cks = []
        for l_contact in l_project_contacts:
            if not contact.is_company:
                fields = l_contact.custom_fields
                ck = 'keine_'+contact.last_name.strip().lower()
                for field in fields:
                    if field.name == 'Campus-Kennung':
                        ck_n = field.value.strip().lower()
                        if ck_n and ck_n == ck:
                            log.debug('Contact [%s] found, has no formal Camus-Kennung but informal placeholder "%s"', contact.id, ck)
                        elif ck_n:
                            ck = ck_n
                        else:
                            log.debug('Contact [%s] found, has no Campus-Kennung set', contact.id)
                        l_project_contacts_cks.append(ck)
        l_fiona_contacts_ck = []
        for group in groups:
            l_fiona_contacts_ck.extend(new_fgm_data[group].get('members',[]))

        l_new_contacts = set(l_fiona_contacts_ck) - set(l_project_contacts_cks)
        l_removed_contacts = set(l_project_contacts_cks) - set(l_fiona_contacts_ck)
        store_project_added_members[project_key] = l_new_contacts
        store_project_removed_members[project_key] = l_removed_contacts

        if l_new_contacts:
            for l_ck in l_new_contacts:
                l_contact = all_contacts.get(l_ck)
                if l_contact:
                    l_contact.project.add(project_key)

        if l_removed_contacts:
            for l_ck in l_removed_contacts:
                l_contact = all_contacts.get(l_ck)
                if l_contact:
                    l_contact.project.remove(project_key)

        # write wiki-page fionagruppen
        content = 'h1. Fionagruppen\n\n'

        for group in groups:
            content += '\n\nh2. {group}\n\n'.format(group=group)
            for member_ck in new_fgm_data[group]['members']:
                contact = all_contacts.get(member_ck.lower())
                if contact:
                    content += '* {{contact(%s)}}: %s \n' % (contact.id, member_ck)
                else:
                    content += '* {ck}'.format(id=member_ck)

                try:
                    page = redmine.wiki_page.get('Fionagruppen',project_id=l_project.id)
                    redmine.wiki_page.update('Fionagruppen',
                                             project_id=l_project.id,
                                             title='Fionagruppen',
                                             text=content)
                except ResourceNotFoundError:
                    redmine.wiki_page.create(project_id=l_project.id,
                                             title='Fionagruppen',
                                             text=content)

    # Write datastore for fiona group information
    wiki_fgm.text = '<pre><code class="json">{json}</code></pre>'.format(pformat(json.dumps(new_fgm_data)))
    wiki_fgm.comment = 'Import from ' + str(today.isoformat())
    wiki_fgm.save()


    # Process all Projects and check if wegweiser exists and create it if not
    _all_projects = redmine.project.all()

    wiki_webprojects_wegweiser = redmine.wiki_page.get('Auto-Webprojekt_Wegweiser_new', project_id=rmaster_project.id)
    wiki_projects_wegweiser = redmine.wiki_page.get('Auto-Projekt_Wegweiser', project_id=rmaster_project.id)



    for project in _all_projects:
        try:
            redmine.wiki_page.get('wegweiser', project_id=project.id)
        except ResourceNotFoundError:
            if project.parent and project.parent.parent and project.parent.parent.id == rmaster_project.id:  # Webprojekt
                redmine.wiki_page.create(project_id=project.id, title='wegweiser', text=wiki_webprojects_wegweiser_text)
            else:  # Normales Projekt
                redmine.wiki_page.create(project_id=project.id, title='wegweiser', text=wiki_projects_wegweiser_text)


    # 4. Fehlerprotokolle

    support_project = redmine.project.get('support')
    office_project = redmine.project.get('office')
    teams = redmine.group.all()
    support_team = None
    koordinations_team = None
    for team in teams:
        if team.name == 'Support':
            support_team = team
        elif team.name == 'Koordination':
            koordinations_team = team


    # 4.1a. New User (Campus-Kennung) not known
    if store_new_users:
        error_message = """Folgende User sind unbekannt:

|_.Campus-Kennung |_.Fionagruppen |_.Projekte |
"""
        for new_user_ck, values in store_new_users.iteritems():
            error_message += '| {ck} | {groups} | {projects} |\n'.format(
                ck=new_user_ck,
                groups=', '.join(set(values.get('groups', []))),
                projects=', '.join(set(values.get('projects', [])))
            )
        ticket_nu = redmine.issue.create(
            project_id=support_project.id,
            subject='Unbekannte Nutzer bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.1b. Existing Users with no Campus-Kennung
    if store_users_without_campus_kennung:
        error_message = """Folgende User haben keine Campus-Kennung:

|_.User-ID |_.Name |_.E-Mail |_.Projekte |
"""
        for user_id, values in store_users_without_campus_kennung.iteritems():
            error_message += '| {id} | {name} | {email} | {projects} |\n'.format(
                id='{{contact_plain(%s)}}' % str(user_id),
                name=values.get('name', ''),
                email=values.get('email', ''),
                projects=', '.join(set(values.get('projects', [])))
            )
        ticket_nck = redmine.issue.create(
            project_id=support_project.id,
            subject='Kontak ohne Campus-Kennung bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.2. New Group
    if store_new_groups:
        error_message = 'Folgende Gruppen sind neu:\n\n* '
        error_message += '\n* '.join(store_new_groups)
        ticket_ng = redmine.issue.create(
            project_id=support_project.id,
            subject='Neue Gruppe bei Import ' + str(datetime.date.isoformat(time_stamp)),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.3. New Projects
    if store_new_projects:
        error_message = 'Folgende Projekte sind neu:\n\n* '
        error_message += '\n* '.join(store_new_projects)
        ticket_np = redmine.issue.create(
            project_id=office_project.id,
            subject='Neue Projekte bei Import ' + str(datetime.date.isoformat(time_stamp)),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.4. Removed Projects
    if store_removed_projects:
        error_message = 'Folgende Projekte sind in Fiona weggefallen:\n\n* '
        error_message += '\n* '.join(store_removed_projects)
        ticket_rp = redmine.issue.create(
            project_id=office_project.id,
            subject='In Fiona als entfernt gemeldete Projekte bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.5. Group with no Projects
    if store_group_with_no_projects:
        error_message = 'Folgende Gruppen sind keinem Projekt zugenordnet:\n\n* '
        error_message += '\n* '.join(store_group_with_no_projects)
        ticket_gwnp = redmine.issue.create(
            project_id=office_project.id,
            subject='Gruppen ohne Projekte bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.6. Group with no Members
    if store_group_with_no_members:
        error_message = 'Folgenden Gruppen sind keine Kontakte zugeordnet:\n\n* '
        error_message += '\n* '.join(store_group_with_no_members)
        ticket_gwnm = redmine.issue.create(
            project_id=support_project.id,
            subject='Gruppen ohne Mitglieder bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)
        wiki_group_temp_ignore_text += '\n* ' + '\n* '.join(store_group_with_no_members)
        wiki_group_temp_ignore.text = wiki_group_temp_ignore_text
        wiki_group_temp_ignore.comments = 'Update on Fiona Import on {date}'.format(date=today.isoformat())
        wiki_group_temp_ignore.save()

    end_time_stamp = datetime.datetime.now()

    # 5. Wiki Log of Import
    content = 'h1. Log of Fiona Data Import {date}\n\nStart-Time: {begin_time}\nEnd-Time: {end_date}\n\n \{\{toc\}\}\n\n'.format(
        date=today.isoformat(),
        begin_time=begin_time_stamp.strftime(datefmt),
        end_date=end_time_stamp.strftime(datefmt)
    )
    # Project Specific Logs
    if store_new_projects or store_removed_projects or store_updated_projects or \
        store_project_added_groups or store_project_removed_groups or \
        store_project_added_members or store_project_removed_members:
        content += '\n\nh2. Projektbezogene Meldungen'

    if store_new_projects:
        content += '\n\nh3. Neue Projekte beim Import (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_np) + '\n* '.join(store_new_projects)

    if store_removed_projects:
        content += '\n\nh3. Projekte die seit dem letzten Import in Fiona weggefallen sind (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_rp) + '\n* '.join(store_removed_projects)

    if store_updated_projects:
        content += '\n\nh3. Veränderungen an Webprojekt-Daten\n\n'
        content += '|_.Projekt |_.Alter Titel |_.Neuer Titel |_.Alter Status |_.Neuer Status |_. Alte Stprachen |_. Neue Sprachen |\n'
        for project, changes in store_updated_projects.iteritems():
            content += '| {project} | {old_title} | {new_title} | {old_status} | {new_status} | {old_langs} | {new_langs} |\n'.format(
                project=project,
                old_title=changes.get('', ''),
                new_title=changes.get('', ''),
                old_status=changes.get('', ''),
                new_status=changes.get('', ''),
                old_langs=', '.join(changes.get('', [])),
                new_langs=', '.join(changes.get('', [])),
            )

    if store_project_added_groups:
        content += '\n\nh3. Zu Webprojekten hinzugefügte Gruppen\n\n'
        for project, groups in store_project_added_groups.iteritems():
            content += '* {project}\n** ' + '\n** '.join(groups)

    if store_project_removed_groups:
        content += '\n\nh3. Aus Webprojekten entfernte Gruppen\n\n'
        for project, groups in store_project_removed_groups.iteritems():
            content += '* {project}\n** ' + '\n** '.join(groups)

    if store_project_added_members:
        content += '\n\nh3. Zu Webprojekten hinzugefügte Fiona-Kontakte\n\n'
        for project, members in store_project_added_members.iteritems():
            content += '\n* {project}\n'
            for member in members:
                l_contact = all_contacts.get(member)
                if l_contact:
                    content += '\n** {{contact_plain(%s)}}' % l_contact.id
                else:
                    content += '\n** ' + member

    if store_project_removed_members:
        content += '\n\nh3. Aus Weprojekten entfernte Fione-Kontakte\n\n'
        for project, members in store_project_removed_members.iteritems():
            content += '* {project}\n** ' + '\n** '.join(members)



    redmine.wiki_page.create(
        project_id=rmaster_project.id,
        title='Fiona-Import-Log-{date}'.format(today.isoformat()),
        text=content
    )

if __name__ == "__main__":
    if len(sys.argv) > 2:
        group_file_param = sys.argv[1]
        group_file_path = os.path.abspath(group_file_param)
        structure_file_param = sys.argv[2]
        structure_file_path = os.path.abspath(structure_file_param)

        update_projects(group_file_path, structure_file_path)
