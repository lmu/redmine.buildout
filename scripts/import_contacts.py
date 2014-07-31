#!/usr/local/Plone/Python-2.7/bin/python

import sys
sys.path[0:0] = [
    '/usr/local/Plone/redmine.buildout/src/python-redmine',
    '/usr/local/Plone/redmine.buildout/src/python-redminecrm',
    '/usr/local/Plone/buildout-cache/eggs/ipython-1.2.1-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/ipdb-0.8-py2.7.egg',
    '/usr/local/Plone/buildout-cache/eggs/requests-2.3.0-py2.7.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ValidationError
#from redminecrm import Contacts

import csv
import os.path
import sys

import ipdb

def import_contacts(file_path):
    print file_path

    redmine = Redmine('http://localhost/spielwiese/', username='admin', password='admin')

    custom_fields = redmine.custom_field.all()
    cf_campus_kennung_id = None
    cf_fiona_gruppe_id = None

    for cf in custom_fields:
        if cf.name == "Campus-Kennung":
            cf_campus_kennung_id = cf.id
        elif cf.name == "Zugeteilte Fionagruppe":
            cf_fiona_gruppe_id = cf.id




    with open(file_path, 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')


        # get Project webauftritte
        project = redmine.project.get('webauftritte')

        for row in reader:
            try:
                redmine.contact.create(
                    project_id  = project.id,
                    is_company  = row.get('Is company', False),
                    first_name  = row.get('First Name', '') ,
                    middle_name = row.get('Middle Name', '') ,
                    last_name   = row.get('Last Name', '') ,
                    company     = row.get('Company', '') ,
                    phone       = row.get('Phone', '') ,
                    email       = row.get('Email', '') ,
                    website     = row.get('Website', '') ,
                    skype_name  = row.get('Skype', '') ,
                    birthday    = row.get('Birthday', '') ,
                    background  = row.get('Background', '') ,
                    job_title   = row.get('Job Title', '') ,
                    tag_list    = row.get('Tags', []) ,
                    address_attributes = {
                        'street1' : row.get('Strasse', '') ,
                        'street2' : row.get('Strasse2', '') ,
                        'city'    : row.get('Stadt', '') ,
                        'zip'     : row.get('PLZ', '') ,
                        'country_code' : row.get('Country', '') ,
                    }, 
                    custom_fields  = [
                        { 'id': cf_campus_kennung_id, 'value' : row.get('Campus Kennung', '') },
                        { 'id': cf_fiona_gruppe_id,   'value' : row.get('Zugeteilte Fionagruppe', '') }
                    ], 
                    visibility = 0,
                    )
            except ValidationError, e:
                #import ipdb; ipdb.set_trace()
                print "Error on {row} with error: {message}".format(row=row, message=e.message)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_contacts(file_path)