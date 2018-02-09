Usage
======

-  from ``root/contracts``:

.. code:: sh

  # compilation
  populus compile

  # tests
  pytest
  pytest -p no:warnings -s
  pytest tests/test_uraiden.py -p no:warnings -s

  # Recommended for speed:
  # you have to comment lines in tests/conftest.py to use this
  pip install pytest-xdist==1.17.1
  pytest -p no:warnings -s -n NUM_OF_CPUs
