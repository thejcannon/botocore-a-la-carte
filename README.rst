``botocore-a-la-carte``
-----------------------

``botocore-a-la-carte`` is a re-packaging of ``botocore`` such that each service's data JSON exists in a
separate package, and are opted-into through package extras.

The package ``botocore-a-la-carte`` contains the base code/resources for ``botocore`` to operate, and has
a package extra per service (referencing a package which contains just the JSON data for that service).

Installation and Usage
----------------------

⚠️ The package extras must be installed in the same directory as this package (such as in a virtual environment).
This package does not support being installed in separate locations pointed to by ``sys.path``.
This is a limitation of the core ``botocore`` package and the Python packaging ecosystem. ⚠️

Example:

``botocore-a-la-carte`` with no extras allows you to use core ``botocore`` functionality
(e.g. load credentials, sign requests, etc...).

.. code-block:: console

    $ pip install botocore-a-la-carte
    ...
    $ python
    >>> import botocore
    ...

If you require specific service support, specify the service name as an extra:

.. code-block:: console

    $ pip install botocore-a-la-carte[s3, ec2]
    ...
    $ python
    >>> import botocore.session
    >>> session = botocore.session.get_session()
    >>> client = session.create_client('ec2')
    >>> print(client.describe_instances())

