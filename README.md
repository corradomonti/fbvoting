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

  * the **[Vagrant](http://www.vagrantup.com/) setup files** (directory `vagrant-setup`); they will
  install a Vagrant Box with all the necessary software (`pip`, VirtualEnv, Gunicorn, MongoDB, Redis, etc.) to run the app, except for the Java part.
  
  * the **Python part** of the project (directory `fbvoting`). It can be run -- provided necessary software has been installed -- with the `deploy.sh` script.

  * the **Java part** (directory `java`). It should be compiled (with its `ivy` dependencies) in order to produce a runnable, complete `jar` file.

How To Install
--------------

1. Download this repo with

		git clone https://github.com/corradomonti/fbvoting.git


1. Compile the Java part into a runnable, self-contained `jar`.
	
2.	Change directory with `cd vagrant-setup` and install the Vagrant Box with
		
		vagrant up
		
3. Enter the box with `vagrant ssh`.

4. Copy the `jar` created before to `/home/vagrant/fbvoting/java/fbvoting-Main.jar`

5. Now, the hard part: you need to open the file 

		/home/vagrant/fbvoting/fbvoting/conf.py

	and insert the correct values for each `None` variable. Also, if you want the virtual machine to be reachable from the outside (and maybe you want apache, too), now it's the time to configure it.

4.	Finally, you can run everything with:
	
		cd /home/vagrant/fbvoting
		sh deploy.sh
  
  
