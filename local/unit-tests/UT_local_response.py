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


import unittest
import requests
import json
import sys
import os
from optparse import OptionParser

ut_path = os.path.abspath(os.path.dirname(__file__))
local_path = os.path.dirname(ut_path)
top_path = os.path.dirname(local_path)
common_path = os.path.join(top_path, "common")
sys.path.append(local_path)
sys.path.append(common_path)
sys.path.append(ut_path)
import table_manager
import opsconfig_loader
import info_populator
import stats_populator



class TestLocalResponses(unittest.TestCase):
    NUM_INS = 10;
    PER_SEC = 0.2;
    BASE_SCHEMA = "http://www.gpolab.bbn.com/monitoring/schema/20140828/"

    CERT_PATH = "/vagrant/collector-gpo-withnpkey2.pem"
    IP_ADDR_FILE = "/tmp/ip.conf"

    def __init__(self, methodName):
        super(TestLocalResponses, self).__init__(methodName)
        db_type = "local"
        config_path = os.path.join(top_path, "config/")
        self.tbl_mgr = table_manager.TableManager(db_type, config_path)
        self.tbl_mgr.poll_config_store()

        ocl = opsconfig_loader.OpsconfigLoader(config_path)
        self.event_types = ocl.get_event_types()

        f = open(TestLocalResponses.IP_ADDR_FILE)
        self.ip = f.read().strip()
        f.close()
        self.base_url = "https://%s" % self.ip

    def db_cleanup(self):
        print
        print "Cleaning up DB tables"
        if not self.tbl_mgr.drop_all_tables():
            self.fail("Could not clean up tables");

    def populate_info(self):
        ip = info_populator.InfoPopulator(self.tbl_mgr, self.base_url)
        if not ip.insert_fake_info():
            self.fail("Could not insert test info data into tables");

    def populate_measurements(self):

        obj_type = "node"
        node_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                 info_populator.InfoPopulator.NODE_IDS[0],
                                                 TestLocalResponses.NUM_INS,
                                                 TestLocalResponses.PER_SEC,
                                                 self.event_types[obj_type])

        obj_type = "interface"
        interface_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                      info_populator.InfoPopulator.IF_IDS[0],
                                                      TestLocalResponses.NUM_INS,
                                                      TestLocalResponses.PER_SEC,
                                                      self.event_types[obj_type])

        obj_type = "interfacevlan"
        interfacevlan_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                          info_populator.InfoPopulator.IFVLAN_IDS[0],
                                                          TestLocalResponses.NUM_INS,
                                                          TestLocalResponses.PER_SEC,
                                                          self.event_types[obj_type])

        obj_type = "aggregate"
        aggregate_sp = stats_populator.StatsPopulator(self.tbl_mgr, obj_type,
                                                      info_populator.InfoPopulator.AGGREGATE_ID,
                                                      TestLocalResponses.NUM_INS,
                                                      TestLocalResponses.PER_SEC,
                                                      self.event_types[obj_type])

        # start threads
        node_sp.start()
        interface_sp.start()
        interfacevlan_sp.start()
        aggregate_sp.start()

        threads = []
        threads.append(node_sp)
        threads.append(interface_sp)
        threads.append(interfacevlan_sp)
        threads.append(aggregate_sp)

        ok = True
        # join all threads
        for t in threads:
            t.join()
            if not t.run_ok:
                ok = False

        if not ok:
            self.fail("Error while inserting measurement data into tables");

    def setUp(self):
        super(TestLocalResponses, self).setUp()
        # dropping existing tables
        self.db_cleanup()  # Recreating tables

        if not self.tbl_mgr.establish_all_tables():
            self.fail("Could not establish tables");

        self.populate_info()
#         self.populate_measurements()


        print
        print "Done with setUp()"


    def tearDown(self):
        self.db_cleanup()
        super(TestLocalResponses, self).tearDown()

    def request_url(self, url, cert_path):
        resp = None
        http_headers = {}
        status_string = "No Response"
        fail_str = None

        try:
            print "fetching content for %s" % url
            resp = requests.get(url, verify=False, cert=cert_path,
                                headers=http_headers)
            status_string = str(resp.status_code) + " " + resp.reason
        except Exception as e:
            fail_str = "No response from local datastore for URL %s\n%s" % (url, str(e))

        return (resp, status_string, fail_str)

    def check_json_dictionary_for_field_presence(self, dict, fieldName, desc):
        self.assertTrue(dict.has_key(fieldName),
                        "json dictionary for %s does not contains the expected field %s" % (desc, fieldName))

    def check_json_dictionary_for_field_absence(self, dict, fieldName, desc):
        self.assertFalse(dict.has_key(fieldName),
                        "json dictionary for %s does contains the unexpected field %s" % (desc, fieldName))

    def check_json_dictionary_for_field(self, dict, fieldName, fieldValue, desc):
        self.check_json_dictionary_for_field_presence(dict, fieldName, desc)
        self.assertEqual(dict[fieldName], fieldValue,
                         "json dictionary for %s does not contains the expected value for field %s" % (desc, fieldName));

    def find_urn_and_href_object_in_json_array(self, json_array, urn, href, obj_desc):
        for i in range(len(json_array)):
            obj_dict = json_array[i]
            if obj_dict.has_key("urn") and obj_dict["urn"] == urn:
                break
        else:
            self.fail("Did not find %s with urn %s" % (obj_desc, urn))

        self.assertTrue(obj_dict.has_key("href"), "%s json object does not have an href field" % obj_desc)
        self.assertEqual(href, obj_dict["href"], "unexpected href for %s %s" % (obj_desc, urn))


    def find_resource_in_json_array(self, res_array, res_urn, res_url):
        for i in range(len(res_array)):
            res_dict = res_array[i]
            if res_dict.has_key("urn") and res_dict["urn"] == res_urn:
                break
        else:
            self.fail("Did not find resource with urn %s" % res_urn)

        self.assertTrue(res_dict.has_key("href"), "resource json object does not have an href field")
        self.assertEqual(res_url, res_dict["href"], "unexpected href for resource %s" % res_urn)

    def get_json_dictionary(self, url):
        (resp, status, fail_msg) = self.request_url(url, TestLocalResponses.CERT_PATH)
        print status
        json_dict = None
        if fail_msg is not None:
            self.fail(fail_msg)
        else:
            try:
                json_dict = json.loads(resp.content)
            except Exception as e:
                self.fail("Could not parse JSON from URL %s, %s\n%s" % (url, resp.content,
                                                                    str(e)))
        return json_dict

    def check_error_response(self, url, expected_error):
        (resp, status, fail_msg) = self.request_url(url, TestLocalResponses.CERT_PATH)
        print status
        if fail_msg is not None:
            self.fail(fail_msg)
        else:
            self.assertEqual(expected_error, resp.content, "Unexpected error response when requesting non-existing aggregate info")

    def test_get_aggregate_info(self):
        url = self.base_url + "/info/aggregate/" + info_populator.InfoPopulator.AGGREGATE_ID
        json_dict = self.get_json_dictionary(url)

        desc = "aggregate %s info" % info_populator.InfoPopulator.AGGREGATE_ID

        self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
        self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "aggregate#", desc)
        self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
        self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.AGGREGATE_ID, desc)
        self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.AGGREGATE_URN, desc)

        expected_measRef = self.base_url + "/data/"
        self.check_json_dictionary_for_field(json_dict, "measRef", expected_measRef, desc)
        self.check_json_dictionary_for_field(json_dict, "operational_status", "development", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "monitoring_version", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "populator_version", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "resources", desc)
        self.check_json_dictionary_for_field_presence(json_dict, "slivers", desc)

        for i in range(len(info_populator.InfoPopulator.SLIVER_IDS)):
            self.find_urn_and_href_object_in_json_array(json_dict["slivers"],
                                                        info_populator.InfoPopulator.SLIVER_URNS[i],
                                                        "%s/info/sliver/%s" % (self.base_url, info_populator.InfoPopulator.SLIVER_IDS[i]),
                                                        "sliver")

        for i in range(len(info_populator.InfoPopulator.NODE_IDS)):
           self.find_resource_in_json_array(json_dict["resources"], info_populator.InfoPopulator.NODE_URNS[i],
                                          "%s/info/node/%s" % (self.base_url, info_populator.InfoPopulator.NODE_IDS[i]))
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
           self.find_resource_in_json_array(json_dict["resources"], info_populator.InfoPopulator.LINK_URNS[i],
                                          "%s/info/link/%s" % (self.base_url, info_populator.InfoPopulator.LINK_IDS[i]))


    def test_get_wrong_aggregate_info(self):
        url = self.base_url + "/info/aggregate/" + info_populator.InfoPopulator.AGGREGATE_ID + "_WRONG"
        self.check_error_response(url, "aggregate not found")


    def test_get_nodes_info(self):
        for i in range(len(info_populator.InfoPopulator.NODE_IDS)):
            url = self.base_url + "/info/node/" + info_populator.InfoPopulator.NODE_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "node %s info" % info_populator.InfoPopulator.NODE_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "node#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.NODE_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.NODE_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "node_type", desc)
            if json_dict["node_type"] == "server" or json_dict["node_type"] == "vm":
                self.check_json_dictionary_for_field_presence(json_dict, "virtualization_type", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:mem_total_kb", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "interfaces", desc)
            if_array = json_dict["interfaces"]
            # expectation is that each node has 1 interface - same idx in constants arrays
            self.find_urn_and_href_object_in_json_array(if_array,
                                                        info_populator.InfoPopulator.IF_URNS[i],
                                                        "%s/info/interface/%s" % (self.base_url, info_populator.InfoPopulator.IF_IDS[i]),
                                                        "interface")


    def test_get_wrong_node_info(self):
        url = self.base_url + "/info/node/" + info_populator.InfoPopulator.NODE_IDS[0] + "_WRONG"
        self.check_error_response(url, "node not found")

    def get_ifvlan_index(self, ifvlan_id):
        """
        Method to return the index in the InfoPopulator IFVLAN_IDS array of a given ifvlan_id
        @param ifvlan_id: the vlan id to look for
        """
        index = -1
        for i in range(len(info_populator.InfoPopulator.IFVLAN_IDS)):
            if ifvlan_id == info_populator.InfoPopulator.IFVLAN_IDS[i]:
                index = i
                break
        else:
            self.fail("could not find the index of interface vlan: %s" % ifvlan_id)

        return index

    def get_endpoints_indexes(self, link_id):
        """
        Method to return the indexes of the interface vlan endpoints of a given link id.
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.LINK_VLAN_RELATIONS)):
            if link_id == info_populator.InfoPopulator.LINK_VLAN_RELATIONS[i][1]:
                indexes.append(self.get_ifvlan_index(info_populator.InfoPopulator.LINK_VLAN_RELATIONS[i][0]))

        return indexes

    def get_link_index(self, link_id):
        """
        Method to return the index in the InfoPopulator LINK_IDS array of a given link_id
        @param link_id: the link id to look for
        """
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
            if link_id == info_populator.InfoPopulator.LINK_IDS[i]:
                index = i
                break
        else:
            self.fail("could not find the index of link: %s" % link_id)

        return index

    def get_children_link_indexes(self, link_id):
        """
        Method to return the indexes of the children link ids of a given link id.
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION)):
            if link_id == info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][0]:
                indexes.append(self.get_link_index(info_populator.InfoPopulator.LINK_PARENT_CHILD_RELATION[i][1]))
        return indexes

    def test_get_links_info(self):
        for i in range(len(info_populator.InfoPopulator.LINK_IDS)):
            url = self.base_url + "/info/link/" + info_populator.InfoPopulator.LINK_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "link %s info" % info_populator.InfoPopulator.LINK_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "link#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.LINK_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.LINK_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "layer", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "endpoints", desc)
            endpoints_array = json_dict["endpoints"]
            vlan_indexes = self.get_endpoints_indexes(info_populator.InfoPopulator.LINK_IDS[i]);
            for vlan_idx in vlan_indexes:
                self.find_urn_and_href_object_in_json_array(endpoints_array,
                                                            info_populator.InfoPopulator.IFVLAN_URNS[vlan_idx],
                                                            "%s/info/interfacevlan/%s" % (self.base_url, info_populator.InfoPopulator.IFVLAN_IDS[vlan_idx]),
                                                            "interfacevlan")
            children_indexes = self.get_children_link_indexes(info_populator.InfoPopulator.LINK_IDS[i])
            if len(children_indexes) != 0:
                self.check_json_dictionary_for_field_presence(json_dict, "children", desc)
                children_array = json_dict["children"]
                for sublink_idx in children_indexes:
                    self.find_urn_and_href_object_in_json_array(children_array,
                                                                info_populator.InfoPopulator.LINK_URNS[sublink_idx],
                                                                "%s/info/link/%s"
                                                                    % (self.base_url, info_populator.InfoPopulator.LINK_IDS[sublink_idx]),
                                                                "link")

    def test_get_wrong_link_info(self):
        url = self.base_url + "/info/link/" + info_populator.InfoPopulator.LINK_IDS[0] + "_WRONG"
        self.check_error_response(url, "link not found")

    def get_if_addresses_indexes(self, if_id):
        """
        Method to return the indexes of the addresses of a given interface id.
        @param if_id: the interface id
        """
        indexes = []
        for i in range(len(info_populator.InfoPopulator.IF_ADDRESS_RELATIONS)):
            if if_id == info_populator.InfoPopulator.IF_ADDRESS_RELATIONS[i][0]:
                indexes.append(info_populator.InfoPopulator.IF_ADDRESS_RELATIONS[i][1])
        return indexes

    def find_if_address_in_json_array(self, json_array, type, scope, addr):
        for i in range(len(json_array)):
            obj_dict = json_array[i]
            if obj_dict.has_key("addrtype") and obj_dict["addrtype"] == type \
                and obj_dict.has_key("address") and obj_dict["address"] == addr:
                if scope is None:
                    if not obj_dict.has_key("scope"):
                        break
                else:
                    if obj_dict.has_key("scope") and obj_dict["scope"] == scope:
                        break

        else:
            self.fail("Did not find %s with urn %s" % (obj_desc, urn))

    def test_get_ifs_info(self):
        for i in range(len(info_populator.InfoPopulator.IF_IDS)):
            url = self.base_url + "/info/interface/" + info_populator.InfoPopulator.IF_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "interface %s info" % info_populator.InfoPopulator.IF_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "interface#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.IF_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.IF_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:max_pps", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:max_bps", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ops_monitoring:role", desc)
            addr_indexes = self.get_if_addresses_indexes(info_populator.InfoPopulator.IF_IDS[i])
            if (len(addr_indexes) == 0):
                self.check_json_dictionary_for_field_absence(json_dict, "addresses", desc)
            else:
                self.check_json_dictionary_for_field_presence(json_dict, "addresses", desc)
                for addr_idx in addr_indexes:
                    self.find_if_address_in_json_array(json_dict["addresses"],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][0],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][1],
                                                       info_populator.InfoPopulator.IF_ADDRESSES[addr_idx][2])


    def test_get_wrong_if_info(self):
        url = self.base_url + "/info/interface/" + info_populator.InfoPopulator.IF_IDS[0] + "_WRONG"
        self.check_error_response(url, "interface not found")

    def test_get_ifvlans_info(self):
        for i in range(len(info_populator.InfoPopulator.IFVLAN_IDS)):
            url = self.base_url + "/info/interfacevlan/" + info_populator.InfoPopulator.IFVLAN_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "interfacevlan %s info" % info_populator.InfoPopulator.IFVLAN_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "interfacevlan#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.IFVLAN_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.IFVLAN_URNS[i], desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field(json_dict, "tag", info_populator.InfoPopulator.VLAN_ID, desc)
            self.check_json_dictionary_for_field_presence(json_dict, "interface", desc)
            interface_obj = json_dict["interface"]
            # just so I can reuse an existing method
            if_array = (interface_obj,)
            # the expectation is that is ifvlan correspond to one if - same idx in the arrays
            self.find_urn_and_href_object_in_json_array(if_array,
                                                        info_populator.InfoPopulator.IF_URNS[i],
                                                        self.base_url + "/info/interface/" + info_populator.InfoPopulator.IF_IDS[i],
                                                        "interface")

    def test_get_wrong_ifvlan_info(self):
        url = self.base_url + "/info/interfacevlan/" + info_populator.InfoPopulator.IFVLAN_IDS[0] + "_WRONG"
        self.check_error_response(url, "interfacevlan not found")

    def test_get_sliver_info(self):
        for i in range(len(info_populator.InfoPopulator.SLIVER_IDS)):
            url = self.base_url + "/info/sliver/" + info_populator.InfoPopulator.SLIVER_IDS[i]
            json_dict = self.get_json_dictionary(url)
            self.assertIsNotNone(json_dict, "Error parsing return from %s" % url)
            desc = "sliver %s info" % info_populator.InfoPopulator.SLIVER_IDS[i]
            self.check_json_dictionary_for_field(json_dict, "$schema", TestLocalResponses.BASE_SCHEMA + "sliver#", desc)
            self.check_json_dictionary_for_field(json_dict, "selfRef", url, desc)
            self.check_json_dictionary_for_field(json_dict, "id", info_populator.InfoPopulator.SLIVER_IDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "urn", info_populator.InfoPopulator.SLIVER_URNS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "uuid", info_populator.InfoPopulator.SLIVER_UUIDS[i], desc)
            self.check_json_dictionary_for_field(json_dict, "slice_uuid",
                                                 info_populator.InfoPopulator.SLICE_UUIDS[info_populator.InfoPopulator.SLIVER_SCLICE_IDX[i]],
                                                 desc)
            self.check_json_dictionary_for_field(json_dict, "creator",
                                                 info_populator.InfoPopulator.USER_URNS[info_populator.InfoPopulator.SLIVER_USER_IDX[i]],
                                                 desc)
            self.check_json_dictionary_for_field_presence(json_dict, "ts", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "expires", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "created", desc)
            self.check_json_dictionary_for_field_presence(json_dict, "aggregate", desc)
            agg_obj = json_dict["aggregate"]
            # just so I can reuse an existing method
            agg_array = (agg_obj,)
            self.find_urn_and_href_object_in_json_array(agg_array,
                                                        info_populator.InfoPopulator.AGGREGATE_URN,
                                                        self.base_url + "/info/aggregate/" + info_populator.InfoPopulator.AGGREGATE_ID,
                                                        "aggregate")
            self.check_json_dictionary_for_field_presence(json_dict, "resource", desc)
            res_obj = json_dict["resource"]
            self.check_json_dictionary_for_field(res_obj, "resource_type",
                                                 info_populator.InfoPopulator.SLIVER_RESOURCE_RELATION[i][0],
                                                 desc)
            idx = info_populator.InfoPopulator.SLIVER_RESOURCE_RELATION[i][1]
            if info_populator.InfoPopulator.SLIVER_RESOURCE_RELATION[i][0] == "node":
                urn = info_populator.InfoPopulator.NODE_URNS[idx]
                url = self.base_url + "/info/node/" + info_populator.InfoPopulator.NODE_IDS[idx]
            elif info_populator.InfoPopulator.SLIVER_RESOURCE_RELATION[i][0] == "link":
                urn = info_populator.InfoPopulator.LINK_URNS[idx]
                url = self.base_url + "/info/link/" + info_populator.InfoPopulator.LINK_IDS[idx]
            else:
                self.fail("unrecognized resource type for sliver %s" % info_populator.InfoPopulator.SLIVER_IDS[i])
            res_array = (res_obj,)
            self.find_urn_and_href_object_in_json_array(res_array, urn, url, "resource")

    def test_get_wrong_sliver_info(self):
        url = self.base_url + "/info/sliver/" + info_populator.InfoPopulator.SLIVER_IDS[0] + "_WRONG"
        self.check_error_response(url, "sliver not found")


def main(argv):

    # Set up command-line options

    parser = OptionParser(usage="usage: %prog [options] ",
                          description="Launch the unit test checking on the local data store responses. "
                          "various unit tests are executed.")
    parser.add_option("-c", "--cert-path", dest="cert_path",
                      help="path to tool certificate file")
    parser.add_option("--xml", dest="xml_output",
#                       default=False, action="store_true",
                      help="path to the results output of the unit tests, which will happen in a JUnit XML format")

    (options, _args) = parser.parse_args()
    # Do some more checking on the options provided
    if options.cert_path:
        if not os.path.isfile(options.cert_path):
            print "cert-path %s is not a file" % (options.cert_path)
            return 1
        else:
            TestLocalResponses.CERT_PATH = options.cert_path

    print "using certificate:", TestLocalResponses.CERT_PATH
    if options.xml_output:
        # we want to output a JUnit style report
        if not os.path.isdir(options.xml_output):
            print "xml_output %s is not a folder" % (options.xml_output)
            return 1

        import xmlrunner
        # need to fake the arguments
        fake_args = [ sys.argv[0] ]
        return unittest.main(testRunner=xmlrunner.XMLTestRunner(output=options.xml_output), argv=fake_args)
    else:
        # we want the output on the console
#     unittest.main()
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalResponses)
        return unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    main(sys.argv[1:])
