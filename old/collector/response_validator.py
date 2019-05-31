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

'''
This contains a set of functions for checking the validity of a response
as compared to json-schema.

'''

import json
import urllib2
import traceback

def parse_schema(schemaurl):

  try:
    schema = json.load(urllib2.urlopen(schemaurl))
  except Exception, e:
      print e, schemaurl
      return None

  if 'extends' in schema and '$ref' in schema['extends']:

    parent_schema = json.load(urllib2.urlopen(schema['extends']['$ref']))
    while (True): # exits loop when no additional extensions (break below)
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
        break; # essentially a do while loop (exit condition)

  return schema


def validate(json_resp, schema, validictory_path):

    # assumes /extern/valedictory exists (see /cm for instructions)
    import sys
    sys.path.append(validictory_path)
    import validictory

    try:
        validictory.validate(json_resp, schema)
        print "JSON is valid" 
        return True
    except Exception, e:
        print "Received exception %s while trying to validate: %s\n  %s" % (
            str(e), json_resp, traceback.format_exc())
        return False
