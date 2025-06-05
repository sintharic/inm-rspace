import os, json
import inm_rspace as rs
import pandas as pd
import matplotlib.pyplot as plt


class PlotColumnsCSV(rs.workflow.Workflow):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.define()

  def define(self):
    self.expected['input_files'] = ['*.csv']
    self.expected['output_files'] = ['*.png']
    self.expected['kwargs'] = {'x': 1, 'y': 2}
    self.description = """Plots two columns from a CSV file as x and y in a plot."""

  def workflow(self, **kwargs):
    data = pd.read_csv(self.input_files[0])
    data.plot(**self.kwargs)
    filename = f"{self.directory}{os.sep}plot.png"
    plt.savefig(filename)
    self.output_files.append(filename)


# the RSpace Form to be used for the workflow
wf_form = json.load(open('default_workflow_form.json','r'))
wf_form['fields'].append({'type': 'String', 'name': 'Note', 'defaultValue': 'auto generated.'})
form = rs.get_form_by_dict(wf_form)

# create a document requesting this workflow to be performed on the uploaded file
file = rs.ELN.upload_file(open('data.csv', 'rb'))
doc = rs.ELN.create_document('PlotColumnsCSV_Test', form_id=form['id'])
fields = doc['fields']
# specify the file
idx = rs.field_index(doc, 'Input Data')
fields[idx]['content'] = rs.html_ref(file)
# specify optional arguments
idx = rs.field_index(doc, 'Arguments (JSON)')
fields[idx]['content'] = '"x": 1, "y": 3'
doc = rs.ELN.update_document(doc['id'], fields=fields)

# set up and run the workflow
wf = PlotColumnsCSV(doc, '.')
wf.run()
