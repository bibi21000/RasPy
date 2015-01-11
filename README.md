
Welcome to RasPy
****************

RasPy will be an automate to manage Aquarium / Terrarium ... and more
...

Actually it does nothing ... So don't install it ... Except if you
want to help me :)

At last, it will :

   * allow scenario

   * start/stop pumps

   * turn on, off and dim lights

   * sensors ...


Installation
************


Raspbian
========

Install official raspbian from here : http://www.raspbian.org/.

Newbies can install it from : http://www.raspberrypi.org/downloads/.

Developpers or others can also install it on standard distributions
(Ubuntu, Debian, RedHat, ...).


Update packages
===============

You can now update packages

   sudo apt-get -y update
   sudo apt-get -y dist-upgrade

We need to install some packages to download and build RasPy:

   sudo apt-get -y install build-essential python-dev python-minimal python python2.7-dev python2.7-minimal python2.7 git python-setuptools python-docutils python-pylint

Some packages need to be removed as new versions are available from
eggs :

   sudo apt-get remove python-zmq libzmq1 libzmq-dev python-nose pylint


Download it
===========

You should now download RasPy using git. You should not download and
install RasPy with root user. Idealy, you should create a special user
for running RasPy or the pi user. Keep in mind root is baaaddddd.

   git clone https://github.com/bibi21000/RasPy.git


Configure your system
=====================

   * access rights

   * sudo nopasswd

   * ...


Installation
============

If you want to develop for RasPy, you need to install it in develop
mode :

   sudo make develop

Otherwise install it normaly ... but not now ;) :

   sudo make install

And be patient ... installation need to compile zmq ... It takes a
while ...

If something goes wrong during install or if you want to remove RasPy
from you computer, you type :

   sudo make uninstall

If you want to remove dependencies, look at setup.py to get the list
and use the following command for every package:

   sudo pip uninstall package


Run the tests
=============

Check that the SLEEP constant in tests/common.py ist set to 1.0 or 1.5

   vim tests/common.py

You can now check that everything is fine running the tests :

   make tests

If it fails ... run it again :) At last, copy / paste the full screen
output and send it to the core team.


Start it
========

In the next monthes, you should be abble to start it :

   make start


Read the doc
============

   * docs/pdf

   * docs/html
