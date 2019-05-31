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

import datetime
import psycopg2
import sys

class CollectorQuerier():
    """
    Class for making queries to the database, not thread safe
    """

    ###########################################################################
    # Class constants 
    ###########################################################################

    # Default value of how many minutes back to query in default case
    _DEFAULT_QUERY_WINDOW=10

    # The major separator used for pieces of a resource ID in the database 
    _DB_RES_MAJOR_SEP=":"
 
    # The minor separator used for pieces of a resource ID in the database
    _DB_RES_MINOR_SEP="_"

    # Nagios resource ID separator
    _NAGIOS_RES_SEP="_"

    ###########################################################################
    # Constructors
    ###########################################################################

    def __init__(self, dbname, hostname, dbuser, dbpassword, 
                 query_window=_DEFAULT_QUERY_WINDOW):

        self._query_window = query_window

        try:
            # Connect to localhost to force password authentication with
            # default postgres config
            self._con = psycopg2.connect(database=dbname, host=hostname, 
                                         user=dbuser, password=dbpassword)
        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    ###########################################################################
    # Public utility functions 
    ###########################################################################

    def close(self):
        try:
            self._con.close()
        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e
        except:
            print "Couldn't close DB connection"

    ###########################################################################
    # Public collector queries
    ###########################################################################

    def get_last_node_mem_util(self, aggregate, since=None):
        """
        Get the latest value of memory utilization for a given aggregate
        """
        # FIXME: we should probably get the shortname from the database, but
        # that is currently what nagios queries uses for aggregates as well
        agg_shortname = aggregate

        # Get IDs for all nodes
        nodes = self._get_ops_nodes_by_aggregate(agg_shortname)

        # initialize return value
        external_result = {}

        # Look at the information for each interface at this aggregate
        for node in nodes:
            ### Do magic parsing to get resource name for nagios
            # Remove the parts of the resource associated with the aggregate
            node_components = node.split(self._DB_RES_MINOR_SEP)

            # The node name is the last element
            node_name = node_components[len(node_components) - 1]

            ### Get the measured percentage swap free
            mem_used_internal = self._get_metric_by_resource(node, 
                                     agg_shortname, "ops_mem_used_kb")
            
            nagios_res_name = node_name

            ### Calculate the memory utilization
            if node in mem_used_internal:
                mem_used = mem_used_internal[node][0]["value"]
                mem_total_kb = self._get_mem_total_kb(node)
                mem_utilization = (mem_used / float(mem_total_kb)) * 100
            else:
                # Return a negative value if the resource doesn't have data 
                mem_utilization = -1

            ### Set the return value for this resource
            external_result[nagios_res_name] = mem_utilization

        return external_result

    def get_last_node_swap_free(self, aggregate, since=None):
        """
        Get the latest value of the percentage of swap free for a given
        aggregate's resources
        """
        # FIXME: we should probably get the shortname from the database, but
        # that is currently what nagios queries uses for aggregates as well
        agg_shortname = aggregate

        # Get IDs for all nodes
        nodes = self._get_ops_nodes_by_aggregate(agg_shortname)

        # initialize return value
        external_result = {}

        # Look at the information for each interface at this aggregate
        for node in nodes:
            ### Do magic parsing to get resource name for nagios
            # Remove the parts of the resource associated with the aggregate
            node_components = node.split(self._DB_RES_MINOR_SEP)

            # The node name is the last element
            node_name = node_components[len(node_components) - 1]

            ### Get the measured percentage swap free
            swap_free_internal = self._get_metric_by_resource(node, 
                                                              agg_shortname, 
                                                              "ops_swap_free")
            
            nagios_res_name = node_name

            ### Set the appropriate swap free 
            if node in swap_free_internal:
                swap_free = swap_free_internal[node][0]["value"]
            else:
                # Return a negative value if the resource doesn't have data 
                swap_free = -1

            ### Set the return value for this resource
            external_result[nagios_res_name] = swap_free

        return external_result

    def get_last_node_cpu_util(self, aggregate, since=None):
        """
        Get the latest value of CPU utilization for a given
        aggregate's resources
        """
        # FIXME: we should probably get the shortname from the database, but
        # that is currently what nagios queries uses for aggregates as well
        agg_shortname = aggregate

        # Get IDs for all nodes
        nodes = self._get_ops_nodes_by_aggregate(agg_shortname)

        # initialize return value
        external_result = {}

        # Look at the information for each interface at this aggregate
        for node in nodes:
            ### Do magic parsing to get resource name for nagios
            # Remove the parts of the resource associated with the aggregate
            node_components = node.split(self._DB_RES_MINOR_SEP)

            # The node name is the last element
            node_name = node_components[len(node_components) - 1]

            ### Get the measured CPU utilization for this node 
            cur_cpu_internal = self._get_metric_by_resource(node, 
                                                            agg_shortname, 
                                                            "ops_cpu_util")
            
            nagios_res_name = node_name

            ### Set the appropriate CPU itilization
            if node in cur_cpu_internal:
                cpu_util = cur_cpu_internal[node][0]["value"]
            else:
                # Return a negative value if the resource doesn't have data 
                cpu_util = -1

            ### Set the return value for this resource
            external_result[nagios_res_name] = cpu_util

        return external_result

    def get_last_interface_tx_util(self, aggregate, since=None):
        """
        Get the latest value of tx utilization for a given
        aggregate's resources
        """
        # FIXME: we should probably get the shortname from the database, but
        # that is currently what nagios queries uses for aggregates as well
        agg_shortname = aggregate

        # Get IDs for all interfaces
        interfaces = self._get_ops_interfaces_by_aggregate(agg_shortname)

        # initialize return value
        external_result = {}

        # Look at the information for each interface at this aggregate
        for interface in interfaces:
            ### Do magic parsing to get resource name for nagios
            # Remove the parts of the resource associated with the aggregate
            if_components = interface.split(self._DB_RES_MAJOR_SEP)

            # The interface name is the last element
            if_name = if_components[len(if_components) - 1]

            # The node ID is the second-to-last element
            node_id = if_components[len(if_components) - 2]
            node_components = node_id.split(self._DB_RES_MINOR_SEP)
            node_name = node_components[len(node_components) - 1]

            # Use a nagios-friendly separator
            nagios_res_name = node_name + self._NAGIOS_RES_SEP + if_name

            ### Get the measured throughput for this interface
            cur_tx_internal = self._get_metric_by_resource(interface, 
                                                           agg_shortname, 
                                                           "ops_tx_bps")
            
            ### Calculate the interface utilization
            if interface in cur_tx_internal:
                cur_tx = cur_tx_internal[interface][0]["value"]
                max_bps = self._get_max_bps(interface)
                tx_utilization = (cur_tx / max_bps) * 100
            else:
                # Return a negative value if the resource doesn't have data 
                tx_utilization = -1

            ### Set the return value for this resource
            external_result[nagios_res_name] = tx_utilization

        return external_result

    def get_last_interface_rx_util(self, aggregate, since=None):
        """
        Get the latest value of rx utilization for a given
        aggregate's resources
        """
        # FIXME: we should probably get the shortname from the database, but
        # that is currently what nagios queries uses for aggregates as well
        agg_shortname = aggregate

        # Get IDs for all interfaces
        interfaces = self._get_ops_interfaces_by_aggregate(agg_shortname)

        # initialize return value
        external_result = {}

        # Look at the information for each interface at this aggregate
        for interface in interfaces:
            ### Do magic parsing to get resource name for nagios
            # Remove the parts of the resource associated with the aggregate
            if_components = interface.split(self._DB_RES_MAJOR_SEP)

            # The interface name is the last element
            if_name = if_components[len(if_components) - 1]

            # The node ID is the second-to-last element
            node_id = if_components[len(if_components) - 2]
            node_components = node_id.split(self._DB_RES_MINOR_SEP)
            node_name = node_components[len(node_components) - 1]

            # Use a nagios-friendly separator
            nagios_res_name = node_name + self._NAGIOS_RES_SEP + if_name

            ### Get the measured throughput for this interface
            cur_rx_internal = self._get_metric_by_resource(interface, 
                                                           agg_shortname, 
                                                           "ops_rx_bps")
            
            ### Calculate the interface utilization
            if interface in cur_rx_internal:
                cur_rx = cur_rx_internal[interface][0]["value"]
                max_bps = self._get_max_bps(interface)
                rx_utilization = (cur_rx / max_bps) * 100
            else:
                # Return a negative value if the resource doesn't have data 
                rx_utilization = -1

            ### Set the return value for this resource
            external_result[nagios_res_name] = rx_utilization

        return external_result

    ###########################################################################
    # Private utility methods
    ###########################################################################

    def _get_ops_interfaces_by_aggregate(self, aggregate):
        """
        Return a list of resource IDs for interfaces at an aggregate
        """
        query = "SELECT id FROM ops_node_interface WHERE node_id IN"
        query = query + "(SELECT id FROM ops_node WHERE id IN "
        query = query + "(SELECT id FROM ops_aggregate_resource WHERE "
        query = query + "aggregate_id=%s));"

        args = (aggregate, )

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            result = []

            # Build the return value from the records
            for record in cur:
                result.append(record[0])

            # Close the cursor now that our object is built
            cur.close()

            return result

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    def _get_ops_nodes_by_aggregate(self, aggregate):
        """
        Return a list of resource IDs for nodes at an aggregate
        """
        query = "SELECT id FROM ops_node WHERE id IN "
        query = query + "(SELECT id FROM ops_aggregate_resource WHERE "
        query = query + "aggregate_id=%s);"

        args = (aggregate, )

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            result = []

            # Build the return value from the records
            for record in cur:
                result.append(record[0])

            # Close the cursor now that our object is built
            cur.close()

            return result

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    def _datetime_to_db_timestamp(self, dt):
        """
        Converts a python datetime object to a timestamp in the format
        that the querier requires
        """
        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = dt - epoch

        # Multiply by 1M to match what is used in the collector database
        return delta.total_seconds() * 1000000

    # get metric by resource
    def _get_metric_by_resource(self, resource, agg_shortname, 
                                metric, since=None):
        """
        Queries for a specific metric associated with a resource at an
        aggregate from a time frame up to now, most recent data first
        """
        # If since is unset, make it default 
        if since is None:
            since = datetime.datetime.now() - \
                    datetime.timedelta(minutes=self._query_window)

        # Convert datetime timestamp to db format
        since = self._datetime_to_db_timestamp(since)

        # Build the query...
        #  Pass the table name to avoid added quotes
        #  Pass all other parameters using the normal psycopg2 method
        query = "SELECT id,ts,v FROM %s " % metric
        query = query + "WHERE (ts > %s) AND (id=%s) AND (aggregate_id=%s)"
        query = query + "ORDER BY ts DESC;"
        args = (since, resource, agg_shortname, )

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            result = {}

            # Build the return value from the records
            for record in cur:
                resource_id = resource 
                time = record[1]
                value = record[2]

                if not resource_id in result:
                    result[resource_id] = []

                measurement = { "time" : time, "value" : value }
                
                result[resource_id].append(measurement)

            # Close the cursor now that our object is built
            cur.close()

            return result

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e


    def _get_metric_by_aggregate(self, aggregate, metric, since=None):
        """
        Queries for a specific metric associated with an aggregate
        from a time frame up to this point in time, orders results
        from most recent data to least recent within window
        """

        # If since is unset, make it default 
        if since is None:
            since = datetime.datetime.now() - \
                    datetime.timedelta(minutes=self._query_window)

        # Convert datetime timestamp to db format
        since = self._datetime_to_db_timestamp(since)

        # Build the query...
        #  Pass the table name to avoid added quotes
        #  Pass all other parameters using the normal psycopg2 method
        query = "SELECT id,ts,v FROM %s " % metric
        query = query + "WHERE (ts > %s) AND (id LIKE %s) ORDER BY ts DESC;"
        args = (since, aggregate + "%")

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            result = {}

            # Build the return value from the records
            for record in cur:
                resource_id = record[0]
                time = record[1]
                value = record[2]

                if not resource_id in result:
                    result[resource_id] = []
                    measurement = { "time" : time, "value" : value }
                
                result[resource_id].append(measurement)

            # Close the cursor now that our object is built
            cur.close()

            return result

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    def _get_max_bps(self, db_resource):
        """
        Gets the max_bps property of an interface using the db resource ID
        """
        query = "SELECT properties$max_bps FROM ops_interface WHERE (id=%s);"
        args = (db_resource, )

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            # Build the return value from the records
            record = cur.fetchone()

            if record is not None:
                max_bps = record[0]
            else:
                # FIXME: for now, just bomb out like we would have if we
                # weren't checking for this at all, but print a warning
                print "MAX BPS for %s not known" % db_resource
                max_bps = record[0]

            # Close the cursor now that our object is built
            cur.close()

            return max_bps 

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    def _get_mem_total_kb(self, db_resource):
        """
        Gets the mem_total_kb property of a node using the db resource ID
        """
        query = "SELECT properties$mem_total_kb FROM ops_node WHERE (id=%s);"
        args = (db_resource, )

        try:
            # Get a cursor and make the query
            cur = self._con.cursor()
            cur.execute(query, args)

            # Build the return value from the records
            record = cur.fetchone()

            if record is not None:
                mem_total_kb = record[0]
            else:
                # FIXME: for now, just bomb out like we would have if we
                # weren't checking for this at all, but print a warning
                print "Mem total KB for %s not known" % db_resource
                mem_total_kb = record[0]

            # Close the cursor now that our object is built
            cur.close()

            return mem_total_kb

        except psycopg2.Error as e:
            # FIXME: do something else, probably cascade the exception
            print e

    ###########################################################################
    # Unit testing code 
    ###########################################################################

    def run_unit_test(self, aggregate):
        result = self.get_last_interface_rx_util(aggregate)
        
        for resource in result:
            print "gpo-ig[%s] latest interface rx utilization is: %s" % \
                (resource, result[resource])

        result = self.get_last_interface_tx_util(aggregate)
        
        for resource in result:
            print "gpo-ig[%s] latest interface tx utilization is: %s" % \
                (resource, result[resource])

        result = self.get_last_node_cpu_util(aggregate)
        
        for resource in result:
            print "gpo-ig[%s] latest cpu utilization is: %s" % \
                (resource, result[resource])

        result = self.get_last_node_swap_free(aggregate)
        
        for resource in result:
            print "gpo-ig[%s] latest percentage of swap free is: %s" % \
                (resource, result[resource])

        result = self.get_last_node_mem_util(aggregate)
        
        for resource in result:
            print "gpo-ig[%s] latest mem utilization: %s" % \
                (resource, result[resource])

        return 0

class ValueUnknownException(Exception):

    def __init__(self, aggregate, resource, metric):
       self._aggregate = aggregate
       self._resource = resource
       self._metric = metric

    def __str__(self):
       message = "No value known for:"
       message = message + "  Aggregate %s" % self._aggregate
       message = message + "  Resource %s" % self._resource
       message = message + "  Metric %s" % self._metric
       return message

if __name__ == "__main__":
    querier = CollectorQuerier("collector", "localhost", "nagios", "19dnH4N,dkv")
    val = querier.run_unit_test("gpo-ig")
    querier.close()
    sys.exit(val)
