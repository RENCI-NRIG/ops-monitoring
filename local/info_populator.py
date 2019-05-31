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
import sys

common_path = "../common/"

sys.path.append(common_path)
import table_manager


# Using these classes for constants because we can't reference a constant to declare another constant in the same class :(
# i.e. LINK_RELATION = ( (InfoPopulator.LINK_IDS[0], InfoPopulator.LINK_IDS[1]) ) fails with NameError: name 'InfoPopulator' is not defined
# because the class has not been fully parsed to be used.

class _HackLink():
    LINK_IDS = ("arbitrary_link_id_001",
                "arbitrary_link_id_002",
                "arbitrary_link_id_003",
                "link_id_egress01"
                )

class _HackVlan():
    VLAN_ID = 1750

class _HackIf():
    IF_IDS = ("instageni.gpolab.bbn.com_interface_pc1:eth1",
              "instageni.gpolab.bbn.com_interface_pc2:eth1",
              "instageni.gpolab.bbn.com_interface_interconnect:port0",
              "instageni.gpolab.bbn.com_interface_newy.ion.internet2.edu:ae0"
              )

    IF_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc1:eth1",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+pc2:eth1",
               "urn:publicid:IDN+instageni.gpolab.bbn.com+interface+interconnect:port0",
               "urn:publicid:IDN+ion.internet2.edu+interface+rtr.newy:ae0"
               )

class _HackIfvlan():
    IFVLAN_IDS = (_HackIf.IF_IDS[0] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[1] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[2] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_IDS[3] + ":" + str(_HackVlan.VLAN_ID),
                   )


class InfoPopulator():




    AGGREGATE_ID = "gpo-ig"
    AGGREGATE_URN = "urn:publicid:IDN+instageni.gpolab.bbn.com+authority+cm"
    NODE_IDS = ("instageni.gpolab.bbn.com_node_pc1",
                "instageni.gpolab.bbn.com_node_pc2",
                "instageni.gpolab.bbn.com_node_interconnect"
                )

    NODE_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc2",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+node+interconnect"
                 )

    LINK_IDS = _HackLink.LINK_IDS

    LINK_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_001",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_002",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_003",
                 "urn:publicid:IDN+instageni.gpolab.bbn.com+link_id_egress01"
                 )

    IF_IDS = _HackIf.IF_IDS

    IF_URNS = _HackIf.IF_URNS

    # tuples of addrtype, scope, address
    IF_ADDRESSES = (("IPv4", "public", "public"),
                     ("802.3", None, "ab:cd:ef:01:23")
                    )

    # tuple of IF IDs, address record idx
    IF_ADDRESS_RELATIONS = ((_HackIf.IF_IDS[0], 0),
                             (_HackIf.IF_IDS[0], 1)
                            )

    VLAN_ID = _HackVlan.VLAN_ID

    IFVLAN_IDS = _HackIfvlan.IFVLAN_IDS


    IFVLAN_URNS = (_HackIf.IF_URNS[0] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[1] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[2] + ":" + str(_HackVlan.VLAN_ID),
                   _HackIf.IF_URNS[3] + ":" + str(_HackVlan.VLAN_ID),
                   )

    LINK_VLAN_RELATIONS = ((_HackIfvlan.IFVLAN_IDS[0], _HackLink.LINK_IDS[0]),
                           (_HackIfvlan.IFVLAN_IDS[1], _HackLink.LINK_IDS[0]),
                           (_HackIfvlan.IFVLAN_IDS[0], _HackLink.LINK_IDS[1]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[1]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[2]),
                           (_HackIfvlan.IFVLAN_IDS[1], _HackLink.LINK_IDS[2]),
                           (_HackIfvlan.IFVLAN_IDS[2], _HackLink.LINK_IDS[3]),
                           (_HackIfvlan.IFVLAN_IDS[3], _HackLink.LINK_IDS[3])
                           )

    # first parent, second child
    LINK_PARENT_CHILD_RELATION = ((_HackLink.LINK_IDS[0], _HackLink.LINK_IDS[1]),
                                  (_HackLink.LINK_IDS[0], _HackLink.LINK_IDS[2])
                                  )

    SLIVER_IDS = ("instageni.gpolab.bbn.com_sliver_26947",
                  "instageni.gpolab.bbn.com_sliver_26950",
                  "instageni.gpolab.bbn.com_sliver_26951",
                  "instageni.gpolab.bbn.com_sliver_26999"
                  )
    SLIVER_URNS = ("urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26947",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26950",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26951",
                   "urn:publicid:IDN+instageni.gpolab.bbn.com+sliver+26999"
                   )

    SLIVER_UUIDS = ("30752b06-8ea8-11e3-8d30-000000000000",
                    "30752b06-8ea8-11e3-8d30-000005000000",
                    "30752b06-8ea8-11e3-8d30-000005000001",
                    "30752b06-8ea8-11e3-8d30-000006000000"
                    )

    SLICE_URNS = ("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive",
                  "urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive2"
                  )
    SLICE_UUIDS = ("8c6b97fa-493b-400f-95ee-19accfaf4ae8",
                   "8c6b97fa-493b-400f-95ee-19accfaf4ae9"
                  )
    # at sliver idx you have slice idx
    SLIVER_SCLICE_IDX = (0, 1, 1, 0)

    USER_URNS = ("urn:publicid:IDN+ch.geni.net+user+tupty",
                 "urn:publicid:IDN+ch.geni.net+user+sblais"
                 )

    # at sliver idx you have user idx
    SLIVER_USER_IDX = (0, 1, 0, 1)

    # at sliver idx, you get resource type, and idx in the corresponding resource array
    SLIVER_RESOURCE_RELATION = (("node", 0),
                                ("node", 1),
                                ("node", 2),
                                ("link", 0)
                                )

    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path


    def append_sliver_resource_info(self, sliver_info_list, sliver_idx):
        if InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx][0] == "node":
            sliver_info_list.append(InfoPopulator.NODE_IDS[InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx][1]])  # node_id
            sliver_info_list.append(None)  # link_id
        elif InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx][0] == "link":
            sliver_info_list.append(None)  # node_id
            sliver_info_list.append(InfoPopulator.LINK_IDS[InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx][1]])  # link_id
        else:
            raise Exception("unidentified resource type %s" % InfoPopulator.SLIVER_RESOURCE_RELATION[sliver_idx][0])
    
    def insert_fake_info(self):
        ok = True

        url_local_info = self.url_base + "/info/"
        url_local_data = self.url_base + "/data/"
        url_opsconfig_local_info = self.url_base + "/info/"

        agg1 = []
        agg1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/aggregate#")
        agg1.append(InfoPopulator.AGGREGATE_ID)
        agg1.append(url_local_info + "aggregate/" + agg1[1])
        agg1.append(InfoPopulator.AGGREGATE_URN)
        agg1.append(str(int(time.time() * 1000000)))
        agg1.append(url_local_data)  # measRef
        agg1.append("1.0")  # populator_version
        agg1.append("development")  # operational_status
        agg1.append("0")  # routable_ip_poolsize

        if not info_insert(self.tbl_mgr, "ops_aggregate", agg1):
            ok = False


        node1 = []
        node1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/node#")
        node1.append(InfoPopulator.NODE_IDS[0])
        node1.append(url_local_info + "node/" + node1[1])
        node1.append(InfoPopulator.NODE_URNS[0])
        node1.append(str(int(time.time() * 1000000)))
        node1.append("server")  # node_type
        node1.append(str(2 * 1000000))  # mem_total_kb
        node1.append("xen")  # virtualization_type

        if not info_insert(self.tbl_mgr, "ops_node", node1):
            ok = False


        node2 = []
        node2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/node#")
        node2.append(InfoPopulator.NODE_IDS[1])
        node2.append(url_local_info + "node/" + node2[1])
        node2.append(InfoPopulator.NODE_URNS[1])
        node2.append(str(int(time.time() * 1000000)))
        node2.append("server")  # node_type
        node2.append(str(2 * 1000000))  # mem_total_kb
        node2.append("xen")  # virtualization_type

        if not info_insert(self.tbl_mgr, "ops_node", node2):
            ok = False

        switch1 = []
        switch1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/node#")
        switch1.append(InfoPopulator.NODE_IDS[2])
        switch1.append(url_local_info + "node/" + switch1[1])
        switch1.append(InfoPopulator.NODE_URNS[2])
        switch1.append(str(int(time.time() * 1000000)))
        switch1.append("switch")  # node_type
        switch1.append(str(2 * 1000000))  # mem_total_kb
        switch1.append(None)  # virtualization_type
        if not info_insert(self.tbl_mgr, "ops_node", switch1):
            ok = False


        sliver1 = []
        sliver1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
        sliver1.append(InfoPopulator.SLIVER_IDS[0])
        sliver1.append(url_local_info + "sliver/" + sliver1[1])
        sliver1.append(InfoPopulator.SLIVER_URNS[0])
        sliver1.append(InfoPopulator.SLIVER_UUIDS[0])  # uuid
        sliver1.append(str(int(time.time() * 1000000)))  # current ts
        sliver1.append(agg1[3])  # agg_urn
        sliver1.append(agg1[2])  # agg_href
        sliver1.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[0]])  # slice_urn
        sliver1.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[0]])  # slice uuid
        sliver1.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[0]])  # creator
        sliver1.append(str(int(1391626683000000)))  # created
        sliver1.append(str(int(1391708989000000)))  # expires
        self.append_sliver_resource_info(sliver1, 0)

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver1):
            ok = False


        sliver2 = []
        sliver2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
        sliver2.append(InfoPopulator.SLIVER_IDS[1])
        sliver2.append(url_local_info + "sliver/" + sliver2[1])
        sliver2.append(InfoPopulator.SLIVER_URNS[1])
        sliver2.append(InfoPopulator.SLIVER_UUIDS[1])  # uuid
        sliver2.append(str(int(time.time() * 1000000)))  # current ts
        sliver2.append(agg1[3])  # agg_urn
        sliver2.append(agg1[2])  # agg_href
        sliver2.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[1]])  # slice_urn
        sliver2.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[1]])  # slice uuid
        sliver2.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[1]])  # creator
        sliver2.append(str(int(1391626683000000)))  # created
        sliver2.append(str(int(1391708989000000)))  # expires
        self.append_sliver_resource_info(sliver2, 1)

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver2):
            ok = False


        sliver3 = []
        sliver3.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
        sliver3.append(InfoPopulator.SLIVER_IDS[2])
        sliver3.append(url_local_info + "sliver/" + sliver3[1])
        sliver3.append(InfoPopulator.SLIVER_URNS[2])
        sliver3.append(InfoPopulator.SLIVER_UUIDS[2])  # uuid
        sliver3.append(str(int(time.time() * 1000000)))  # current ts
        sliver3.append(agg1[3])  # agg_urn
        sliver3.append(agg1[2])  # agg_href
        sliver3.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[2]])  # slice_urn
        sliver3.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[2]])  # slice uuid
        sliver3.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[2]])  # creator
        sliver3.append(str(int(1391626683000000)))  # created
        sliver3.append(str(int(1391708989000000)))  # expires
        self.append_sliver_resource_info(sliver3, 2)

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver3):
            ok = False


        link1 = []
        link1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/link#")
        link1.append(InfoPopulator.LINK_IDS[0])
        link1.append(url_local_info + "link/" + link1[1])
        link1.append(InfoPopulator.LINK_URNS[0])
        link1.append("layer2")
        link1.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_link", link1):
            ok = False

        sublink1 = []
        sublink1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/link#")
        sublink1.append(InfoPopulator.LINK_IDS[1])
        sublink1.append(url_local_info + "link/" + sublink1[1])
        sublink1.append(InfoPopulator.LINK_URNS[1])
        sublink1.append("layer2")
        sublink1.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_link", sublink1):
            ok = False

        sublink2 = []
        sublink2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/link#")
        sublink2.append(InfoPopulator.LINK_IDS[2])
        sublink2.append(url_local_info + "link/" + sublink2[1])
        sublink2.append(InfoPopulator.LINK_URNS[2])
        sublink2.append("layer2")
        sublink2.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_link", sublink2):
            ok = False

        egress_link = []
        egress_link.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/link#")
        egress_link.append(InfoPopulator.LINK_IDS[3])
        egress_link.append(url_local_info + "link/" + egress_link[1])
        egress_link.append(InfoPopulator.LINK_URNS[3])
        egress_link.append("layer2")
        egress_link.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_link", egress_link):
            ok = False

        sliver4 = []
        sliver4.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/sliver#")
        sliver4.append(InfoPopulator.SLIVER_IDS[3])
        sliver4.append(url_local_info + "sliver/" + sliver4[1])
        sliver4.append(InfoPopulator.SLIVER_URNS[3])
        sliver4.append(InfoPopulator.SLIVER_UUIDS[3])  # uuid
        sliver4.append(str(int(time.time() * 1000000)))  # current ts
        sliver4.append(agg1[3])  # agg_urn
        sliver4.append(agg1[2])  # agg_href
        sliver4.append(InfoPopulator.SLICE_URNS[InfoPopulator.SLIVER_SCLICE_IDX[3]])  # slice_urn
        sliver4.append(InfoPopulator.SLICE_UUIDS[InfoPopulator.SLIVER_SCLICE_IDX[3]])  # slice uuid
        sliver4.append(InfoPopulator.USER_URNS[InfoPopulator.SLIVER_USER_IDX[3]])  # creator
        sliver4.append(str(int(1391626683000005)))  # created
        sliver4.append(str(int(1391708989000006)))  # expires
        self.append_sliver_resource_info(sliver4, 3)

        if not info_insert(self.tbl_mgr, "ops_sliver", sliver4):
            ok = False


        interface1 = []
        interface1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        interface1.append(InfoPopulator.IF_IDS[0])
        interface1.append(url_local_info + "interface/" + interface1[1])
        interface1.append(InfoPopulator.IF_URNS[0])
        interface1.append(str(int(time.time() * 1000000)))
        interface1.append("control")  # role
        interface1.append(str(10000000))  # max bps
        interface1.append(str(1000000))  # max pps

        if not info_insert(self.tbl_mgr, "ops_interface", interface1):
            ok = False

        interface2 = []
        interface2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        interface2.append(InfoPopulator.IF_IDS[1])
        interface2.append(url_local_info + "interface/" + interface2[1])
        interface2.append(InfoPopulator.IF_URNS[1])
        interface2.append(str(int(time.time() * 1000000)))
        interface2.append("control")  # role
        interface2.append(str(10000000))  # max bps
        interface2.append(str(1000000))  # max pps

        if not info_insert(self.tbl_mgr, "ops_interface", interface2):
            ok = False

        interface3 = []
        interface3.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        interface3.append(InfoPopulator.IF_IDS[2])
        interface3.append(url_local_info + "interface/" + interface3[1])
        interface3.append(InfoPopulator.IF_URNS[2])
        interface3.append(str(int(time.time() * 1000000)))
        interface3.append("control")  # role
        interface3.append(str(10000000))  # max bps
        interface3.append(str(1000000))  # max pps

        if not info_insert(self.tbl_mgr, "ops_interface", interface3):
            ok = False

        remoteinterface1 = []
        remoteinterface1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interface#")
        remoteinterface1.append(InfoPopulator.IF_IDS[3])
        remoteinterface1.append(url_local_info + "interface/" + remoteinterface1[1])
        remoteinterface1.append(InfoPopulator.IF_URNS[3])
        remoteinterface1.append(str(int(time.time() * 1000000)))
        remoteinterface1.append("stub")  # role
        remoteinterface1.append(str(10000000))  # max bps
        remoteinterface1.append(str(1000000))  # max pps

        if not info_insert(self.tbl_mgr, "ops_interface", remoteinterface1):
            ok = False

        for i in range(len(InfoPopulator.IF_IDS)):
            for j in range(len(InfoPopulator.IF_ADDRESS_RELATIONS)):
                if InfoPopulator.IF_IDS[i] == InfoPopulator.IF_ADDRESS_RELATIONS[j][0]:
                    addr_idx = InfoPopulator.IF_ADDRESS_RELATIONS[j][1]
                    interfaceaddr = []
                    interfaceaddr.append(InfoPopulator.IF_IDS[i])  # interface_id
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][0])  # addrtype
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][1])  # scope
                    interfaceaddr.append(InfoPopulator.IF_ADDRESSES[addr_idx][2])  # address
                    if not info_insert(self.tbl_mgr, "ops_interface_addresses", interfaceaddr):
                        ok = False


        vlan1 = InfoPopulator.VLAN_ID

        interfacevlan1 = []
        interfacevlan1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        interfacevlan1.append(InfoPopulator.IFVLAN_IDS[0])
        interfacevlan1.append(url_local_info + "interfacevlan/" + interfacevlan1[1])
        interfacevlan1.append(InfoPopulator.IFVLAN_URNS[0])
        interfacevlan1.append(str(int(time.time() * 1000000)))
        interfacevlan1.append(str(vlan1))  # tag type
        interfacevlan1.append(interface1[3])  # interface urn
        interfacevlan1.append(interface1[2])  # interface href

        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan1):
            ok = False


        interfacevlan2 = []
        interfacevlan2.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        interfacevlan2.append(InfoPopulator.IFVLAN_IDS[1])
        interfacevlan2.append(url_local_info + "interfacevlan/" + interfacevlan2[1])
        interfacevlan2.append(InfoPopulator.IFVLAN_URNS[1])
        interfacevlan2.append(str(int(time.time() * 1000000)))
        interfacevlan2.append(str(vlan1))  # tag type
        interfacevlan2.append(interface2[3])  # interface urn
        interfacevlan2.append(interface2[2])  # interface href
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan2):
            ok = False

        interfacevlan3 = []
        interfacevlan3.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        interfacevlan3.append(InfoPopulator.IFVLAN_IDS[2])
        interfacevlan3.append(url_local_info + "interfacevlan/" + interfacevlan3[1])
        interfacevlan3.append(InfoPopulator.IFVLAN_URNS[2])
        interfacevlan3.append(str(int(time.time() * 1000000)))
        interfacevlan3.append(str(vlan1))  # tag type
        interfacevlan3.append(interface3[3])  # interface urn
        interfacevlan3.append(interface3[2])  # interface href
        if not info_insert(self.tbl_mgr, "ops_interfacevlan", interfacevlan3):
            ok = False


        remoteinterfacevlan1 = []
        remoteinterfacevlan1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/interfacevlan#")
        remoteinterfacevlan1.append(InfoPopulator.IFVLAN_IDS[3])
        remoteinterfacevlan1.append(url_local_info + "interfacevlan/" + remoteinterfacevlan1[1])
        remoteinterfacevlan1.append(InfoPopulator.IFVLAN_URNS[3])
        remoteinterfacevlan1.append(str(int(time.time() * 1000000)))
        remoteinterfacevlan1.append(str(vlan1))  # tag type
        remoteinterfacevlan1.append(remoteinterface1[3])  # interface urn
        remoteinterfacevlan1.append(remoteinterface1[2])  # interface href

        if not info_insert(self.tbl_mgr, "ops_interfacevlan", remoteinterfacevlan1):
            ok = False


        authority1 = []
        authority1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/authority#")
        authority1.append("ch.geni.net")
        authority1.append(url_local_info + "authority/" + authority1[1])
        authority1.append("urn:publicid:IDN+ch.geni.net+authority+ch")
        authority1.append(str(int(time.time() * 1000000)))

        if not info_insert(self.tbl_mgr, "ops_authority", authority1):
            ok = False

        slice1 = []
        slice1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/slice#")
        slice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        slice1.append(url_local_info + "slice/" + slice1[1])
        slice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
        slice1.append("8c6b97fa-493b-400f-95ee-19accfaf4ae8")
        slice1.append(str(int(time.time() * 1000000)))
        slice1.append(authority1[3])  # authority urn
        slice1.append(authority1[2])  # authority href
        slice1.append("1391626683000000")
        slice1.append("1391708989000000")

        if not info_insert(self.tbl_mgr, "ops_slice", slice1):
            ok = False


        user1 = []
        user1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/user#")
        user1.append("tupty")
        user1.append(url_local_info + "user/" + user1[1])
        user1.append("tupty_user_urn")
        user1.append(str(int(time.time() * 1000000)))
        user1.append("urn:publicid:IDN+ch.geni.net+authority+ch")  # authority urn
        user1.append(url_opsconfig_local_info + "authority/ch.geni.net")  # authority href
        user1.append("Tim Exampleuser")
        user1.append("tupty@example.com")

        if not info_insert(self.tbl_mgr, "ops_user", user1):
            ok = False


        aggres1 = []
        aggres1.append(node1[1])
        aggres1.append(agg1[1])
        aggres1.append(node1[3])
        aggres1.append(node1[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres1):
            ok = False

        aggres2 = []
        aggres2.append(node2[1])
        aggres2.append(agg1[1])
        aggres2.append(node2[3])
        aggres2.append(node2[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres2):
            ok = False


        aggres3 = []
        aggres3.append(link1[1])
        aggres3.append(agg1[1])
        aggres3.append(link1[3])
        aggres3.append(link1[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres3):
            ok = False


        aggres4 = []
        aggres4.append(sublink1[1])
        aggres4.append(agg1[1])
        aggres4.append(sublink1[3])
        aggres4.append(sublink1[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres4):
            ok = False


        aggres5 = []
        aggres5.append(sublink2[1])
        aggres5.append(agg1[1])
        aggres5.append(sublink2[3])
        aggres5.append(sublink2[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres5):
            ok = False


        aggres6 = []
        aggres6.append(egress_link[1])
        aggres6.append(agg1[1])
        aggres6.append(egress_link[3])
        aggres6.append(egress_link[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres6):
            ok = False


        aggres7 = []
        aggres7.append(switch1[1])
        aggres7.append(agg1[1])
        aggres7.append(switch1[3])
        aggres7.append(switch1[2])

        if not info_insert(self.tbl_mgr, "ops_aggregate_resource", aggres7):
            ok = False


        aggsliv1 = []
        aggsliv1.append(sliver1[1])  # id
        aggsliv1.append(agg1[1])
        aggsliv1.append(sliver1[3])  # urn
        aggsliv1.append(sliver1[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv1):
            ok = False


        aggsliv2 = []
        aggsliv2.append(sliver2[1])  # id
        aggsliv2.append(agg1[1])
        aggsliv2.append(sliver2[3])  # urn
        aggsliv2.append(sliver2[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv2):
            ok = False


        aggsliv3 = []
        aggsliv3.append(sliver3[1])  # id
        aggsliv3.append(agg1[1])
        aggsliv3.append(sliver3[3])  # urn
        aggsliv3.append(sliver3[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv3):
            ok = False


        aggsliv4 = []
        aggsliv4.append(sliver4[1])  # id
        aggsliv4.append(agg1[1])
        aggsliv4.append(sliver4[3])  # urn
        aggsliv4.append(sliver4[2])  # href

        if not info_insert(self.tbl_mgr, "ops_aggregate_sliver", aggsliv4):
            ok = False


        nodeiface1 = []
        nodeiface1.append(interface1[1])
        nodeiface1.append(node1[1])
        nodeiface1.append(interface1[3])
        nodeiface1.append(interface1[2])

        if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface1):
            ok = False


        nodeiface2 = []
        nodeiface2.append(interface2[1])
        nodeiface2.append(node2[1])
        nodeiface2.append(interface2[3])
        nodeiface2.append(interface2[2])

        if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface2):
            ok = False


        nodeiface3 = []
        nodeiface3.append(interface3[1])
        nodeiface3.append(switch1[1])
        nodeiface3.append(interface3[3])
        nodeiface3.append(interface3[2])

        if not info_insert(self.tbl_mgr, "ops_node_interface", nodeiface3):
            ok = False


        for i in range(len(InfoPopulator.LINK_VLAN_RELATIONS)):
            link1ifacevlan = []
            link1ifacevlan.append(InfoPopulator.LINK_VLAN_RELATIONS[i][0])  # id
            link1ifacevlan.append(InfoPopulator.LINK_VLAN_RELATIONS[i][1])  # link_id

            if not info_insert(self.tbl_mgr, "ops_link_interfacevlan", link1ifacevlan):
                ok = False


        for i in range(len(InfoPopulator.LINK_PARENT_CHILD_RELATION)):
            link_rel = []
            link_rel.append(InfoPopulator.LINK_PARENT_CHILD_RELATION[i][0])  # parent id
            link_rel.append(InfoPopulator.LINK_PARENT_CHILD_RELATION[i][1])  # child id
            if not info_insert(self.tbl_mgr, "ops_link_relations", link_rel):
                ok = False


        sliceuser1 = []
        sliceuser1.append("tupty")
        sliceuser1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        sliceuser1.append("urn:publicid:IDN+instageni.gpolab.bbn.com+node+pc1")
        sliceuser1.append("lead")
        sliceuser1.append(url_opsconfig_local_info + "user/" + sliceuser1[0])

        if not info_insert(self.tbl_mgr, "ops_slice_user", sliceuser1):
            ok = False


        authuser1 = []
        authuser1.append("tupty")
        authuser1.append("ch.geni.net")
        authuser1.append("urn:publicid:IDN+ch.geni.net+user+tupty")
        authuser1.append(url_local_info + "user/" + authuser1[0])

        if not info_insert(self.tbl_mgr, "ops_authority_user", authuser1):
            ok = False


        authslice1 = []
        authslice1.append("ch.geni.net_gpo-infra_slice_tuptyexclusive")
        authslice1.append("ch.geni.net")
        authslice1.append("urn:publicid:IDN+ch.geni.net:gpo-infra+slice+tuptyexclusive")
        authslice1.append(url_local_info + "slice/" + authslice1[0])

        if not info_insert(self.tbl_mgr, "ops_authority_slice", authslice1):
            ok = False

        return ok

    # Dummy information to test the external check store
    def insert_externalcheck_store(self):
        return self.insert_externalcheck_store_info()

    def insert_externalcheck_store_info(self):
        ok = True
        extck_id = "gpo"
        ts = str(int(time.time() * 1000000))
        extck = []
        extck.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#")
        extck.append(extck_id)
        extck.append(self.url_base + "/info/externalcheck/" + extck_id)
        extck.append(ts)
        extck.append(self.url_base + "/data/")
        if not info_insert(self.tbl_mgr, "ops_externalcheck", extck):
            ok = False

        exp1_id = "missouri_ig_to_gpo_ig"

        exp1 = []
        exp1.append("http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#")
        exp1.append(exp1_id)
        exp1.append(self.url_base + "/info/experiment/" + exp1_id)
        exp1.append(ts)
        exp1.append("urn:slice_urn")
        exp1.append("uuid:slice_uuid")
        exp1.append("urn:source_aggregate_urn")
        exp1.append("source aggregate local datastore href")
        exp1.append("urn:destination_aggregate_urn")
        exp1.append("destination aggregate local datastore href")
        if not info_insert(self.tbl_mgr, "ops_experiment", exp1):
            ok = False

        extck_exp1 = []
        extck_exp1.append(exp1_id)
        extck_exp1.append(extck_id)
        extck_exp1.append(self.url_base + "/info/experiment/" + exp1_id)
        if not info_insert(self.tbl_mgr, "ops_externalcheck_experiment", extck_exp1):
            ok = False

        mon_agg = []
        mon_agg.append(InfoPopulator.AGGREGATE_ID)
        mon_agg.append(extck_id)
        mon_agg.append(self.url_base + "/info/aggregate/" + InfoPopulator.AGGREGATE_ID)
        if not info_insert(self.tbl_mgr, "ops_externalcheck_monitoredaggregate", mon_agg):
            ok = False

        return ok


def info_insert(tbl_mgr, table_str, row_arr):
    """
    Function to insert values into a table.
    :param tbl_mgr: the instance of TableManager to use.
    :param table_str: the name of the table to insert into.
    :param row_arr: a list of values.  If any of the values are None,
                    they are translated to a SQL NULL.
    :return: True if the insertion happened correctly, false otherwise.
    """
    val_str = "("

    for col in range(len(row_arr)):
        if col > 0:
            val_str += ", "
        if row_arr[col] is None:
            val_str += "NULL"
        else:
            val_str += "'" + row_arr[col] + "'"
    val_str += ")"

    return tbl_mgr.insert_stmt(table_str, val_str)


def main():

    db_name = "local"
    config_path = "../config/"

    tbl_mgr = table_manager.TableManager(db_name, config_path)
    tbl_mgr.poll_config_store()

    tbl_mgr.drop_all_tables()
    tbl_mgr.establish_all_tables()
    ip = InfoPopulator(tbl_mgr)

    if not ip.insert_fake_info():
        sys.stderr.write("Error executing info populator\n")
        sys.exit(-1)


    q_res = tbl_mgr.query("select count(*) from ops_aggregate");
    if q_res is not None:
        print "num entries", q_res[0][0]


if __name__ == "__main__":
    main()
