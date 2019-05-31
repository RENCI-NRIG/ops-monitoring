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
import sys
import os
import time
sys.path.append("../common/")
import table_manager
import opsconfig_loader

db_type = "local"
config_path = "../config/"
# debug = False

tbl_mgr = table_manager.TableManager(db_type, config_path)

tbl_mgr.poll_config_store()

ocl = opsconfig_loader.OpsconfigLoader(config_path)

experiment_event_types = ocl.get_event_types()["experiment"]

ipConfigPath="/users/amcanary/ips.conf"
outputFile = "raw_rows"
outputFileLocal = "/home/amcanary/raw_rows"
outputFileRemote="/users/amcanary/raw_rows"
keyPath = "/home/amcanary/.ssh/id_rsa"



srcPing={"gpo-ig":["amcanary@pc1.instageni.gpolab.bbn.com", "30266"],\
         "utah-ig": ["amcanary@pc1.utah.geniracks.net", "30010"],\
         "gpo-ig-3715_core":["amcanary@pc1.instageni.gpolab.bbn.com","31290"],\
         "gpo-ig-3716_core":["amcanary@pc1.instageni.gpolab.bbn.com", "30522"] }

for site in srcPing:
    port = srcPing[site][1]
    sshStr = "ssh -i " + keyPath + " " + srcPing[site][0] + " -p " + port +\
               " \"rm -f " + outputFile + " && python pinger.py -o " + outputFile  + " -c " + ipConfigPath + " -s " + site + "\"" 
    os.system(sshStr)
    scpStr="scp -i " + keyPath + " -P " + port + " " + srcPing[site][0]+ ":" + outputFileRemote + " /home/amcanary"
    os.system(scpStr)
    file_handle = open(outputFileLocal, 'r')
    val_str = ""
    for line in file_handle:
        val_str += line + ","
    table_str = "ops_experiment_" + experiment_event_types[0]
    tbl_mgr.insert_stmt(table_str, val_str[:-1])
    old_ts = int((time.time()-504*60*60)*1000000) # Purge data older than 12 hours (504, every 3 wks)
    tbl_mgr.purge_old_tsdata(table_str, old_ts)
