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

import sys
import json
import getopt
import time
from pprint import pprint as pprint
local_path = "../"
common_path = "../../common/"

sys.path.append(local_path)
sys.path.append(common_path)
import table_manager

def usage():
    print('local_restart_gram_info.py --base-url <local-store-base-url> --debug \n')
    sys.exit(2)

def get_gram_defaults():

    # External IP addr of Gram rack local datastore
    base_url = "128.1.1.1"  

    # json-schema
    agg_schema = "http://www.gpolab.bbn.com/monitoring/schema/20140131/aggregate#"
    node_schema = "http://unis.incntre.iu.edu/schema/20120709/node#"


    # Print debug messages from this program and others
    debug = False

    # Node info used for info and data query
    # memory per node in kB
    mem_total_kb = 4000000 # 4 GB
    
    # aggregate dictionary
    aggregate = {}

    # aggregate id (GENI globally unique short name)
    agg_id = "gpo-gram"
    aggregate['id'] = agg_id

    aggregate['urn'] = 'urn:aggregate'
    
    # aggregate info query url
    aggregate['href'] = base_url + '/info/aggregate/' + agg_id

    # time-series data measurement reference
    aggregate['meas_ref'] = base_url + "/data/"
    
    # json schema
    aggregate['schema'] = agg_schema

    # Contains node information in a dictionary
    nodes = {}

    # node_id in datastore node id
    node_id = 'head_node'
    nodes[node_id] = {}
    nodes[node_id]['id'] = node_id

    nodes[node_id]['urn'] = 'urn:head_node'

    # node info query url
    nodes[node_id]['href'] = base_url + '/info/node/' + node_id

    # change if different
    nodes[node_id]['mem_total_kb'] = mem_total_kb 
    
    nodes[node_id]['schema'] = node_schema

    # setting the rest of the nodes dictionary using dense code
    # format is the same as above
    node_id = 'compute_node_1'
    nodes[node_id] = {'id':node_id, 'urn':'urn'+node_id, 'href': base_url + '/info/node/' + node_id, 'mem_total_kb': mem_total_kb, 'schema': node_schema}

    node_id = 'compute_node_2'
    nodes[node_id] = {'id':node_id, 'urn':'urn'+node_id, 'href': base_url + '/info/node/' + node_id, 'mem_total_kb': mem_total_kb, 'schema': node_schema}

    node_id = 'compute_node_3'
    nodes[node_id] = {'id':node_id, 'urn':'urn'+node_id, 'href': base_url + '/info/node/' + node_id, 'mem_total_kb': mem_total_kb, 'schema': node_schema}

    return [aggregate, nodes, debug]


# sets ops_aggregate table
# sets ops_aggregate_resource table
def set_aggregate_info(tbl_mgr, aggregate, nodes):
    ts = str(int(time.time()*1000000))
    agg = [aggregate['schema'], 
            aggregate['id'], 
            aggregate['href'], 
            aggregate['urn'],
            ts,
            aggregate['meas_ref']]
    info_insert(tbl_mgr, "ops_aggregate", agg)

    for node_i in nodes:
        nd = nodes[node_i] # shorter var name to node dict
        agg_node = [nd['id'], aggregate['id'], nd['urn'], nd['href']]
        info_insert(tbl_mgr, "ops_aggregate_resource", agg_node)


# sets ops_node
def set_node_info(tbl_mgr, nodes):

    ts = str(int(time.time()*1000000))
    for node_i in nodes:
        nd = nodes[node_i] # shorter var name to node dict
        node = [nd['schema'], nd['id'], nd['href'], nd['urn'], ts, nd['mem_total_kb']]
        info_insert(tbl_mgr, "ops_node", node)


# creates a values string from an ordered array of values
def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:
        val_str += str(val) + "','" # join won't do this
    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )
    tbl_mgr.insert_stmt(table_str, val_str)


def main(argv):

    [aggregate, nodes, debug] = get_gram_defaults()

    pprint(aggregate)
    pprint(nodes)

    # Local for local datastore (vs collector for a collector)
    # This is not the database name or database program
    # Those are set in /ops-monitoring/config/<db_type>_operator.conf
    db_type = "local" 
    config_path = "../../config/"
    tbl_mgr = table_manager.TableManager(db_type, config_path, debug)

    # get schemas from config store
    tbl_mgr.poll_config_store()

    # get info schema from table manager
    info_schema = tbl_mgr.info_schema
        
    # Drops all informational tables
    table_str_arr = info_schema.keys()
    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)

    # supports aggregate info query
    set_aggregate_info(tbl_mgr, aggregate, nodes)

    set_node_info(tbl_mgr, nodes)    

    tbl_mgr.con.close()

if __name__ == "__main__":
    main(sys.argv[1:])
