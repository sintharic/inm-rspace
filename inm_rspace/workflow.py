import os, sys
import shutil
import traceback
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch
from . import core



SHARED_FOLDER_ID = '1018'
HOME = str(Path.home())


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
    self.expected = dict()
    self.expected['input_files'] = ['*']
    self.expected['output_files'] = ['*.txt']
    self.directory = f"{path}{os.sep}{self.name}{os.sep}{self.document['globalId']}_{self.document['name']}"
    
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    self.info = f'Workflow \'{self.name}\' initiated {date}.\n'
    self.code = 0
    self.traceback = ''
    self.input_files = []
    self.output_files = []

  def prepare(self):
    """Prepare for workflow execution: 
    - check if request has already been completed
    - check if the requested workflow matches this one
    - create a working directory for the workflow
    - try to download files from the request
    """
    self.check_completed()
    if self.code: return
    
    os.makedirs(self.directory, exist_ok=True)

    self.check_workflow()
    if self.code: return
    
    self.get_input_files()
  
  def check_completed(self):
    """Check if the requested workflow has already been completed.
    """
    completed = core.get_field(self.document, 'Completed')['content']
    if completed != 'no': 
      self.code = 1

  def check_workflow(self):
    """Check if the requested workflow matches this one.
    """
    workflow = core.get_field(self.document, 'Workflow')['content']
    if workflow!=self.name: 
      self.code = 2

  def get_input_files(self):
    """Check if all expected input files have been provided in the request. 
    If yes, download them.
    """
    files_found = core.get_files(self.document, 'Input Data')
    files_matched = [{'name': '__missing__'}]*len(self.expected['input_files'])
    for ifile, file_pattern in enumerate(self.expected['input_files']):
      for file in files_found:
        if fnmatch(file['name'], file_pattern): files_matched[ifile] = file

    for file in files_matched:
      if file['name']=='__missing__': 
        self.code = 3
        return

    self.download_files(files_matched)

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
        self.traceback = traceback.format_exc()
        self.code = 4
        return
      self.input_files.append(filepath)

  def workflow(self):
    """The actual workflow to be executed
    """
    filepath = f"{self.directory}{os.sep}result.txt"
    with open(filepath, 'w') as fid:
      fid.write('Dummy result of base Workflow class.')
    self.output_files.append(filepath)

  def summary(self):
    """Summarize the success of the workflow based on generated error codes.
    """
    if self.traceback != '':
      filepath = f"{self.directory}{os.sep}error_traceback.txt"
      with open(filepath, 'w') as fid:
        fid.write(self.traceback)
      self.output_files.append(filepath)

    msg = f'Exit with the error code {self.code}: '
    if self.code == 1:
      msg += 'Request already completed. Nothing to be done.'
    elif self.code == 2:
      msg += 'Requested workflow does not match.\n'
      workflow = core.get_field(self.document, 'Workflow')['content']
      msg += f"Initialized workflow is '{self.name}', but {self.document['globalId']} requests '{workflow}'."
    elif self.code == 3:
      msg += 'Supplied files do not match.\n'
      msg += f"Workflow '{self.name}' expects the following files: {self.expected['input_files']}"
    elif self.code == 4:
      msg += 'Unable to download files.\n'
      msg += 'Check the attached traceback for more info.'
    elif self.code == 5:
      msg += 'Error while executing the workflow itself.\n'
      msg += 'Check the attached traceback for more info.'
    elif self.code == 6:
      msg += 'Unable to upload files.\n'
      msg += f'A full traceback of the error has been saved in {self.directory}.'
    else: 
      msg = 'Completed without errors.'

    return msg

  def update_document(self):
    """Update the request document with the results of the workflow.
    """
    # upload result files
    uploads = []
    for file in self.output_files:
      try: 
        file_obj = core.ELN.upload_file(open(file, 'rb'))
        uploads.append(file_obj)
      except:
        self.traceback = traceback.format_exc()
        self.code = 6

    self.info += self.summary()
    print(self.info)

    # link result files to document
    fields = self.document['fields']
    for i in range(len(fields)):
      if fields[i]['name']=='Completed' and not self.code:
        fields[i]['content'] = 'yes'
      elif fields[i]['name']=='Output Data':
        fields[i]['content'] = self.info.replace('\n', '<br/>')
        for upload in uploads:
          fields[i]['content'] += f"<br/>{core.html_ref(upload)}"

    # update document
    if self.code: return
    core.ELN.update_document(self.document['id'], fields=fields)

  def run(self):
    """Run the entire workflow.
    """
    self.prepare()
    if not self.code:
      try: self.workflow()
      except: self.code = 5
    self.update_document()
    