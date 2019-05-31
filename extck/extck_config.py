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
import ConfigParser
import os
import sys
import re

extck_path = os.path.abspath(os.path.dirname(__file__))

class ExtckConfigLoader:
    __EXTCK_SECTION = "extck"
    __AM_TEST_CMD = "am_test_cmd"
    __AM_URL_STR = "AM_URL"
    __AM_TEST_VERSION_ARG = "am_test_version_arg"
    __AM_API_VERSION_STR = "API_VERSION"
    __AM_KNOWN_TYPES = "am_known_types"
    __AM_NICK_CACHE_FILE = "am_nick_cache_file"
    __OPSCONFIG_URL = "opsconfig_url"
    __EXTCK_STORE_ID = "extck_id"
    __EXTCK_STORE_BASE_URL = "extck_base_url"
    __GENI_LIB_PATH = "geni_lib_path"
    __GENI_LIB_CONFIG_PATH = "geni_lib_config_path"
    __GCF_DIR = "gcf_dir"
    __POPULATOR_POOL_SIZE = "populator_pool_size"
    __SCS_TIMEOUT = "scs_timeout"

    __EXPERIMENT_SECTION = "experiment"
    __SRC_PING_CAMPUS = "src_ping_campus"
    __SRC_PING_CORE = "src_ping_core"
    __SLICENAMES = "slicenames"
    __COORDINATION_POOL_SIZE = "coordination_pool_size"
    __PING_THREAD_POOL_SIZE = "ping_thread_pool_size"
    __PING_INITIAL_COUNT = "ping_initial_count"
    __PING_MEASURMENT_COUNT = "ping_measurement_count"
    __SLICE_URN = "urn"
    __SLICE_UUID = "uuid"
    __PING_SLICE = "slicename"
    __PING_NETWORK = "network"
    __IPS_FILE_REMOTE_LOCATION = "ips_file_remote_location"
    __PINGER_FILE_REMOTE_LOCATION = "pinger_file_remote_location"
    __LOCAL_OUTPUT_DIR = "local_output_dir"
    __REMOTE_OUTPUT_DIR = "remote_output_dir"
    __SSH_KEY_FILE = "ssh_key_file"
    __VM_ADDRESS = "vm_address"
    __VM_PORT = "vm_port"
    __SCS_AGGREGATES_SECTION_PREFIX = "scs_aggregates_"
    __SOURCE_PING_SECTION_PREFIX = "ping_"



    def __init__(self, logger):
        self._logger = logger
        self._table_json = json.load(open(os.path.join(extck_path, "extck_tables.json")))
        self._extck_config = ConfigParser.ConfigParser()
        configfile = os.path.join(extck_path, "extck.conf")
        if configfile not in self._extck_config.read(configfile):
            self._logger.critical("Could not read external check configuration file: %s" % configfile)
            sys.exit(-1)

        self._parse_table_schemas()
        self._parse_table_constraints()
        self.__get_api_versions_regular_expressions()


    def _parse_table_schemas(self):
        table_defs = self._table_json["tables"]
        table_schemas = dict()
        for table in table_defs:
            table_name = table["name"]
            table_schemas[table_name] = table["db_schema"]

        self._table_schemas = table_schemas

    def _parse_table_constraints(self):
        table_defs = self._table_json["tables"]
        table_constraints = dict()
        for table in table_defs:
            table_name = table["name"]
            table_constraints[table_name] = table["constraints"]

        self._table_constraints = table_constraints


    def __get_api_versions_regular_expressions(self):
        am_types = self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__AM_KNOWN_TYPES)
        types = am_types.split(",")
        api_versions = {}
        for t in types:
            t1 = t.strip()
            version_dict = self.__get_am_type_api_version_regular_expressions(t1)
            api_versions[t1] = version_dict
        self._api_versions = api_versions

    def __get_am_type_api_version_regular_expressions(self, am_type):
        am_section = "am_" + am_type
        version_dict = {}
        for version in ('1', '2', '3'):
            try:
                regexs = self._extck_config.get(am_section, version)
                regexsA = regexs.split('\n')
                res = []
                for re in regexsA:
                    res.append(re)
                version_dict[version] = res
            except ConfigParser.NoOptionError:
                pass
        return version_dict

    def get_extck_table_schemas(self):
        return self._table_schemas

    def get_extck_table_constraints(self):
        return self._table_constraints

    def __get_am_test_command(self, am_url):
        cmd_str = self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__AM_TEST_CMD)
        return cmd_str.replace(ExtckConfigLoader.__AM_URL_STR, am_url)

    def __get_am_test_version_arg(self, api_version):
        version_arg = self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__AM_TEST_VERSION_ARG)
        return version_arg.replace(ExtckConfigLoader.__AM_API_VERSION_STR, api_version)

    def get_nickname_cache_file_location(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__AM_NICK_CACHE_FILE)

    def get_opsconfigstore_url(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__OPSCONFIG_URL)

    def get_extck_store_id(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__EXTCK_STORE_ID)

    def get_extck_store_base_url(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__EXTCK_STORE_BASE_URL)

    def get_apiversion_from_am_url(self, am_url, am_type):
        matched_version = 0
        if (self._api_versions.has_key(am_type)):
            versions_and_reg_exes = self._api_versions[am_type]
            found = False
            for version in versions_and_reg_exes.keys():
                reg_exes = versions_and_reg_exes[version]
                for reg_ex in reg_exes:
                    if re.match(reg_ex, am_url) is not None:
                        found = True
                        matched_version = version
                        break
                if found:
                    break
        return matched_version

    def get_am_full_test_command(self, am_url, am_type):
        cmd_str = self.__get_am_test_command(am_url)
        matched_version = self.get_apiversion_from_am_url(am_url, am_type)
        if matched_version != 0:
            cmd_str += " "
            cmd_str += self.__get_am_test_version_arg(matched_version)

        return cmd_str

    def get_gcf_path(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__GCF_DIR)

    def get_populator_pool_size(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__POPULATOR_POOL_SIZE)

    def get_geni_lib_path(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__GENI_LIB_PATH)

    def get_geni_lib_config_path(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__GENI_LIB_CONFIG_PATH)

    def get_scs_timeout(self):
        return self._extck_config.get(ExtckConfigLoader.__EXTCK_SECTION, ExtckConfigLoader.__SCS_TIMEOUT)

    def get_expected_aggregates_for_scs(self, scs_id):
        section_name = ExtckConfigLoader.__SCS_AGGREGATES_SECTION_PREFIX + scs_id
        results = dict()
        if self._extck_config.has_section(section_name):
            aggregates = self._extck_config.items(section_name)
            for nickname, am_urn in aggregates:
                results[nickname] = am_urn
        return results

    def __get_value_set_from_comma_separated_string(self, valstr):
        vals = valstr.split(',')
        srcs = set()
        for val in vals:
            srcs.add(val.strip())
        return srcs

    def get_experiment_source_ping_campus(self):
        valstr = self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__SRC_PING_CAMPUS)
        return self.__get_value_set_from_comma_separated_string(valstr)

    def get_experiment_source_ping_core(self):
        valstr = self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__SRC_PING_CORE)
        return self.__get_value_set_from_comma_separated_string(valstr)

    def get_experiment_slices_info(self):
        valstr = self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__SLICENAMES)
        slicenames = self.__get_value_set_from_comma_separated_string(valstr)
        slices_dict = dict()
        for slice_name in slicenames:
            section_name = "slice_" + slice_name
            urn = self._extck_config.get(section_name, ExtckConfigLoader.__SLICE_URN)
            uuid = self._extck_config.get(section_name, ExtckConfigLoader.__SLICE_UUID)
            slices_dict[slice_name] = (urn, uuid)
        return slices_dict

    def get_experiment_coordination_thread_pool_size(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__COORDINATION_POOL_SIZE)

    def get_experiment_source_ping_slice_name(self, srcping):
        return self._extck_config.get(ExtckConfigLoader.__SOURCE_PING_SECTION_PREFIX + srcping, ExtckConfigLoader.__PING_SLICE)

    def get_experiment_ping_thread_pool_size(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__PING_THREAD_POOL_SIZE)

    def get_experiment_ping_initial_count(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__PING_INITIAL_COUNT)

    def get_experiment_ping_measurmentl_count(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__PING_MEASURMENT_COUNT)

    def get_experiment_source_ping_vm_address(self, srcping):
        return self._extck_config.get(ExtckConfigLoader.__SOURCE_PING_SECTION_PREFIX + srcping, ExtckConfigLoader.__VM_ADDRESS)

    def get_experiment_source_ping_vm_port(self, srcping):
        return self._extck_config.get(ExtckConfigLoader.__SOURCE_PING_SECTION_PREFIX + srcping, ExtckConfigLoader.__VM_PORT)

    def get_ips_file_remote_location(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__IPS_FILE_REMOTE_LOCATION)

    def get_pinger_file_remote_location(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__PINGER_FILE_REMOTE_LOCATION)

    def get_local_output_dir(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__LOCAL_OUTPUT_DIR)

    def get_remote_output_dir(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__REMOTE_OUTPUT_DIR)

    def get_ssh_key_file_location(self):
        return self._extck_config.get(ExtckConfigLoader.__EXPERIMENT_SECTION, ExtckConfigLoader.__SSH_KEY_FILE)


