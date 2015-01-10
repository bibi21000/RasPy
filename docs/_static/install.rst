Raspbian
--------

Install official raspbian from here : http://www.raspbian.org/.

Newbies can install it from : http://www.raspberrypi.org/downloads/.

Developpers or others can also install it on standard distributions (Ubuntu, Debian, RedHat, ...).

Update packages
---------------

You can now update packages

.. code-block:: bash

        sudo apt-get -y update
        sudo apt-get -y dist-upgrade

Some packages need to be removed as some new version are available from eggs :

.. code-block:: bash

        sudo apt-get remove python-zmq libzmq1 libzmq3 libzmq3-dev libzmq-dev python-nose2 python-nose pylint

We also need to install some packages :

.. code-block:: bash

        sudo apt-get -y install build-essential python-dev python-minimal python python2.7-dev python2.7-minimal python2.7 git

Download it
-----------

You should now download RasPy using git. You should not download and install RasPy with root user.
Idealy, you should create a special user for running RasPy or the pi user. Keep in mind root is baaaddddd.

.. code-block:: bash

        git clone https://github.com/bibi21000/RasPy.git

Configure your system
---------------------

 - access rights
 - sudo nopasswd
 - ...

Installation
------------

If you want to develop for RasPy, you need to install it in develop mode :

.. code-block:: bash

        sudo make develop

Otherwise install it normaly

.. code-block:: bash

        sudo make install

Install some missing eggs ... to be sure

.. code-block:: bash

        sudo pip install nose-progressive nose-html

Run the tests
-------------

You can now check that everything is fine running the tests :

.. code-block:: bash

        make tests

If it fails ... run it again :)
At last, copy / paste the full screen output and send it to the core team.

Start it
--------

In the next monthes, you should be abble to start it :

.. code-block:: bash

        make start

Read the doc
------------

 - docs/pdf
 - docs/html
