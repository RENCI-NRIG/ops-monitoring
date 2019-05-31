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
from pprint import pprint as pprint

sys.path.append("../")
import response_validator

urls_in_resp = []


def usage():
    print "Correct usage is:"
    print "python multi_rest_call.py -u https://<datastore url>/info/<object_type>/<object_id> -c <certificate_path> -v <validictory_path>"
    print "-v is equivalent to --validictory-path"
    print "-c is equivalent to --cert-path"
    print "-u is equivalent to --url"
    print "-h is equivalent to --help"
    sys.exit(0)


def parse_args(argv):
    if argv == []:
        usage()

    url = ""
    cert_path = ""
    validictory_path = ""

    try:
        opts, args = getopt.getopt(argv,"hu:c:v:",["help","url=","cert-path=","validictory-path="])
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
        else:
            print "Error:",opt, "not a valid argument"
            usage()

    return [url, cert_path, validictory_path]



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


def recurse_urls(d):

    global urls_in_resp

    if "href" in d:
        urls_in_resp.append(d["href"])

    if "selfRef" in d:
        urls_in_resp.append(d["selfRef"])

    if type(d)==type({}):
        for k in d:
            if type(d[k])==type({}):
                recurse_urls(d[k])
            elif type(d[k])==type([]):
                for k in d[k]:
                    if type(k)==type({}):
                        recurse_urls(k)


def which_url_next(json_dict):

    global urls_in_resp
    urls_in_resp = []

    # populates globale variable
    recurse_urls(json_dict)

    user_input = -1
    while user_input <= -1 or user_input >= len(urls_in_resp):
        print ""
        for idx in xrange(len(urls_in_resp)):
            print str(idx) + ": " + urls_in_resp[idx]
        user_input = int(raw_input("-- Which URL to go to (enter number) --\n\n"))
        print "you entered", user_input

    return urls_in_resp[user_input]

def main(argv): 

    [url, cert_path, validictory_path] = parse_args(argv)

    if url == "" or cert_path == "":
        usage()

    
    user_input = 'y'
    while (user_input == 'y'):
        json_dict = make_request_print_response(url, cert_path)
        
        if json_dict and validictory_path != "":
            schema = response_validator.parse_schema(json_dict["$schema"])
            valid = response_validator.validate(json_dict, schema, validictory_path)
            print "Response from", url, "is",
            if valid is False:
                print "*NOT*",
            print "valid"

        user_input = ' '
        while (user_input != 'y' and user_input != 'n'):
            user_input = raw_input("Continue? (y/n)")

        if json_dict and user_input == 'y':            
            url = which_url_next(json_dict)
    


if __name__ == "__main__":
    main(sys.argv[1:])

