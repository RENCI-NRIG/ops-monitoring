#!/usr/bin/python
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
import os
import time
import tempfile
import multiprocessing
import multiprocessing.pool

extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)

import table_manager
import opsconfig_loader
import extck_config


def execute_cmd(cmdStr, opslogger, lock):
    lock.acquire()
    opslogger.debug("about to execute: " + cmdStr)
    lock.release()
    os.system(cmdStr)

def sync_up_files(local_path, remote_path, remote_addr, remote_port, ssh_key_file, opslogger, lock):
    rsyncStr = "rsync -z -e \"ssh -i " + ssh_key_file + " -p " + remote_port + "\" " + local_path + " " + remote_addr + ":" + remote_path
    execute_cmd(rsyncStr, opslogger, lock)

def insert_ping_times(outputfile, tbl_mgr, table_str, lock):
    file_handle = open(outputfile, 'r')
    val_str = ""

    first = True
    for line in file_handle:
        # if the ping failed (delay set to -1 in pinger.py) we're not inserting the value.
        line = line.strip()
        if line[-3:] != "-1)":
            if first:
                first = False
            else:
                val_str += ","
            val_str += line
    lock.acquire()
    tbl_mgr.insert_stmt(table_str, val_str)
    lock.release()

def run_remote_pings((ext_config, site, campus_sources, ipConfigPathLocal,
                     ipConfigPathRemote, keyPath, pingerLocal, pingerRemote,
                     poolSize, initialPingCount, measurementPingCount, table_str,
                     lock, table_mgr)):
    addr = ext_config.get_experiment_source_ping_vm_address(site)
    port = ext_config.get_experiment_source_ping_vm_port(site)
    # First make sure the src site have the latest ips.conf and pinger.py
    # using rsync commands to avoid copying over & over the same files.
    sync_up_files(ipConfigPathLocal, ipConfigPathRemote, addr, port, keyPath, table_mgr.logger, lock)
    sync_up_files(pingerLocal, pingerRemote, addr, port, keyPath, table_mgr.logger, lock)

    remote_output_dir = ext_config.get_remote_output_dir()
    pref = "extck_tmp_"
    suff = ".pings"
    # clean up old tmp file in case some process was interrupted...
    # delete files older than 60 minutes, matching what we output.
    sshStr = "ssh -i " + keyPath + " " + addr + " -p " + port + \
               " \"find " + remote_output_dir + " -mmin +60 -name '" + pref + "*" + suff + "' | xargs rm -vrf" + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    if site in campus_sources:
        ping_type = 'campus'
    else:
        ping_type = 'core'

    (fh, outputFileLocal) = tempfile.mkstemp(suffix=suff, prefix=pref, dir=ext_config.get_local_output_dir())
    os.close(fh)  # closing tmp file that was just created.
    filename = os.path.basename(outputFileLocal)
    outputFileRemote = os.path.join(remote_output_dir, filename)
    sshStr = "ssh -i " + keyPath + " " + addr + " -p " + port + \
               " \"rm -f " + outputFileRemote + \
               " && python pinger.py -o " + outputFileRemote + " -c " + ipConfigPathRemote + " -s " + site + " -t " + ping_type + \
               " -p " + poolSize + " -i " + initialPingCount + " -m " + measurementPingCount + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    scpStr = "scp -i " + keyPath + " -P " + port + " " + addr + ":" + outputFileRemote + " " + outputFileLocal
    execute_cmd(scpStr, table_mgr.logger, lock)
    sshStr = "ssh -i " + keyPath + " " + addr + " -p " + port + \
               " \"rm -f " + outputFileRemote + "\""
    execute_cmd(sshStr, table_mgr.logger, lock)

    insert_ping_times(outputFileLocal, table_mgr, table_str, lock)
    # Delete tmp file
    os.remove(outputFileLocal)

def main(argv):
    multiprocessing.util.log_to_stderr(multiprocessing.util.DEBUG)
    db_type = "local"

    tbl_mgr = table_manager.TableManager(db_type, config_path)

    tbl_mgr.poll_config_store()

    ocl = opsconfig_loader.OpsconfigLoader(config_path)

    experiment_event_types = ocl.get_event_types()["experiment"]

    ext_config = extck_config.ExtckConfigLoader(tbl_mgr.logger)

    ipConfigPathLocal = os.path.join(extck_path, "ips.conf")
    ipConfigPathRemote = ext_config.get_ips_file_remote_location()
    pingerLocal = os.path.join(extck_path, "pinger.py")
    pingerRemote = ext_config.get_pinger_file_remote_location()
    keyPath = ext_config.get_ssh_key_file_location()
    poolSize = ext_config.get_experiment_ping_thread_pool_size()
    initialPingCount = ext_config.get_experiment_ping_initial_count()
    measurementPingCount = ext_config.get_experiment_ping_measurmentl_count()


    campus_sources = ext_config.get_experiment_source_ping_campus()
    core_sources = ext_config.get_experiment_source_ping_core()

    all_sources = campus_sources.union(core_sources)
    table_str = "ops_experiment_" + experiment_event_types[0]
    myLock = multiprocessing.Lock()

    argsList = []
    for site in all_sources:
        args = (ext_config, site, campus_sources,
                         ipConfigPathLocal, ipConfigPathRemote, keyPath,
                         pingerLocal, pingerRemote,
                         poolSize, initialPingCount, measurementPingCount,
                         table_str, myLock, tbl_mgr)
        argsList.append(args)
    pool = multiprocessing.pool.ThreadPool(processes=int(ext_config.get_experiment_coordination_thread_pool_size()))
    pool.map(run_remote_pings, argsList)
    # Purge data older than 168 hours (1 wk)
    old_ts = int((time.time() - 168 * 60 * 60) * 1000000)
    tbl_mgr.purge_old_tsdata(table_str, old_ts)

if __name__ == "__main__":
    main(sys.argv[1:])
