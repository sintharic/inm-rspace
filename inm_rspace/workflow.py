"""
----------
 Examples
----------

A fully outomated workflow that takes RSpace documents with attached CSV files and plots them:

The Input fields in the RSpace document look like this:

.. image:: images/Input_PlotColumnsCSV.png
    :alt: Notebook Inputs.
    :align: center


The automatically generated Output field looks like this:

.. image:: images/Output_PlotColumnsCSV.png
    :alt: Automatically generated Notebook Output.
    :align: center

The code for this example can be found `here <https://github.com/sintharic/inm-rspace/tree/main/examples>`_.

-------------------
 API documentation
-------------------

"""

import os, sys
import shutil
import traceback
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch
from . import core



SHARED_FOLDER_ID = '1018'
HOME = str(Path.home())
ERROR_CODE = {
  "SUCCESS": 0,
  "ALREADY_COMPLETED": 1,
  "WRONG_FORM": 2,
  "WRONG_WORKFLOW": 3,
  "WRONG_FILES": 4,
  "WRONG_KWARGS": 5,
  "FAILED_DOWNLOAD": 6,
  "FAILED_UPLOAD": 7,
  "FAILED_WORKFLOW": 8
}
ERROR_NAME = {v: k for k, v in ERROR_CODE.items()}



def get_file_paths(field):
  """Not yet working!
  """
  
  files = []
  lines = field['content'].split('\n')
  xml = core.parse_xml(field['content'])
  paragraphs = xml.getElementsByTagName('p')
  paragraphs = [str(p) for p in paragraphs]
  for paragraph in paragraphs:
    print(paragraph)
    if os.path.isfile(paragraph): files.append(paragraph)

  return files


class Workflow:
  def __init__(self, document: dict, path=HOME):
    self.name = str(self.__class__.mro()[0]).split('.')[-1][:-2]
    self.document = document
    self.directory = f"{path}{os.sep}{self.name}{os.sep}{self.document['globalId']}_{self.document['name']}"
    self.time_signature = ''

    self.expected = dict()
    self.field_name = {'input': 'Unknown', 'output': 'Unknown', 'workflow': 'Unknown', 'kwargs': 'Unknown', 'completed': 'Unknown'}

    self.description = ''
    self.define()

    self.init_members()

  def define(self):
    """Define the properties of the Workflow.

    This function should be redefined for every subclass of Workflow.
    """
    self.field_name['workflow'] = 'Workflow'
    self.field_name['completed'] = 'Completed'

    self.expected['input'] = {'*': -1}
    self.field_name['input'] = 'Input Data'
    
    self.expected['output'] = ['*.txt']
    self.field_name['output'] = 'Output Data'
    
    self.expected['kwargs'] = []
    self.field_name['kwargs'] = 'Arguments (JSON)'
    
    self.description = ''

  def init_members(self):
    self.time_signature = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    self.info = f"Workflow '{self.name}' initialized from {self.document['globalId']} on {self.time_signature}.\n"
    self.code = 0
    self.traceback = ''
    self.kwargs = dict()
    self.input_files = []
    self.output_files = []

  def prepare(self):
    """Prepare for workflow execution: 

- check if request has already been completed
- check if the requested workflow matches this one
- create a working directory for the workflow
- try to download files from the request
    """
    self.init_members()

    self.check_completed()
    if self.code: return
    
    os.makedirs(self.directory, exist_ok=True)

    self.check_workflow()
    if self.code: return
    
    self.get_args()
    self.get_input_files()
  
  def check_completed(self):
    """Check if the requested workflow has already been completed.
    """
    try: completed = core.get_field(self.document, self.field_name['completed'])['content']
    except KeyError:
      self.code = ERROR_CODE['WRONG_FORM']
      return

    if completed != 'no': 
      self.code = ERROR_CODE['ALREADY_COMPLETED']

  def check_workflow(self):
    """Check if the requested workflow matches this one.
    """
    if self.field_name['workflow'] is None: return

    try: workflow = core.get_field(self.document, self.field_name['workflow'])['content']
    except KeyError:
      self.code = ERROR_CODE['WRONG_FORM']
      return

    if workflow!=self.name: 
      self.code = ERROR_CODE['WRONG_WORKFLOW']

  def get_args(self):
    """Read the keyword arguments from the kwargs field of the Rspace document.
    """
    # if len(self.expected['kwargs']) == 0: return
    if self.field_name['kwargs'] is None: return

    try: kwargs = core.get_field(self.document, self.field_name['kwargs'])['content']
    except KeyError:
      self.code = ERROR_CODE['WRONG_FORM']
      return

    if not isinstance(kwargs, str):
      self.kwargs = dict()
      return
    
    kwargs = kwargs.lstrip(' ')
    kwargs = kwargs.rstrip(' ')
    print('DEBUG', kwargs)#DEBUG
    if kwargs=='':
      self.kwargs = dict()
      return
    if kwargs[0]!='{': kwargs = '{'+kwargs
    if kwargs[-1]!='}': kwargs = kwargs+'}'

    try: self.kwargs = dict(eval(kwargs))
    except:
      self.traceback += traceback.format_exc()
      self.code = ERROR_CODE['WRONG_KWARGS']

  def check_args(self, fun):
    if len(self.kwargs)==0: return
    try:
      kwdefaults = fun.__kwdefaults__
      for key in self.kwargs.keys():
        if key not in kwdefaults.keys():
          raise KeyError(f"Specified keyword '{key}' not in kwargs of function '{fun.__name__}': {kwdefaults}")
    except:
      self.code = ERROR_CODE['WRONG_KWARGS']
      self.traceback += traceback.format_exc()


  def get_input_files(self):
    """Check if all expected input files have been provided in the request. 
    If yes, download them.
    """
    files_found = core.get_files(self.document, self.field_name['input'])
    files_matched = {pattern: [] for pattern in self.expected['input'].keys()}
    for file in files_found:
      for pattern in self.expected['input'].keys():
        if fnmatch(file['name'], pattern): files_matched[pattern].append(file)

    for pattern,files in files_matched.items():
      num = self.expected['input'][pattern]
      if (num > 0) and (len(files) != num):
        self.code = ERROR_CODE['WRONG_FILES']
        return
      
      self.download_files(files)

  def download_files(self, files):
    """Download files from the Rspace Gallery into this workflow's working directory.
    
    Parameters
    ----------
    files : list<dict>
        List of Rspace file objects
    """
    for file in files:
      filepath = f"{self.directory}{os.sep}{file['name']}"
      try: core.ELN.download_file(file['id'], filepath)
      except: 
        self.traceback += traceback.format_exc()
        self.code = ERROR_CODE['FAILED_DOWNLOAD']
        return
      self.input_files.append(filepath)

  def workflow(self):
    """The actual workflow to be executed
    """
    if not self.code: 
      self.info += f"Successfully downloaded files: {[file['name'] for file in self.input_files]}\n"
    filepath = f"{self.directory}{os.sep}result.txt"
    with open(filepath, 'w') as fid:
      fid.write('Dummy result of base Workflow class.')
    self.output_files.append(filepath)

  def summary(self):
    """Summarize the success of the workflow based on generated error codes.
    """
    msg = f'Exit with the error code {self.code}: '
    if ERROR_NAME[self.code] == 'ALREADY_COMPLETED':
      msg += 'Request already completed. Nothing to be done.'
    elif ERROR_NAME[self.code] == 'WRONG_WORKFLOW':
      msg += 'Requested workflow does not match.\n'
      workflow = core.get_field(self.document, self.field_name['workflow'])['content']
      msg += f"Initialized workflow is '{self.name}' with workflow field '{self.field_name['workflow']}', but {self.document['globalId']} requests '{workflow}'."
    elif ERROR_NAME[self.code] == 'WRONG_FORM':
      msg += 'RSpace document\'s form does not match.\n'
      form = self.document['form']
      docID = self.document['globalId']
      fields = [field for field in self.field_name.values() if field is not None]
      msg += f"Document '{docID}' was created from Form '{form['name']}' ({form['globalId']}), "
      msg += f"Workflow '{self.name}' expects Form with fields {fields}."
    elif ERROR_NAME[self.code] == 'WRONG_FILES':
      msg += 'Supplied files do not match.\n'
      msg += f"Workflow '{self.name}' expects the following files:"
      for pattern,num in self.expected['input'].items():
        msg += f"\n- {num} files matching pattern '{pattern}'"
    elif ERROR_NAME[self.code] == 'WRONG_KWARGS':
      msg += f"Supplied field {self.field_name['kwargs']} is wrong: '{core.get_field(self.document, self.field_name['kwargs'])['content']}'\n"
      msg += f"Workflow '{self.name}' supports the following kwargs: {self.expected['kwargs']}\n"
      msg += 'There may be an traceback attached to this field with more info.'
    elif ERROR_NAME[self.code] == 'FAILED_DOWNLOAD':
      msg += 'Unable to download files.\n'
      msg += 'Check the attached traceback for more info.'
    elif ERROR_NAME[self.code] == 'FAILED_WORKFLOW':
      msg += 'Error while executing the workflow itself.\n'
      msg += 'Check the attached traceback for more info.'
    elif ERROR_NAME[self.code] == 'FAILED_UPLOAD':
      msg += 'Unable to upload files.\n'
      msg += f'A full traceback of the error has been saved in {self.directory}.'
    else: 
      msg = 'Completed without errors.'

    return msg

  def update_document(self):
    """Update the request document with the results of the workflow.
    """

    if self.traceback != '':
      filepath = f"{self.directory}{os.sep}error_traceback.txt"
      with open(filepath, 'w') as fid:
        fid.write(self.traceback)
      self.output_files.append(filepath)

    # upload result files
    uploads = []
    for file in self.output_files:
      try: 
        file_obj = core.ELN.upload_file(open(file, 'rb'))
        uploads.append(file_obj)
      except:
        self.traceback += traceback.format_exc()
        self.code = ERROR_CODE['FAILED_UPLOAD']

    self.info += self.summary()
    print(self.info)

    # link result files to document
    fields = self.document['fields']
    # print([f['name'] for f in core.ELN.get_form(self.document['form']['id'])['fields']])#DEBUG
    # print([f['name'] for f in fields])#DEBUG
    for i in range(len(fields)):
      if self.field_name['completed'] is not None and (fields[i]['name']==self.field_name['completed']) and not self.code:
        fields[i]['content'] = 'yes'
      elif fields[i]['name']==self.field_name['output']:
        if self.code == ERROR_CODE['ALREADY_COMPLETED']: 
          fields[i]['content'] += '<p>'+self.info.replace('\n', '<br/>')+'</p>'
          continue
        else:
          fields[i]['content'] = '<p>'+self.info.replace('\n', '<br/>')+'</p>'
        for upload in uploads:
          fields[i]['content'] += f"<br/>{core.html_ref(upload)}"

    # update document
    # if self.code: return
    # print([f['name'] for f in fields])#DEBUG
    core.ELN.update_document(self.document['id'], fields=fields)

  def reset_document(self):
    """Reset the request document to an empty 'output' field and 'completed' field 'no'.
    """

    fields = self.document['fields']
    for i in range(len(fields)):
      if fields[i]['name']==self.field_name['completed'] and fields[i]['content'] == 'yes':
        fields[i]['content'] = 'no'
      elif fields[i]['name']==self.field_name['output']:
        fields[i]['content'] = ''

    core.ELN.update_document(self.document['id'], fields=fields)
    print(f"Reset Rspace document {self.document['id']}")

  def run(self):
    """Run the entire Workflow.

    This function should be redefined for every subclass of Workflow.
    """

    self.prepare()
    if not self.code:
      try: self.workflow()
      except:
        self.code = ERROR_CODE['FAILED_WORKFLOW']
        self.traceback += traceback.format_exc()
    self.update_document()
    