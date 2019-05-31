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

import json
import os
import time
import urllib2
import requests
from pprint import pprint as pprint

# TODO if response has an extra key, exception is thrown and currently
# not handled, ok



def has_keys_values(schema, a_dict):
    
    keys = schema.keys()
    values = schema.values()

    for i in xrange (len(keys)):
        if keys[i] not in a_dict:
            return False

        if values[i] == 'schema:string':
            if not isinstance(a_dict[keys[i]], unicode):
                return False
        elif values[i] == 'schema:number':
            if not (isinstance(a_dict[keys[i]], int) or isinstance(a_dict[keys[i]], float)):
                return False
       

    return True


def check_list(schema, resp):
    del schema["schema:type"]
    #print "LIST", resp, "is of schema:", schema
    for obj_i in resp:
        if not has_keys_values(schema, obj_i):
            return False
    return True

def check_dict(schema, resp):
    del schema["schema:type"]

    return has_keys_values(resp, schema)


def validate_response(schema, resp):

    for k in resp.keys():

        if isinstance(schema[k], dict):
            if schema[k]["schema:type"] == "schema:list":
                if isinstance(resp[k], list):
                    if not check_list(dict(schema[k]), resp[k]):
                        return (False, str(resp[k]) + " list did not match the schema")
                else:
                    return (False, str(resp[k]) + " is not a list")
            elif schema[k]["schema:type"] == "schema:dict":
                if isinstance(resp[k], dict):
                    if not check_dict(dict(schema[k]), resp[k]):
                        return (False, str(resp[k]) + " dict did not match the schema")
                else:
                    return (False, str(resp[k]) + " is not a dict")
        elif isinstance(schema[k], list):
            print k, "schema is a list"
        elif schema[k] == 'schema:string':
            if not isinstance(resp[k], unicode):
                return (False, schema[k] + " is not a string")
        elif schema[k] == 'schema:number':
            if not (isinstance(resp[k], int) or isinstance(resp[k], float)):
                return (False, schema[k] + " is not an number")
        else:
            "no match in type"

    return (True, "")

def validate_list_of_responses(schema, resp):
    for resp_i in resp:
        (t_or_f, ret_str) = validate_response(schema, resp_i)
        if (t_or_f == False):
            return (t_or_f, ret_str)

    return (True, "")


# refresh database at local store
#os.system("python local_restart_node_interface_stats.py")

json_schema_path = "./"
json_schema = json.load(open(json_schema_path + "json_schema"))
#pprint(json_schema)
base_url = "https://127.0.0.1:5000/"

aggregate = base_url + "info/aggregate/gpo-ig"
node = base_url + "info/node/instageni.gpolab.bbn.com_node_pc1"
interface = base_url + "info/interface/instageni.gpolab.bbn.com_interface_pc1:eth1"
slice_  = base_url + "info/slice/ch.geni.net_gpo-infra_slice_tuptyexclusive"
sliver  = base_url + "info/sliver/instageni.gpolab.bbn.com_sliver_26947"
authority = base_url + "info/authority/ch.geni.net"
user  = base_url + "info/user/tupty"
#opsconfig = base_url + "info/opsconfig/geni-prod"
link = base_url + "info/link/arbitrary_link_id_001"
#interfacevlan = base_url + "info/interfacevlan/instageni.gpolab.bbn.com_interface_pc2:eth1:1750"

urls = {}
urls["opsconfig"] = opsconfig
urls["node"] = node
urls["interface"] = interface
urls["aggregate"] = aggregate
urls["authority"] = authority
urls["slice"] = slice_
urls["sliver"] = sliver
urls["user"] = user
urls["link"] = link
urls["interfacevlan"] = interfacevlan


for key in urls:
    print "testing", key, "at", urls[key]
    resp = json.loads(requests.get(urls[key],verify=False, cert='/vagrant/collector-gpo-withnpkey.pem').content)
    schema = json_schema[key]
    print key,"response is valid?",validate_response(schema, resp)



node_data_url = base_url + 'data/?q={"filters":{"eventType":["ops_monitoring:mem_used_kb","ops_monitoring:cpu_util","ops_monitoring:disk_part_max_used","ops_monitoring:is_available"],"ts":{"gte":3,"lt":' + str(int(time.time() * 1000000)) + '},"obj":{"type":"node","id":["instageni.gpolab.bbn.com_node_pc1"]}}}'

interface_data_url = base_url + 'data/?q={"filters":{"eventType":["ops_monitoring:rx_bps","ops_monitoring:tx_bps","ops_monitoring:rx_pps","ops_monitoring:tx_pps","ops_monitoring:rx_dps","ops_monitoring:tx_dps","ops_monitoring:rx_eps","ops_monitoring:tx_eps"],"ts":{"gte":3,"lt":' + str(int(time.time() * 1000000)) + '},"obj":{"type":"interface","id":["instageni.gpolab.bbn.com_interface_pc1:eth0"]}}}'

resp = json.load(urllib2.urlopen(node_data_url))
print "node_data response is valid?", validate_list_of_responses(json_schema["data"], resp)

resp = json.load(urllib2.urlopen(interface_data_url))
print "interface_data response is valid?", validate_list_of_responses(json_schema["data"], resp)
