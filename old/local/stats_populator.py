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
import psutil
import sys
import json
import threading
import random
from pprint import pprint as pprint


common_path = "../common/"

sys.path.append(common_path)
import table_manager
import opsconfig_loader


class StatsPopulator(threading.Thread):
    def __init__(self, tbl_mgr, obj_type, obj_id, num_inserts, sleep_period_sec, event_types_arr, data_life_time_sec = 12*60*60):
        threading.Thread.__init__(self)
        self.tbl_mgr = tbl_mgr # ldp = local datastore populator
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.num_inserts = num_inserts
        self.sleep_period_sec = sleep_period_sec
        self.event_types_arr = event_types_arr
        self.data_life_time_sec = data_life_time_sec

        self.ts_last_rx_bps = int(time.time())
        self.bits_last_rx_bps = psutil.network_io_counters().bytes_recv
        self.ts_last_tx_bps = int(time.time())
        self.bits_last_tx_bps = psutil.network_io_counters().bytes_sent
        
        self.ts_last_rx_pps = int(time.time())
        self.pkts_last_rx_pps = psutil.network_io_counters().packets_recv
        self.ts_last_tx_pps = int(time.time())
        self.pkts_last_tx_pps = psutil.network_io_counters().packets_sent
        
        self.ts_last_rx_eps = int(time.time())
        self.pkts_last_rx_eps = psutil.network_io_counters().errin
        self.ts_last_tx_eps = int(time.time())
        self.pkts_last_tx_eps = psutil.network_io_counters().errout
        
        self.ts_last_rx_dps = int(time.time())
        self.pkts_last_rx_dps = psutil.network_io_counters().dropin
        self.ts_last_tx_dps = int(time.time())
        self.pkts_last_tx_dps = psutil.network_io_counters().dropout


    def run(self):

        print "Starting thread for populating stats about" + self.obj_id
        
        self.run_stats_main()

        print "Exiting thread for populating stats about" + self.obj_id

    def run_stats_main(self):

        for i in range(self.num_inserts):
            print "%d %s wakeup and sample" % (time.time()*1000000, self.obj_id)
            for ev_t in self.event_types_arr:
                self.stat_insert(ev_t)
            time.sleep(self.sleep_period_sec)    

    def stat_insert(self, ev_t):    

        time_sec_epoch = int(time.time()*1000000)
        data = self.get_data(ev_t)
        if data != None:
            val_str = "('" + self.obj_id + "'," + str(time_sec_epoch) + "," + str(data) + ")" 
            table_str = "ops_" + self.obj_type + "_" +  ev_t
            old_ts = (time.time()-self.data_life_time_sec)*1000000

            self.tbl_mgr.insert_stmt(table_str, val_str)

            self.tbl_mgr.purge_old_tsdata(table_str, old_ts)
        else:
            print "No data received for event_type:", ev_t

    # Simple calls to get data
    # These should be non-blocking
    def get_data(self, event_type):
    
        if event_type == "mem_used_kb":
            return psutil.virtual_memory().used/1000
        elif event_type == "swap_free":
            return (100.0 - psutil.swap_memory().percent)
        elif event_type == "cpu_util":
            return psutil.cpu_percent(interval=0)
        elif event_type == "disk_part_max_used":
            return psutil.disk_usage('/').percent
        elif event_type == "rx_bps":
            prev_val = self.bits_last_rx_bps
            curr_val = psutil.network_io_counters().bytes_recv
            prev_ts = self.ts_last_rx_bps
            curr_ts = int(time.time())
            if curr_ts != prev_ts:
                rx_bps = 8*(curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                rx_bps = 0
            self.ts_last_rx_bps = curr_ts
            self.bits_last_rx_bps = curr_val
            return max(0, rx_bps) # TODO handle rollover
        elif event_type == "tx_bps":
            prev_val = self.bits_last_tx_bps
            curr_val = psutil.network_io_counters().bytes_sent
            prev_ts = self.ts_last_tx_bps
            curr_ts = int(time.time())
            if curr_ts != prev_ts:
                tx_bps = 8*(curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                tx_bps = 0
            self.ts_last_tx_bps = curr_ts
            self.bits_last_tx_bps = curr_val
            return max(0, tx_bps) # TODO handle rollover
        elif event_type == "rx_pps":
            prev_val = self.pkts_last_rx_pps
            curr_val = psutil.network_io_counters().packets_recv
            prev_ts = self.ts_last_rx_pps
            curr_ts = int(time.time())
            if curr_ts != prev_ts:
                rx_pps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                rx_pps = 0
            self.ts_last_rx_pps = curr_ts
            self.pkts_last_rx_pps = curr_val
            return max(0, rx_pps) # TODO handle rollover
        elif event_type == "tx_pps":
            prev_val = self.pkts_last_tx_pps
            curr_val = psutil.network_io_counters().packets_sent
            prev_ts = self.ts_last_tx_pps
            curr_ts = int(time.time())
            if curr_ts != prev_ts:
                tx_pps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                tx_pps = 0
            self.ts_last_tx_pps = curr_ts
            self.pkts_last_tx_pps = curr_val
            return max(0, tx_pps) # TODO handle rollover
        elif event_type == "rx_eps":
            prev_val = self.pkts_last_rx_eps
            curr_val = psutil.network_io_counters().errin
            prev_ts = self.ts_last_rx_eps
            curr_ts = int(time.time())
            if curr_ts != prev_ts:
                rx_eps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                rx_eps = 0
            self.ts_last_rx_eps = curr_ts
            self.pkts_last_rx_eps = curr_val
            return max(0, rx_eps) # TODO handle rollover
        elif event_type == "tx_eps":
            prev_val = self.pkts_last_tx_eps
            curr_val = psutil.network_io_counters().errout
            prev_ts = self.ts_last_tx_eps
            curr_ts = int(time.time()) 
            if curr_ts != prev_ts:
                tx_eps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                tx_eps = 0
            self.ts_last_tx_eps = curr_ts
            self.pkts_last_tx_eps = curr_val
            return max(0, tx_eps) # TODO handle rollover
        elif event_type == "rx_dps":
            prev_val = self.pkts_last_rx_dps
            curr_val = psutil.network_io_counters().dropin
            prev_ts = self.ts_last_rx_dps
            curr_ts = int(time.time()) 
            if curr_ts != prev_ts:
                rx_dps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                rx_dps = 0
            self.ts_last_rx_dps = curr_ts
            self.pkts_last_rx_dps = curr_val
            return max(0, rx_dps) # TODO handle rollover
        elif event_type == "tx_dps":
            prev_val = self.pkts_last_tx_dps
            curr_val = psutil.network_io_counters().dropout
            prev_ts = self.ts_last_tx_dps
            curr_ts = int(time.time()) 
            if curr_ts != prev_ts:
                tx_dps = (curr_val - prev_val)/(curr_ts - prev_ts)
            else:
                tx_dps = 0
            self.ts_last_tx_dps = curr_ts
            self.pkts_last_tx_dps = curr_val
            return max(0, tx_dps) # TODO handle rollover
        elif event_type == "is_available":
            return 1
        elif event_type == "num_vms_allocated":
            return random.randint(0,10)
        elif event_type == "ping_rtt_ms":
            return random.uniform(10,100)
        else: # TODO add more
            return None

def arg_parser(argv):

    if (len(argv) != 3):
        print "Provide exactly two args: (1) for num inserts, (2) for period between inserts in seconds"
        sys.exit(1)

    num_ins = 0

    try:
        num_ins = int(argv[1])
    except ValueError:
        print "Not a postive int. Provide number of inserts for run of program."
        sys.exit(1)

    per_sec = 0

    try:
        per_sec = float(argv[2])
    except ValueError:
        print "Not a postive float. Provide period of time in seconds between inserts."
        sys.exit(1)

    if (per_sec < 0 or num_ins < 0):
        print "Both numeric args should be positive"
        sys.exit(1)

    return num_ins, per_sec


def main():

    (num_ins, per_sec) = arg_parser(sys.argv)


    db_name = "local"
    config_path = "../config/"
    debug = False
    tbl_mgr = table_manager.TableManager(db_name, config_path, debug)
    tbl_mgr.poll_config_store()
    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    data_schema = ocl.get_info_schema()
    event_types = ocl.get_event_types()

    table_str_arr = data_schema.keys()
    tbl_mgr.drop_tables(table_str_arr)
    tbl_mgr.establish_tables(table_str_arr)

    node_id="instageni.gpolab.bbn.com_node_pc1"
    event_types_arr = event_types["node"]
    nsp = StatsPopulator(tbl_mgr, node_id, num_ins, per_sec, event_types_arr)
 
    iface_id="instageni.gpolab.bbn.com_interface_pc1:eth0"
    event_types_arr = event_types["interface"]
    isp = StatsPopulator(tbl_mgr, iface_id, num_ins, per_sec, event_types_arr)

    nsp.start()
    isp.start()
    
    cur = tbl_mgr.con.cursor();
    cur.execute("select count(*) from ops_" + event_types_arr[0]);
    print "num entries", cur.fetchone()[0]

    cur.close();

    threads = []
    threads.append(nsp)
    threads.append(isp)

    # join all threads
    for t in threads:
        t.join()

    tbl_mgr.close_con();
    
if __name__ == "__main__":
    main()
