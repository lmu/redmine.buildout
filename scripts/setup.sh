#!/bin/bash

export RAILS_ENV=production 
export REDMINE_LANG=en

bundle install --without development test rmagick

rake db:drop

#psql -h 10.153.101.205 -c "CREATE DATABASE redmine_livetest WITH ENCODING='UTF8' OWNER=redmine;" --user=redmine --password
createdb redmine_livetest --h 10.153.101.205 -U redmine -W -O redmine -E UTF8

svn co http://svn.redmine.org/redmine/branches/2.4-stable .
svn up

rm -fR plugins/*/
rm -fR public/themes/*/

svn up

gem install bundler

bundle install --without development test rmagick

mkdir -p tmp tmp/pdf public/plugin_assets
chmod -R 755 files log tmp public/plugin_assets

rake generate_secret_token

rake db:migrate
rake redmine:load_default_data

echo "Clean build abgeschlossen"
echo "copy plugins"
sleep 15


cp -R ../redmine-plugins/redmine_backlogs plugins/.
cp -R ../redmine-plugins/redmine_contacts plugins/.
cp -R ../redmine-plugins/redmine_contacts_helpdesk plugins/.

cp -R ../redmine-themes/* public/themes/.


bundle install --without development test rmagick

rake db:migrate

rake redmine:plugins
rake redmine:plugins:migrate

rake redmine:backlogs:install story_trackers=story task_tracker=task corruptiontest=true labels=true

rake redmine:plugins NAME=redmine_contacts
rake redmine:plugins NAME=redmine_contacts_helpdesk

rake tmp:cache:clear
rake tmp:sessions:clear
