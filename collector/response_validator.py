#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
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

import sys
import json
import urllib2
import traceback


def parse_schema(schemaurl, schema_dir=None):
    """
    Convert a JSON schema into a python dict representation suitable for
    use by validictory.

    :param schemaurl: URL of the schema to convert
    :param schema_dir: if None, the schema to convert is fetched from
      schemaurl.  If not None, it is used as a directory name on the
      local machine from which to retrieve the schema.  In this case
      the schema name is extracted from schemaurl to form the complete
      filename.
    :return: the python dict representation of the schema, or None if
      there was an error in the conversion.
    """
    if schema_dir:
        try:
            # attempts to open .schema file in directory schema_dir
            local_schema_path = schema_dir + "/" + \
                schemaurl[schemaurl.rfind('/') + 1:-1] + ".schema"
            print "Looking for schema in file %s" % (local_schema_path)
            schema = json.load(open(local_schema_path))
        except Exception as e:
            print "Couldn't load schema %s from file %s\n%s" % (
                schemaurl, schema_dir, str(e))
            return None
    else:
        # load the schema directly from schemaurl, i.e., from the web
        try:
            schema = json.load(urllib2.urlopen(schemaurl))
        except Exception as e:
            print "Couldn't load schema %s\n%s" % (schemaurl, str(e))
            return None

    if 'extends' in schema and '$ref' in schema['extends']:

        parent_schema = json.load(urllib2.urlopen(schema['extends']['$ref']))
        while (True):  # exits loop when no additional extensions (break below)
            for key in sorted(parent_schema.keys()):
                if key not in schema:
                    schema[key] = parent_schema[key]
                # need to merge these keys individually
                if key == 'properties':
                    for key in sorted(parent_schema['properties'].keys()):
                        if key not in schema['properties']:
                            schema['properties'][key] = parent_schema[
                                'properties'][key]
            if 'extends' in parent_schema:
                parent_schema = json.load(
                    urllib2.urlopen(parent_schema['extends']['$ref']))
            else:
                break
                # essentially a do while loop (exit condition)

    return schema


def validate(json_resp, schema, validictory_path, schema_base=None):
    """
    Validate JSON data according to its schema.

    :param json_resp: JSON data to check against the schema.  This should be
      a dictionary with the field names as keys.
    :param schema: schema to validate json_resp against
    :param validictory_path: path to validictory python module
    :param schema_base: if not None, checks whether the $schema key starts
      with this string, and prints a warning if it isn't.
      If None, this check is not performed.  In any case, the return
      value is not affected.
    :return: True if validation succeeded, else False
    """
    # assumes /extern/validictory exists (see /cm for instructions)
    if not validictory_path in sys.path:
        sys.path.append(validictory_path)
    import validictory

    try:
        if schema_base and not json_resp["$schema"].startswith(schema_base):
            print "Warning: JSON schema is ", json_resp["$schema"], "instead of ", schema_base
        validictory.validate(json_resp, schema, required_by_default=False)
        return True
    except Exception as e:
        print "Received exception %s while trying to validate: %s" % (
            str(e), json_resp)
        return False
