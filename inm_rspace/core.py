"""
----------
 Examples
----------

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

import os
from xml.dom.minidom import parseString as parse_xml
from fnmatch import fnmatch
from rspace_client.eln import eln
from rspace_client.inv import inv

class ELNDummy:
  """Dummy ELN object for testing
  """
  
  def __init__(self):
    return
  
  def list_folder_tree(*args):
    return {'records': []}
  
  def get_document(*args):
    return {'name': '', 'form': dict()}

  def get_folder(*args):
    return {'name': ''}

try:
  ELN = eln.ELNClient(os.getenv("RSPACE_URL"), os.getenv("RSPACE_API_KEY"))
  Inventory = inv.InventoryClient(os.getenv("RSPACE_URL"), os.getenv("RSPACE_API_KEY"))
except:
  ELN = ELNDummy()
  Inventory = ELNDummy()

replace = {' ': '_', ',': '.', '<p>': '', '</p>': ''}



def html_ref(rspace_obj):
  """html string to reference an Rspace object
  
  Parameters
  ----------
  rspace_obj : file or document
      Rspace object
  
  Returns
  -------
  string : str
      string that can be inserted in an html string to reference the given object.
  
  Raises
  ------
  ValueError
      raised if the rspace object type is not recognized
  """
  link = rspace_obj['_links'][0]['link']
  obj_loc = link.split('/')[-2]
  if obj_loc=='documents':
    id_str = 'docId'
  elif obj_loc=='files':
    id_str = 'fileId'
  else: 
    raise ValueError(f'Unknown rspace object type: {obj_loc}')
  
  return f"<{id_str}={rspace_obj['id']}>"

def get_line(string, index):
  idx_beg = idx_end = index
  while string[idx_beg]!='\n': idx_beg -= 1
  while string[idx_end]!='\n': idx_end += 1

  return string[(idx_beg+1):idx_end]



def tables_from_xml(xml_string, file, delimiter=',', replace=replace):
  """
  extract all tabular data from an xml string and save it as a csv file.
  
  Parameters
  ----------
  xml_string : str
      input xml string
  file : str
      file path to use, although an appendix is going to be inserted 
      to enumerate multiple tables in the xml string.
  delimiter : str, optional
      field delimiter to be used in the csv file
  replace : dict, optional
      key,value pairs indicating strings (keys) to be replaced with their corresponding value.
  
  Returns
  -------
  files : list<str>
      List of files exported.
  """

  num = 0 # used to name file exports
  stub, ext = os.path.splitext(file)
  if ext=='': ext = '.csv'

  files = []
  while True:
    # any table is delimited by the tag 'tbody'
    idx_tab_beg = xml_string.find('<tbody')
    if idx_tab_beg < 0: break
    idx_tab_end = xml_string.find('</tbody>')+8

    # some replacements are necessary for successful parsing
    table_str = xml_string[idx_tab_beg:idx_tab_end]
    table_str = table_str.replace('\n','')
    table_str = table_str.replace('""','\'')
    table_str = table_str.replace('&nbsp;',' ')

    # parse table and save as rows, as indicated by the tag 'tr'
    table_xml = parse_xml(table_str)
    rows = table_xml.getElementsByTagName('tr')
    
    # write the detected table to a file
    num += 1
    outfile = f'{stub}_{str(num).zfill(2)}{ext}'
    files.append(outfile)
    with open(outfile,'w') as fid:
      for row in rows:
        for element in row.getElementsByTagName('td'):
          try: 
            # cells containing text with formatting of tag 'span'
            sub_elements = element.getElementsByTagName('span')
            value = sub_elements[0].firstChild.nodeValue
          except: 
            try:
              # cells containing text with formatting of tag 'p'
              sub_elements = element.getElementsByTagName('p')
              value = sub_elements[0].firstChild.nodeValue
            except:
              # cells containing unformatted text
              value = element.firstChild.nodeValue

          value = str(value)
          for char in replace.keys():
            value = value.replace(char, replace[char])

          fid.write(value+delimiter)
        fid.write('\n')

    # remove the processed part from the xml_string before the next iteration
    xml_string = xml_string[idx_tab_end:]

  return files



def get_files(document, field_key=None):
  """list files attached to (a field in) an Rspace document
  
  Parameters
  ----------
  document : RspaceDocument
      input document
  field_key : int or str, optional
      name of the field, from which files are extracted. 
      If None, files from all fields are listed.
  
  Returns
  -------
  files : list<tuple<str,str>>
      files found as globalId,filename-pairs.
  """
  if isinstance(field_key, str): 
    fields = [f['name'] for f in document['fields']]
    field_key = fields.index(field_key)
  elif field_key is None:
    files = []
    for ifield in range(len(document['fields'])):
      files += get_files(document, ifield)
    return files
  
  return document['fields'][field_key]['files']
  # return [(file['globalId'], file['name']) for file in document['fields'][field_key]['files']]
  # try: 
  #   return [file['globalId'] for file in document['fields'][field_key]['files']]
  # except: 
  #   return []

def get_docs_in_notebook(notebook_id, form_pattern=None, verbose=False):
  """
  scan for Rspace documents in a given folder whose form name matches a pattern
  
  Parameters
  ----------
  notebook_id : str
      notebookID of the Rspace notebook to search for matches
  form_pattern : str
      glob-style pattern that the form name must match

  Returns
  -------
  results : list<dict>
      list of documents matching the form name
  """

  results = []
  records = ELN.list_folder_tree(notebook_id)
  nb_name = ELN.get_folder(notebook_id)['name']
  for page in records['records']:
    doc = ELN.get_document(page['id'])
    print(f"- {nb_name}/{doc['name']} ({doc['form']['name']})")
    if form_pattern is None: 
      results.append(doc)
      continue
    form_name = doc['form']['name']
    if fnmatch(form_name, form_pattern): results.append(doc)

  return results

def get_docs_in_folder(folder_id, form_pattern=None, verbose=False):
  """
  scan for Rspace documents in a given folder whose form name matches a pattern
  
  Parameters
  ----------
  folder_id : str
      folderID of the Rspace folder to search for matches
  form_pattern : str
      glob-style pattern that the form name must match

  Returns
  -------
  results : list<dict>
      list of documents matching the form name
  """
  records = ELN.list_folder_tree(folder_id)
  results = []
  for share in records['records']:
    if share['type']=='NOTEBOOK':
      results += get_docs_in_notebook(share['id'], form_pattern=form_pattern, verbose=verbose)
      continue
    
    doc = ELN.get_document(share['id'])
    if verbose: print(f"- {doc['name']} ({doc['form']['name']})")
    if form_pattern is None: 
      results.append(doc)
      continue
    form_name = doc['form']['name']
    if fnmatch(form_name, form_pattern): results.append(doc)

  return results


def get_requests(shared_folder_id, verbose=False):
  """get all shared documents requesting a workflow to be performed
  
  Parameters
  ----------
  shared_folder_id : str
      folderId of the "Shared" Folder in Rspace
  
  Returns
  -------
  results : list<dict>
      list of shared Rspace documents using a `Request:*` form
  """
  user_folders = ELN.list_folder_tree(shared_folder_id)
  results = []
  for folder in user_folders['records']:
    if verbose: print(f"{folder['name']} ({folder['id']}):")
    results += get_docs_in_folder(folder['id'], 'Request:*', verbose=verbose)
    if verbose: print()

  return results

def get_field(document, field_name):
  """get (the first) field from an Rspace document dict with a given name.
  
  Parameters
  ----------
  document : dict
      input document
  field_name : str
      name of the field to be accessed
  
  Returns
  -------
  field : dict
      field with the given name
  """
  for field in document['fields']:
    if field['name']==field_name: return field
  return {}