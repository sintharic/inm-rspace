import os, sys
import shutil
from fnmatch import fnmatch
from . import core



SHARED_FOLDER_ID = '1018'


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
  def __init__(self, document: dict):
    self.document = document
    self.expected = dict()
    self.expected['name'] = str(self.__class__.mro()[0]).split('.')[-1]
    self.expected['input_files'] = ['*']
    self.expected['output_data'] = [str]

  def check(self):
    workflow = core.get_field(self.document, 'workflow')
    if workflow!=self.expected['name']:
      raise ValueError(f"initialized workflow '{self.expected['name']}', but {self.document['globalId']} requests '{workflow}'.")

  def run(self):
    input_files = core.get_files(self.document, 'Input Data')
    file_objects = []
    for file in input_files:
      pass
    self.info = 'Read'





def update_document(document, info='', files=[]):
  """update a request documents
  
  Parameters
  ----------
  document : dict
      the request document to be updates
  info : str, optional
      info to be written to the "Output Data" text field (e.g. error messages)
  files : list<str>, optional
      list of files to append to the "Output Data" field
  """

  # upload result files
  uploads = []
  for file in files:
    file_obj = core.ELN.upload_file(open(file, 'rb'))
    uploads.append(file_obj)

  # link result files to document
  fields = document['fields']
  for i in range(len(fields)):
    if fields[i]['name']=='Completed':
      fields[i]['content'] = 'yes'
    elif fields[i]['name']=='Output Data':
      fields[i]['content'] = info
      for upload in uploads:
        fields[i]['content'] += f"<br/>{core.html_ref(upload)}"
  
  # update document
  core.ELN.update_document(document['id'], fields=fields)



# requests = get_requests()
# requests = [core.ELN.get_document('12640')]
# print(f'Processing {len(requests)} new requests...')

# sys.path.append('..')#TEMP



# import create_doe

# for doc in requests:
#   completed = get_field(doc, 'Completed')['content']
#   if completed != 'no': continue

#   info = ''
#   output_files = []

#   try:
#     workflow = get_field(doc, 'Workflow')['content']
#     print(workflow)

#     folder = f"rspace_processing{os.sep}{doc['name']}"
#     os.makedirs(folder, exist_ok=True)
#     input_attachments = core.get_files(doc, 'Input Data')
#     print(input_attachments)
#     input_files = []  
#     for file in input_attachments:
#       filepath = f"{folder}{os.sep}{file[1]}"
#       input_files.append(filepath)
#       core.ELN.download_file(file[0], filepath)

#     if workflow!='create_SiHy_doe': #TEMP
#       raise ValueError(f"Workflow '{workflow}' not supported.")
#     output_files = create_doe.run(*input_files)
#     output_files = list(output_files)

#     for i,file in enumerate(output_files):
#       new_file = f"{folder}{os.sep}{os.path.split(file)[-1]}"
#       shutil.move(file, new_file)
#       output_files[i] = new_file
#   except Exception as e:
#     info = e.__repr__()

#   update_document(doc, info=info, files=output_files)
