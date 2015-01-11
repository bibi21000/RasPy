******************************
Developper manual of RasPy
******************************

Installation
============

.. include:: _static/install.rst

Develop
=======

If you want to develop you surely need vim :

.. code-block:: bash

        sudo apt-get -y install vim-nox vim-addon-manager

Phylosophy
----------

Tests, tests, ... and tests :

 - A bug -> a test -> a patch
 - A new feature -> many test

And documentation

 - A new feature -> documentation

Documentation
-------------

If you want to generate the documentation, you need to install some packages :

 .. code-block:: bash

    sudo apt-get -y install python-sphinx graphviz

And some eggs :

 .. code-block:: bash

    sudo pip install seqdiag sphinxcontrib-seqdiag
    sudo pip install blockdiag sphinxcontrib-blockdiag
    sudo pip install nwdiag sphinxcontrib-nwdiag
    sudo pip install actdiag sphinxcontrib-actdiag

You can now generate the full documentation using :

 .. code-block:: bash

    make docs

You can also generate a part of it, for example :

 .. code-block:: bash

    cd docs
    make html

Tests
-----

Nosetests and pylint are used to test quality of code. There reports are here :

 - `Nosetests report <file:../nosetests/nosetests.html>`_
 - `Coverage report <file:../coverage/index.html>`_
 - `Pylint report <file:../pylint/report.html>`_

Coverage is not the goal but it's one : a module must have a coverage of 90% to be accpeted by core team. Otherwise it will block the packaging process.
Of course, a FAILED test will also.

You can run the developpers test running :

.. code-block:: bash

        make devtests

If you're on a raspberry, you can run the full tests like this :

.. code-block:: bash

        make tests

Running only one test module :

.. code-block:: bash

        /usr/local/bin/nosetests --verbosity=2 --cover-package=raspy --with-coverage --cover-inclusive --cover-tests tests/devices/test_sensor.py

A new device
------------

A new server
------------

.. include:: raspy.rst
