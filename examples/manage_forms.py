import json
import inm_rspace as rs

# Create RSpace Form from exact Form definition
form_basics = json.load(open('form_basics.json','r'))
rs_form_basics = rs.ELN.create_form(form_basics['name'], fields=form_basics['fields'])
print(f"Created form {rs_form_basics['globalId']}")

# Retrieve the previous RSpace Form by matching the exact Form definition
retrieved_form_basics = rs.get_form_by_dict(form_basics)
print(f"Retrieved form {retrieved_form_basics['globalId']}\n")

# Create RSpace Form from convenvional JSON metadata file
json_content = json.load(open('metadata.json'))
form_fields = rs.form_fields_from_json(json_content)
rs_form_json = rs.ELN.create_form('inm-rspace_json', fields=form_fields)
print(f"Created form {rs_form_json['globalId']}\n")

# Create RSpace Form from convenvional JSON metadata file (with default values)
json_content = json.load(open('metadata.json'))
form_fields_w_defaults = rs.form_fields_from_json(json_content, default=True)
rs_form_json_w_defaults = rs.ELN.create_form('inm-rspace_json_w_defaults', fields=form_fields_w_defaults)
print(f"Created form {rs_form_json_w_defaults['globalId']}")

# Retrieve the previous RSpace Form by matching a subset of its fields
form_w_defaults = {'name': 'inm-rspace_json_w_defaults', 'fields': form_fields_w_defaults[:-1]}
retrieved_form_json_w_defaults = rs.get_form_by_dict(rs_form_json_w_defaults, subset=True)

print(f"Retrieved form {retrieved_form_json_w_defaults['globalId']}")



"""
TESTING

This json file contains valid field types according to official documentation
(https://community.researchspace.com/public/apiDocs).
Creating the form creates no error, but using it in the RSpace GUI does. 
Do not use this unless you know what you are doing!
"""

# form_extras = json.load(open('form_extras.json','r'))
# form1 = rs.ELN.create_form(form_extras['name'], fields=form_extras['fields'])
# print(f"Created form {form1['globalId']}")
