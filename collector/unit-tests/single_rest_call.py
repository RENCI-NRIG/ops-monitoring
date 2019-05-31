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
This program is designed to make it easier to debug a (local)datastore's 
output.  If the datastore's database tables are populated properly, then
everything will work fine.  This program enables debugging of this, since
debugging in the web-browser is no longer possible with the client 
certificate credential system.

This requires sudo pip install requests --upgrade

and

git clone https://github.com/sunlightlabs/validictory.git
to ops-monitoring/extern/validictory

'''

import json
import sys
import requests
import getopt

sys.path.append("../")
import response_validator

from pprint import pprint as pprint

def usage():
    print "Correct usage is:"
    print "python single_rest_call.py -u https://<datastore url>/info/<object_type>/<object_id> -c <certificate_path> -v <validictory_path>"
    print "-v is equivalent to --validictory-path"
    print "-c is equivalent to --cert-path"
    print "-u is equivalent to --url"
    print "-h is equivalent to --help"
    print "-s schema base"
    sys.exit(0)


def parse_args(argv):
    if argv == []:
        usage()

    url = ""
    cert_path = ""
    validictory_path = ""
    schema_base = "http://www.gpolab.bbn.com/monitoring/schema/20140501/"


    try:
        opts, args = getopt.getopt(argv,"hu:c:v:s:",["help","url=","cert-path=","validictory-path=","schema-base="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in("-h","--help"):
            usage()
        elif opt in ("-u", "--url"):
            url = arg
        elif opt in ("-c", "--cert-path"):
            cert_path = arg
        elif opt in ("-v", "--validictory-path"):
            validictory_path = arg
        elif opt in ("-s", "--schema-base"):
            schema_base = arg
        else:
            print "Error:",opt, "not a valid argument"
            usage()

    return [url, cert_path, validictory_path, schema_base]



def make_request_print_response(url, cert_path):

    resp = None
    json_dict = None

    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        print "No response from local datastore at: " + url
        print e

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            print "Could not load into JSON",
            print resp.content
            print e

        pprint(json_dict)
    else:
        print "resp object is None from", url

    return json_dict



def main(argv): 

    [url, cert_path, validictory_path, schema_base] = parse_args(argv)

    if url == "" or cert_path == "":
        usage()

    json_dict = make_request_print_response(url, cert_path)

    # custom prints of parts of the dictionary
    if json_dict:

        if validictory_path != "":
            # get json-schema from $schema
            schema = response_validator.parse_schema(json_dict["$schema"])
            valid = response_validator.validate(json_dict, schema, validictory_path, schema_base)
            print "Response from", url, "is",
            if valid:
                print "valid"
            else:
                print "NOT valid"

        '''
        # Uncomment to checks part of response dictionary
        part_of_dict = "resources"
        # avoids error if not in dict
        if part_of_dict in json_dict:
            print " ----- "
            pprint(json_dict[part_of_dict])
        '''

if __name__ == "__main__":
    main(sys.argv[1:])

