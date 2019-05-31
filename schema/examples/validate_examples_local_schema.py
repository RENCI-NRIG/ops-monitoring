#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------

# This file is the same as validate_examples.py except that it tries to
# load the schema files local for testing prior to publishing them 
#
#
# Invoke this as:
#   python validate_examples_local_schema.py [/path/to/validictory]

# If you provide a path to validictory, it'll assume that it's not
# installed in your normal python path, and include the path you provide

import os
import subprocess
import sys
import traceback
from pprint import pprint as pprint

if len(sys.argv) > 1:
  sys.path.append(sys.argv[1])

import json
import urllib2
import validictory

def parse_schema(schemaurl):

  try:
    # attempts to open .schema file in parent directory
    local_schema_path = "../" + schemaurl[schemaurl.rfind('/')+1:-1] + ".schema"
    schema = json.load(open(local_schema_path))
  except Exception, e:
    # gets it from the web by the url if not found locally
    schema = json.load(urllib2.urlopen(schemaurl))

  if 'extends' in schema and '$ref' in schema['extends']:
    parent_schema = json.load(urllib2.urlopen(schema['extends']['$ref']))
    while (True): # breaks when no additional extensions
      for key in sorted(parent_schema.keys()):
        if key not in schema:
          schema[key] = parent_schema[key]
        if key == 'properties': # need to merge these keys individually
          for key in sorted(parent_schema['properties'].keys()):
            if key not in schema['properties']:
              schema['properties'][key] = parent_schema['properties'][key]
      if 'extends' in parent_schema:
        parent_schema = json.load(urllib2.urlopen(parent_schema['extends']['$ref']))
      else:
        break; # essentially a do while loop

  return schema

def validate_file(datafile):
  try:
    data = json.load(open(datafile))
    schema = parse_schema(data['$schema'])

    # Manually set to false here
    # not needed if top level schema sets to false
    # with current implementation in parse_schema()
    #schema['additionalProperties'] = False 

    validictory.validate(data, schema)
    print "JSON file %s is valid" % datafile
    #sys.exit(0)
    return True
  except Exception, e:
    print "Received exception %s while trying to validate: %s\n  %s" % (
      str(e), datafile, traceback.format_exc())
    sys.exit(0)
  return False

def find_json_files(dirname):
  p = subprocess.Popen(
    ["find", dirname, "-type", "f", "-name", "*.json"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  [output, errout] = p.communicate()
  if p.returncode == 0:
    return output.split()
  else:
    print "find failed - couldn't look for JSON files"
    sys.exit(1)

for jsonfile in find_json_files('.'):
  validate_file(jsonfile)
