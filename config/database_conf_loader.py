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

import ConfigParser

def generic_config_parser(config_path, local):
    """
    Method to create a ConfigParser object and parse in the appropriate configuration file.
    :param config_path: the path to the ops-monitoring configuration folder.
    :param local: boolean indicating whether the local datastore configuration file will be read in or the collector configuration file.
    :return: a ConfigParser object loaded with the configuration parameters.
    """
    config = ConfigParser.ConfigParser()
    if local:
        filename = config_path + "/local_datastore_operator.conf"
    else:
        filename = config_path + "/collector_operator.conf"
    config.read(filename)
    return config

def generic_main(config):
    """
    Method to return the dbtype parameter value of the [main] section.
    :param config: the ConfigParser object loaded with the configuration.
    :return: the dbtype parameter value of the [main] section
    """
    dbtype = config.get("main", "dbtype")
    return [dbtype]

def main_local(config_path):
    """
    Method to get the type of database from the local datastore configuration file.
    :param config_path: the path to the ops-monitoring configuration folder.
    :return: the type of database from the local datastore configuration file
    """
    config = generic_config_parser(config_path, True)
    return generic_main(config)

def main_collector(config_path):
    """
    Method to get the type of database from the collector configuration file
    :param config_path: the path to the ops-monitoring configuration folder.
    :return: the type of database from the collector configuration file
    """
    config = generic_config_parser(config_path, False)
    return generic_main(config)


def main(config_path, dbconfigtype):
    """
    Method to get the DB engine type from the appropriate configuration file.
    :param config_path: the path to the ops-monitoring configuration folder.
    :param dbconfigtype: the kind of DB configuration. ("local" or "collector" so far)
    :return: the type of database from the corresponding configuration file
    """
    import sys
    import logger
    if dbconfigtype == "local":
        return main_local(config_path)
    elif dbconfigtype == "collector":
        return main_collector(config_path)
    else:
        logger.get_logger(config_path).critical("No collector or local database selected.  Exiting\n")
        sys.exit(1)

def generic_db_param(config, dbengine):
    """
    Method to get the database parameters values from a given configuration file.
    :param config: the ConfigParser object loaded with the configuration.
    :param dbengine: the name of the DB engine. This corresponds to the section name in the configuration file.
    :return: a tuple of configuration parameters containing the DB name, username, password, DB hostname, DB port and desired DB connection pool size.
    """
    database = config.get(dbengine, "database")
    username = config.get(dbengine, "username")
    password = config.get(dbengine, "password")
    host = config.get(dbengine, "host")
    port = config.get(dbengine, "port")
    poolsize = config.get(dbengine, "poolsize")
    return [database, username, password, host, port, poolsize]

def psql_local(config_path):
    """
    Method to get the postgresql database parameters values from the local datastore configuration file.
    :param config_path: he path to the ops-monitoring configuration folder.
    :return: a tuple of configuration parameters containing the DB name, username, password, DB hostname, DB port and desired DB connection pool size.
    """
    config = generic_config_parser(config_path, True)
    return generic_db_param(config, "postgres")

def psql_collector(config_path):
    """
    Method to get the postgresql database parameters values from the collector configuration file.
    :param config_path: he path to the ops-monitoring configuration folder.
    :return: a tuple of configuration parameters containing the DB name, username, password, DB hostname, DB port and desired DB connection pool size.
    """
    config = generic_config_parser(config_path, False)
    return generic_db_param(config, "postgres")

def mysql_local(config_path):
    """
    Method to get the mysql database parameters values from the local datastore configuration file.
    :param config_path: he path to the ops-monitoring configuration folder.
    :return: a tuple of configuration parameters containing the DB name, username, password, DB hostname, DB port and desired DB connection pool size.
    """
    config = generic_config_parser(config_path, True)
    return generic_db_param(config, "mysql")

def mysql_collector(config_path):
    """
    Method to get the mysql database parameters values from the collector configuration file.
    :param config_path: he path to the ops-monitoring configuration folder.
    :return: a tuple of configuration parameters containing the DB name, username, password, DB hostname, DB port and desired DB connection pool size.
    """
    config = generic_config_parser(config_path, False)
    return generic_db_param(config, "mysql")

def get_db_parameters(config_path, dbengine, dbconfigtype):
    """
    Method to get the database parameters values for a dbengine kind of database and for a dbconfigtype of configuration.
    :param config_path: 
    :param dbengine: the kind of database ("mysql" or "postgres" so far)
    :param dbconfigtype: the kind of DB configuration. ("local" or "collector" so far)
    """
    import sys
    import logger
    if dbconfigtype == "local":
        if dbengine == "postgres":
            return psql_local(config_path)
        elif dbengine == "mysql":
            return mysql_local(config_path)
        else:
            logger.get_logger(config_path).critical("Unrecognized dbengine %s.  Exiting\n" % (dbengine))
            sys.exit(1)
    elif dbconfigtype == "collector":
        if dbengine == "postgres":
            return psql_collector(config_path)
        elif dbengine == "mysql":
            return mysql_collector(config_path)
        else:
            logger.get_logger(config_path).critical("Unrecognized dbengine %s.  Exiting\n" % (dbengine))
            sys.exit(1)
    else:
        logger.get_logger(config_path).critical("No collector or local database selected.  Exiting\n")
        sys.exit(1)
