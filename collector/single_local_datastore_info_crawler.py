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

import json
import sys
import requests
import getopt
import multiprocessing
import multiprocessing.pool
import os

collector_path = os.path.abspath(os.path.dirname(__file__))
top_path = os.path.dirname(collector_path)
common_path = os.path.join(top_path, "common")
config_path = os.path.join(top_path, "config")
sys.path.append(common_path)

import table_manager
import logger

# am_urls is a list of dictionaies with hrefs to reach the datastore of
# the am urn

# This program populates the collector database on every fetch

def usage():
    usage = '''
    single_local_datastore_info_crawler.py performs information
    fetching. It puts data in the collector database.  It needs to be
    called with four arguments specifying a certificate, a base URL,
    either an aggregate id or an external check id and the list of object
    types to retrieve.

     -c or --certpath= <pathname> provides the path to your tool certificate
     -b or --baseurl= <local-store-info-base-url>
        This usually starts with "https://" and the convention is to end with "/info"
     -a or --aggregateid= <aggregate_id>
        This is the aggregate ID at the base URL (value of -b) data store (i.e., gpo-ig)
     -e or --extckid= <external_check_id>
        This is the external check store ID at the base URL (value of -b) data store (i.e., gpo)
     -o or --object-types= <objecttypes-of-interest>
        This is a list of letters of object types to get info on.
        If querying information on an aggregate store:
         - n: for node
         - i: for interface
         - s: for sliver
         - l: for link
         - v: for vlan
        If querying information on an external check store:
         - x: for experiments
         - e: for external checks
        So argument -o nislv will get information on all object types for an aggregate.
     -d or --debug will print what changes would be made to the collector database
        to the screen and does not modify the database
     -h or --help prints the usage information.
    '''
    print(usage)
    sys.exit(1)

def parse_args(argv):
    if argv == []:
        usage()

    base_url = ""
    aggregate_id = ""
    extck_id = ""
    object_types = ""
    cert_path = ""
    debug = False

    try:
        opts, _ = getopt.getopt(argv, "hb:a:e:c:o:d", ["help", "baseurl=", "aggregateid=", "extckid=", "certpath=", "objecttypes=", "debug"])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt in("-h", "--help"):
            usage()
        elif opt in ("-b", "--baseurl"):
            base_url = arg
        elif opt in ("-a", "--aggregateid"):
            aggregate_id = arg
        elif opt in ("-e", "--extckid"):
            extck_id = arg
        elif opt in ("-c", "--certpath"):
            cert_path = arg
        elif opt in ("-o", "--objecttypes"):
            object_types = arg
        elif opt in ("-d", "--debug"):
            debug = True
        else:
            usage()

    return [base_url, aggregate_id, extck_id, object_types, cert_path, debug]

def refresh_one_links_information((crawler, link_ref_object, link_schema, resource_schema)):
    return crawler.refresh_one_link_info(link_ref_object, link_schema, resource_schema)

def refresh_one_sliver_information((crawler, sliver_ref_object, sliver_schema, agg_sliver_schema)):
    return crawler.refresh_one_sliver_info(sliver_ref_object, sliver_schema, agg_sliver_schema)

def refresh_one_node_information((crawler, resource_object, schema, res_schema)):
    return crawler.refresh_one_node_info(resource_object, schema, res_schema)

def refresh_interface_information_for_one_node((crawler, node_url, nodeif_schema, ifaddr_schema)):
    return crawler.refresh_interface_info_for_one_node(node_url, nodeif_schema, ifaddr_schema)

def refresh_interfacevlans_info_for_one_link((crawler, link_url, ifvlan_schema, link_ifvlan_schema)):
    return crawler.refresh_interfacevlans_info_for_one_link(link_url, ifvlan_schema, link_ifvlan_schema)

class SingleLocalDatastoreInfoCrawler:

    __THREAD_POOL_SIZE = 6

    def __init__(self, tbl_mgr, info_url, aggregate_id, extck_id, cert_path, debug, config_path):
        self.tbl_mgr = tbl_mgr
        self.logger = logger.get_logger(config_path)
        # ensures tables exist in database
        if not self.tbl_mgr.establish_all_tables():
            self.logger.critical("Could not establish all the tables. Exiting")
            sys.exit(-1)

        if info_url[-1] == '/':
            info_url = info_url[:-1]
        self.info_url = info_url
        self.aggregate_id = aggregate_id
        self.extck_id = extck_id
        self.debug = debug

        # collector certificate path
        self.cert_path = cert_path

        self.am_dict = None
        self.extck_dict = None
        self.lock = multiprocessing.Lock()
        self.pool = multiprocessing.pool.ThreadPool(processes=SingleLocalDatastoreInfoCrawler.__THREAD_POOL_SIZE)

    # Updates head aggregate information
    def refresh_aggregate_info(self):
        am_url = self.info_url + '/aggregate/' + self.aggregate_id
        self.logger.info("Refreshing aggregate %s info from %s" % (self.aggregate_id, am_url))
        self.am_dict = handle_request(am_url, self.cert_path, self.logger)
        return self.refresh_specific_aggregate_info(self.am_dict)

    def refresh_specific_aggregate_info(self, agg_dict):
        """
        Method to insert aggregate information into the aggregate table given an aggregate dictionary
        :param agg_dict: the aggregate json dictionary object containing the information to insert or
          update into the database
        :return: True if the information was inserted or updated correctly, False otherwise
        """
        ok = True
        if agg_dict:
            db_table_schema = self.tbl_mgr.schema_dict["ops_aggregate"]
            am_info_list = self.extract_row_from_json_dict(db_table_schema, agg_dict, "aggregate")

            if not info_update(self.tbl_mgr, "ops_aggregate", db_table_schema, am_info_list, \
                               self.tbl_mgr.get_column_from_schema(db_table_schema, "id"), self.debug, self.logger):
                ok = False
        else:
            ok = False
        return ok

    # Updates externalcheck information
    def refresh_externalcheck_info(self):
        ok = True
        self.extck_dict = handle_request(self.info_url + '/externalcheck/' + self.extck_id, self.cert_path, self.logger)
        if self.extck_dict:
            db_table_schema = self.tbl_mgr.schema_dict["ops_externalcheck"]
            extck_info_list = self.extract_row_from_json_dict(db_table_schema, self.extck_dict, "external check")

            if not info_update(self.tbl_mgr, "ops_externalcheck", db_table_schema, extck_info_list, \
                               self.tbl_mgr.get_column_from_schema(db_table_schema, "id"), self.debug, self.logger):
                ok = False
        return ok

    # Updates all the monitored aggregates
    def refresh_all_monitoredaggregates_info(self):
        ok = True
        if self.extck_dict:
            schema = self.tbl_mgr.schema_dict["ops_externalcheck_monitoredaggregate"]
#             mon_aggs = []
            if "monitored_aggregates" in self.extck_dict:
                for mon_agg in self.extck_dict["monitored_aggregates"]:
                    # Check that monitored aggregate ID exists in ops_aggregates
                    # if not, get the info from the href and insert it
                    agg_id = mon_agg["id"]
                    agg_url = mon_agg["href"]
                    insert = True
                    if not self.check_exists("ops_aggregate", "id", agg_id):
                        agg_dict = handle_request(agg_url, self.cert_path, self.logger)
                        if not self.refresh_specific_aggregate_info(agg_dict):
                            ok = False
                            insert = False
                    if insert:
                        mon_agg_info = [agg_id, self.extck_dict["id"], agg_url]
                        if not info_update(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", schema, mon_agg_info, \
                                           (self.tbl_mgr.get_column_from_schema(schema, "id"), self.tbl_mgr.get_column_from_schema(schema, "externalcheck_id")),
                                           self.debug, self.logger):
                            ok = False
        return ok

    def refresh_all_experiments_info(self):
        """
        Method to refresh the experiment information associated with an external check store
        :return: True if everything went fine, false otherwise.
        """
        ok = True
        if self.extck_dict:
            schema = self.tbl_mgr.schema_dict["ops_externalcheck_experiment"]
            exp_schema = self.tbl_mgr.schema_dict["ops_experiment"]

            if "experiments" in self.extck_dict:
                for experiment in self.extck_dict["experiments"]:
                    # Check that monitored aggregate ID exists in ops_aggregates
                    # if not, get the info from the href and insert it
                    experiment_url = experiment["href"]
                    insert = True
                    experiment_dict = handle_request(experiment_url, self.cert_path, self.logger)
                    experiment_info_list = self.get_experiment_attributes(experiment_dict, exp_schema)
                    if not info_update(self.tbl_mgr, "ops_experiment", exp_schema, experiment_info_list, \
                                       self.tbl_mgr.get_column_from_schema(exp_schema, "id"),
                                       self.debug, self.logger):
                            ok = False
                            insert = False
                    if insert:
                        experiment_relation_info = [experiment_dict["id"], self.extck_dict["id"], experiment_url]
                        if not info_update(self.tbl_mgr, "ops_externalcheck_experiment", schema, experiment_relation_info, \
                                           (self.tbl_mgr.get_column_from_schema(schema, "id"), self.tbl_mgr.get_column_from_schema(schema, "externalcheck_id")),
                                           self.debug, self.logger):
                            ok = False
        return ok

    def refresh_one_link_info(self, resource_object, link_schema, resource_schema):
        ok = True
        # counting on v2.0 schema improvements
        if resource_object["resource_type"] and resource_object["resource_type"] != "link":
            # we skip this resource
            return ok
        # either v2.0 told us it's a link, or we'll have to check the schema
        res_dict = handle_request(resource_object["href"], self.cert_path, self.logger)
        if res_dict:
            if resource_object["resource_type"] or res_dict["$schema"].endswith("link#"):  # if a link
                # get each attribute out of response into list
                link_info_list = self.get_link_attributes(res_dict, link_schema)
                if not info_update(self.tbl_mgr, "ops_link", link_schema, link_info_list, \
                                   self.tbl_mgr.get_column_from_schema(link_schema, "id"), self.debug, self.logger):
                    ok = False
                agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
                if not info_update(self.tbl_mgr, "ops_aggregate_resource", resource_schema, agg_res_info_list, \
                                   self.tbl_mgr.get_column_from_schema(resource_schema, "id"), self.debug, self.logger):
                    ok = False
        return ok

    def refresh_all_links_info(self):
        self.logger.info("Refreshing all links information for aggregate %s " % (self.aggregate_id,))
        ok = True
        if self.am_dict:
            link_schema = self.tbl_mgr.schema_dict["ops_link"]
            resource_schema = self.tbl_mgr.schema_dict["ops_aggregate_resource"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                argsArray = []
                for res_i in self.am_dict["resources"]:
                    args = (self, res_i, link_schema, resource_schema)
                    argsArray.append(args)
                results = self.pool.map(refresh_one_links_information, argsArray)
                for tmp_ok in results:
                    if not tmp_ok:
                        ok = False
        return ok

    def refresh_one_sliver_info(self, sliver_ref_object, sliver_schema, agg_sliver_schema):
        ok = True
        slv_dict = handle_request(sliver_ref_object["href"], self.cert_path, self.logger)
        if slv_dict:
            # get each attribute out of response into list
            slv_info_list = self.get_sliver_attributes(slv_dict, sliver_schema)
            if not info_update(self.tbl_mgr, "ops_sliver", sliver_schema, slv_info_list, \
                               self.tbl_mgr.get_column_from_schema(sliver_schema, "id"), self.debug, self.logger):
                ok = False
            agg_slv_info_list = [slv_dict["id"], self.am_dict["id"], slv_dict["urn"], slv_dict["selfRef"]]
            if not info_update(self.tbl_mgr, "ops_aggregate_sliver", agg_sliver_schema, agg_slv_info_list, \
                               self.tbl_mgr.get_column_from_schema(agg_sliver_schema, "id"), self.debug, self.logger):
                ok = False
        return ok

    def refresh_all_slivers_info(self):
        self.logger.info("Refreshing all slivers information for aggregate %s " % (self.aggregate_id,))
        ok = True
        if self.am_dict:
            sliver_schema = self.tbl_mgr.schema_dict["ops_sliver"]
            agg_sliver_schema = self.tbl_mgr.schema_dict["ops_aggregate_sliver"]
            # Need to check because "slivers" is optional
            if "slivers" in self.am_dict:
                argsArray = []
                for slv_i in self.am_dict["slivers"]:
                    args = (self, slv_i, sliver_schema, agg_sliver_schema)
                    argsArray.append(args)
                results = self.pool.map(refresh_one_sliver_information, argsArray)
                for tmp_ok in results:
                    if not tmp_ok:
                        ok = False
        return ok

    def refresh_one_node_info(self, resource_object, node_schema, resource_schema):
        ok = True
        # counting on v2.0 schema improvements
        if resource_object["resource_type"] and resource_object["resource_type"] != "node":
            # we skip this resource
            return ok
        # either v2.0 told us it's a node, or we'll have to check the schema
        res_dict = handle_request(resource_object["href"], self.cert_path, self.logger)
        if res_dict:
            if res_dict["$schema"].endswith("node#"):  # if a node
                # get each attribute out of response into list
                node_info_list = self.get_node_attributes(res_dict, node_schema)
                self.lock.acquire()
                if not info_update(self.tbl_mgr, "ops_node", node_schema, node_info_list, \
                                   self.tbl_mgr.get_column_from_schema(node_schema, "id"), self.debug, self.logger):
                    ok = False
                self.lock.release()
            agg_res_info_list = [res_dict["id"], self.am_dict["id"], res_dict["urn"], res_dict["selfRef"]]
            self.lock.acquire()
            if not info_update(self.tbl_mgr, "ops_aggregate_resource", resource_schema, agg_res_info_list, \
                               self.tbl_mgr.get_column_from_schema(resource_schema, "id"), self.debug, self.logger):
                ok = False
            self.lock.release()
        return ok

    def refresh_all_nodes_info(self):
        self.logger.info("Refreshing all nodes information for aggregate %s " % (self.aggregate_id,))
        ok = True
        if self.am_dict:
            schema = self.tbl_mgr.schema_dict["ops_node"]
            res_schema = self.tbl_mgr.schema_dict["ops_aggregate_resource"]
            # Need to check because "resources" is optional
            if "resources" in self.am_dict:
                argsArray = []
                for res_i in self.am_dict["resources"]:
                    args = (self, res_i, schema, res_schema)
                    argsArray.append(args)
                results = self.pool.map(refresh_one_node_information, argsArray)
                for tmp_ok in results:
                    if not tmp_ok:
                        ok = False

        return ok

    def refresh_interfacevlans_info_for_one_link(self, link_url, ifvlan_schema, link_ifvlan_schema):
        ok = True
        link_dict = handle_request(link_url, self.cert_path, self.logger)
        if link_dict:
            if "endpoints" in link_dict:
                for endpt in link_dict["endpoints"]:
                    ifacevlan_dict = handle_request(endpt["href"], self.cert_path, self.logger)
                    if ifacevlan_dict:
                        # before updating the ifvlan info we need to make sure the if info exists
                        if not "interface" in ifacevlan_dict or not "href" in ifacevlan_dict["interface"] \
                                or ifacevlan_dict["interface"]["href"] == "":
                            self.lock.acquire()
                            self.logger.warn("Can not record interface vlan not linked to an interface.")
                            self.logger.debug(json.dumps(ifacevlan_dict, indent=1))
                            self.lock.release()
                            ok = False
                            continue
                        if not self.check_exists("ops_interface", "selfRef", ifacevlan_dict["interface"]["href"]):
                            interface_dict = handle_request(ifacevlan_dict["interface"]["href"], self.cert_path, self.logger)
                            if not self.refresh_interface_info(interface_dict):
                                ok = False
                        ifacevlan_info_list = self.get_interfacevlan_attributes(ifacevlan_dict, ifvlan_schema)
                        self.lock.acquire()
                        if not info_update(self.tbl_mgr, "ops_interfacevlan", ifvlan_schema, ifacevlan_info_list, \
                                           self.tbl_mgr.get_column_from_schema(ifvlan_schema, "id"), self.debug, self.logger):
                            ok = False
                        self.lock.release()
                        link_ifacevlan_info_list = [ifacevlan_dict["id"], link_dict["id"]]
                        self.lock.acquire()
                        if not info_update(self.tbl_mgr, "ops_link_interfacevlan", link_ifvlan_schema, link_ifacevlan_info_list, \
                                           self.tbl_mgr.get_column_from_schema(link_ifvlan_schema, "id"), self.debug, self.logger):
                            ok = False
                        self.lock.release()
        return ok

    def refresh_all_interfacevlans_info(self):
        self.logger.info("Refreshing all interface vlans information for aggregate %s " % (self.aggregate_id,))
        ok = True
        link_urls = self.get_all_links_of_aggregate()
        ifvlan_schema = self.tbl_mgr.schema_dict["ops_interfacevlan"]
        link_ifvlan_schema = self.tbl_mgr.schema_dict["ops_link_interfacevlan"]
        argsArray = []
        for link_url in link_urls:
            args = (self, link_url, ifvlan_schema, link_ifvlan_schema)
            argsArray.append(args)
        results = self.pool.map(refresh_interfacevlans_info_for_one_link, argsArray)
        for tmp_ok in results:
            if not tmp_ok:
                ok = False
        return ok


    def refresh_interface_info_for_one_node(self, node_url, nodeif_schema, ifaddr_schema):
        ok = True
        node_dict = handle_request(node_url, self.cert_path, self.logger)
        if node_dict:
            if "interfaces" in node_dict:
                for interface in node_dict["interfaces"]:
                    interface_dict = handle_request(interface["href"], self.cert_path, self.logger)
                    if interface_dict:
                        if not self.refresh_interface_info(interface_dict):
                            ok = False
                        node_interface_info_list = [interface_dict["id"], node_dict["id"], interface_dict["urn"], interface_dict["selfRef"]]
                        self.lock.acquire()
                        if not info_update(self.tbl_mgr, "ops_node_interface", nodeif_schema, node_interface_info_list, \
                                           self.tbl_mgr.get_column_from_schema(nodeif_schema, "id"), self.debug, self.logger):
                            ok = False
                        self.lock.release()
                        interface_address_list = self.get_interface_addresses(interface_dict, ifaddr_schema)
                        primary_key_columns = [self.tbl_mgr.get_column_from_schema(ifaddr_schema, "interface_id"),
                                               self.tbl_mgr.get_column_from_schema(ifaddr_schema, "address")]
                        for address in interface_address_list:
                            self.lock.acquire()
                            if not info_update(self.tbl_mgr, "ops_interface_addresses", ifaddr_schema, address,
                                               primary_key_columns, self.debug, self.logger):
                                ok = False
                            self.lock.release()
        return ok

    # Updates all interfaces information
    # First queries all nodes at aggregate and looks for their interfaces
    # Then, loops through each interface in the node_dict
    def refresh_all_interfaces_info(self):
        self.logger.info("Refreshing all interfaces information for aggregate %s " % (self.aggregate_id,))
        ok = True
        node_urls = self.get_all_nodes_of_aggregate()
        nodeif_schema = self.tbl_mgr.schema_dict["ops_node_interface"]
        ifaddr_schema = self.tbl_mgr.schema_dict["ops_interface_addresses"]
        argsArray = []
        for node_url in node_urls:
            args = (self, node_url, nodeif_schema, ifaddr_schema)
            argsArray.append(args)
        results = self.pool.map(refresh_interface_information_for_one_node, argsArray)
        for tmp_ok in results:
            if not tmp_ok:
                ok = False
        return ok

    def refresh_interface_info(self, interface_dict):
        """
        Method to update one interface information at a time
        :param interface_dict: the json dictionary corresponding to the interface information
        :return: True if the update went well, False otherwise.
        """
        ok = True
        schema = self.tbl_mgr.schema_dict["ops_interface"]
        interface_info_list = self.get_interface_attributes(interface_dict, schema)
        self.lock.acquire()
        if not info_update(self.tbl_mgr, "ops_interface", schema, interface_info_list, \
                           self.tbl_mgr.get_column_from_schema(schema, "id"), self.debug, self.logger):
            ok = False
        self.lock.release()
        return ok

    def get_default_attribute_for_type(self, vartype):
        val = "";
        if vartype.startswith("int"):
            val = 0
        return val

    def get_node_attributes(self, res_dict, db_table_schema):
        """
        method to get the attribute of a node given its json dictionary representation
        :param res_dict: the json dictionary of the node of interest
        :param db_table_schema: the database table schema corresponding to the node table.
        :return: a list of attributes for the node, in the database node table column order.
        """
        node_info_list = self.extract_row_from_json_dict(db_table_schema, res_dict, "node")

        return node_info_list


    def get_link_attributes(self, res_dict, db_table_schema):
        """
        method to get the attribute of a link given its json dictionary representation
        :param res_dict: the json dictionary of the link of interest
        :param db_table_schema: the database table schema corresponding to the link table.
        :return: a list of attributes for the link, in the database link table column order.
        """
        link_info_list = self.extract_row_from_json_dict(db_table_schema, res_dict, "link")

        return link_info_list


    def get_sliver_attributes(self, slv_dict, db_table_schema):
        """
        Method to parse the json dictionary object corresponding to a
        sliver object and returning the information in a list corresponding
        to a database record for the sliver table.
        :param slv_dict: the json dictionary for the sliver object
        :param db_table_schema: the database schema for the sliver table (in its
        usual format)
        :return: a list of sliver attributes ready to be inserted in the
        sliver table.
        """
        mapping = {}
        mapping["aggregate_href"] = ("aggregate", "href")
        mapping["aggregate_urn"] = ("aggregate", "urn")
        # circumvoluted way of using the standard extraction method.
        # the resource urn will be put in the node_id column
        # the resource type will be put in the link_id column
        mapping["node_id"] = ("resource", "urn")
        mapping["link_id"] = ("resource", "resource_type")

        slv_info_list = self.extract_row_from_json_dict(db_table_schema, slv_dict, "sliver", mapping)

        # now let's reestablish the proper node id or link id
        node_id_idx = self.tbl_mgr.get_column_from_schema(db_table_schema, "node_id")
        link_id_idx = self.tbl_mgr.get_column_from_schema(db_table_schema, "link_id")
        res_urn = slv_info_list[node_id_idx]
        res_type = slv_info_list[link_id_idx]
        if (res_type == "node") and (res_urn is not None):
            node_id = self.get_id_from_urn("ops_node", res_urn)
            slv_info_list[node_id_idx] = node_id
            slv_info_list[link_id_idx] = None
        elif (res_type == "link") and (res_urn is not None):
            link_id = self.get_id_from_urn("ops_link", res_urn)
            slv_info_list[node_id_idx] = None
            slv_info_list[link_id_idx] = link_id
        else:
            self.logger.warn("Found a sliver with no resource associated");
            slv_info_list[node_id_idx] = None
            slv_info_list[link_id_idx] = None

        return slv_info_list


    def get_interfacevlan_attributes(self, ifv_dict, db_table_schema):
        """
        Method to parse the json dictionary object corresponding to an
        interface-vlan object and returning the information in a list corresponding
        to a database record for the interface-vlan table.
        :param ifv_dict: the json dictionary for the interface-vlan object
        :param db_table_schema: the database schema for the interface-vlan table (in its
        usual format)
        :return: a list of interface-vlan attributes ready to be inserted in the
        interface-vlan table.
        """
        mapping = {}
        mapping["interface_href"] = ("interface", "href")
        mapping["interface_urn"] = ("interface", "urn")

        ifv_info_list = self.extract_row_from_json_dict(db_table_schema, ifv_dict, "interface-vlan", mapping)
        return ifv_info_list


    def get_interface_attributes(self, interface_dict, db_table_schema):
        """
        Method to parse the json dictionary object corresponding to an
        interface object and returning the information in a list corresponding
        to a database record for the interface table.
        :param interface_dict: the json dictionary for the interface object
        :param db_table_schema: the database schema for the interface table (in its
        usual format)
        :return: a list of interface attributes ready to be inserted in the
        interface table.
        """
        interface_info_list = self.extract_row_from_json_dict(db_table_schema, interface_dict, "interface")
        return interface_info_list


    def get_experiment_attributes(self, experiment_dict, db_table_schema):
        """
        Method to parse the json dictionary object corresponding to an
        experiment object and returning the information in a list corresponding
        to a database record for the experiment table.
        :param experiment_dict: the json dictionary for the experiment object
        :param db_table_schema: the database schema for the experiment table (in its
        usual format)
        :return: a list of experiment attributes ready to be inserted in the
        experiment table.
        """
        mapping = {}
        mapping["source_aggregate_urn"] = ("source_aggregate", "urn")
        mapping["source_aggregate_href"] = ("source_aggregate", "href")
        mapping["destination_aggregate_urn"] = ("destination_aggregate", "urn")
        mapping["destination_aggregate_href"] = ("destination_aggregate", "href")
        experiment_info_list = self.extract_row_from_json_dict(db_table_schema, experiment_dict, "experiment", mapping)
        return experiment_info_list


    def get_interface_addresses(self, interface_dict, db_table_schema):
        """
        Extract addresses from an interface dictionary.
        :param interface_dict: the interface to extract addresses from
        :param db_table_schema: database schema for the ops_interface_addresses table
        :return: a list of lists, where each of the inner lists contains
                 a row of values representing one address
        """
        address_list = []
        if "addresses" in interface_dict:
            for json_address in interface_dict["addresses"]:
                # duplicating the dictionary so as to not modify the original
                if_address_dict = dict(json_address)
                # sticking the interface_id value in.
                if_address_dict["interface_id"] = interface_dict["id"]
                oneaddr_row = self.extract_row_from_json_dict(db_table_schema, if_address_dict, "interface")
                if len(oneaddr_row) > 1:
                    address_list.append(oneaddr_row)

        return address_list


    def get_all_nodes_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("selfRef")
                              + " from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_interfaces_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select id from ops_node_interface where node_id in (select id from ops_node where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "'))")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res


    def get_all_links_of_aggregate(self):
        tbl_mgr = self.tbl_mgr
        aggregate_id = self.aggregate_id

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("selfRef") + " from ops_link where id in (select id from ops_aggregate_resource where aggregate_id = '" + aggregate_id + "')")
        res = [];
        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        return res

    def get_meas_ref(self):
        tbl_mgr = self.tbl_mgr
        object_id = self.aggregate_id
        meas_ref = None

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("measRef") + " from ops_aggregate where id = '" + object_id + "' limit 1")
        if q_res is not None:
            meas_ref = q_res[0][0]  # gets first of single tuple

        return meas_ref

    def check_exists(self, table_name, fieldname, value):
        """
        Method to check if data exists in a given table that has a certain value for a given field name.
        :param table_name: the name of the table
        :param fieldname: the name of the field
        :param value: the value for the field
        :return: True if such data exists, False otherwise.
        """
        exists = False
        if value is None:
            valuestr = "NULL"
        else:
            valuestr = "'" + value + "'"
        q_res = self.tbl_mgr.query("select " + self.tbl_mgr.get_column_name(fieldname) + " from " + table_name + " where " \
                                   + self.tbl_mgr.get_column_name(fieldname) + " = " + valuestr + " limit 1")
        if q_res is not None:
            if len(q_res) > 0:
                exists = True
        return exists


    def get_id_from_urn(self, table_name, urn):
        """
        Given a urn and a table name, find its id.

        :param table_name: database table name to search
        :param urn: urn to look for
        :return: the id that goes with urn, or None if not found
        """
        tbl_mgr = self.tbl_mgr
        objid = None

        q_res = tbl_mgr.query("select " + tbl_mgr.get_column_name("id") +
                              " from " + table_name + " where urn = '" + urn +
                              "' limit 1")
        if q_res is not None:
            objid = q_res[0][0]  # gets first of single tuple

        return objid

    def extract_row_from_json_dict(self, db_table_schema, object_dict, object_desc, db_to_json_map=None):
        """
        Method to extract values from a json dictionary corresponding to database columns.
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
                    self.logger.warn("value for required json " + object_desc + " field "
                                     + jsondesc + " is missing. Replacing with default value...")
                    object_attribute_list.append(self.get_default_attribute_for_type(db_column_schema[1]))
                else:
                    # This is OK. This was an optional field.
                    object_attribute_list.append(None)
        return object_attribute_list


def handle_request(url, cert_path, logger):

    resp = None

    try:
        resp = requests.get(url, verify=False, cert=cert_path)
    except requests.exceptions.RequestException, e:
        logger.warning("No response from local datastore at: " + url)
        logger.warning(e)

    if resp:
        if (resp.status_code == requests.codes.ok):
            try:
                json_dict = json.loads(resp.content)
                return json_dict
            except ValueError, e:
                logger.warning("Could not load into JSON with response from " + url)
                logger.warning("response = \n" + resp.content)
                logger.warning(e)
        else:
            logger.warning("Response from " + url + " is invalid, code = " + str(resp.status_code))

    return None


def info_update(tbl_mgr, table_str, table_schema, row_arr, id_columns, debug, logger):
    """
    Function to update the information about an object.
    :param tbl_mgr: an instance of TableManager that will be used to execute the SQL statements.
    :param table_str: the name of the table to operate on.
    :param obj_id: the id of the object
    :param row_arr: a list of values for the object to be updated with.
    :param debug: boolean to decide whether to truly update the information (False) or
        just print statements of what would be executed (True)
    :param logger: the logger instance.
    :return: True if the update happened with any issue, False otherwise.
    """
    ok = True
    if debug:
        # Convert id_columns to a list if it is not one already.
        try:
            _ = iter(id_columns)  # attempt to access it as an iterable
        except TypeError:
            id_columns = [id_columns]

        # Create a list of NAME=VALUE, for all of the id_columns
        name_value_pairs = ""
        for col in id_columns:
            name_value_pairs += table_schema[col][0] + "=" + str(row_arr[col]) + ", "
        logger.info("<print only> updating or inserting " + name_value_pairs + "in table " + table_str)
    else:
        if not tbl_mgr.upsert(table_str, table_schema, row_arr, id_columns):
            ok = False

    return ok


def main(argv):
    ok = True
    [info_url, aggregate_id, extck_id, objecttypes, cert_path, debug] = parse_args(argv)

    if info_url == "" or cert_path == "" or (extck_id == "" and aggregate_id == ""):
        usage()

    db_type = "collector"
    # If in debug mode, make sure to overwrite the logging configuration to print out what we want,
    if debug:
        logger.configure_logger_for_debug_info(config_path)


    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()
    crawler = SingleLocalDatastoreInfoCrawler(tbl_mgr, info_url, aggregate_id, extck_id, cert_path, debug, config_path)

    # Only do head aggregate info query if nodes, sliver, interface, vlan objects are in objecttypes
    if 'n' in objecttypes or 'l' in objecttypes or 's' in objecttypes or 'v' in objecttypes or 'i' in objecttypes:
        if not crawler.refresh_aggregate_info():
            ok = False

    if 'x' in objecttypes or 'e' in objecttypes:
        if not crawler.refresh_externalcheck_info():
            ok = False

    # depending on what is in the objecttypes string, get other object
    # info.  Order of these should stay as is (v after l, i after n).
    if 'n' in objecttypes:
        if not crawler.refresh_all_nodes_info():
            ok = False
    if 'l' in objecttypes:
        if not crawler.refresh_all_links_info():
            ok = False
    if 's' in objecttypes:
        if not crawler.refresh_all_slivers_info():
            ok = False
    if 'i' in objecttypes:
        if not crawler.refresh_all_interfaces_info():
            ok = False
    if 'v' in objecttypes:
        if not crawler.refresh_all_interfacevlans_info():
            ok = False
    if 'e' in objecttypes:
        if not crawler.refresh_all_monitoredaggregates_info():
            ok = False
    if 'x' in objecttypes:
        if not crawler.refresh_all_experiments_info():
            ok = False
    if not ok:
        sys.stderr.write("Error while crawling data store...\n")
        sys.exit(-1)

if __name__ == "__main__":
    main(sys.argv[1:])

