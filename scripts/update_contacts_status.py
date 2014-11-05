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


def import_contacts():

    redmine = Redmine(
        #'https://www.scm.verwaltung.uni-muenchen.de/internetdienste/',
        'http://localhost/internetdienste/',
        username='admin',
        password='admin',
        requests={'verify': False})

#    custom_fields = redmine.custom_field.all()
#    cf_status_id = None

#    for cf in custom_fields:
#        if cf.name == "Status":
#            cf_status_id = cf.id

    _all_contacts = redmine.contact.all()

#    ipdb.set_trace()

    ck = ''

    for contact in _all_contacts:
        fields = contact.custom_fields
        ck = 'keine_' + contact.last_name.lower()

        new_fields = []

        for field in fields:
            if field.name == 'Campus-Kennung':
                if field.value != '':
                    fval = field.value.strip().lower()
                else:
                    fval = ck
                ck = fval
            elif field.name == 'Status':
                fval = field.value
                if fval == 'Aktiv':
                    fval = 'Aktiver Fiona Nutzer'
                elif fval == 'Deaktiviert':
                    fval = 'Aktiver Fiona Nutzer'

            new_fields.append({'id': field.id, 'value': fval})

        contact.custom_fields = new_fields
        contact.save()
        print 'Updated Contact: {ck}'.format(ck=ck)

if __name__ == "__main__":
    import_contacts()
