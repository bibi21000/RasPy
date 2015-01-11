******************************
Developper manual of RasPy
******************************

Installation
============

The following lines "clone" a GitHub repository. If you want to submit "pull requests", you need to "fork" RasPy using this `guide <https://help.github.com/articles/fork-a-repo/>`_.

.. include:: _static/install.rst

Before starting
===============

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

Keep in mind that all tests must succeed before submitting pull request. But :

 - if a test is a work in progress, you can skip it using self.wipTest()
 - if a test can only be run on Raspberry (ie onewire), it must call self.skipTest(message) at its start.

There is 2 ways to launch the tests. The first one to use on a Raspberry :

.. code-block:: bash

        make tests

You can also run the developpers tests (without skipped one) on a standard computer running :

.. code-block:: bash

        make devtests

If you're on a raspberry, you can run the full tests like this :

.. code-block:: bash

        make tests

Running only one test module :

.. code-block:: bash

        /usr/local/bin/nosetests --verbosity=2 --cover-package=raspy --with-coverage --cover-inclusive --cover-tests tests/devices/test_sensor.py

You can follow automatic tests on `travis-ci <https://travis-ci.org/bibi21000/RasPy>`_.

GitHub
------

You can test the code, build the doc and commit it using the following command :

.. code-block:: bash

        make git

You may use ssh_keys to do it automatically without typing password.


Develop
=======

A new device
------------

A new server
------------

.. include:: raspy.rst

.. include:: raspyweb.rst
