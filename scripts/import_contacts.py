#!/usr/bin/env python

import sys
sys.path[0:0] = [
    '/data/redmine.buildout/src/python-redmine',
    '/data/redmine.buildout/src/python-redminecrm',
    '/data/redmine.buildout/eggs/ipython-1.2.1-py2.6.egg',
    '/data/redmine.buildout/eggs/ipdb-0.8-py2.6.egg',
    '/data/redmine.buildout/eggs/requests-2.3.0-py2.6.egg',
    ]

from redmine import Redmine
from redmine.exceptions import ValidationError
#from redminecrm import Contacts

from exceptions import KeyError

import csv
import os.path
import sys
import datetime

import ipdb

def import_contacts(file_path):
    print file_path

    redmine = Redmine('https://www.scm.verwaltung.uni-muenchen.de/internetdienste/', username='admin', password='admin',requests={'verify': False})
    #redmine = Redmine('http://localhost/internetdienste/', username='admin', password='admin')

    custom_fields = redmine.custom_field.all()
    cf_campus_kennung_id = None
    cf_fiona_gruppe_id = None
    cf_anrede_id = None
    cf_activ_id = None
    cf_inactiv_id = None

    for cf in custom_fields:
        if cf.name == "Campus-Kennung":
            cf_campus_kennung_id = cf.id
        elif cf.name == "Status":
            cf_status_id = cf.id
        elif cf.name == "Anrede":
            cf_anrede_id = cf.id
        elif cf.name == "Fiona aktiviert":
            cf_activ_id = cf.id
        elif cf.name == "Fiona deaktiviert":
            cf_inactiv_id = cf.id

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
        row_number = 1

        # get Project webauftritte
        #project = redmine.project.get('webauftritte')
        project = redmine.project.get('webprojekte')

        for row in reader:
            print row_number
            row_number += 1
            try:
                ck = row.get('Campus_Kennung', '').strip().lower()
                email = row.get('Email', '').strip(',')
                phone = row.get('Phone', '').strip(',')
                
                aktiviert_am = row.get('Aktiviert am', '') 
                if aktiviert_am != '':
                    aktiviert_am = datetime.datetime.strptime(aktiviert_am,'%d.%m.%Y %H:%M:%S').date().isoformat()

                deaktiviert_am = row.get('Deaktiviert am', '') 
                if deaktiviert_am != '':
                    deaktiviert_am = datetime.datetime.strptime(deaktiviert_am,'%d.%m.%Y %H:%M:%S').date().isoformat()

                if ck != '' and ck in all_contacts:

                    #ipdb.set_trace()
                    contact = all_contacts[ck].refresh()
                    contact.first_name  = row.get('First Name', '').strip() 
                    contact.middle_name = row.get('Middle Name', '').strip() 
                    contact.last_name   = row.get('Last Name', '').strip() 

                    contact.company     = row.get('Company', '').strip() 
                    contact.phone       = phone
                    contact.email       = email
                    contact.website     = row.get('Website', '').strip() 
                    contact.background  = row.get('Background', '').strip() 
                    contact.job_title   = row.get('Job Title', '').strip()
                    contact.tag_list    = row.get('Tags', [])
                    contact.address_attributes = {
                        'street1' : row.get('Strasse', '').strip() ,
                        'street2' : row.get('Strasse2', '').strip() ,
                        'city'    : row.get('Stadt', '').strip() ,
                        'zip'     : row.get('PLZ', '').strip() ,
                        'country_code' : row.get('Country', '').strip() ,
                    }
                    
                    contact.custom_fields  = [
                        { 'id': cf_campus_kennung_id, 'value' : row.get('Campus_Kennung', '').strip().lower() },
                        #{ 'id': cf_fiona_gruppe_id,   'value' : row.get('Zugeteilte Fionagruppe', '') },
                        { 'id': cf_status_id,         'value' : row.get('Status', '').strip() },
                        { 'id': cf_anrede_id,         'value' : row.get('Anrede', '').strip() },
                        #{ 'id': cf_activ_id,          'value' : aktiviert_am },
                        #{ 'id': cf_inactiv_id,        'value' : deaktiviert_am },
                    ]

                    contact.save()


                else: 
                    redmine.contact.create(
                            project_id  = project.id,
                            is_company  = row.get('Is company', False),
                            first_name  = row.get('First Name', '').strip() ,
                            middle_name = row.get('Middle Name', '').strip() ,
                            last_name   = row.get('Last Name', '').strip() ,
                            company     = row.get('Company', '').strip() ,
                            phone       = row.get('Phone', '').strip() ,
                            email       = row.get('Email', '').strip() ,
                            website     = row.get('Website', '').strip() ,
                            skype_name  = row.get('Skype', '').strip() ,
                            birthday    = row.get('Birthday', '').strip() ,
                            background  = row.get('Background', '').strip() ,
                            job_title   = row.get('Job Title', '').strip() ,
                            tag_list    = row.get('Tags', []) , 
                            visibility  = 0,
                            address_attributes = {
                                'street1' : row.get('Strasse', '').strip() ,
                                'street2' : row.get('Strasse2', '').strip() ,
                                'city'    : row.get('Stadt', '').strip() ,
                                'zip'     : row.get('PLZ', '').strip() ,
                                'country_code' : row.get('Country', '').strip() ,
                            }, 
                            custom_fields  = [
                                { 'id': cf_campus_kennung_id, 'value' : row.get('Campus_Kennung', '').strip().lower() },
                                #{ 'id': cf_fiona_gruppe_id,   'value' : row.get('Zugeteilte Fionagruppe', '') },
                                { 'id': cf_status_id,         'value' : row.get('Status', '').strip() },
                                { 'id': cf_anrede_id,         'value' : row.get('Anrede', '').strip() },
                                { 'id': cf_activ_id,          'value' : aktiviert_am },
                                { 'id': cf_inactiv_id,        'value' : deaktiviert_am },
                            ],
                        )

            except ValidationError, e:
                #import ipdb; ipdb.set_trace()
                print "Error on {row} with error: {message}".format(row=row, message=e.message)
            except KeyError, e: 
                print "KeyError {message}".format(message=e.message)
                ipdb.set_trace()
            except:
                print sys.exc_info()[0]
                ipdb.set_trace()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_param = sys.argv[1]
        file_path = os.path.abspath(file_param)
        import_contacts(file_path)