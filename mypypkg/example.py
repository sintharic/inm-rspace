"""
---------
 Example
---------

Print a string

.. code-block:: python

    e = print_this('hello')

Output:

.. image:: images/output.png
    :alt: The generated output.
    :align: center

-------------------
 API documentation
-------------------

"""

def print_this(thing):
  """ 
    prints the input.

    Parameters
    ----------
    thing : whatever
      what you want to print.

    Returns
    -------
    code: int
      error code

    Warning
    -------
    Purely instructional!
  """

  code = 0

  try: print(thing)
  except: code = 1

  return code