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
from pprint import pprint as pprint
local_path = "../"
common_path = "../../common/"

sys.path.append(local_path)
sys.path.append(common_path)
import os
import table_manager
import opsconfig_loader
import info_populator
import stats_populator

def usage():
    print('local_restart_node_interface_stats.py -b <local-store-base-url> -n <node-id> -i <interface-id> -a <aggregate-id> -e <experiment-id> -r <num-inserts> -s <sleep-period-seconds>')
    sys.exit(2)

def parse_args(argv):
    base_url = "http://127.0.0.1:5000"
    node_id = "instageni.gpolab.bbn.com_node_pc1"
    interface_id = "instageni.gpolab.bbn.com_interface_pc1:eth1"
    interfacevlan_id = "instageni.gpolab.bbn.com_interface_pc1:eth1:1750"
    aggregate_id = "gpo-ig"
    experiment_id = "missouri_ig_to_gpo_ig"
    num_ins = 10;
    per_sec = 0.2;

    try:
        opts, args = getopt.getopt(argv, "hb:n:i:r:s:a:e:", ["baseurl=", "nodeid=", "interfaceid=", "numinserts=", "sleepperiodsec=", "aggregateid=", "experimentid="])
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
        elif opt in ("-v", "--interfacevlanid"):
            interfacevlan_id = arg
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-e", "--experimentid"):
            experiment_id = arg
        elif opt in ("-r", "--numinserts"):
            num_ins = int(arg)
        elif opt in ("-s", "--sleepperiodsec"):
            per_sec = float(arg)

    return [base_url, node_id, interface_id, interfacevlan_id, aggregate_id, experiment_id, num_ins, per_sec]


def main(argv):

    [base_url, node_id, interface_id, interfacevlan_id, aggregate_id, experiment_id, num_ins, per_sec] = parse_args(argv)

    db_type = "local"
    config_path = "../../config/"
    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()

    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    event_types = ocl.get_event_types()

    if not tbl_mgr.drop_all_tables():
        sys.stderr.write("\nCould not drop all tables.\n")
        sys.exit(-1)
    if not tbl_mgr.establish_all_tables():
        sys.stderr.write("\nCould not create all tables.\n")
        sys.exit(-1)

    # info population
    ip = info_populator.InfoPopulator(tbl_mgr, base_url)
    error = False
    if not ip.insert_fake_info():
        error = True
    if not ip.insert_externalcheck_store():
        error = True

    if error:
        sys.stderr.write("Error populating local datastore\n")
        sys.exit(-1)

    q_res = tbl_mgr.query("select count(*) from ops_aggregate")
    if q_res is not None:
        print "Aggregate has ", q_res[0][0], "entries"

    # data population
    node_event_str_arr = event_types["node"]
    interface_event_str_arr = event_types["interface"]
    interfacevlan_event_str_arr = event_types["interfacevlan"]
    aggregate_event_str_arr = event_types["aggregate"]
    experiment_event_str_arr = event_types["experiment"]

    print node_event_str_arr + interface_event_str_arr
    obj_type = "node"
    node_sp = stats_populator.StatsPopulator(tbl_mgr, obj_type, node_id, num_ins, per_sec, node_event_str_arr)

    obj_type = "interface"
    interface_sp = stats_populator.StatsPopulator(tbl_mgr, obj_type, interface_id, num_ins, per_sec, interface_event_str_arr)

    obj_type = "interfacevlan"
    interfacevlan_sp = stats_populator.StatsPopulator(tbl_mgr, obj_type, interfacevlan_id, num_ins, per_sec, interfacevlan_event_str_arr)

    obj_type = "aggregate"
    aggregate_sp = stats_populator.StatsPopulator(tbl_mgr, obj_type, aggregate_id, num_ins, per_sec, aggregate_event_str_arr)

    obj_type = "experiment"
    experiment_sp = stats_populator.StatsPopulator(tbl_mgr, obj_type, experiment_id, num_ins, per_sec, experiment_event_str_arr)

    # start threads
    node_sp.start()
    interface_sp.start()
    interfacevlan_sp.start()
    aggregate_sp.start()
    experiment_sp.start()

    threads = []
    threads.append(node_sp)
    threads.append(interface_sp)
    threads.append(interfacevlan_sp)
    threads.append(aggregate_sp)
    threads.append(experiment_sp)

    ok = True
    # join all threads
    for t in threads:
        t.join()
        if not t.run_ok:
            ok = False

    if not ok:
        sys.stderr.write("\nCould not populate statistics properly.\n")
        sys.exit(-1)

    # for ev in (node_event_str_arr + interface_event_str_arr):
    #    cur.execute("select * from ops_" + ev + " limit 1");
    #    print ev, "has this entry:\n", cur.fetchone()


if __name__ == "__main__":
    main(sys.argv[1:])
