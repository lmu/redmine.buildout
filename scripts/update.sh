# -*- coding: utf-8 -*-
#!/bin/bash

export GEM_HOME=
export PATH=$GEM_HOME/bin:$PATH
export RAILS_ENV=production 
export REDMINE_LANG=en

svn up

bundle install --without development test rmagick

rake db:migrate

rake redmine:plugins
rake redmine:plugins:migrate

rake redmine:plugins NAME=redmine_contacts
rake redmine:plugins NAME=redmine_contacts_helpdesk
rake redmine:plugins NAME=redmine_agile
rake redmine:plugins NAME=redmine_backlogs
rake redmine:plugins NAME=redmine_favorite_projects
rake redmine:plugins NAME=redmine_issue_checklist

rake tmp:cache:clear
rake tmp:sessions:clear
