#!/usr/bin/env python
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
import time
import subprocess
import shlex
import os
import multiprocessing
import multiprocessing.pool
import threading
# import requests

extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)
import extck_config
import logger
import table_manager
opslogger = logger.get_logger(config_path)
config = extck_config.ExtckConfigLoader(opslogger)


##################################################
# gcf path for stitch/scs.py script
sys.path.append(os.path.join(config.get_gcf_path(), "src"))
import gcf.oscript
import gcf.omnilib.stitch.scs

##################################################
# geni-lib config for FOAM/FV listresources test #
sys.path.append(config.get_geni_lib_config_path())  #
sys.path.append(config.get_geni_lib_path())  #

import amcanary_config  #
context = amcanary_config.buildContext()  #
from geni.aggregate.core import AM  #
##################################################






class SiteOF(AM):
    def __init__ (self, name, url, apiversion):
        if apiversion == 0:
            apiversionstr = "amapiv2"
        else:
            apiversionstr = "amapiv" + str(apiversion)
        super(SiteOF, self).__init__(name, url, apiversionstr, "foam")
        self.apiversion = apiversion

def getOFState(context, site, lock):

    lock.acquire()
    opslogger.debug("Listing resources for FOAM/FV Aggregate Manager %s at %s." % (site.name, site.url))
    lock.release()
    try:
        ad = site.listresources(context)  # Run listresources for a particular site
    except Exception, e:
        lock.acquire()
        opslogger.warning(str(e))
        opslogger.warning("Control plane connection for FOAM/FV Aggregate Manager to %s is Offline via API version %s" % (site.name, str(site.apiversion)))
        lock.release()
        return 0  # Can't reach the site via control pat

    # Check to see if dpids have ports.
    #  No ports on all dpids for a given switch indicates possible FV issues.
    switch_nb = 0
    for switch in ad.datapaths:
        switch_nb += 1
        if len(switch.ports) == 0:
            lock.acquire()
            opslogger.warning("NO ports found on " + switch.dpid + ". FV may be hang or connection from dpid to FV is broken.")
            lock.release()
        else:  # If any dpid has ports listed, FV is working for that switch
            lock.acquire()
            opslogger.info("FOAM/FV Aggregate Manager %s is available at %s." % (site.name, site.url))
            lock.release()
            return 1
    if switch_nb == 0:
        # Basically the site has no resources configured yet.
        # The consensus is that we declare it available still.
        lock.acquire()
        opslogger.info("No switches listed for %s." % site.name)
        lock.release()
        return 1

    lock.acquire()
    opslogger.warning("NO ports found on any switch. FV may be hang or connection from dpid to FV is broken. Declaring foam aggregate %s (%s) unavailable" % (site.name, site.url))
    lock.release()
    return 0  # All dpids on that switch had no ports. FV is down.

class DataPopulator():

    __IS_AVAILABLE_TBLNAME = "ops_aggregate_is_available"

    def __init__(self, tbl_mgr):
        self.tbl_mgr = tbl_mgr

    def insert_agg_is_avail_datapoint(self, agg_id, ts, state):

        datapoint = (agg_id, ts, state)
        self.__db_insert(DataPopulator.__IS_AVAILABLE_TBLNAME, datapoint)

    def __db_purge(self, table_str):
        old_ts = int((time.time() - 168 * 60 * 60) * 1000000)  # Purge data older than 1 week (168 hours)
        self.tbl_mgr.purge_old_tsdata(table_str, old_ts)


    def __db_insert(self, table_str, row_arr):
        val_str = "('"
        first = True
        for val in row_arr:
            if first:
                first = False
            else:
                val_str += "', '"
            val_str += str(val)
        val_str += "')"
        self.tbl_mgr.insert_stmt(table_str, val_str)

    def db_purge_agg_is_available(self):
        self.__db_purge(DataPopulator.__IS_AVAILABLE_TBLNAME)


def getAMStateForURL(agg_id, am_url, amtype, config, lock):
    cmd_str = config.get_am_full_test_command(am_url, amtype)
    args = shlex.split(cmd_str)
    lock.acquire()
    opslogger.debug("About to execute: " + cmd_str)
    lock.release()
    # Searching for the name of the test being executed
    for arg in args:
        if arg.startswith("Test.test_"):
            test = arg[10:]  # the ending of that argument.
            break
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, _err = p.communicate()
    state = 0
    retcode = 1  # Assuming we've got an error
    for line in output.split('\n'):
        words = line.split()
        if len(words) == 3 \
            and words[0] == 'MONITORING' \
            and words[1] == ('test_%s' % test):
            retcode = int(words[2])
            break;
    qualifier = "NOT "
    if retcode == 0:
        state = 1
        qualifier = ""

    lock.acquire()
    opslogger.info("aggregate %s is %sreachable at %s" % (agg_id, qualifier, am_url))
    lock.release()
    return state

def getOmniCredentials():
    argv = []
    [_fram, config, _args, _opts] = gcf.oscript.initialize(argv)
    key = config['selected_framework']['key']
    cert = config['selected_framework']['cert']
    return key, cert

class ListAggregateThread(threading.Thread):
    def __init__(self, scsInstance):
        super(ListAggregateThread, self).__init__()
        self.scsInstance = scsInstance
        self.daemon = True

    def run(self):
        self.result = listScsAggregate(self.scsInstance)

def listScsAggregate(scsInstance):
    return scsInstance.ListAggregates(False)

def getStitcherState(scs_id, scs_url, config, lock):
#     cmd = "cat /home/amcanary/getversion_SCS.xml | curl -X POST -H 'Content-type: text/xml' -d \@- http://oingo.dragon.maxgigapop.net:8081/geni/xmlrpc"
#     echoCmd = "echo $?"
#     os.popen(cmd)
#     out = os.popen(echoCmd)
#     result = int(out.read())
#     if result == 0:
#         return "1"
#     else:
#         return "0"
    state = 0
    qualifier = "NOT "
    secure = False
    timeo = int(config.get_scs_timeout())

    if scs_url.startswith("https"):
        secure = True
        # Get key and cert from omni file.
        [keyfile, certfile] = getOmniCredentials()
    try:
        if secure:
            scsI = gcf.omnilib.stitch.scs.Service(scs_url, key=keyfile, cert=certfile, timeout=timeo)
        else:
            scsI = gcf.omnilib.stitch.scs.Service(scs_url, timeout=timeo)
        if secure:
            result = listScsAggregate(scsI)
        else:
            # launch a daemon thread to list the aggregate and join for timeout
            t = ListAggregateThread(scsI)
            t.start()
            t.join(timeout=timeo)
            if t.is_alive():
                lock.acquire()
                opslogger.warning("ERROR: SCS checking at %s timed out" % scs_url)
                lock.release()
                raise Exception()
            result = t.result
        retval = 1
        try:
            verStruct = result
#             if verStruct and verStruct.has_key("value") and verStruct["value"].has_key("code_tag"):
#                 tag = verStruct["value"]["code_tag"]
            if verStruct and verStruct.has_key("code") and verStruct["code"].has_key("geni_code"):
                retval = verStruct["code"]["geni_code"]
            if retval == 0:
                mandatory_aggregates = config.get_expected_aggregates_for_scs(scs_id)
                if len(mandatory_aggregates) == 0:
                    # Nothing to check so we're good
                    lock.acquire()
                    opslogger.debug("list of mandatory aggregates for SCS %s is empty. No check will be performed on the returned list" % scs_id)
                    lock.release()
                    state = 1
                    qualifier = ""
                else:
                    if verStruct.has_key("value") and verStruct["value"].has_key("geni_aggregate_list"):
                        # This is a dictionary. Keys are "AM" names. Values are dictionary objects with url and urn entries.
                        listed_aggregates = verStruct["value"]["geni_aggregate_list"]
                        for am_urn in mandatory_aggregates.values():
                            for entry in listed_aggregates.values():
                                if entry.has_key('urn') and am_urn == entry['urn']:
                                    break
                            else:
                                # we did not find a match exiting the outer loop
                                lock.acquire()
                                opslogger.warning("ERROR: list of aggregates returned by SCS %s does not contain a mandatory URN (%s)" % (scs_id, am_urn))
                                lock.release()
                                break
                        else:
                            # we never exited this loop via a break, so we matched all mandatory URNs
                            lock.acquire()
                            opslogger.debug("All %d mandatory aggregates are present in the list of aggregates returned by SCS %s" % (len(mandatory_aggregates), scs_id))
                            lock.release()
                            state = 1
                            qualifier = ""
        except:
            lock.acquire()
            opslogger.warning("ERROR: SCS return not parsable")
            lock.release()
    except Exception:
        pass

    lock.acquire()
    opslogger.info("SCS %s is %savailable at %s" % (scs_id, qualifier, scs_url))
    lock.release()
    return state


def check_aggregate_state_for_one_url((monitored_aggregate_id, amtype, am_url, lock)):
#     print "Checking %s at %s" % (monitored_aggregate_id, am_url)
    if amtype == "foam":
        version = config.get_apiversion_from_am_url(am_url, amtype)
        site = SiteOF(monitored_aggregate_id, am_url, version)
        state = getOFState(context, site, lock)
    elif amtype == "protogeni" or \
        amtype == "instageni" or \
        amtype == "exogeni" or \
        amtype == "opengeni" or \
        amtype == "network-aggregate":
        state = getAMStateForURL(monitored_aggregate_id, am_url, amtype, config, lock)
    elif amtype == "stitcher":
        state = getStitcherState(monitored_aggregate_id, am_url, config, lock)
    ts = int(time.time() * 1000000)
    return (monitored_aggregate_id, ts, state)

def insert_aggregate_result(monitored_aggregate_id, results, dp):
    overall_state = 1  # let's be optimistic
    sum_ts = 0
    for (ts, state) in results:
        sum_ts += ts
        if state == 0:
            overall_state = 0
    avg_ts = int(sum_ts / len(results))
    dp.insert_agg_is_avail_datapoint(monitored_aggregate_id, avg_ts, overall_state)

def check_aggregate_state((monitored_aggregate_id, amtype, am_urls, dp, lock)):
    overall_state = 0  # unavailable until confirmed available.
    if amtype == "foam":
        first = True
        for url_tuple in am_urls:
            url = url_tuple[0]
            version = config.get_apiversion_from_am_url(url, amtype)
            site = SiteOF(monitored_aggregate_id, url, version)
            state = getOFState(context, site, lock)
            if first:
                overall_state = state
                first = False
            else:
                if (overall_state != 0):
                    if state == 0:
                        overall_state = 0
    elif amtype == "protogeni" or \
        amtype == "instageni" or \
        amtype == "exogeni" or \
        amtype == "opengeni" or \
        amtype == "network-aggregate":
        first = True
        for url_tuple in am_urls:
            url = url_tuple[0]
            state = getAMStateForURL(monitored_aggregate_id, url, amtype, config, lock)
            if first:
                overall_state = state
                first = False
            else:
                if (overall_state != 0):
                    if state == 0:
                        overall_state = 0
    elif amtype == "stitcher":
        first = True
        for url_tuple in am_urls:
            url = url_tuple[0]
            state = getStitcherState(monitored_aggregate_id, url, config, lock)
            if first:
                overall_state = state
                first = False
            else:
                if (overall_state != 0):
                    if state == 0:
                        overall_state = 0
    ts = int(time.time() * 1000000)
    lock.acquire()
    dp.insert_agg_is_avail_datapoint(monitored_aggregate_id, ts, overall_state)
    lock.release()

def main():

    db_name = "local"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    dp = DataPopulator(tbl_mgr)

    extck_id = config.get_extck_store_id()


    # get all monitored aggregates

    monitored_aggregates = tbl_mgr.query("SELECT id FROM ops_externalcheck_monitoredaggregate WHERE externalcheck_id = '%s'" % extck_id)
    if monitored_aggregates is None:
        opslogger.warning("Could not find any monitored aggregate. Has extck_store been executed?")
        return

    myLock = multiprocessing.Lock()
    argsList = []
    for monitored_aggregate_tuple in monitored_aggregates:
        monitored_aggregate_id = monitored_aggregate_tuple[0]
        opslogger.info("Checking availability of AM: %s", monitored_aggregate_id)
        amtype = tbl_mgr.query("SELECT type FROM extck_aggregate WHERE aggregate_id = '%s'" % monitored_aggregate_id)
        if amtype is None:
            opslogger.warning("Error trying to determine type of aggregate: %s" % monitored_aggregate_id)
            continue
        amtype = amtype[0][0]  # first value of first tuple...
        am_urls = tbl_mgr.query("SELECT amurl FROM extck_aggregate_amurl WHERE aggregate_id = '%s'" % monitored_aggregate_id)
        if am_urls is None:
            opslogger.warning("Did not find any registered AM URL for aggregate: %s" % monitored_aggregate_id)
            continue
#         args = (monitored_aggregate_id, amtype, am_urls, dp, myLock)
        for url_tuple in am_urls:
            url = url_tuple[0]
            args = (monitored_aggregate_id, amtype, url, myLock)
            argsList.append(args)
#         argsList.append(args)

    pool = multiprocessing.pool.ThreadPool(processes=int(config.get_populator_pool_size()))
    results = pool.map(check_aggregate_state_for_one_url, argsList)
    # Building the results
    # regroup results by aggregate_id
    agg_results = dict()
    for (monitored_aggregate_id, ts, state) in results:
        if not monitored_aggregate_id in agg_results:
            agg_results[monitored_aggregate_id] = list()
        agg_results[monitored_aggregate_id].append((ts, state))
    for monitored_aggregate_id in agg_results.keys():
        insert_aggregate_result(monitored_aggregate_id, agg_results[monitored_aggregate_id], dp)
    dp.db_purge_agg_is_available()

if __name__ == "__main__":
    main()
