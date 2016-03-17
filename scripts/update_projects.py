#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.1.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-3.0.0-py2.7.egg',
#        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.6.0-py2.7.egg',
    ]
elif hostname.startswith('redmine'):
    sys.path[0:0] = [
        '/data/buildout-cache/eggs/python_redmine-1.1.1-py2.6.egg',
        #'/data/buildout-cache/eggs/ipython-1.2.1-py2.6.egg',
        # '/data/buildout-cache/eggs/ipdb-0.8-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ResourceNotFoundError
from pprint import pformat

import csv
import datetime
import json
import logging
import os.path
import time
#import ipdb

ca_certs = "/etc/ssl/certs/ca-certificates.crt"


def update_projects(_group_file_path, _structure_file_path):
    """
    Update Script to import Fiona CMS data into Redmine

    :param _group_file_path: Path to a CSV-File of style Group-Name;Group-Member,Group-Member,...
    :param _structure_file_path: Path to a CSV-File of style Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fiona-Group-Name,Fiona-Group-Name,...
    """
    # Set up log handler for Fiona Redmine Import:
    log = logging.getLogger('Redmine-Fiona-Import-Logger')
    # Set Basic Log-Level for this
    log.setLevel(logging.DEBUG)
    #log.setLevel(logging.INFO)

    my_formatter = logging.Formatter(
        fmt='%(name)s: %(asctime)s - %(levelname)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    stdout_hanlder = logging.StreamHandler(sys.stdout)
    stdout_hanlder.setFormatter(my_formatter)
    stdout_hanlder.setLevel(logging.DEBUG)

    log.addHandler(stdout_hanlder)
    file_handler_info = logging.FileHandler(
        'fiona_import_info.log',
        mode='w',
        encoding='utf-8')
    file_handler_info.setFormatter(my_formatter)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)
    file_handler_debug = logging.FileHandler(
        'fiona_import_debug.log',
        mode='w',
        encoding='utf-8')
    file_handler_debug.setFormatter(my_formatter)
    file_handler_debug.setLevel(logging.DEBUG)
    log.addHandler(file_handler_debug)

    # Timestamp for reporting
    datefmt = '%Y-%m-%d %H:%M'  # user timestamp.strf(datefmt) for output
    today = datetime.date.today()
    begin_time_stamp = datetime.datetime.now()

    # Setup Internal Storage Variables for later Messaging trough Redmine - error-logs
    # Contact related
    store_new_users = {}  # {campus_kennung : {'projects': [], 'groups': []}] <-- from Fiona group file
    store_users_without_campus_kennung = {}  # from all_contacts --> { contact_id : { name: _, email: -, projects: [] }
    store_duplicated_campus_kennung = []  # [id, id, ...]
    # project related
    store_new_projects = []  # [project_identifiers] <-- from Fiona structure file
    store_removed_projects = []  # [project_identfier]
    store_updated_projects = {}  # { project_identifiers : { change_field_old/new: changed_value_old/new } }
    store_project_added_groups = {}  # {project_identifier: [group]}
    store_project_removed_groups = {}  # {project_identifier: [group]}
    store_project_added_members = {}  # {project_identifier: [campus-kennung]}
    store_project_removed_members = {}  # {project_identifier: [campus-kennung]}
    store_project_non_fiona_members = {}  # {project_identifier: [campus-kennung]}
    # group related
    store_new_groups = []  # [group_names]
    store_removed_groups = []  # [group_names]  # NOQA
    store_new_members_in_group = {}  # {group_name: [members]}
    store_removed_members_in_group = {}  # {group_name: [members]}
    store_group_with_no_projects = []  # [group_names]
    store_group_with_no_members = []  # [group_names]
    # Fiona Group prefix error store
    store_prefix_nonexisting_project = []  # [project_identifiers]
    store_prefix_nonexisting_group = []  # [group_names]
    # special stores - no error log
    store_project_data = {}  # {project_idetifier : [group_names]}
    store_fiona_contacts = []  # [campus-kennung]
    store_no_fiona_contacts = []  # [campus-kennung]
    store_fiona_projects = []  # [project_identifier]
    store_no_fiona_projects = []  # [project_identifier]
    store_no_webproject_projects = []  # [project_identifier]
    store_fiona_special_projects = []  # [project_identifier]

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
        #'https://localhost/internetdienste/',
        'https://localhost/spielwiese',
        # 'http://localhost/internetdienste/',
        # username='admin',
        # password='admin',
        key='6824fa6b6ad10fa4828e003faf793a2260688486',
        requests={
            'verify': False,
            #'verify': True,
            #'cert_reqs': 'CERT_REQUIRED', 'ca_certs': ca_certs,
            #'cert': (ca_certs, 'keys.key')
            #'cert': ('server_cert.pem', 'server_cert.key'),
        },
        raise_attr_exception=False
    )

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
    cf_campus_kennung_id = None

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
        elif cf.name == 'Campus-Kennung':
            cf_campus_kennung_id = cf.id

    log.debug(u"Custom Field ID für Sprache: %s", cf_lang_id)
    log.debug(u"Custom Field ID für Status: %s", cf_status_id)
    log.debug(u"Custom Field ID für Host: %s", cf_host_id)
    log.debug(u"Custom Field ID für Hostname: %s", cf_hostname_id)
    log.debug(u"Custom Field ID für Analytic-Tool: %s", cf_analytic_tool_id)
    log.debug(u"Custom Field ID für Analytic-URL: %s", cf_analytic_url_id)
    log.debug(u"Custom Field ID für Campus-Kennung: %s", cf_campus_kennung_id)

    all_contacts = {}
    # get all existing Contacts from Redmine Instance:
    _all_rc_ids = []
    _all_contacts = redmine.contact.all()
    for contact in _all_contacts:
        _all_rc_ids.append(contact.id)
        contact = contact.refresh()
        if not getattr(contact, 'is_company', False):
            fields = contact.custom_fields
            ck = 'keine_' + '_'.join([contact.first_name.strip().lower(), contact.last_name.strip().lower(), str(contact.id)])
            update = False
            no_ck = False
            for field in fields:
                if field.name == 'Campus-Kennung':
                    ck_n = field.value.strip().lower()
                    if ck_n and ck_n == ck:
                        log.debug(u'Contact [%s] found, has no formal Campus-Kennung but informal placeholder "%s" that is persitent', contact.id, ck)
                        no_ck = True
                    elif ck_n.lower() in ['', '-', 'keine', 'ohne']:
                        log.debug(u'Contact [%s] found, has no formal persistent Campus-Kennung stored, save informal placeholder "%s"', contact.id, ck)
                        no_ck = True
                        update = True
                    elif ck_n:
                        ck = ck_n
                    else:
                        log.debug(u'Contact [%s] found, has no Campus-Kennung', contact.id)
                        no_ck = True
                        update = True

            if no_ck and not 'Checked-SPAM' in contact.tag_list:
                try:
                    contact = contact.refresh()
                    cprojects = contact.projects
                    if cprojects:
                        cproj = [p for p in cprojects]
                        cprojects = []
                        for p in cproj:
                            p = p.refresh()
                            cprojects.append(p.identifier)
                    else:
                        cprojects = []
                    store_users_without_campus_kennung[contact.id] = {
                        'name': contact.last_name,
                        'email': contact.emails,
                        'projects': cprojects
                    }
                except:
                    log.error('Error on Strore %s in store_users_without_campus_kennung', contact.id)

            if update:
                contact.custom_fields = [{'id': field.id, 'value': ck if field.name == 'Campus-Kennung' else field.value} for field in fields]
                #contact.custom_fields = [{'id': cf_campus_kennung_id, 'value': ck}]
                contact.is_company = False
                log.info(u'Update Contact data of Contact-ID: {id} with changes: {changes}'.format(id=contact.id, changes=contact._changes))
                contact.save()
            log.debug("add Contact (%00000d of %00000d) to all_contacts: %00000d  - %s", int(len(_all_rc_ids)), int(max(_all_rc_ids)), int(contact.id), ck)
            all_contacts[ck] = contact
        else:
            # Company
            ck = 'company_' + contact.first_name.strip().lower() + '_' + str(contact.id)
            log.debug("add company %s to all_contacts", ck)
            all_contacts[ck] = contact

    _all_rc_ids = set([ccontact.id for ccontact in _all_contacts])
    _all_ckc_ids = set([ccontact.id for ccontact in all_contacts.values()])

    diff = _all_rc_ids - _all_ckc_ids
    store_duplicated_campus_kennung = sorted([elem for elem in diff])

    log.info(u"Anzahl an Kontakten aus Redmine: %s", str(len(_all_rc_ids)))
    log.info(u"Anzahl an bekannten Kontakten: %s", str(len(all_contacts)))
    log.info(u"Anzahl an Unterschieden: %s; Fehlende IDs: %s", str(len(diff)), str(store_duplicated_campus_kennung))

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
    # old_fgm_data = {}  # later directly overwritten by json data from wiki page
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
                                '{{lastupdated_at}} von {{lastupdated_by}}',
                                '</div>',
                                '<pre><code class="json">',
                                '</code></pre>']

    for elem in wiki_common_footer_elems:
        log.debug(u'Remove %s from wiki_text', elem)
        wiki_text = wiki_text.replace(elem, '')
        if elem in wiki_text:
            log.error(u'Not allowed string "%s" in wiki_text found', elem)
    wiki_text = wiki_text.strip()
    #log.debug(u'Try to load wiki_text:\n%s', pformat(wiki_text))
    old_fgm_data = json.loads(wiki_text)

    log.debug(u"Content of Auto-Fiona-Gruppen-Mitglieder Wiki Seite read into JSON:\n%s", pformat(old_fgm_data))

    if log.getEffectiveLevel() == logging.DEBUG:  # make it possible to read debug message of wiki_text
        time.sleep(10)

    # 1.2. Read NEW Fionagruppen and group membership data from input file
    log.debug("Try to open file: %s", _group_file_path)
    with open(_group_file_path, 'r') as csvfile_groups:
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
                        members.append(user)
                        if user not in all_contacts:
                            l_group = store_new_users.get(user, {})
                            e_webauftritt = l_group.get('projects', [])
                            e_group = l_group.get('groups', [])
                            e_group.append(gruppenname)

                            store_new_users[user] = {
                                'projects': e_webauftritt,
                                'groups': e_group
                            }
            log.debug(u'Found Group "%s", with Members: %s', gruppenname, ', '.join(members))
            new_fgm_data[gruppenname] = {'projects': [], 'members': members}

    log.info(u'Finish: AUTO-Fiona-Gruppen-Mitglieder Step')

    # 1.3. Assign special Fiona groups to projects
    log.info(u'Begin: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')
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
                                new_fgm_data[c_group_name]['projects'] = new_fgm_data[c_group_name].get('projects', []).append(
                                    {'id': project.id, 'fiona_id': project.identifier})
                                log.debug(u'Add project: "%s" to group: "%s"', project.identifier, c_group_name)
                            except ResourceNotFoundError:
                                log.error(u'No Project with id "%s" found', prefix_project)
                                store_prefix_nonexisting_project.append(prefix_project)

            else:
                for prefix_project in prefix_projects:
                    try:
                        project = redmine.project.get(prefix_project.strip())
                        new_fgm_data[group_name]['projects'] = new_fgm_data[group_name].get('projects', []).append(
                            {'id': project.id, 'fiona_id': project.identifier})
                        log.debug(u'Add project: "%s" to group: "%s"', project.identifier, group_name)
                    except ResourceNotFoundError:
                        log.error(u'No Project with id "%s" found', prefix_project)
                        store_prefix_nonexisting_project.append(prefix_project)
                    except KeyError:
                        log.error(u'A Group provided that is unknown: %s', group_name)
                        store_prefix_nonexisting_group.append(group_name)

    log.info(u'Finished: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')

    # 2. Import Fiona Stucture
    log.info(u'Begin: Import Step of Fiona Structure File')
    with open(_structure_file_path, 'r') as csvfile_structure:
        reader = csv.DictReader(csvfile_structure, delimiter=';', quotechar='"')

        # Fiona-Name;Fiona-Pfad;Playland-Titel;Erstellungsdatum;Status;URL;Sprache;Fionagruppe;  # NOQA
        for row in reader:
            fiona_id = row.get('Fiona-Name')
            fiona_title = row.get('Playland-Titel').decode('utf-8')
            path = row.get('Fiona-Pfad')
            url = row.get('URL')
            path_list = path.split('/')
            user_data = row.get('Fionagruppe')

            log.debug("update Project: %s", fiona_id)
            myproject = None
            try:
                myproject = redmine.project.get(fiona_id)
                myproject.refresh()
                l_message = {}
                if myproject.name != fiona_title:
                    log.info(u'Update project: "%s" with new Title: "%s", old Title was "%s"', myproject.identifier, fiona_title, myproject.name)
                    l_message['title_old'] = myproject.name
                    l_message['title_new'] = fiona_title
                    myproject.name = fiona_title

                if myproject.homepage != url:
                    log.info(u'Update project: "%s" with new homepage URL: "%s"', myproject.identifier, url)
                    l_message['homepage_old'] = myproject.homepage
                    l_message['homepage_new'] = url
                    myproject.homepage = url
                cfs = myproject.custom_fields
                new_fields = []

                for field in cfs:
                    fval = getattr(field, 'value', '')
                    if field.name == 'Status':
                        nfval = row.get('Status', '')
                        if nfval != fval:
                            log.info(u'Update project: "%s" with new Status: "%s"', myproject.identifier, nfval)
                            l_message['status_old'] = fval
                            l_message['status_new'] = nfval
                            fval = nfval
                            new_fields.append({'id': field.id, 'value': fval})
                    elif field.name == 'Sprache':
                        nfval = row.get('Sprache', None)
                        if nfval:
                            nfval = nfval.split(',')
                            if '' in nfval:
                                nfval.remove('')
                        else:
                            nfval = []
                        # nfval is not None, fval is either [] or ['lang-code', ...]
                        if nfval != fval:
                            log.info(u'Update project: "%s" with new Language: "%s", old was: "%s"', myproject.identifier, nfval, fval)
                            l_message['lang_old'] = fval
                            l_message['lang_new'] = nfval
                            fval = nfval
                            new_fields.append({'id': field.id, 'value': fval})
                if new_fields:
                    myproject.custom_fields = new_fields
                if myproject._changes:
                    try:
                        log.debug(u'Full Changes on Project: %s', myproject._changes)
                        myproject.save()
                    except:
                        log.error(u'Try to save changes failed on project:%s', myproject.identifier)
                if l_message:
                    store_updated_projects[myproject.identifier] = l_message

            except ResourceNotFoundError:
                log.info(u'No Project with identifier: "%s" found, will be created', fiona_id)
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
                elif len(path_list) > 3:
                    parent_project_name = '-'.join(path_list[2:-1])
                    try:
                        parent_project = redmine.project.get(parent_project_name)
                    except ResourceNotFoundError:
                        parent_project = redmine.project.get(path_list[1])
                        parent_project = redmine.project.create(
                            name=parent_project_name,
                            identifier=parent_project_name,
                            homepage='',
                            is_public=False,
                            inherit_members=True,
                            parent_id=parent_project.id)
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
                        new_fgm_data[group]['projects'] = [{'id': myproject.id,
                                                            'identifier': myproject.identifier}] \
                            if new_fgm_data[group].get('projects') is None else \
                            new_fgm_data[group].get('projects', []).append(
                                {'id': myproject.id,
                                 'identifier': myproject.identifier})

    # 3. Compare and handle difference on Fiona Data:

    # 3.1. Remove Ignored Groups from New Fiona Group Data:
    log.info(u'Begin: Auto-Fiona-Gruppen-Prefix-Zuordnung Step')

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

    for elem in wiki_common_footer_elems:
        wiki_group_temp_ignore_text = wiki_group_temp_ignore_text.replace(elem, '')
    wiki_group_temp_ignore_text = wiki_group_temp_ignore_text.strip()

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
                project_identifier = project['identifier']
                store_project_data[project_identifier] = [l_group_key] if \
                    store_project_data.get(project_identifier) is None else \
                    store_project_data.get(project_identifier, []).append(l_group_key)

    # 3.1. Compare old and new Fiona Group Data
    for group_entry in new_fgm_data:
        if group_entry in old_fgm_data:
            new_members = set(new_fgm_data[group_entry]['members']) - set(old_fgm_data[group_entry]['members'])  # NOQA
            removed_members = set(old_fgm_data[group_entry]['members']) - set(new_fgm_data[group_entry]['members'])  # NOQA
            if new_members:
                store_new_members_in_group[group_entry] = new_members
                log.warn(u'Found new members in group "%s": %s', group_entry, ', '.join(new_members))
            if removed_members:
                store_removed_members_in_group[group_entry] = new_members
                log.warn(u'Found removed members in group "%s": %s', group_entry, ', '.join(removed_members))
        else:
            # diff_store_groups
            log.warn(u'group "%s" not known till today', group_entry)
            store_new_groups.append(group_entry)
    store_new_groups = set(new_fgm_data.keys()) - set(old_fgm_data.keys())
    store_removed_groups = set(old_fgm_data.keys()) - set(new_fgm_data.keys())
    if store_new_groups:
        log.warn(u'Found new groups: %s', ', '.join(store_new_groups))
    if store_removed_groups:
        log.warn(u'Found removed groups: %s', ', '.join(store_removed_groups))

    # 3.2. Write Fionagroup Information into Webproject
    for project_key, groups in store_project_data.iteritems():
        l_project = redmine.project.get(project_key)
        l_project_contacts = l_project.contacts
        l_project_contacts_cks = []
        for l_contact in l_project_contacts:
            if not getattr(contact, 'is_company', False):
                fields = l_contact.custom_fields
                for field in fields:
                    if field.name == 'Campus-Kennung':
                        ck = field.value.strip().lower()
                        l_project_contacts_cks.append(ck)
        l_fiona_contacts_ck = []
        for group in groups or []:
            l_fiona_contacts_ck.extend(new_fgm_data[group].get('members', []))

        l_new_contacts = set(l_fiona_contacts_ck) - set(l_project_contacts_cks)
        l_old_contacts = old_fgm_data.get(project_key, {}).get('members', [])
        l_removed_contacts = set(l_old_contacts) - set(l_fiona_contacts_ck)
        l_non_fiona_contacts = set(l_project_contacts_cks) - set(l_fiona_contacts_ck)
        store_project_added_members[project_key] = l_new_contacts
        store_project_removed_members[project_key] = l_removed_contacts
        store_project_non_fiona_members[project_key] = l_non_fiona_contacts

        if l_new_contacts:
            for l_ck in l_new_contacts:
                l_contact = all_contacts.get(l_ck)
                if l_contact:
                    l_contact.project.add(project_key)

        if l_removed_contacts:
            for l_ck in l_removed_contacts:
                l_contact = all_contacts.get(l_ck)
                if l_contact:
                    try:
                        l_contact.project.remove(project_key)
                    except:
                        log.error(u'Could not remove %s - %s from project: %s', l_contact.id. l_ck, project_key)

        # write wiki-page fionagruppen
        content = u'h1. Fionagruppen\n\n'

        for group in groups or []:
            content += u'\n\nh2. {group}\n\n'.format(group=group)
            for member_ck in new_fgm_data[group]['members'] or []:
                contact = all_contacts.get(member_ck.lower())
                if contact:
                    content += u'* {{contact(%s)}}: %s \n' % (contact.id, member_ck)
                else:
                    content += u'* {ck}'.format(ck=member_ck)
        else:
            content += u'\n\nh2. Zusätzliche Kontakte nicht aus Fiona\n\n'
            for member_ck in l_non_fiona_contacts or []:
                contact = all_contacts.get(member_ck.lower())
                if contact:
                    content += u'* {{contact(%s)}}: %s \n' % (contact.id, member_ck)
                else:
                    content += u'* {ck}'.format(ck=member_ck)

        try:
            redmine.wiki_page.get('Fionagruppen', project_id=l_project.id)
            redmine.wiki_page.update('Fionagruppen',
                                     project_id=l_project.id,
                                     title='Fionagruppen',
                                     text=content)
        except ResourceNotFoundError:
            redmine.wiki_page.create(project_id=l_project.id,
                                     title='Fionagruppen',
                                     text=content)

    # Write datastore for fiona group information
    wiki_fgm.text = '<pre><code class="json">{json}</code></pre>'.format(json=json.dumps(new_fgm_data, indent=2))
    wiki_fgm.comment = 'Import from ' + str(today.isoformat())
    wiki_fgm.save()

    for values in new_fgm_data.itervalues():
        store_fiona_contacts.extend(values.get('members', []) or [])
        store_fiona_projects.extend(values.get('projects', []) or [])

    all_contacts_ck = set(all_contacts.keys())

    store_no_fiona_contacts = all_contacts_ck - set(store_fiona_contacts)

    # Process all Projects and check if wegweiser exists and create it if not
    _all_projects = redmine.project.all()

    wiki_webprojects_wegweiser = redmine.wiki_page.get('Auto-Webprojekt_Wegweiser_new', project_id=rmaster_project.id)
    wiki_projects_wegweiser = redmine.wiki_page.get('Auto-Projekt_Wegweiser', project_id=rmaster_project.id)

    wiki_special_fiona_projects = redmine.wiki_page.get('Auto-Fiona-Sonderprojekte', project_id=rmaster_project.id)

    wiki_webprojects_wegweiser_text = wiki_webprojects_wegweiser.text
    wiki_projects_wegweiser_text = wiki_projects_wegweiser.text
    wiki_special_fiona_projects_text = wiki_special_fiona_projects.text

    for elem in wiki_common_footer_elems:
        wiki_webprojects_wegweiser_text = wiki_webprojects_wegweiser_text.replace(elem, '')
    wiki_webprojects_wegweiser_text = wiki_webprojects_wegweiser_text.strip()

    for elem in wiki_common_footer_elems:
        wiki_projects_wegweiser_text = wiki_projects_wegweiser_text.replace(elem, '')
    wiki_projects_wegweiser_text = wiki_projects_wegweiser_text.strip()

    for elem in wiki_common_footer_elems:
        wiki_special_fiona_projects_text = wiki_special_fiona_projects_text.replace(elem, '')
    wiki_special_fiona_projects_text = wiki_special_fiona_projects_text.strip()

    for line in wiki_special_fiona_projects_text:
        if line.strip().startswith('* '):
            store_fiona_special_projects.append(line.replace('* ', '').strip())

    for project in _all_projects:
        identifier = project.identifier
        try:
            redmine.wiki_page.get('wegweiser', project_id=identifier)
        except ResourceNotFoundError:
            try:
                if identifier in store_fiona_projects:  # Webprojekt
                    redmine.wiki_page.create(project_id=identifier, title='wegweiser', text=wiki_webprojects_wegweiser_text)
                else:  # Normales Projekt
                    redmine.wiki_page.create(project_id=identifier, title='wegweiser', text=wiki_projects_wegweiser_text)
            except:
                log.error('Project: %s has not wiki module activated', identifier)

        if identifier not in store_fiona_projects and identifier not in store_fiona_special_projects:
            store_no_webproject_projects.append(identifier)

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

    # Ticket IDs for reference in Fiona-Import-Log
    ticket_np = 0  # Ticket ID: New Projects
    ticket_rp = 0  # Ticket ID: Removed Projects
    ticket_ng = 0  # Ticket ID: New Groups
    ticket_rg = 0  # Ticket ID: Removed Groups
    ticket_gwnm = 0  # Ticket ID: Group with no Members
    ticket_gwnp = 0  # Ticket ID: Group with no Projects
    ticket_nmg = 0  # Ticket ID: Group with new Members
    ticket_nu = 0  # Ticket ID: New Users
    ticket_nck = 0  # Ticket ID: Users with Campus-Kennung not set
    ticket_dck = 0  # Ticket ID: Potential duplicated Campus-Kennung

    # 4.1a. New User (Campus-Kennung) not known
    if store_new_users:
        error_message = u"""Folgende User sind unbekannt:

|_.Campus-Kennung |_.Fionagruppen |_.Projekte |
"""
        for new_user_ck, values in store_new_users.iteritems():
            error_message += u'| {ck} | {groups} | {projects} |\n'.format(
                ck=new_user_ck,
                groups=', '.join(set(values.get('groups', []))),
                projects='project:' + ', project:'.join(set(values.get('projects', [])))
            )
        ticket_nu = redmine.issue.create(
            project_id=support_project.id,
            subject=u'Unbekannte Nutzer bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.1b. Existing Users with no Campus-Kennung
    if store_users_without_campus_kennung:
        error_message = u"""Folgende User haben keine Campus-Kennung:

|_.User-ID |_.Name |_.E-Mail |_.Projekte |
"""
        for user_id, values in store_users_without_campus_kennung.iteritems():
            error_message += u'| {id} | {name} | {email} | {projects} |\n'.format(
                id='{{contact_plain(%s)}}' % str(user_id),
                name=values.get('name', ''),
                email='; '.join(values.get('email', [])),
                projects='project:'+', project:'.join(set(values.get('projects', [])))
            )
        ticket_nck = redmine.issue.create(
            project_id=support_project.id,
            subject='Kontakt ohne Campus-Kennung bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    if store_duplicated_campus_kennung:
        error_message = u"Folgende Kontakte haben eine bereits verwendete Campus-Kennung, Möglicher Kontakt-Duplikat:\n\n"
        for user_id in store_duplicated_campus_kennung:
            error_message += u'* {{contact_plain(%s)}}\n' % user_id
        ticket_dck = redmine.issue.create(
            project_id=support_project.id,
            subject=u'Kontakt mit Campus-Kennung Duplikat bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.2. New Group
    if store_new_groups:
        error_message = u'Folgende Gruppen sind neu:\n\n* '
        error_message += u'\n* '.join(store_new_groups)
        ticket_ng = redmine.issue.create(
            project_id=support_project.id,
            subject=u'Neue Gruppe bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)

    # 4.3. New Projects
    if store_new_projects:
        error_message = u'Folgende Projekte sind neu:\n\n* '
        error_message += '\n* '.join(store_new_projects)
        ticket_np = redmine.issue.create(
            project_id=office_project.id,
            subject=u'Neue Projekte bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.4. Removed Projects
    if store_removed_projects:
        error_message = u'Folgende Projekte sind in Fiona weggefallen:\n\n* '
        error_message += '\n* '.join(store_removed_projects)
        ticket_rp = redmine.issue.create(
            project_id=office_project.id,
            subject='In Fiona als entfernt gemeldete Projekte bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.5. Group with no Projects
    if store_group_with_no_projects:
        error_message = u'Folgende Gruppen sind keinem Projekt zugenordnet:\n\n* '
        error_message += u'\n* '.join(store_group_with_no_projects)
        ticket_gwnp = redmine.issue.create(
            project_id=office_project.id,
            subject=u'Gruppen ohne Projekte bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=koordinations_team.id)

    # 4.6. Group with no Members
    if store_group_with_no_members:
        error_message = u'Folgenden Gruppen sind keine Kontakte zugeordnet:\n\n* '
        error_message += u'\n* '.join(store_group_with_no_members)
        ticket_gwnm = redmine.issue.create(
            project_id=support_project.id,
            subject=u'Gruppen ohne Mitglieder bei Import ' + str(today.isoformat()),
            description=error_message,
            assigned_to_id=support_team.id)
        wiki_group_temp_ignore_text += u'\n* ' + '\n* '.join(store_group_with_no_members)
        wiki_group_temp_ignore.text = wiki_group_temp_ignore_text
        wiki_group_temp_ignore.comments = u'Update on Fiona Import on {date}'.format(date=today.isoformat())
        wiki_group_temp_ignore.save()

    end_time_stamp = datetime.datetime.now()

    # 5. Wiki Log of Import
    content = u'h1. Log of Fiona Data Import {date}\n\nStart-Time: {begin_time}\nEnd-Time: {end_date}\n\n{toc_macro}\n\n'.format(
        date=today.isoformat(),
        begin_time=begin_time_stamp.strftime(datefmt),
        end_date=end_time_stamp.strftime(datefmt),
        toc_macro='{{toc}}'
    )
    # Project Specific Logs
    if store_new_projects or store_removed_projects or store_updated_projects or \
       store_project_added_groups or store_project_removed_groups or \
       store_project_added_members or store_project_removed_members:
        content += u'\n\nh2. Projektbezogene Meldungen\n'

        if store_new_projects:
            content += u'\n\nh3. Neue Projekte beim Import (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_np)
            content += u'\n* '.join(store_new_projects)

        if store_removed_projects:
            content += u'\n\nh3. Projekte die seit dem letzten Import in Fiona weggefallen sind (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_rp) + u'\n* '.join(store_removed_projects)

        if store_updated_projects:
            content += u'\n\nh3. Veränderungen an Webprojekt-Daten\n\n'
            content += u'|_.Projekt |_.Alter Titel |_.Neuer Titel |_.Alte URL |_.Neue URL |_.Alter Status |_.Neuer Status |_. Alte Stprachen |_. Neue Sprachen |\n'
            for project, changes in store_updated_projects.iteritems():
                content += u'| {project} | {old_title} | {new_title} | {old_homepage} | {new_homepage} | {old_status} | {new_status} | {old_langs} | {new_langs} |\n'.format(
                    project='project:' + project,
                    old_title=changes.get('title_old', ''),
                    new_title=changes.get('title_new', ''),
                    old_homepage=changes.get('hompage_old', ''),
                    new_homepage=changes.get('hompage_new', ''),
                    old_status=changes.get('status_old', ''),
                    new_status=changes.get('status-new', ''),
                    old_langs=', '.join(changes.get('lang_old', [])),
                    new_langs=', '.join(changes.get('lang_new', [])),
                )

        if store_project_added_groups:
            content += u'\n\nh3. Zu Webprojekten hinzugefügte Gruppen\n\n'
            for project, groups in store_project_added_groups.iteritems():
                content += u'\n* project:{project}\n** '.format(project=project) + u'\n** '.join(groups)

        if store_project_removed_groups:
            content += u'\n\nh3. Aus Webprojekten entfernte Gruppen\n\n'
            for project, groups in store_project_removed_groups.iteritems():
                content += u'\n* project:{project}\n** '.format(project=project) + u'\n** '.join(groups)

        if store_project_added_members:
            content += u'\n\nh3. Zu Webprojekten hinzugefügte Fiona-Kontakte\n\n'
            for project, members in store_project_added_members.iteritems():
                if members:
                    content += u'\n* project:{project}'.format(project=project)
                    for member in members:
                        l_contact = all_contacts.get(member)
                        if l_contact:
                            content += u'\n** {{contact_plain(%s)}}' % l_contact.id
                        else:
                            content += u'\n** ' + member

        if store_project_removed_members:
            content += u'\n\nh3. Aus Weprojekten entfernte Fione-Kontakte\n\n'
            for project, members in store_project_removed_members.iteritems():
                if members:
                    content += u'\n* project:{project}** '.format(project=project) + '\n** '.join(members)

    if store_new_groups or store_removed_groups or \
       store_group_with_no_projects or store_group_with_no_members or \
       store_new_members_in_group or store_removed_members_in_group:

        content += u'\n\nh2. Gruppenbezogene Meldungen:\n\n'

        if store_new_groups:
            content += u'\n\nh3. Neue Gruppen beim Import (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_ng.resource_id)
            content += u'\n* '.join(store_new_groups)

        if store_removed_groups:
            content += u'\n\nh3. Gruppen die seit dem letzten Import in Fiona weggefallen sind\n\n* '
            content += u'\n* '.join(store_removed_groups)

        if store_group_with_no_projects:
            content += u'\n\nh3. Folgende Gruppen haben sind keinem Projekt zugeordnet (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_gwnp.resource_id)
            content += u'\n* '.join(store_group_with_no_projects)

        if store_group_with_no_members:
            content += u'\n\nh3. Folgenden Gruppen sind keine Mitglieder zugeordnet, sie wurden Auto-Fiona-Group-Temp-Ignore hinzugefügt (siehe #{ticket_id})\n\n* '.format(ticket_id=ticket_gwnm)
            content += u'\n* '.join(store_group_with_no_members)

        if store_new_members_in_group:
            content += u'\n\nh3. Folgende Gruppen haben neue Mitglieder\n\n* '
            for group, members in store_new_members_in_group.iteritems():
                content += u'\n* {group}\n** '.format(group=group) + '\n** '.join(members)

        if store_removed_members_in_group:
            content += u'\n\nh3. Aus folgenden Gruppen wurden Mitglieder entfernt\n\n* '
            for group, members in store_removed_members_in_group.iteritems():
                content += u'\n* {group}\n** '.format(group=group) + u'\n** '.join(members)

    if store_prefix_nonexisting_project or store_prefix_nonexisting_group:
        content += u'\n\nh2. Verarbeitungsspezifische Meldungen bezüglich Prefix-Ignore\n'

        if store_prefix_nonexisting_project:
            content += u"\n\nh3. Wiki-Page [[{project}:{page_name}]] enthält Projekte die nicht existieren\n\n* ".format(project=master_project,page_name=wiki_prefix.title)
            content += u'\n* '.join(store_prefix_nonexisting_project)

        if store_prefix_nonexisting_group:
            content += u"\n\nh3. Wiki-Page [[{project}:{page_name}]] enthält Gruppen die nicht existieren\n\n* ".format(project=master_project,page_name=wiki_prefix.title)
            content += u'\n* '.join(store_prefix_nonexisting_group)
    try:
        redmine.wiki_page.create(
            project_id=rmaster_project.id,
            title='Fiona-Import-Log-{date}'.format(date=today.isoformat()),
            parent='FionaImportLogs',
            text=content
        )
    except Exception as e:
        log.error('Error on create Import Log, error was: %s', e)
    log.info('Finished Fiona Data Import')

if __name__ == "__main__":
    if len(sys.argv) > 2:
        group_file_param = sys.argv[1]
        group_file_path = os.path.abspath(group_file_param)
        structure_file_param = sys.argv[2]
        structure_file_path = os.path.abspath(structure_file_param)

        update_projects(group_file_path, structure_file_path)
