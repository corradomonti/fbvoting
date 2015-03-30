Liquid FM: music recommendations with liquid democracy for Facebook
===================================================================

A liquid democracy Facebook app to find best music through friends.

The app was developed in the [Laboratory for Web Algorithmics](http://law.di.unimi.it/)
(in [Università degli studi di Milano](http://www.unimi.it/)) by
Paolo Boldi, Corrado Monti, Massimo Santini and Sebastiano Vigna.
The above attribution notice must be indicated in every copy and derivative work.

Contents
---------

This repository contains:

  * the **[Vagrant](http://www.vagrantup.com/) setup files** (folder `vagrant-setup`); they will
  install a Vagrant Box with all the necessary software (`pip`, VirtualEnv, Gunicorn, MongoDB, Redis, etc.) to run the app, except for the Java part.
  
  * the **Python part** of the project (folder `fbvoting`). It can be run -- provided necessary software has been installed -- with the `deploy.sh` script.

  * the **Java part** (folder `java`). It should be compiled (with its `ivy` dependencies) in order to produce a runnable, complete `jar` file. This can then be copied into the running Vagrant Box as `/home/vagrant/fbvoting/java/fbvoting-Main.jar`.

Configuration
-------------
**IMPORTANT: you have to set up properly the file `fbvoting/conf.py` in order to run the project correctly!**
  
  
