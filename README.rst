================
redmine.buildout
================

Das ist ein Buildout des Referats Internetdienste der Ludwig-Maximilians-Universität München, dass eine vollständige Umgebung für Projekt- und Softwarekonfigurationsmanagement erstellt.

-----
Setup
-----


Systemvoraussetzungen
=====================

SLES11SP3
---------




Ubuntu 14.04 LTS
----------------



Vorarbeiten
===========

Bitte checken Sie dieses Projekt aus:

.. code:: bash  

    # Load project from github
    git clone https://github.com/loechel/redmine.buildout.git
    
    # go into project directory
    cd redmine.buildout

    # bootstrap your buildout
    python bootstrap.py
    # this will generate you some directories and scripts
    # * bin/
    # * bin/buildout*
    # * develop-eggs/
    # * parts/ <-- Path to where all buildout based installations will go in by default

Jetzt erstellen Sie bitte folgende Verzeichnisse:

* redmine-plugins
* redmine-themes

bzw. ggf. zusätzlich folgende Verzeichnisse:

* redmine-plugins-download
* redmine-themes-download

und laden Sie bitte die Plugins und Themes herunter und legen diese entpackt in die jeweiligen Verzeichnisse.

.. code:: bash  

    # Initialize directories 
    mkdir redmine-plugins redmine-themes redmine-plugins-download redmine-themes-download

    # download plugins and themes that are only distributed by source control systems
    git clone https://github.com/thorin/redmine_auto_watch.git                  redmine-plugins/redmine_auto_watch
    git clone https://github.com/abahgat/redmine_didyoumean.git                 redmine-plugins/redmine_didyoumean
    git clone https://github.com/alexbevi/redmine_knowledgebase.git             redmine-plugins/redmine_knowledgebase
    git clone https://github.com/bdemirkir/sidebar_hide.git                     redmine-plugins/sidebar_hide
    git clone https://github.com/alexandermeindl/redmine_tweaks.git             redmine-plugins/redmine_tweaks
    git clone https://github.com/alexandermeindl/redmine_local_avatars.git      redmine-plugins/redmine_local_avatars
    git clone https://github.com/alexandermeindl/redmine_spent_time_column.git  redmine-plugins/redmine_spent_time_column

    git clone https://github.com/loechel/redmine-theme-lmu.git                  redmine-themes/redmine-theme-lmu
    git clone https://github.com/loechel/redmine_lmu_modifications.git          redmine-plugins/redmine_lmu_modifications

    # download plugins and themes that are distributed as zip files
    wget --directory-prefix=redmine-plugins-download http://redminecrm.com/license_manager/5383/redmine_favorite_projects-1_0_1.zip
    wget --directory-prefix=redmine-plugins-download https://bitbucket.org/haru_iida/redmine_wiki_extensions/downloads/redmine_wiki_extensions-0.6.4.zip
    wget --directory-prefix=redmine-plugins-download https://bitbucket.org/kusu/redmine_wiki_lists/downloads/redmine_wiki_lists-0.0.3.zip

    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_wiki_extensions-0.6.4.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_wiki_lists-0.0.3.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_agile-1_3_2-pro.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_contacts-3_2_17-pro.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_contacts_helpdesk-2_2_11.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_contacts_invoices-3_1_4-pro.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_finance-1_1_0-pro.zip
    wget --directory-prefix=redmine-plugins-download https://www.scm.verwaltung.uni-muenchen.de/redmine-plugins/redmine_products-1_0_3-pro.zip 

    wget --directory-prefix=redmine-themes-download http://redminecrm.com/license_manager/7644/a1-1_1_2.zip
    wget --directory-prefix=redmine-themes-download http://redminecrm.com/license_manager/11619/circle_theme-1_0_2.zip

    # unzip plugins and themes, downloaded as zips
    unzip  -d redmine-plugins redmine-plugins-download/redmine_favorite_projects-
    unzip  -d redmine-plugins redmine-plugins-download/redmine_wiki_extensions-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_wiki_lists-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_agile-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_contacts-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_contacts_helpdesk-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_contacts_invoices-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_finance-*.zip
    unzip  -d redmine-plugins redmine-plugins-download/redmine_products-*.zip 

    unzip  -d redmine-themes redmine-themes-download/a1-*.zip
    unzip  -d redmine-themes redmine-themes-download/circle_theme-*.zip

Installation 
============

Mit ausführen der Funktion 

.. code:: bash

    python bootstrap.py



Nacharbeiten
============


SLES11SP3
---------

.. code:: bash

    chown -R wwwdata:www .




