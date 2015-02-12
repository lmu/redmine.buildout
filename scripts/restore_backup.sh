#!/usr/bin/env bash
export DATE=`date +%F`
export  PGPASSWORD="redmine"
export BACKUPFILE="redmine_ref-vi.5_db_2015-02-10.sql"

dropdb --if-exists -U postgres redmine-ref_vi.5
createdb -O redmine -U postgres -E UTF-8 redmine-ref_vi.5

sleep 20s

pg_restore -c /usr/local/Plone/redmine.buildout/Data/${BACKUPFILE}
