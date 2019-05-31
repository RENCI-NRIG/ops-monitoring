#!/usr/bin/python
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

import time
import sys
import json
import ConfigParser

from pprint import pprint as pprint

common_path = "../common/"

sys.path.append(common_path)
import table_manager
import opsconfig_loader

class ConfigStorePopulator():
    def __init__(self, tbl_mgr):

        self.tbl_mgr = tbl_mgr 
        self.config_path = tbl_mgr.config_path

    def init_config_datastore_info(self):
       
        config = ConfigParser.ConfigParser()
        config.read(self.config_path + "/config_datastore_operator.conf")
        self.config_store_url = config.get("main", "configstoreurl")
                
        self.tbl_mgr.reset_opsconfig_tables()

        self.insert_opsconfig_base()
        self.insert_opsconfig_info_schema()
        self.insert_opsconfig_events_schema()
        self.insert_opsconfig_datastore_urls()

    def insert_opsconfig_base(self):

        opsconfig1 = []
        opsconfig1.append("http://www.gpolab.bbn.com/monitoring/schema/20140501/opsconfig#")
        opsconfig1.append("geni-prod")
        opsconfig1.append(self.config_store_url) # selfRef
        opsconfig1.append(str(int(time.time()*1000000))) 
        
        info_insert(self.tbl_mgr, "ops_opsconfig", opsconfig1)
        
        opsconfigauth1 = []
        opsconfigauth1.append("ch.geni.net") # authority name
        opsconfigauth1.append("geni-prod")
        opsconfigauth1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
        opsconfigauth1.append(self.config_store_url) # authority datastore href (FIXME: now points to config store)
        info_insert(self.tbl_mgr, "ops_opsconfig_authority", opsconfigauth1)

        
    # This populates the config datastore of events.
    # The first entry is written in expanded form
    # below are condensed forms without comments
    def insert_opsconfig_events_schema(self):
        self.insert_opsconfig_node_events()
        self.insert_opsconfig_interface_events()
        self.insert_opsconfig_interfacevlan_events()
        self.insert_opsconfig_aggregate_events()
        self.insert_opsconfig_experiment_events()


    def insert_opsconfig_node_events(self):
        opsconfigevent = []
        opsconfigevent.append("node")       # object type
        opsconfigevent.append("cpu_util")   # name
        opsconfigevent.append("varchar")    # id schema type
        opsconfigevent.append("int8")       # ts schema type
        opsconfigevent.append("float4")     # v schema type
        opsconfigevent.append("percent")    # units
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
       
        opsconfigevent = ["node","mem_used_kb","varchar","int8", "int8","kilobytes"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["node","swap_free","varchar","int8","float4","percent"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["node","is_available","varchar","int8","int2","boolean"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["node","disk_part_max_used","varchar","int8","float4","percent"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["node","num_vms_allocated","varchar","int8","int4","count"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)


    def insert_opsconfig_interface_events(self):
        opsconfigevent = ["interface","rx_bps","varchar","int8","float8","bps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
    
        opsconfigevent = ["interface","tx_bps","varchar","int8","float8","bps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interface","rx_pps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
    
        opsconfigevent = ["interface","tx_pps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interface","rx_dps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
    
        opsconfigevent = ["interface","tx_dps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interface","rx_eps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interface","tx_eps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)

    
    def insert_opsconfig_interfacevlan_events(self):
        opsconfigevent = ["interfacevlan","rx_bps","varchar","int8","float8","bps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","tx_bps","varchar","int8","float8","bps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","rx_pps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
    
        opsconfigevent = ["interfacevlan","tx_pps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","rx_dps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","tx_dps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","rx_eps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
        opsconfigevent = ["interfacevlan","tx_eps","varchar","int8","float8","pps"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)


    def insert_opsconfig_aggregate_events(self):
        opsconfigevent = ["aggregate","is_available","varchar","int8","int2","boolean"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)


    def insert_opsconfig_experiment_events(self):
        opsconfigevent = ["experiment","ping_rtt_ms","varchar","int8","float8","boolean"]
        info_insert(self.tbl_mgr, "ops_opsconfig_event", opsconfigevent)
        
   
    # This populates the info schema for the config local datastore to
    # publish.  
    #
    # This should reflect what is in /config/opsconfig.json 
    #
    # Since different tables have a different number of
    # columns, we'll just store the schema as a "document" like a
    # key,value store or document database would store this.  Postgres
    # 9.3 has json format to store objects like this, but for now
    # we'll just store json text in a varchar.
    def insert_opsconfig_info_schema(self):
        opsconfiginfoschema = []
        opsconfiginfoschema.append("aggregate")  # table name
        opsconfiginfoschema.append('[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"], ["ts","int8"], ["measRef","varchar"]]') # array of schema
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["node", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"], ["ts","int8"], ["properties$mem_total_kb","int8"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["link", '[["$schema", "varchar"],["id", "varchar"],["selfRef","varchar"], ["urn","varchar"], ["ts","int8"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["sliver", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"],	 ["uuid","varchar"], ["ts","int8"], ["aggregate_urn","varchar"], ["aggregate_href","varchar"], ["slice_urn","varchar"], ["slice_uuid","varchar"], ["creator","varchar"], ["created","int8"], ["expires","int8"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["interface", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"], ["ts","int8"], ["address_type","varchar"], ["address_address","varchar"], ["properties$role","varchar"], ["properties$max_bps","int8"], ["properties$max_pps","int8"] ]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["interfacevlan", '[["$schema", "varchar"],["id", "varchar"],["selfRef","varchar"], ["urn","varchar"], ["ts","int8"], ["tag","int8"], ["interface_urn","varchar"], ["interface_href","varchar"]]' ]
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["slice", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"], ["uuid","varchar"], ["ts","int8"], ["authority_urn","varchar"], ["authority_href","varchar"], ["created","int8"], ["expires","int8"]]' ]
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["user", '[["$schema", "varchar"],["id", "varchar"],["selfRef","varchar"],["urn","varchar"],["ts","int8"],["authority_urn","varchar"], ["authority_href","varchar"], ["fullname","varchar"], ["email","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["authority", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["urn","varchar"], ["ts","int8"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["externalcheck", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["ts","int8"], ["measRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["experiment", '[["$schema", "varchar"], ["id", "varchar"], ["selfRef","varchar"], ["ts","int8"], ["slice_urn","varchar"], ["slice_uuid","varchar"], ["source_aggregate_urn","varchar"], ["source_aggregate_href","varchar"], ["destination_aggregate_urn","varchar"], ["destination_aggregate_href","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        # Is this table still necessary?
        opsconfiginfoschema = ["opsconfig", '[["$schema", "varchar"], ["id","varchar"], ["selfRef","varchar"], ["ts","int8"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["aggregate_resource", '[["id","varchar"], ["aggregate_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["aggregate_sliver", '[["id","varchar"], ["aggregate_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["link_interfacevlan", '[["id","varchar"],["link_id","varchar"],["urn","varchar"],["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["sliver_resource", '[["id","varchar"], ["sliver_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["node_interface", '[["id","varchar"], ["node_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["slice_user", '[["id","varchar"], ["slice_id","varchar"], ["urn","varchar"], ["role","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["authority_user", '[["id","varchar"], ["authority_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["authority_slice", '[["id","varchar"], ["authority_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["opsconfig_aggregatestore", '[["id","varchar"], ["opsconfig_id","varchar"], ["amtype","varchar"], ["urn","varchar"], ["href","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["opsconfig_externalstore", '[["id","varchar"], ["opsconfig_id","varchar"], ["href","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["opsconfig_authority", '[["id","varchar"], ["opsconfig_id","varchar"], ["urn","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["opsconfig_event", '[["object_type","varchar"], ["name","varchar"], ["id","varchar"], ["ts","varchar"], ["v","varchar"], ["units","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["externalcheck_experiment", '[["id","varchar"], ["externalcheck_id","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)

        opsconfiginfoschema = ["externalcheck_monitoredaggregate", '[["id","varchar"], ["externalcheck_id","varchar"], ["selfRef","varchar"]]']
        info_insert(self.tbl_mgr, "ops_opsconfig_info", opsconfiginfoschema)


    def insert_opsconfig_datastore_urls(self):
        self.insert_opsconfig_aggregatestore_urls()
        self.insert_opsconfig_externalcheckstore_urls()


    def insert_opsconfig_aggregatestore_urls(self):

        aggstore = ["ion.internet2.edu", "geni-prod", "ion", "urn:publicid:IDN+ion.internet2.edu+authority+cm", "http://aj-dev6.grnoc.iu.edu/geni-local-datastore/info/aggregate/ion.internet2.edu"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)

        aggstore = ["al2s.net.internet2.edu", "geni-prod", "al2s", "urn:publicid:IDN+al2s.net.internet2.edu+authority+cm", "http://aj-dev6.grnoc.iu.edu/geni-local-datastore/info/aggregate/al2s.net.internet2.edu"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)

        aggstore = ["dragon.maxgigapop.net", "geni-prod", "ion", "urn:publicid:IDN+dragon.maxgigapop.net+authority+am", "http://maxam.maxgigapop.net/info/aggregate/dragon.maxgigapop.net"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)

        aggstore = ["rci-eg", "geni-prod", "exogeni", "urn:rci", "https://rci-hn.exogeni.net/ops-monitoring/info/aggregate/rci-eg"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)

        aggstore = ["utah-ig", "geni-prod", "instageni", "urn:publicid:IDN+utah.geniracks.net+authority+cm", "http://datastore.utah.geniracks.net:5001/info/aggregate/utah-ig"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)


    def insert_opsconfig_externalcheckstore_urls(self):

        extckstore = ["gpo", "geni-prod", "http://aquarion.gpolab.bbn.com/info/externalcheck/gpo"]
        info_insert(self.tbl_mgr, "ops_opsconfig_aggregatestore", aggstore)


def info_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:
        val_str += val + "','" # join won't do this

    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )

    tbl_mgr.insert_stmt(table_str, val_str)


def main():

   
    db_name = "local"
    config_path = "../config"
    debug = False
    tbl_mgr = table_manager.TableManager(db_name, config_path, debug)
    tbl_mgr.poll_config_store()
    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    info_schema = ocl.get_info_schema()
   
    tbl_mgr.drop_tables(info_schema.keys())
    tbl_mgr.establish_tables(info_schema.keys())
    ip = InfoPopulator(tbl_mgr)

    ip.insert_fake_info()
   
    
    cur = tbl_mgr.con.cursor();
    cur.execute("select count(*) from aggregate");
    print "num entries", cur.fetchone()[0]

    cur.close();
    tbl_mgr.close_con();
    
if __name__ == "__main__":
    main()
