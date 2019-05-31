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

from flask import Flask, request, Response
import httplib

import sys

class LocalDatastoreServer:
    def __init__(self, parent_path):
        self.local_path = parent_path + "/local/"
        self.common_path = parent_path + "/common/"
        self.config_path = parent_path + "/config/"

        self.debug = False
        sys.path.append(self.local_path)
        sys.path.append(self.common_path)
        sys.path.append(self.config_path)

        import rest_call_handler
        import table_manager
        import logger

        opslog = logger.get_logger(self.config_path)
        opslog.info("Starting ops monitoring")

        self.db_name = "local"

        # uses postgres by default
        self.tm = table_manager.TableManager(self.db_name, self.config_path)
        self.tm.poll_config_store()

        # Try to get the software version we're running from the VERSION file
        # in the top-level directory.
        version_filename = parent_path + "/VERSION"
        try:
            version_file = open(version_filename)
            self.monitoring_version = version_file.readline().strip()
            version_file.close()
        except Exception, e:
            opslog.warning("Could not read monitoring version from file %s: %s" % (
                    version_filename, str(e)))
            self.monitoring_version = "unknown"

        opslog.info("Monitoring version is %s" % (self.monitoring_version))

        self.app = Flask(__name__)

        def make_resp(json_resp):
            """
            Function to make an HTTP Response given a json response
            :param json_resp: the json response in text format
            :return: an HTTP Response given the json response
            """
            return Response(json_resp, status=httplib.OK, mimetype='application/json; charset=utf-8')



        @self.app.route('/info/aggregate/<path:agg_id>', methods=['GET'])
        def info_aggregate_args(agg_id):
            return make_resp(rest_call_handler.handle_aggregate_info_query(self.tm, agg_id, self.monitoring_version))

        @self.app.route('/info/externalcheck/<path:extck_id>', methods=['GET'])
        def info_externalcheck_args(extck_id):
            return make_resp(rest_call_handler.handle_externalcheck_info_query(self.tm, extck_id))

        @self.app.route('/info/experiment/<path:exp_id>', methods=['GET'])
        def info_experiment_args(exp_id):
            return make_resp(rest_call_handler.handle_experiment_info_query(self.tm, exp_id))

        @self.app.route('/info/node/<path:node_id>', methods=['GET'])
        def info_node_args(node_id):
            return make_resp(rest_call_handler.handle_node_info_query(self.tm, node_id))

        @self.app.route('/info/interface/<path:iface_id>', methods=['GET'])
        def info_interface_args(iface_id):
            return make_resp(rest_call_handler.handle_interface_info_query(
                self.tm, iface_id))

        @self.app.route('/info/interfacevlan/<path:ifacevlan_id>', methods=['GET'])
        def info_interfacevlan_args(ifacevlan_id):
            return make_resp(rest_call_handler.handle_interfacevlan_info_query(self.tm, ifacevlan_id))

        @self.app.route('/info/sliver/<path:sliver_id>', methods=['GET'])
        def info_sliver_args(sliver_id):
            return make_resp(rest_call_handler.handle_sliver_info_query(self.tm, sliver_id))

        @self.app.route('/info/link/<path:link_id>', methods=['GET'])
        def info_link_args(link_id):
            return make_resp(rest_call_handler.handle_link_info_query(self.tm, link_id))

        @self.app.route('/info/slice/<path:slice_id>', methods=['GET'])
        def info_slice_args(slice_id):
            return make_resp(rest_call_handler.handle_slice_info_query(self.tm, slice_id))

        @self.app.route('/info/user/<path:user_id>', methods=['GET'])
        def info_user_args(user_id):
            return make_resp(rest_call_handler.handle_user_info_query(self.tm, user_id))

        @self.app.route('/info/authority/<path:authority_id>', methods=['GET'])
        def info_authority_args(authority_id):
            return make_resp(rest_call_handler.handle_authority_info_query(self.tm, authority_id))

        @self.app.route('/info/opsconfig/<path:opsconfig_id>', methods=['GET'])
        def info_opsconfig_args(opsconfig_id):
            return rest_call_handler.handle_opsconfig_info_query(
                self.tm, opsconfig_id)

        @self.app.route('/data/', methods=['GET'])
        def data():
            # get everything to the right of ?q= as string from flask.request
            filters = request.args.get('q', None)
            return make_resp(rest_call_handler.handle_ts_data_query(self.tm, filters))

    def __del__(self):
        import logger
        logger.get_logger(self.config_path).info("Stopping ops monitoring")

if __name__ == '__main__':
    # We only come here when running directly under Flask, i.e.,
    # when run as "python ./web_server.py"
    server = LocalDatastoreServer('..')
    server.app.run(debug=True, host="0.0.0.0", port=4334)
