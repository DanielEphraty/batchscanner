.. Batchscanner documentation master file, created by
   sphinx-quickstart on Tue Aug 15 19:22:14 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Batchscanner
===========================================

:Author: Daniel Ephraty
:Source code: https://github.com/DanielEphraty/batchscanner
:PyPI project: https://pypi.org/project/bachscanner-siklu
:Licence: MIT Licence
:Version: |version|

.. warning::
   Project still under development.

:program:`Batchscanner` is a script to batch-scan and/or query and/or configure multiple Siklu radios
via their CLI (SSH) interface. It operates over a user-defined range of IP addresses and/or networks,
executes some action, and writes the results to csv/txt files.

.. note::
   This program is a personal initiative and contribution.
   Although it is designed for managing radios by `Siklu Communications <https://www.siklu.com>`_, no use
   has been made of any company resources, nor any intellectual proprietary nor
   confidential information.

.. toctree::
   :maxdepth: 2
   :caption: Start Here

   quick_start

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   synopsis
   sikcli
   sikcommander
   batchscan
   credentials
   parsers
   



.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
