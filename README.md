# GENI Monitoring
Fork of GENI monitoring code from InstaGENI

## Specs
### Layout

#### Directories which implement components of the ops monitoring model:

* `alerting/`: reference alerting utilities 

* `collector/`: 

  * **Collector Programs that Collect Data**

    * `collector/single_local_datastore_info_crawler.py` - 
   crawls a single datastore based on the arguments for what the
   crawler should look for.  This populates info tables (not
   time-series data tables).

    * `collector/single_local_datastore_object_type_fetcher.py` - This
   program fetches time-series data about objects of a single type out
   of a single datastore.  It is configured to query all event types
   for the requested objects' type.  It is configured to query all
   objects of the requested type.

    * `collector/rest_call.py` - This program sends a REST call to a datastore,
   prints the response, and validates it with validictory.  It can crawl an
   entire datastore either all at once or interactively.  Run with
   `--help` for more information.

  * **Collector Testing Programs**

    * `collector/unit-tests/collector_table_reset.py` - for reseting/initializing
   database tables at the collector.

    * `collector/response_validator.py` - Technically a set of functions
   that help determine if the json response from a datastore is
   formatted according to the json schema.

  * **Collector Nagios Programs**

    * `collector/psql_queries.py` - This is a program for Nagios sitting on
   top of the collector database.  It makes queries on behalf of Nagios.

* `schema/`: schema/examples for datastore polling API

* `local/`: reference local datastore 

  * **Local Datastore Database Handling Programs**

    * `local/unit-tests/local_table_reset.py` for reseting/initializing
   database tables at the local datastore

    * `local/unit-tests/local_restart_node_interface_stats.py` for
   populating the datastore's database with test data.  It uses
   local/stats_populator.py and local/info_populator.py classes

  * **External Check Datastore Data Generation Programsd**

    * `local/coordinate_mesoscale_experiments.py` logs into a node of the
   monitoring sliver and calls the pinger program to record ping times
   across the mesoscale.  It grabs results from the pinger and inserts
   them into the database of the external check datastore.

    * `local/unit-tests/pinger.py` to be install along with
   local/unit-tests/ip_addresses.conf on a node called by the
   coordinate_mesoscale_experiments.py program to perform pings to
   addresses in ip_addresses.conf and write result tuples in a flat
   file for the coordinate_mesoscale_experiments.py to grab. 

    * local/extck_store.py` this program populates a few of the basic
   tables at the external check store that are called during info
   queries (not time-series data queries). 

    * `local/extck_populator.py` this program populates the table
   ops_aggregate_is_available with time-series data about the
   health of the control plane.  This program requires omni to
   be configured in order to run because it actually calls 
   getVersion on each aggregate.

#### Directories containing helper code:
* `common/`: python libraries used by multiple components
* `config/`: python configuration files used by multiple components
* `test/`: generic utilities for testing code
* `cm/`: configuration management utilities
### Schema
The database table schema is listed in the file `config/opsconfig.json.jwc` and in the directory `schema/`.

## Installation
Puppet script installs rpm package `/usr/local/ops-monitoring` in the head node.
### Config
