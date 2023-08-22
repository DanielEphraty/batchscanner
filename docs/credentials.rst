Credentials: login details
=============================

``credentials.py`` implements two classes for managing radio login credentials:

 * :class:`~batchscanner.credentials.Credential` representing a single set of credentials
   (IP address, username, password).
 * :class:`~batchscanner.credentials.Credentials` representing a sequence of
   (one or more) :class:`~batchscanner.credentials.Credential`.


Usage Examples:
----------------------

.. code-block::
   :caption: Contents of 'list_ip_addresses.txt'
   
   username = admin
   password = adminpassw
   192.168.0.0/28
 
.. code-block:: 
   :caption: Code example
   
   >>> from batchscanner.credentials import Credentials
   >>> creds = Credentials(filename='list_ip_addresses.txt')
   >>> for batch in creds.get_batches(5):
           print(batch)
   Reading credentials from 'list_ip_addresses.txt'
   Read a total of 14 credentials
   5 Credentials: from 192.168.0.1 to 192.168.0.5
   5 Credentials: from 192.168.0.6 to 192.168.0.10
   4 Credentials: from 192.168.0.11 to 192.168.0.14
   
   >>> print(batch[-1])
   Credential(192.168.0.14, admin, adminpassw)


Class Information:
------------------

.. autoclass:: batchscanner.credentials.Credentials

.. autoclass:: batchscanner.credentials.Credential



