#!/usr/bin/env bash
export DATE=`date +%F` 
export  PGPASSWORD="redmine"
pg_dump -Fc --file "/data/redmine.buildout/backup/redmine_ref-vi.3_db_${DATE}.sql" -h 10.153.101.205 -U redmine redmine-ref_vi.3 
tar -zcvf "/data/redmine.buildout/backup/redmine_ref-vi.3_files_${DATE}.tar.gz" "/data/redmine.buildout/var/ref_vi.3/files"

pg_dump -Fc --file "/data/redmine.buildout/backup/redmine_ref-vi.4_db_${DATE}.sql" -h 10.153.101.205 -U redmine redmine-ref_vi.4 
tar -zcvf "/data/redmine.buildout/backup/redmine_ref-vi.4_files_${DATE}.tar.gz" "/data/redmine.buildout/var/ref_vi.4/files"

pg_dump -Fc --file "/data/redmine.buildout/backup/redmine_ref-vi.5_db_${DATE}.sql" -h 10.153.101.205 -U redmine redmine-ref_vi.5 
tar -zcvf "/data/redmine.buildout/backup/redmine_ref-vi.5_files_${DATE}.tar.gz" "/data/redmine.buildout/var/ref_vi.5/files"
