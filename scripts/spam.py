#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys

hostname = socket.gethostname()
if hostname == 'Pumukel-GNU-Tablet':
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.2-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]

elif hostname.startswith('Pumukel-MacBook'):
    sys.path[0:0] = [
        '/usr/local/Plone/buildout-cache/eggs/python_redmine-1.0.2-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
        '/usr/local/Plone/buildout-cache/eggs/requests-2.5.1-py2.7.egg',
    ]
elif hostname == 'redmine1':
    sys.path[0:0] = [
        '/data/buildout-cache/eggs/python_redmine-1.0.2-py2.6.egg',
        '/data/buildout-cache/eggs/ipython-1.2.1-py2.6.egg',
        #'/data/buildout-cache/eggs/ipdb-0.8-py2.6.egg',
        '/data/buildout-cache/eggs/requests-2.3.0-py2.6.egg',
    ]

# from ConfigParser import SafeConfigParser
from redmine import Redmine
from pprint import pformat

import datetime
import logging


# Set up log handler for Fiona Redmine Import:
log = logging.getLogger('Redmine-SPAM-Handler')
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

#tags = redmine.contact_tag.all()

spam_tag = 'SPAM'
new_tag = 'Neuer Kontakt'

new_contacts = redmine.contact.filter(tags=new_tag)
for contact in new_contacts:

    #import ipdb; ipdb.set_trace()
    log.debug(
        u'Found Contact "%s" in Tag: "%s" with e-mail: %s and tags: %s',
        str(contact.id),
        new_tag,
        ', '.join(contact.emails),
        ', '.join(contact.tag_list),
    )

    if not len(getattr(contact, 'issues', [])) and not len(getattr(contact, 'notes', [])):
        log.info(
            u'Found Contact "%s" in Tag: "%s" with e-mail: %s having no open Issues and no Notes. Move to SPAM.',
            str(contact.id),
            new_tag,
            ', '.join(contact.emails)
        )
        contact.tag_list = [spam_tag.lower(),'Test']
        log.info('Changes: %s', pformat(contact._changes))
        contact.save()

        contact.project.add('spam')

        contact = contact.refresh()
        projects = contact.projects
        for project in projects:
            #project = project.refresh()
            #import ipdb; ipdb.set_trace()
            identifier = project.refresh().identifier
            if identifier != 'spam':
                log.info('Removed from project: %s', identifier)
                contact.project.remove(identifier)
        log.info(
            'Contact "%s" moved into project: spam',
            contact.id
        )
