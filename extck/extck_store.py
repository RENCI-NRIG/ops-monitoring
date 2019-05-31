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
import getopt
import json
import ConfigParser
import os
import requests
import multiprocessing
import multiprocessing.pool


extck_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(extck_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)
sys.path.append(extck_path)

# import opsconfig_loader
import table_manager
import extck_config

# input file with short-names and Urls aggregates
# Need this file for sites like EG that aren't in prod but url is not in opsconfig
# inputFileBackup=open('/home/amcanary/src/gcf/agg_nick_cache.base')

# inputFile = open('/home/amcanary/.bssw/geni/nickcache.json')

# Dic to store short name and corresponding url
# Format: shortName[urn]=[aggShortName, amType, selfRef, measRef, url, fqdn, schema]

# shortName = {}



class InfoPopulator():
    PING_CAMPUS = object()
    PING_CORE = object()

    def __init__(self, tbl_mgr, config, nickCache):
        """
        Constructor for InfoPopulator object
        :param tbl_mgr: the instance of table manager used to access the database.
        :param config: the ExtckConfigLoader instance used to get the configuration of the external check store.
        :param nickCache:the AggregateNickCache instance used to get urns from site nicknames.
        """
        self.tbl_mgr = tbl_mgr
        self._config = config
        self._nickCache = nickCache
        self.extckStoreBaseUrl = self._config.get_extck_store_base_url()
        self._extckStoreSite = self._config.get_extck_store_id()

        ipsconfig = ConfigParser.ConfigParser()
        ipsconfig.read(os.path.join(extck_path, "ips.conf"))
        self._ip_campus = dict(ipsconfig.items("campus"))
        self._ip_core = dict(ipsconfig.items("core"))

    def _getSiteInfo(self, srcSiteName, aggStores):
        am_urn = self._nickCache.get_am_urn(srcSiteName)
        am_url = ""
        # First let's try from the cache.
        if am_urn is not None:
            for store in aggStores:
                if store["urn"] == am_urn:
                    am_url = store["href"]
                    break;
        else:
            # then let's try from the opsconfig
            am_urn = ""
            for store in aggStores:
                if store.has_key("am_nickname") and store["am_nickname"] == srcSiteName:
                    am_urn = store["urn"]
                    am_url = store["href"]
                    break;
        return (am_urn, am_url)

    def populateExperimentInfoTables(self, aggStores):
        slices = self._config.get_experiment_slices_info()
        srcPingCampus = self._config.get_experiment_source_ping_campus()
        srcPingCore = self._config.get_experiment_source_ping_core()
        # Populate "ops_externalcheck_experiment" and "ops_experiment" tables
        self._populateExperimentInfoTables(slices, srcPingCampus, InfoPopulator.PING_CAMPUS, aggStores)
        self._populateExperimentInfoTables(slices, srcPingCore, InfoPopulator.PING_CORE, aggStores)

    def _populateExperimentInfoTables(self, slices, srcPing, ping_type, aggStores):
        exp_tablename = "ops_experiment"
        exp_schema = self.tbl_mgr.schema_dict[exp_tablename]
        ext_exp_tablename = "ops_externalcheck_experiment"
        ext_exp_schema = self.tbl_mgr.schema_dict[ext_exp_tablename]
        if ping_type == InfoPopulator.PING_CAMPUS:
            ipList = self._ip_campus
        elif ping_type == InfoPopulator.PING_CORE:
            ipList = self._ip_core
        else:
            self.tbl_mgr.logger.warning("Unrecoginzed ping type")
            return

        for srcSite in srcPing:
            for dstSite in ipList:
                if srcSite == dstSite:
                    # A site must not ping itself
                    continue

                slice_name = self._config.get_experiment_source_ping_slice_name(srcSite)
                sliceUrn = slices[slice_name][0]
                sliceUuid = slices[slice_name][1]

                if ping_type == InfoPopulator.PING_CAMPUS:
                    exp_id = srcSite + "_to_" + dstSite + "_campus"
                    srcSiteName = srcSite
                    dstSiteName = dstSite
                else:
                    # ip_core then
                    srcSiteFlag = srcSite.strip().split('-')
                    network = srcSiteFlag[-1:][0]  # last element
                    # getting the suffix of the destination
                    dstSiteFlag = dstSite.strip().split('-')
                    if network != dstSiteFlag[-1:][0]:
                        # Can't ping between hosts in different networks
                        continue
                    exp_id = srcSite + "_to_" + dstSite
                    srcSiteName = srcSite[:-len(network) - 1]
                    dstSiteName = dstSite[:-len(network) - 1]

                (srcAmUrn, srcAmHref) = self._getSiteInfo(srcSiteName, aggStores)
                (dstAmUrn, dstAmHref) = self._getSiteInfo(dstSiteName, aggStores)
                if srcAmUrn == '' or srcAmHref == '' or dstAmUrn == '' or dstAmHref == '':
                    self.tbl_mgr.logger.warning("Error when getting info from source %s and dest %s, got src urn %s, src href %s, dst urn %s, dst href %s"
                                                % (srcSite, dstSite, srcAmUrn, srcAmHref, dstAmUrn, dstAmHref))
                    continue
                else:
                    ts = str(int(time.time() * 1000000))
                    exp = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/experiment#",
                           exp_id,
                           self.extckStoreBaseUrl + "/info/experiment/" + exp_id,
                           ts,
                           sliceUrn,
                           sliceUuid,
                           srcAmUrn,
                           srcAmHref,
                           dstAmUrn,
                           dstAmHref
                           ]
                    self.tbl_mgr.upsert(exp_tablename, exp_schema, exp, self.tbl_mgr.get_column_from_schema(exp_schema, "id"))
                    extck_exp = [exp_id, self._extckStoreSite, self.extckStoreBaseUrl + "/info/experiment/" + exp_id]
                    self.tbl_mgr.upsert(ext_exp_tablename, ext_exp_schema, extck_exp,
                                        (self.tbl_mgr.get_column_from_schema(ext_exp_schema, "id"),
                                         self.tbl_mgr.get_column_from_schema(ext_exp_schema, "externalcheck_id")))

    def insert_externalcheck_monitoredaggregate(self, urn, aggRow):
        aggregate_id = aggRow[1]  # agg_id
        dataStoreHref = aggRow[2]
        mon_agg = [aggregate_id, self._extckStoreSite, dataStoreHref]
        ext_monagg_tablename = "ops_externalcheck_monitoredaggregate"
        ext_monagg_schema = self.tbl_mgr.schema_dict[ext_monagg_tablename]

        self.tbl_mgr.upsert(ext_monagg_tablename, ext_monagg_schema, mon_agg,
                    (self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "id"),
                     self.tbl_mgr.get_column_from_schema(ext_monagg_schema, "externalcheck_id")))


    def insert_aggregate(self, urn, aggRow):
        agg_tablename = "ops_aggregate"
        agg_schema = self.tbl_mgr.schema_dict[agg_tablename]

        self.tbl_mgr.upsert(agg_tablename, agg_schema, aggRow,
                    self.tbl_mgr.get_column_from_schema(agg_schema, "id"))

    def insert_aggregate_url(self, aggregate_id, aggregate_manager_url):
        agg_amurl_tablename = "extck_aggregate_amurl"
        agg_amurl_schema = self.tbl_mgr.schema_dict[agg_amurl_tablename]
        index_agg = self.tbl_mgr.get_column_from_schema(agg_amurl_schema, "aggregate_id")
        index_amurl = self.tbl_mgr.get_column_from_schema(agg_amurl_schema, "amurl")
        if index_agg < index_amurl:
            row = (aggregate_id, aggregate_manager_url)
        else:
            row = (aggregate_manager_url, aggregate_id)
        self.tbl_mgr.upsert(agg_amurl_tablename, agg_amurl_schema, row, (index_agg, index_amurl))

    def insert_aggregate_type(self, aggregate_id, aggregate_type):
        agg_tablename = "extck_aggregate"
        agg_schema = self.tbl_mgr.schema_dict[agg_tablename]
        index_agg = self.tbl_mgr.get_column_from_schema(agg_schema, "aggregate_id")
        index_type = self.tbl_mgr.get_column_from_schema(agg_schema, "type")
        if index_agg < index_type:
            row = (aggregate_id, aggregate_type)
        else:
            row = (aggregate_type, aggregate_id)
        self.tbl_mgr.upsert(agg_tablename, agg_schema, row, index_agg)

    def insert_externalcheck(self):
        ts = str(int(time.time() * 1000000))
        extck = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#",
                 self._extckStoreSite,
                 self.extckStoreBaseUrl + "/info/externalcheck/" + self._extckStoreSite,
                 ts,
                 self.extckStoreBaseUrl + "/data/"]
        table_str = "ops_externalcheck"
        extck_schema = self.tbl_mgr.schema_dict[table_str]
        self.tbl_mgr.upsert(table_str, extck_schema, extck, self.tbl_mgr.get_column_from_schema(extck_schema, "id"))

    def cleanUpObsoleteAggregates(self, aggStores):
        """
        Method to clean up existing aggregate manager entries that no longer exists 
        in the opsconfig data store.
        :param aggStores: a json dictionary object corresponding to the "aggregatestores" 
          entry of the opsconfig json.
        """
        registeredAggs = self.tbl_mgr.query("select urn, id from ops_aggregate");
        if registeredAggs is None:
            return
        currentUrnList = []
        for store in aggStores:
            currentUrnList.append(store["urn"])
        for agg_details in registeredAggs:
            if agg_details[0] not in currentUrnList:
                # Looks like we had an old aggregate registered
                self.tbl_mgr.logger.info("Aggregate %s (%s) is obsolete: deleting corresponding records" % (agg_details[1], agg_details[0]))
                self.tbl_mgr.execute_sql("delete from ops_aggregate_is_available where id='%s'" % agg_details[1])
                self.tbl_mgr.execute_sql("delete from ops_externalcheck_monitoredaggregate where id='%s'" % agg_details[1])
                self.tbl_mgr.execute_sql("delete from extck_aggregate where aggregate_id='%s'" % agg_details[1])
                self.tbl_mgr.execute_sql("delete from extck_aggregate_amurl where aggregate_id='%s'" % agg_details[1])
                self.tbl_mgr.execute_sql("delete from ops_aggregate where id='%s'" % agg_details[1])


# def db_insert(tbl_mgr, table_str, row_arr):
#     val_str = "('"
#
#     for val in row_arr:
#         val_str += val + "','"  # join won't do this
#
#     val_str = val_str[:-2] + ")"  # remove last 2 of 3 chars: ',' and add )
#
#     tbl_mgr.insert_stmt(table_str, val_str)

def get_default_attribute_for_type(vartype):
    val = "";
    if vartype.startswith("int"):
        val = 0
    return val


def extract_row_from_json_dict(logger, db_table_schema, object_dict, object_desc, db_to_json_map=None):
    """
    Method to extract values from a json dictionary corresponding to database columns.
    :param logger: logger object
    :param db_table_schema: a database table schema in the usual format (list of tuples whose first value is
    column name, second is column type, third is whether the value is optional or not)
    :param object_dict: the json dictionary for an object
    :param object_desc: object short description. This will be used in a warning message if the object
    attribute was expected but not present in the json dictionary
    :param db_to_json_map: a map to get the json key(s) from a column name.
    :return: the list of attributes for the object. This list will be
    formed with the values from the json dictionary in the order of the database table columns.
    A value will be None if the field was optional and not present, or a default value if the field
    was required and not present.
    """
    object_attribute_list = []
    for db_column_schema in db_table_schema:
        missing = False
        if (db_to_json_map is not None) and (db_column_schema[0] in db_to_json_map):
            jsonkeys = db_to_json_map[db_column_schema[0]]
            missing = False
            jsondict = object_dict
            for jsonkey in jsonkeys:
                if jsonkey in jsondict:
                    jsondict = jsondict[jsonkey]
                else:
                    missing = True
                    break
            if not missing:
                object_attribute_list.append(jsondict)  # the last iteration is the value itself, not another dictionary.
            else:
                jsondesc = ""
                for jsonkey in jsonkeys:
                    jsondesc += "[\"" + jsonkey + "\"]"
        else:
            if db_column_schema[0].startswith("properties$"):
                jsonkey = "ops_monitoring:" + db_column_schema[0].split('$')[1]
            else:
                jsonkey = db_column_schema[0]

            if jsonkey in object_dict:
                object_attribute_list.append(object_dict[jsonkey])
            else:
                missing = True
                jsondesc = jsonkey

        if missing:
            if db_column_schema[2]:
                logger.warn("value for required json " + object_desc + " field "
                             + jsondesc + " is missing. Replacing with default value...")
                object_attribute_list.append(get_default_attribute_for_type(db_column_schema[1]))
            else:
                # This is OK. This was an optional field.
                object_attribute_list.append(None)
    return object_attribute_list

class AggregateNickCache:

    __NICKNAMES_SECTION = "aggregate_nicknames"

    def __init__(self, nickfile):
        """
        :param nickfile: the name of the aggregate nickname cache configuration file.
        """
        self._nickfile = nickfile
        self._nickconfig = ConfigParser.ConfigParser()
        self._has_read = False

    def parseNickCache(self):
        """
        method to parse an omni-type  aggregate nickname cache configuration file.
        :return: a map that has aggregate managers as keys and sets of AM API URLs 
        as values.
        """
        urn_to_urls_map = dict()
        if not self._has_read:
            if self._nickfile in self._nickconfig.read(self._nickfile):
                self._has_read = True

        # Going over the whole section
        nicknames = self._nickconfig.items(AggregateNickCache.__NICKNAMES_SECTION)
        for _key, urn_url in nicknames:
            [urn, url] = urn_url.split(",")
            urn = urn.strip()
            url = url.strip()
            if urn != "":
                if not urn_to_urls_map.has_key(urn):
                    urn_to_urls_map[urn] = set()
                urn_to_urls_map[urn].add(url)
        return urn_to_urls_map

    def updateCache(self, urn_to_urls_map, aggStores):
        """
        method to update the map of urns to AM API URLS for the Aggregate Managers, per 
        the ops config information, which may contain the AM API URL, for AM that are not 
        in production yet.
        :param urn_to_urls_map: the map of urns to AM API URLS for the Aggregate Managers.
        :param aggStores: a json dictionary object corresponding to the "aggregatestores" 
          entry of the opsconfig json.
        """
        for aggregate in aggStores:
            if aggregate.has_key('amurl'):
                urn = aggregate['urn']
                if not urn_to_urls_map.has_key(urn):
                    urn_to_urls_map[urn] = set()
                for agg_key in aggregate.keys():
                    # Add url for all keys starting with amurl
                    if agg_key[:5] == "amurl":
                        urn_to_urls_map[urn].add(aggregate[agg_key])

    def get_am_urn(self, am_nickname):
        """
        Method to get the AM URN given its nickname.
        :param am_nickname: the nickname of the AM
        :return: Returns the AM URN or None if the nickname wasn't found.
        """
        try:
            valstr = self._nickconfig.get(AggregateNickCache.__NICKNAMES_SECTION, am_nickname)
        except:
            return None

        vals = valstr.split(',')
        return vals[0].strip()

def registerOneAggregate((cert_path, urn_to_urls_map, ip, amtype, urn,
                         ops_agg_schema, agg_schema_str, monitoring_version,
                         extck_measRef, aggregate, lock)):
    if amtype == 'instageni' or \
            amtype == 'protogeni' or \
            amtype == "exogeni" or \
            amtype == "opengeni" or \
            amtype == "network-aggregate":
        if not urn_to_urls_map.has_key(urn):
            lock.acquire()
            ip.tbl_mgr.logger.warning("No known AM API URL for aggregate: %s\n Will NOT monitor" % urn)
            lock.release()
            return
        aggDetails = handle_request(ip.tbl_mgr.logger, cert_path, aggregate['href'])  # Use url for site's store to query site
        if aggDetails == None:
            return
        agg_attributes = extract_row_from_json_dict(ip.tbl_mgr.logger, ops_agg_schema, aggDetails, "aggregate")
    elif amtype == "stitcher":  # Special case
        selfRef = aggregate['href'];
        if not aggregate.has_key('am_nickname'):
            lock.acquire()
            ip.tbl_mgr.logger.warning("stitcher AM has missing nickname for %s\n Will NOT monitor" % selfRef)
            lock.release()
            return
        if not aggregate.has_key('am_status'):
            lock.acquire()
            ip.tbl_mgr.logger.warning("stitcher AM has missing status for %s\n Will NOT monitor" % selfRef)
            lock.release()
            return
        aggId = aggregate['am_nickname']
        ts = str(int(time.time() * 1000000))
        ops_status = aggregate['am_status']
        agg_attributes = (agg_schema_str,  # schema
                          aggId,  # id
                          selfRef,  # selfref
                          urn,  # urn
                          ts,  # time stamp
                          extck_measRef,  # meas Ref
                          monitoring_version,  # # populator version
                          ops_status,  # operational status
                          None  # routable IP poolsize
                          )
    elif amtype == "foam" :
        # FOAM
        if not urn_to_urls_map.has_key(urn):
            lock.acquire()
            ip.tbl_mgr.logger.warning("No known AM API URL for aggregate: %s\n Will NOT monitor" % urn)
            lock.release()
            return

        selfRef = aggregate['href']

        if aggregate.has_key('amurl'):  # For non-prod foam aggregates
            ops_status = "development"
        else:
            ops_status = "production"

        # Get aggregate id
        cols = selfRef.strip().split('/')
        aggId = cols[len(cols) - 1]  # Grab last component in cols

        ts = str(int(time.time() * 1000000))
        agg_attributes = (agg_schema_str,  # schema
                          aggId,  # id
                          selfRef,  # selfref
                          urn,  # urn
                          ts,  # time stamp
                          extck_measRef,  # meas Ref
                          monitoring_version,  # # populator version
                          ops_status,  # operational status
                          None  # routable IP poolsize
                          )
    elif amtype == "wimax":
        # wimax are not really aggregates...
        # So no AM API can't be queried for their availability
        lock.acquire()
        ip.tbl_mgr.logger.info("Wimax aggregate won't be monitored (%s)" % urn)
        lock.release()
        return
    else:
        lock.acquire()
        ip.tbl_mgr.logger.warning("Unrecognized AM type: " + amtype)
        lock.release()
        return

    lock.acquire()
    # Populate "ops_aggregate" table
    ip.insert_aggregate(urn, agg_attributes)
    # Populate "ops_externalcheck_monitoredaggregate" table
    ip.insert_externalcheck_monitoredaggregate(urn, agg_attributes)
    ip.insert_aggregate_type(agg_attributes[1], amtype)

    am_urls = urn_to_urls_map[urn]
    for am_url in am_urls:
        ip.insert_aggregate_url(agg_attributes[1], am_url)
    lock.release()

def registerAggregates(aggStores, cert_path, urn_to_urls_map, ip, config):
    """
    Function to register aggregates in the database.
    :param aggStores: a json dictionary object corresponding to the "aggregatestores" 
      entry of the opsconfig json.
    :param cert_path: the path to the collector certificate used to retrieve the 
      aggregate manager characteristics from the aggregate data store.
    :param urn_to_urls_map: Map of aggregate manager URN to AM API URLs.
    :param ip: instance of the InfoPopulator object used to populate the DB
    """
    ops_agg_schema = ip.tbl_mgr.schema_dict["ops_aggregate"]
    # TODO parameterize these
    agg_schema_str = "http://www.gpolab.bbn.com/monitoring/schema/20140828/aggregate#"
    version_filename = top_path + "/VERSION"
    try:
        version_file = open(version_filename)
        monitoring_version = version_file.readline().strip()
        version_file.close()
    except Exception, e:
        ip.tbl_mgr.logger.warning("Could not read monitoring version from file %s: %s" % (
                version_filename, str(e)))
        monitoring_version = "unknown"

    extck_measRef = ip.extckStoreBaseUrl + "/data/"

    myLock = multiprocessing.Lock()
    argsList = []
    for aggregate in aggStores:
        amtype = aggregate['amtype']
        urn = aggregate['urn']
        args = (cert_path, urn_to_urls_map, ip, amtype, urn,
                ops_agg_schema, agg_schema_str, monitoring_version,
                extck_measRef, aggregate, myLock)
        argsList.append(args)


    pool = multiprocessing.pool.ThreadPool(processes=int(config.get_populator_pool_size()))
    pool.map(registerOneAggregate, argsList)

def handle_request(logger, cert_path, url):

    resp = None
    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except Exception, e:
        logger.warning("No response from datastore at: " + url)
        logger.warning(e)
        return None

    if resp:
        try:
            json_dict = json.loads(resp.content)
        except Exception, e:
            logger.warning("Could not load response from " + url + " into JSON")
            logger.warning(e)
            return None

        return json_dict
    else:
        logger.warning("could not reach datastore at " + url)
        return None


def usage():
    usage = '''
    extck_store.py performs information fetching on the different aggregates listed by opsconfig. 
    It puts aggregate and experiment information in the local database.  It needs to be
    called with the arguments specifying a certificate

     -c or --certpath= <pathname> provides the path to your tool certificate
     -h or --help prints the usage information.
    '''
    print(usage)
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    cert_path = ""

    try:
        opts, _ = getopt.getopt(argv, "hc:", ["help", "certpath="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in("-h", "--help"):
            usage()
        elif opt in ("-c", "--certpath"):
            cert_path = arg
        else:
            usage()

    return [cert_path]


def main(argv):

    [cert_path] = parse_args(argv)
    db_name = "local"
    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()
    config = extck_config.ExtckConfigLoader(tbl_mgr.logger)
    extck_tables_schemas = config.get_extck_table_schemas()
    extck_tables_constraints = config.get_extck_table_constraints()
    for table_name in extck_tables_schemas.keys():
        tbl_mgr.add_table_schema(table_name, extck_tables_schemas[table_name])
        tbl_mgr.add_table_constraints(table_name, extck_tables_constraints[table_name])
        tbl_mgr.establish_table(table_name)


    nickCache = AggregateNickCache(config.get_nickname_cache_file_location())

    ip = InfoPopulator(tbl_mgr, config, nickCache)
    # Populate "ops_externalCheck" table
    ip.insert_externalcheck()

    # Grab urns and urls for all agg stores
    opsconfig_url = config.get_opsconfigstore_url()
    aggRequest = handle_request(tbl_mgr.logger, cert_path, opsconfig_url)

    if aggRequest == None:
        tbl_mgr.logger.warning("Could not not contact opsconfigdatastore!")
        return
    aggStores = aggRequest['aggregatestores']


    urn_map = nickCache.parseNickCache()
    nickCache.updateCache(urn_map, aggStores)

    ip.cleanUpObsoleteAggregates(aggStores)

    registerAggregates(aggStores, cert_path, urn_map, ip, config)

    # Populate "ops_externalcheck_experiment" and "ops_experiment" tables
    ip.populateExperimentInfoTables(aggStores)

if __name__ == "__main__":
    main(sys.argv[1:])
