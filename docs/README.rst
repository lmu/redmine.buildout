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

Bitte checken Sie dieses Projekt aus und erstellen sie folgende Verzeichnisse:

* redmine-plugins
* redmine-themes

ggf. 

* redmine-plugins-download
* redmine-themes-download

.. code_block:: bash  
    git clone https://github.com/loechel/redmine.buildout.git




Nacharbeiten
============


SLES11SP3
---------

.. code_block:: bash
    chown -R wwwdata:www .




