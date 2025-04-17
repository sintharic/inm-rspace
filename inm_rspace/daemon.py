import os, sys
import shutil
from fnmatch import fnmatch
from . import core



SHARED_FOLDER_ID = '1018'

def get_docs_by_form(form_pattern, folder_id):
  """
  scan for Rspace documents in a given folder whose form name matches a pattern
  
  Parameters
  ----------
  form_pattern : str
      glob-style pattern that the form name must match
  folder_id : str
      folderID of the Rspace folder to search for matches

  Returns
  -------
  results : list<RspaceDocument>
      list of documents matching the form name
  """
  records = core.ELN.list_folder_tree(folder_id)
  results = []
  for share in records['records']:
    if share['type']=='NOTEBOOK':
      for page in core.ELN.list_folder_tree(share['id'])['records']:
        doc = core.ELN.get_document(page['id'])
        print(f"- {share['name']}/{doc['name']} ({doc['form']['name']})")
        form_name = doc['form']['name']
        if fnmatch(form_name, form_pattern): results.append(doc)
    else:
      doc = core.ELN.get_document(share['id'])
      print(f"- {doc['name']} ({doc['form']['name']})")
      form_name = doc['form']['name']
      if fnmatch(form_name, form_pattern): results.append(doc)

  return results


def get_requests(shared_folder_id):
  """get all shared documents requesting a workflow to be performed
  
  Parameters
  ----------
  shared_folder_id : str
      folderId of the "Shared" Folder in Rspace
  
  Returns
  -------
  result : list<RspaceDocument>
      list of shared Rspace documents using a `Request:*` form
  """
  user_folders = core.ELN.list_folder_tree(shared_folder_id)
  result = []
  for folder in user_folders['records']:
    print(f"{folder['name']}:")
    result += get_docs_by_form('Request:*', folder['id'])
    print()

  return result

def get_field(document, field_name):
  """get (the first) field from an Rspace document with a given name.
  
  Parameters
  ----------
  document : RspaceDocument
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



def update_document(document, info='', files=[]):
  """update a request documents
  
  Parameters
  ----------
  document : RspaceDocument
      the request document to be updates
  info : str, optional
      info to be written to the "Output Data" text field (e.g. error messages)
  files : list, optional
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
requests = [core.ELN.get_document('12640')]
print(f'Processing {len(requests)} new requests...')

sys.path.append('..')#TEMP
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
