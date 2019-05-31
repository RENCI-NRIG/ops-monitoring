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

import time
import json
import sys
import getopt
import requests
import pprint
import os
import multiprocessing
import multiprocessing.pool

collector_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(collector_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
import table_manager
import opsconfig_loader
import logger

def usage():
    sys.stderr.write('single_datastore_object_type_fetcher.py -d -a <aggregateid> -e <extckid> -c </cert/path/cert.pem> -o <objecttype (ex: -o n for nodes -o i interfaces, s for slivers, l for links, v for vlans, a for aggregate, x for experiments)>\n')
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    aggregate_id = ""
    extck_id = ""
    object_type = ""
    cert_path = ""
    debug = False

    try:
        opts, _ = getopt.getopt(argv, "ha:e:c:o:d", ["help", "aggregateid=", "extckid=", "certpath=", "objecttype=", "debug"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-e", "--extckid"):
            extck_id = arg
        elif opt in ("-c", "--certificate"):
            cert_path = arg
        elif opt in ("-o", "--objecttype"):
            object_type = arg
        elif opt in ("-d" or "--debug"):
            debug = True
        else:
            usage()

    return [aggregate_id, extck_id, object_type, cert_path, debug]


def fetch_content((fetcher, url)):
    return fetcher.fetch_content(url)

def tsdata_insert((fetcher, datastore_id, obj_id, table_str, tsdata)):
    return fetcher.tsdata_insert(datastore_id, obj_id, table_str, tsdata)

class SingleLocalDatastoreObjectTypeFetcher:

    __THREAD_POOL_SIZE = 6

    def __init__(self, tbl_mgr, aggregate_id, extck_id, obj_type, event_types, cert_path, debug, config_path):

        self.logger = logger.get_logger(config_path)
        self.tbl_mgr = tbl_mgr

        # The local datastore this thread queries
        # Exactly one of these should be ""
        self.aggregate_id = aggregate_id
        self.extck_id = extck_id

        # Query filter parameters
        self.obj_type = obj_type

        # collector certificate path
        self.cert_path = cert_path

        # ensures tables exist
        if not self.tbl_mgr.establish_all_tables():
            self.logger.critical("Could not establish all the tables. Exiting")
            sys.exit(-1)
        self.db_event_tables = ["ops_" + obj_type + "_" + ev_str for ev_str in event_types]

        self.event_types = ["ops_monitoring:" + ev_str for ev_str in event_types]

        # Set parameter to avoid query for all history since epoch = 0
        self.time_of_last_update = self.get_latest_ts()

        self.debug = debug

        if self.aggregate_id != "":
            self.meas_ref = self.get_meas_ref("ops_aggregate", self.aggregate_id)
        elif self.extck_id != "":
            self.meas_ref = self.get_meas_ref("ops_externalcheck", self.extck_id)

        self.obj_ids = self.get_object_ids(obj_type)
        self.lock = multiprocessing.Lock()
        self.pool = multiprocessing.pool.ThreadPool(processes=SingleLocalDatastoreObjectTypeFetcher.__THREAD_POOL_SIZE)


    def fetch_and_insert(self):
        """
        Method to fetch the data and store it in the collector DB.
        :return: True if everything went OK, False otherwise.
        """
        ok = True
        # poll datastore
        json_texts = self.poll_datastore()
#        if self.debug:
#            print json_texts

        onlyErr = True

        # there should be at least one answer unless we had issues retrieving it
        argsArray = []
        for json_text in json_texts:
            data = None
            try:
                data = json.loads(json_text)
            except ValueError, e:
                self.logger.warning("Unable to load response in json %s\n" % e)
                self.logger.warning("response = \n" + json_text)
                ok = False

            if data is not None:
                onlyErr = False
                for result in data:
                    self.logger.debug("Result received from %s about:" % self.aggregate_id)
                    self.logger.debug(pprint.pformat(result["id"]))

                    event_type = result["eventType"]
                    if event_type.startswith("ops_monitoring:"):
                        table_str = "ops_" + self.obj_type + "_" + event_type[15:]

                        # if id is event:obj_id_that_was_queried,
                        # TODO straighten out protocol with monitoring group
                        # for now go with this
                        id_str = result["id"]

                        # remove event: and prepend aggregate_id:
                        if self.aggregate_id != "":
                            datastore_id = self.aggregate_id
                        elif self.extck_id != "":
                            datastore_id = self.extck_id
                        obj_id = id_str[id_str.find(':') + 1:]

                        tsdata = result["tsdata"]
                        if len(tsdata) > 0:
                            argsArray.append((self, datastore_id, obj_id, table_str, tsdata))
#                             if not self.tsdata_insert(datastore_id, obj_id, table_str, tsdata):
#                                 ok = False
        if len(argsArray) > 0:
            results = self.pool.map(tsdata_insert, argsArray)
            for tmp_ok in results:
                if not tmp_ok:
                    ok = False

        if onlyErr:
            ok = False
        return ok

    def get_latest_ts(self):
        max_ts = 0
        for table_str in self.db_event_tables:
            ts = self.get_latest_ts_at_table(table_str)
            if ts > max_ts:
                max_ts = ts
        return max_ts

    # Retrieves these from the collector database
    def get_object_ids(self, obj_type):

        obj_ids = []

        if obj_type == "node":
            obj_ids = self.get_all_nodes_of_aggregate()

        elif obj_type == "aggregate":
            obj_ids = self.get_all_aggregates_of_extckstore()

        elif obj_type == "interface":
            obj_ids = self.get_all_interfaces_of_aggregate()

        elif obj_type == "interfacevlan":
            obj_ids = self.get_all_interfacevlans_of_aggregate()

        elif obj_type == "experiment":
            obj_ids = self.get_all_experiments_of_extckstore()

        else:
            sys.stderr.write("Invalid object type %s" % obj_type)
            sys.exit(1)

        return obj_ids


    def create_datastore_query(self, obj_ids, req_time):
        """
        Creates a data query URL for specific objects and a specific time range.
        :param obj_ids: the arrays of object IDs to request
        :param req_time: the upper bound of the time range.
        :return: the expected data query URL. 
        """
        # Making sure we're querying a 3 months interval max.
        _MAX_DIFF = 2592000000000  #  90 * 24 * 60 * 60 * 1000000
        last_update = self.time_of_last_update
        if (req_time - self.time_of_last_update) > _MAX_DIFF:
            last_update = req_time - _MAX_DIFF
        q = {"filters":{"eventType":self.event_types,
                        "obj":{"type": self.obj_type,
                               "id": obj_ids},
                        "ts": {"gt": last_update,
                               "lt": req_time}
                        }
             }

        url = self.meas_ref + "?q=" + json.dumps(q)
        url = url.replace(' ', '')
        return url;

    def fetch_content(self, url):
        self.lock.acquire()
        self.logger.debug(url)
        self.logger.debug("URL length = " + str(len(url)))
        self.lock.release()

        resp = None
        try:
            resp = requests.get(url, verify=False, cert=self.cert_path)
        except requests.exceptions.RequestException, e:
            self.lock.acquire()
            self.logger.warning("No response from local datastore at: " + url)
            self.logger.warning(e)
            self.lock.release()

        if resp is not None:
            if (resp.status_code == requests.codes.ok):
                return resp.content
            else:
                self.lock.acquire()
                self.logger.warning("Response from " + url + " is invalid, code = " + str(resp.status_code))
                self.lock.release()
        return None

    def poll_datastore(self):
        _MAX_URL_LEN = 2000
        # current time for lt filter and record keeping
        req_time = int(time.time() * 1000000)

        url = self.create_datastore_query(self.obj_ids, req_time)
        urls = []

        if (len(url) > _MAX_URL_LEN):
            if self.debug:
                print "Data query URL too big. Breaking it"
            ids_len = 0
            for obj_id in self.obj_ids:
                ids_len += len(obj_id) + 3  # 2 quotes and a comma
            ids_len -= 1  # removing one comma too many
            baselen = len(url) - ids_len;  # that's how big the url is without any object ids in in.
            maxids_len = _MAX_URL_LEN - baselen;  # that's the max len we can have to list obj IDs
            obj_ids = []
            running_len = 0
            for obj_id in self.obj_ids:
                obj_len = len(obj_id)
                if running_len == 0:
                    nextlen = obj_len + 2
                else:
                    nextlen = running_len + obj_len + 3
                if (nextlen) <= maxids_len:
                    # we keep going
                    obj_ids.append(obj_id)
                    running_len = nextlen
                else:
                    # it's a wrap for that portion
                    urls.append(self.create_datastore_query(obj_ids, req_time))
                    running_len = obj_len + 2
                    obj_ids = [ obj_id ]
            # out of the loop
            if (running_len > 0):
                urls.append(self.create_datastore_query(obj_ids, req_time))
            if self.debug:
                print "Will request " + str(len(urls)) + " data urls"
        else:
            urls = [url]

        contents = []
        argsArray = []
        for url in urls:
            argsArray.append((self, url))
        results = self.pool.map(fetch_content, argsArray)
        for cont in results:
            if cont is not None:
                contents.append(cont)

        return contents


    def get_latest_ts_at_table(self, table_str):
        tbl_mgr = self.tbl_mgr
        if self.aggregate_id != "":
            desc = "aggregate store"
            column_id = "aggregate_id"
            datastore_id = self.aggregate_id
        elif self.extck_id != "":
            desc = "external check store"
            column_id = "externalcheck_id"
            datastore_id = self.extck_id

        self.logger.debug("Getting latest timestamp in " + table_str + " for " + desc + " " + datastore_id)
        res = 0
        q_res = tbl_mgr.query("select max(ts) from " + table_str
                              + " where " + column_id + " = '" + datastore_id + "'")
        if q_res is not None:
            res = q_res[0][0]  # gets first of single tuple

        # We may have gotten a None for the timestamp if the table was empty.
        if res is None:
            res = 0
        self.logger.debug("latest timestamp in " + table_str + " for aggregate " + datastore_id
                          + " is: " + str(res) + " (" + time.asctime(time.gmtime(res / 1000000)) + ")")
        return res


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_aggregates_of_extckstore(self):
        tbl_mgr = self.tbl_mgr

        res = [];
        q_res = tbl_mgr.query("select id from ops_externalcheck_monitoredaggregate where externalcheck_id = '" + self.extck_id + "'")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_experiments_of_extckstore(self):
        tbl_mgr = self.tbl_mgr

        res = [];
        q_res = tbl_mgr.query("select id from ops_externalcheck_experiment where externalcheck_id = '" + self.extck_id + "'")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select id from ops_node_interface where node_id in \
                               (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" \
                               + aggregate_id + "'))")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfacevlans_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        res = [];
        q_res = tbl_mgr.query("select distinct id from ops_link_interfacevlan where link_id in \
                               (select id from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" \
                               + aggregate_id + "'))")
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_meas_ref(self, tbl_str, object_id):
        tbl_mgr = self.tbl_mgr

        meas_ref = None
        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("measRef") + " from " + tbl_str + " where id = '" + object_id + "' limit 1")
        if q_res is not None:
            meas_ref = q_res[0][0]  # gets first of single tuple

        if meas_ref is None:
            sys.stderr.write("ERROR: No measurement ref found for aggregate: %s\nRun the info_crawler to find this or wrong argument passed \n" % self.aggregate_id)
            sys.exit(1)

        return meas_ref

    def tsdata_insert(self, agg_id, obj_id, table_str, tsdata):
        """
        Method to insert time series data into a given table about a given object.
        :param agg_id: the id of the aggregate that reported the data
        :param obj_id: the id of the object that the data is pertaining to.
        :param table_str: the name of the table
        :param tsdata: the list of time series data in dictionary format
        :return: True if the insertion happened (or would have happened in debug mode) correctly, False otherwise.
        """
        _CHUNK_SIZE = 10
        ok = True
        vals_str = ""
        for i in range(len(tsdata)):
            tsdata_i = tsdata[i]
            vals_str += "('" + str(agg_id) + "','" + str(obj_id) + "','" + str(tsdata_i["ts"]) + "','" + str(tsdata_i["v"]) + "'),"
            if (i != 0) and (i % _CHUNK_SIZE == 0):
                vals_str = vals_str[:-1]  # remove last ','
                if self.debug:
                    self.logger.info("<print only> insert " + table_str + " values: " + vals_str)
                else:
                    if not self.tbl_mgr.insert_stmt(table_str, vals_str):
                        ok = False
                vals_str = ""

        if vals_str != "":
            vals_str = vals_str[:-1]  # remove last ','
            if self.debug:
                self.logger.info("<print only> insert " + table_str + " values: " + vals_str)
            else:
                if not self.tbl_mgr.insert_stmt(table_str, vals_str):
                    ok = False


        return ok


def main(argv):

    [aggregate_id, extck_id, object_type_param, cert_path, debug] = parse_args(argv)
    if (aggregate_id == "" and extck_id == "") or object_type_param == "" or cert_path == "":
        usage()

    db_type = "collector"
    # If in debug mode, make sure to overwrite the logging configuration to print out what we want,
    if debug:
        logger.configure_logger_for_debug_info(config_path)

    logger.get_logger(config_path).info("Starting object data fetching")

    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()

    ocl = opsconfig_loader.OpsconfigLoader(config_path)
    all_event_types = ocl.get_event_types()


    node_event_types = all_event_types["node"]
    interface_event_types = all_event_types["interface"]
    interface_vlan_event_types = all_event_types["interfacevlan"]
    aggregate_event_types = all_event_types["aggregate"]
    experiment_event_types = all_event_types["experiment"]

    # pprint(all_event_types)

    if object_type_param == 'n':
        logger.get_logger(config_path).debug("Fetching node events")
        event_types = node_event_types
        object_type = "node"
    elif object_type_param == 'i':
        logger.get_logger(config_path).debug("Fetching interface events")
        event_types = interface_event_types
        object_type = "interface"
    elif object_type_param == 'v':
        logger.get_logger(config_path).debug("Fetching interfacevlan events")
        event_types = interface_vlan_event_types
        object_type = "interfacevlan"
    elif object_type_param == 'a':
        logger.get_logger(config_path).debug("Fetching aggregate events")
        event_types = aggregate_event_types
        object_type = "aggregate"
    elif object_type_param == 'x':
        logger.get_logger(config_path).debug("Fetching experiements events")
        event_types = experiment_event_types
        object_type = "experiment"
    else:
        logger.get_logger(config_path).critical("invalid object type arg %s\n" % object_type_param)
        sys.stderr.write("invalid object type arg %s\n" % object_type_param)
        sys.exit(1)

    fetcher = SingleLocalDatastoreObjectTypeFetcher(tbl_mgr, aggregate_id, extck_id, object_type, event_types, cert_path, debug, config_path)

    if not fetcher.fetch_and_insert():
        logger.get_logger(config_path).critical("fetch_and_insert() failed")
        sys.exit(-1)


if __name__ == "__main__":
    main(sys.argv[1:])
