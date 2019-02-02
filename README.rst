Professor Dogwood - Pokemon Decklist Pricer
===========================================

This is the source for the `Professor Dogwood <https://professordogwood.com/>`_ website. It's a
simple pricing calculator for the Pokemon Trading Card Game (PTCG). It takes exported decklists from
the online version of the game  (PTCGO) and prices them from `PokePrices <http://pokeprices.doeiqts.com/>`_.
This doc is aimed towards anyone curious about how this pricing calculator works or wanting to improve
its functionality. This will not teach you how to play PTCG. This guide assumes a basic knowledge of
Python and comfort working on the command line for installing packages and using git.


Getting Started
---------------

The primary requirements to running this project are `Python 3.7 <https://www.python.org/downloads/>`_
and `Redis <https://redis.io/download>`_. Please refer to their project documentation on how to
install on your operating system. The Python package requirements are listed in the
`requirements.txt` file at the root of the repository and can be installed via::

    pip install -r requirements.txt

It's recommended (but not required) to install these packages in a Python
`virtual environment <https://docs.python.org/3/library/venv.html>`_ dedicated for this project.


Importing Card Data
-------------------

The deck pricing relies on mapping card information from the `Pokemon TCG API <https://pokemontcg.io/>`_
to PokePrices. To avoiding continually hitting this API, the data is imported and cached in Redis.
To get started, you should run the import to cache the card info into Redis::

    python src/importer.py

By default this will fetch the data for each set currently legal in the Expanded format.
It can take a long time to complete because it pauses between each set to avoid hitting the API
too frequently. If you only want to get the current cards for Standard then you can instead run::

    python src/importer.py --standard

As new sets come out you can also import them one at a time via::

    python src/importer.py --set-name 'Team Up'

To see the set of valid set names you should refer to the Pokemon TCG API documentation.


Running the Server Locally
--------------------------

With the Python requirements installed you can launch start the server locally via::

    python src/app.py

This assumes that your Redis server is configured to listen on `localhost` port 6379 which is
the default. If you are running this on a different port this can be configured with the
`REDIS_URL` environment variable. This will start running on port 8080 and you can then
access it in your browser by navigating to http://localhost:8080/.


Contributing Changes
--------------------

This project is hosted on Github and if you'd like to contribute back changes then you
are encouraged to fork this project to your own account and make modifications there. Once
you feel a change is ready, please send a Pull Request with a description of the change you
are making. This will be reviewed potentially with feedback to address before it can be merged.
Please understand that not all requested changes will be merged. We reserve the option to reject
requests which modify this project in a way that doesn't fit this project's goal or focus. If
you have any questions about a potential feature, please feel free to open an issue for
discussion.


Licensing
---------

This project is licensed under the BSD 2-clause included in this repository. That means you
are welcome to redistribute and modify this project for your own project within the terms of
the license which requires you to retain the original copyright notice and disclaimer. The
disclaimer notes this this software is provided without any warranties and this project and
its owners are not responsible or liable damages or problems you might encounter. One notable
exception to this is the Professor Dogwood name and logo. If you choose to host this yourself
then you cannot use this name and logo, except for the purpose of describing the origin of
the work.
