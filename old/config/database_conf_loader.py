#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
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

def main_local(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/local_datastore_operator.conf")
    dbtype = config.get("main", "dbtype")
    return [dbtype]

def main_collector(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/collector_operator.conf")
    dbtype = config.get("main", "dbtype")
    return [dbtype]

def psql_local(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/local_datastore_operator.conf")
    database = config.get("postgres","database")
    username = config.get("postgres","username")
    password = config.get("postgres","password")
    host = config.get("postgres","host")
    port = config.get("postgres","port")
    return [database, username, password, host, port]

def psql_collector(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/collector_operator.conf")
    database = config.get("postgres","database")
    username = config.get("postgres","username")
    password = config.get("postgres","password")
    host = config.get("postgres","host")
    port = config.get("postgres","port")
    return [database, username, password, host, port]

def mysql_local(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/local_datastore_operator.conf")
    database = config.get("mysql","database")
    username = config.get("mysql","username")
    password = config.get("mysql","password")
    host = config.get("mysql","host")
    port = config.get("mysql","port")
    return [database, username, password, host, port]

def mysql_collector(config_path):
    config = ConfigParser.ConfigParser()
    config.read(config_path + "/collector_operator.conf")
    database = config.get("mysql","database")
    username = config.get("mysql","username")
    password = config.get("mysql","password")
    host = config.get("mysql","host")
    port = config.get("mysql","port")
    return [database, username, password, host, port]
