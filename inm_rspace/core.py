"""
----------
 Examples
----------

Get all documents in an RSpace Folder or Notebook:
--------------------------------------------------

.. image:: images/RSpace_UV-vis.png
    :alt: Notebook contents.
    :align: center

.. code-block:: python

    import inm_rspace as rs
    docs = rs.get_docs_in_notebook(7074)
    print([doc['name'] for doc in docs])

Output:

.. image:: images/Code_UV-vis.png
    :alt: The generated output.
    :align: center

Create a new RSpace Form from a JSON metadata file:
---------------------------------------------------

.. code-block:: python

    json_content = json.load(open('metadata.json'))
    form_fields = rs.form_fields_from_json(json_content, default=True)
    rs_form = rs.ELN.create_form('inm-rspace_json', fields=form_fields)
    print(f"Created form {rs_form['globalId']}")

For more examples on managing JSON schemas and RSpace Forms, refer to `this script 
<https://github.com/sintharic/inm-rspace/blob/main/examples/manage_forms.py>`_.

-------------------
 API documentation
-------------------

"""

import os
from datetime import datetime
from xml.dom.minidom import parseString as parse_xml
from fnmatch import fnmatch
from rspace_client.eln import eln
from rspace_client.inv import inv

class ELNClass(eln.ELNClient):
  """ELN class enhancing the rspace_client.eln.ELNClient class
  """
  
  def __init__(self):
    return

  def connect(self, url, key):
    # self = eln.ELNClient(url, key)
    eln.ELNClient.__init__(self, url, key)

class InventoryClass(inv.InventoryClient):
  """Inventory class enhancing the rspace_client.inv.InventoryClient class
  """
  def __init__(self):
    return

  def connect(self, url, key):
    inv.InventoryClient.__init__(self, url, key)


ELN = ELNClass()
Inventory = InventoryClass()

try:
  ELN.connect(os.getenv("RSPACE_URL"), os.getenv("RSPACE_API_KEY"))
  Inventory.connect(os.getenv("RSPACE_URL"), os.getenv("RSPACE_API_KEY"))
except:
  pass

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
    try: field_key = fields.index(field_key)
    except ValueError:
      return []
  elif field_key is None:
    files = []
    for ifield in range(len(document['fields'])):
      files += get_files(document, ifield)
    return files
  
  return document['fields'][field_key]['files']
  
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

def field_index(document, field_name):
  """get index of the (first) field from an Rspace document dict with a given name.
  
  Parameters
  ----------
  document : dict
      input document
  field_name : str
      name of the field to be accessed
  
  Returns
  -------
  idx : int
      the index of the field with the given name
  """
  for idx, field in enumerate(document['fields']):
    if field['name']==field_name: return idx
  return -1



def fields_are_compatible(fields1, fields2, subset=False):
    """determine whether two field lists are identical (or one is a subset of the
    other).
    
    Parameters
    ----------
    fields1 : dict
        a list of RSpace field dicts containing at least the keys 'name' and 'type'.
    
    fields2 : dict
        a list of RSpace field dicts containing at least the keys 'name' and 'type'.

    subset : bool
        if `True`, the function only checks whether the fields of <form1> are 
        a subset of the fields in <form2>.
  
    Returns
    -------
    match : bool
        True if both forms are compatible, False otherwise.
    """

    if subset:
        field_names2 = [field['name'] for field in fields2]
        field_types2 = [field['type'] for field in fields2]

        for field1 in fields1:
            try: 
                idx = field_names2.index(field1['name'])
                if field_types2[idx] != field1['type']: return False
            except:
                return False

    else:
        if len(fields1) != len(fields2):
            return False

        for field1, field2 in zip(fields1, fields2):
            # if field1 != field2: return False
            if field1['name'] != field2['name']: return False
            if field1['type'] != field2['type']: return False

    return True


def forms_are_compatible(form1, form2, subset=False):
    """determine whether two forms are identical (or one is a subset of the 
    other).
    
    Parameters
    ----------
    form1 : dict
        an RSpace Form-style dict containing at least the keys 'name' and 'fields'.
    
    form2 : dict
        an RSpace Form-style dict containing at least the keys 'name' and 'fields'.

    subset : bool
        if `True`, the function only checks whether the fields of <form1> are 
        a subset of the fields in <form2>.
  
    Returns
    -------
    match : bool
        True if both forms are compatible, False otherwise.
    """

    if subset:
        return fields_are_compatible(form1['fields'], form2['fields'], subset=True)

    if form1['name'] != form2['name']: 
        return False

    return fields_are_compatible(form1['fields'], form2['fields'], subset=False)



def compare_forms(form1, form2):
    """Deprecated version of forms_are_compatible.
    """
    print('WARNING: compare_forms() is deprecated. Use forms_are_compatible() instead.')
    return forms_are_compatible(form1, form2, subset=False)



def document_fields_from_json(json_dict:dict):
    """Convert a JSON-style dict with key,value pairs into a list of
    RSpace document fields of format `[{'name': <key>, 'content': <value>}, ...]`
    
    Parameters
    ----------
    json_dict : dict
        JSON-style dict
    
    Returns
    -------
    list<dict>
        RSpace document-style list of {'name': ..., 'content': ...} dicts.
    """
    return [{'name': key, 'content': json_dict[key]} for key in json_dict.keys()]



def form_fields_from_json(json_dict:dict, default:bool=False):
    """Convert a JSON-style dict with key,value pairs into a list of
    RSpace Form fields of format `[{'name': <key>, 'type': type(<value>)}, ...]`
    
    Parameters
    ----------
    json_dict : dict
        JSON-style dict

    default : bool
        if `True`, supplied values in the JSON-style dict are considered to be 
        the default in the RSpace Form.
    
    Returns
    -------
    list<dict>
        RSpace Form field list of {'name': ..., 'type': ..., (...)} dicts.
    """
    result = []
    for key in json_dict.keys():
        field = {'name': key}
        value = json_dict[key]
        if isinstance(value, (list, tuple, set)):
            if not len(value): 
                field['type'] = 'Text'
                continue
            field['type'] = 'Choice'
            field['options'] = [str(element) for element in value]
        elif isinstance(value, bool):
            field['type'] = 'Radio'
            field['options'] = ['yes', 'no']
        elif isinstance(value, int):
            field['type'] = 'Number'
            field['decimalPlaces'] = 0
        elif isinstance(value, float):
            field['type'] = 'Number'
            field['decimalPlaces'] = len(f'{value:g}')-len(str(int(value)))
        elif isinstance(value, datetime):
            field['type'] = 'Date'
            value = value.strftime('%Y-%m-%d')
        elif isinstance(value, str):
            try:
                date = datetime.fromisoformat(value)
                value = date.strftime('%Y-%m-%d')
                field['type'] = 'Date'
            except:
                field['type'] = 'String'
        else: 
            field['type'] = 'Text'

        if default:
            if field['type'] == 'Radio':
                if value: field['defaultOption'] = 'yes'
                else: field['defaultOption'] = 'no'
            elif field['type'] == 'Choice':
                field['defaultOptions'] = field['options']
            elif field['type'] in ('Date', 'String', 'Number'):
                field['defaultValue'] = value

        result.append(field)

    return result



def get_form_by_dict(new_form, subset=False):
    """If it exists, return the (first) Rspace Form matching a given 
    RSpace Form definition dict. Otherwise, create this Form and return it.
    
    Parameters
    ----------
    new_form : dict
        a dict corresponding to an RSpace Form definition containing at least 
        the keys 'name' and 'fields'.

    subset : bool
        if `True`, the function only checks whether the fields of <new_form> 
        are a subset of the fields in an existing RSpace Form.
    
    Returns
    -------
    rs_form : dict
        the found/newly created RSpace form. 
    """
    forms = ELN.get_forms()['forms']
    found_form = False
    for form in forms:
        form = ELN.get_form(form['id'])
        if forms_are_compatible(new_form, form, subset=subset):
            return form
    
    rs_form = ELN.create_form(new_form['name'], fields=new_form['fields'])
    print(f"No matching Form found. Publishing new Form: {rs_form['globalId']}")
    ELN.publish_form(rs_form['globalId'])

    return rs_form



def fill_form_fields(meta:dict, form_fields:list, term_map={}, strict=False):
    """Create RSpace Document (list of document fields) from a JSON-style 
    metadata dict and an RSpace Form (list of form fields).
    
    Parameters
    ----------
    meta : dict
        JSON-style metadata dict

    form_fields : list<dict>
        list of Form field dicts of format `{'name': ..., 'type': ..., (...)}`

    term_map : dict
        map between terms in the form and in the metadata

    strict : bool
        If `True`, an error will be raised if the metadata dict contains any
        terms that are present in neither the `form_fields` nor the `term_map`.
        If `False`, only a warning is printed.
    
    Returns
    -------
    list<dict>
        List of RSpace Document fields.
    """

    # sanity checks
    map_terms = list(term_map.values())
    form_terms = [field['name'] for field in form_fields]
    for term in meta.keys():
        if term not in form_terms:
            if term not in map_terms:
                if strict:
                    raise KeyError(f"metadata term '{term}' not in form fields or term_map")
                else:
                    print(f"WARNING: metadata term '{term}' not in form fields or term_map")
    for term in term_map.keys():
        if term not in form_terms:
            raise KeyError(f"map term '{term}' not in form fields")

    # create doc fields
    doc_fields = []
    for field in form_fields:
        value = ''

        # try to fill field with metadata
        if field['name'] in meta.keys():
            value = str(meta[field['name']])
        elif field['name'] in term_map.keys():
            value = meta[term_map[field['name']]]
        if field['type']=='Number':
            try: value = float(value)
            except: value = None
        elif field['type'] in ('String', 'Radio'):
            value = str(value)
        elif field['type']=='Choice':
            if isinstance(value, (list, dict, set)):
                value = [str(val) for val in value]
            else: 
                value = [str(value)]
        
        # otherwise, use default
        elif 'defaultValue' in field.keys(): 
            value = field['defaultValue']
        elif 'defaultValues' in field.keys(): 
            value = field['defaultValues']
        
        doc_fields.append({'name': field['name'], 'content': value})

    return doc_fields