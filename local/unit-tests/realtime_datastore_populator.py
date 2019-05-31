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

import sys
import json
import getopt

local_path = "../"
common_path = "../../common/"
config_path = "../../config/"

sys.path.append(local_path)
sys.path.append(common_path)
import table_manager
import opsconfig_loader
import info_populator
import stats_populator

def usage():
    print 'local_restart_node_interface_stats.py -b <local-store-base-url> -n <node-id> -i <interface-id> -r <num-inserts> -s <sleep-period-seconds>'
    sys.exit(2)

def parse_args(argv):
    base_url = "http://127.0.0.1:5000"
    node_id = "instageni.gpolab.bbn.com_node_pc1"
    interface_id = "instageni.gpolab.bbn.com_interface_pc1:eth1"
    num_ins = 12 * 10; # 10 minutes if 12 and 5
    per_sec = 5; # interval in seconds between inserts

    try:
        opts, args = getopt.getopt(argv,"hb:n:i:r:s:",["baseurl=","nodeid=","interfaceid=","numinserts=","sleepperiodsec="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-b", "--baseurl"):
            base_url = arg
        elif opt in ("-n", "--nodeid"):
            node_id = arg
        elif opt in ("-i", "--interfaceid"):
            interface_id = arg
        elif opt in ("-r", "--numinserts"):
            num_ins = int(arg)
        elif opt in ("-s", "--sleepperiodsec"):
            per_sec = float(arg)

    return [base_url, node_id, interface_id, num_ins, per_sec]


def main(argv):

    [base_url, node_id, interface_id, num_ins, per_sec] = parse_args(argv)

    db_type = "local"
    config_path = "../../config"
    debug = False

    tbl_mgr = table_manager.TableManager(db_type, config_path, debug)
    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    event_types = ocl.get_event_types()

    tbl_mgr.drop_all_tables()
    tbl_mgr.establish_all_tables()

    # info population
    ip = info_populator.InfoPopulator(tbl_mgr, base_url)
    ip.insert_fake_info()
       
    q_res = tbl_mgr.query("select count(*) from ops_aggregate")
    if q_res is not None:
        print "Aggregate has entries", q_res[0][0], "entries"
    
    # data population 
    node_event_str_arr = event_types["node"]
    interface_event_str_arr = event_types["interface"]

    print node_event_str_arr + interface_event_str_arr
    tsdata_lifespan_sec = 60 

    node_sp = stats_populator.StatsPopulator(tbl_mgr, node_id, num_ins, per_sec, node_event_str_arr,tsdata_lifespan_sec)


    interface_sp = stats_populator.StatsPopulator(tbl_mgr, interface_id, num_ins, per_sec, interface_event_str_arr,tsdata_lifespan_sec)

    # start threads
    node_sp.start()
    interface_sp.start()

    threads = []
    threads.append(node_sp)
    threads.append(interface_sp)

    # join all threads
    for t in threads:
        t.join()

    #for ev in (node_event_str_arr + interface_event_str_arr):
    #    cur.execute("select * from ops_" + ev + " limit 1");
    #    print ev, "has this entry:\n", cur.fetchone()

if __name__ == "__main__":
    main(sys.argv[1:])
