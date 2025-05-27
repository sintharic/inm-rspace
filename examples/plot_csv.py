import os
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



doc = rs.ELN.get_document(13887)
wf = PlotColumnsCSV(doc, '.')
# wf.reset_document()
wf.run()
