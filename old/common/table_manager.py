#!/usr/bin/python
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

import json
import sys
import threading
from pprint import pprint as pprint
import opsconfig_loader

class TableManager:

    def __init__(self, db_type, config_path, debug=False):

        self.config_path = config_path

        # load a 2-function package for reading database connection config
        sys.path.append(config_path)
        import database_conf_loader
        
        self.conf_loader = database_conf_loader # clarify naming conventions
        self.debug = debug

        if db_type == "local":
            [db_prog] = self.conf_loader.main_local(config_path)
        elif db_type == "collector":
            [db_prog] = self.conf_loader.main_collector(config_path)
        else:
            sys.stderr.write("%s is not a valid database type (local or collector)\n" % db_type)
            sys.exit(1)

        if db_prog == "postgres":
            self.con = self.init_psql_conn(db_type, config_path)
        elif db_prog == "mysql":
            self.con = self.init_mysql_conn(db_type, config_path)
        else:
            sys.stderr.write("%s is not a valid database program\n" % db_prog)
            sys.exit(1)

        self.database_type = db_type # local or collector
        self.database_program = db_prog # postgres or mysql

        self.db_lock = threading.Lock()


    # fetches DB schemas from config local datastore
    def poll_config_store(self):

        self.ocl = opsconfig_loader.OpsconfigLoader(self.config_path) 

        # parses the DB schemas
        self.info_schema = self.ocl.get_info_schema()
        self.data_schema = self.ocl.get_data_schema()
        self.event_types = self.ocl.get_event_types()

        # hold the DB schemas in the schema dictionary
        self.schema_dict = self.create_schema_dict(self.data_schema, self.info_schema)

        if self.debug:
            print "Schema loaded with keys:" 
            print self.schema_dict.keys() 
            print ""


    # This is a special table for bootstrapping the configuration
    # It stores the other schemas. This function drops and creates
    # these tables
    def reset_opsconfig_tables(self):

        table_str = "ops_opsconfig_info"
        schema_arr = [['tablename', 'varchar'],['schemaarray','varchar']]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)

        self.db_lock.acquire()
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            cur.execute("create table if not exists " + table_str + schema_str)
            self.con.commit()
            
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.stderr.write("Exception while reseting opsconfig info table %s %s" % (table_str, schema_str))


        table_str = "ops_opsconfig_event"
        schema_arr = [["object_type", "varchar"], ["name", "varchar"], ["id", "varchar"], ["ts", "varchar"], ["v", "varchar"], ["units", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            cur.execute("create table if not exists " + table_str + schema_str)
            self.con.commit()
            
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.stderr.write("Exception while reseting opsconfig event table %s %s" % (table_str, schema_str))
        

        table_str = "ops_opsconfig"
        schema_arr = [["$schema", "varchar"], ["id", "varchar"], ["selfRef", "varchar"], ["ts", "int8"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            cur.execute("create table if not exists " + table_str + schema_str)
            self.con.commit()
            
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.stderr.write("Exception while reseting opsconfig table %s %s" % (table_str, schema_str))

        table_str = "ops_opsconfig_aggregate"
        schema_arr = [["id", "varchar"], ["opsconfig_id", "varchar"], ["amtype", "varchar"], ["urn", "varchar"], ["selfRef", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            cur.execute("create table if not exists " + table_str + schema_str)
            self.con.commit()
            
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.stderr.write("Exception while reseting opsconfig aggregate table %s %s" % (table_str, schema_str))
            

        table_str = "ops_opsconfig_authority"
        schema_arr = [["id", "varchar"], ["opsconfig_id", "varchar"], ["urn", "varchar"], ["selfRef", "varchar"]]
        schema_str = self.translate_table_schema_to_schema_str(schema_arr, table_str)
        try:
            cur = self.con.cursor()
            cur.execute("drop table if exists " + table_str)
            cur.execute("create table if not exists " + table_str + schema_str)
            self.con.commit()
            
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.stderr.write("Exception while reseting opsconfig aggregate table %s %s" % (table_str, schema_str))


        self.db_lock.release()



    def init_psql_conn(self, db_type, config_path):

        import psycopg2

        if db_type == "local":
            [database_, username_, password_, host_, port_] = \
                self.conf_loader.psql_local(config_path)
        elif db_type == "collector":
            [database_, username_, password_, host_, port_] = \
                self.conf_loader.psql_collector(config_path)
        else:
            sys.stderr.write("No collector or local database selected.  Exiting\n")
            sys.exit(1)

        try:
            con = psycopg2.connect(database = database_, user = username_, password = password_, host = host_, port = port_)
        except Exception, e:
            sys.stderr.write("%s \nCannot open a connection to database %s. \n Exiting.\n" % (e, database_))
            sys.exit(1)

        return con

    def init_mysql_conn(self, db_type, config_path):

	import MySQLdb as mysqldb
       
        if db_type == "local":
            [database_, username_, password_, host_, port_] = \
                self.conf_loader.mysql_local(config_path)
        elif db_type == "collector":
            [database_, username_, password_, host_, port_] = \
                self.conf_loader.mysql_collector(config_path)
        else:
            sys.stderr.write("No collector or local database selected.  Exiting\n\n")
            sys.exit(1)

        try:

            con = mysqldb.connect(db = database_, user = username_, passwd = password_, host = host_, port = int(port_))
        except Exception, e:
            sys.stderr.write("%s \nCannot open a connection to database %s. \n Exiting.\n" % (e, database_))
            sys.exit(1)

        return con

    def create_schema_dict(self, data_schema, info_schema):
        schema_dict = {}
        schema_dict["units"] = {}
        if (len(dict(data_schema.items() + info_schema.items())) != len(data_schema) + len(info_schema)):
            sys.stderr.write("Error: table namespace collision\n")
            return None

        for ds_k in data_schema.keys():
            # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            if self.database_type == "local":
                schema_dict[ds_k] = data_schema[ds_k][:-1] 
            elif self.database_type == "collector":
                l = data_schema[ds_k][:-1]
                l.insert(0,["aggregate_id","varchar"])
                schema_dict[ds_k] = l
            schema_dict["units"][ds_k] = data_schema[ds_k][-1][1] 

        for is_k in info_schema.keys():
            schema_dict[is_k] = info_schema[is_k]

        return schema_dict

    def purge_old_tsdata(self, table_name, delete_older_than_ts):
        self.db_lock.acquire()

        try: 
            cur = self.con.cursor()            
            del_str = "delete from " + table_name + " where ts < " + str(delete_older_than_ts) + ";";
            if self.debug:
                print del_str
            cur.execute(del_str);
            self.con.commit() 
            cur.close()
        except Exception, e:
            sys.stderr.write("Trouble deleting data to %s.\n" % table_name)
            sys.stderr.write("delete_older_than_ts %s\n" % delete_older_than_ts)
            sys.stderr.write("%s\n" % e)

        self.db_lock.release()
   
    # inserts done here to handle cursor write locking
    def insert_stmt(self, table_name, val_str):

        self.db_lock.acquire()

        try:
            cur = self.con.cursor()            
            ins_str = "insert into " + table_name + " values " + val_str + ";";
            if self.debug:
                print ins_str
            cur.execute(ins_str);
            self.con.commit() 
            cur.close()
        except Exception, e:
            sys.stderr.write("Trouble inserting data to %s.\n" % table_name)
            sys.stderr.write("val str %s\n" % val_str)
            sys.stderr.write("%s\n" % e)

        self.db_lock.release()

    # deletes done here to handle cursor write locking
    def delete_stmt(self, table_name, obj_id):

        self.db_lock.acquire()

        try:
            cur = self.con.cursor()            
            del_str = "delete from " + table_name + " where id = '" + obj_id + "';";
            if self.debug:
                print del_str
            cur.execute(del_str);
            self.con.commit() 
            cur.close()
        except Exception, e:
            sys.stderr.write("Trouble deleting %s as id from %s.\n" % (obj_id, table_name))
            sys.stderr.write("%s\n" % e)

        self.db_lock.release()

    def close_con(self):
        try:
            self.con.close()
        except Exception, e:
            sys.stderr.write("%s\nCannot close connection to database.\n" % e)

    '''
    Not allowed in a transaction block, connection implies a database 
    TODO drop database
    def drop_database(self, dbname_str): 
        try:
            cur = self.con.cursor()
            cur.execute("drop database if exists " + dbname_str)
            self.con.commit()
            print "Dropping database", dbname_str
            cur.close()
        except Exception, e:
            print e

    def create_database(self, dbname_str):
        try:
            cur = self.con.cursor()
            cur.execute("create database " + dbname_str)
            self.con.commit()
            print "Creating database", dbname_str
            cur.close()
        except Exception, e:
            print e
    '''

    # break this into postgres and mysql
    def table_exists(self, table_str):
        if self.database_program == "postgres":
            return self.table_exists_psql(table_str)
        elif self.database_program == "mysql":
            return self.table_exists_mysql(table_str)

    def table_exists_mysql(self, table_str):
        exists = False
        self.db_lock.acquire()
        try:
            cur = self.con.cursor()
            cur.execute("show tables like '" + table_str + "'")
            if cur.fetchone():
                exists = True
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
        self.db_lock.release()

        return exists

    def table_exists_psql(self, table_str):
        exists = False
        self.db_lock.acquire()
        try:
            cur = self.con.cursor()

            cur.execute("select exists(select relname from pg_class where relname='" + table_str + "')")
            exists = cur.fetchone()[0]
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)
        self.db_lock.release()

        return exists


    def get_col_names(self, table_str):
        if (self.database_program == "postgres"):
            self.get_col_names_psql(table_str)
        if (self.database_program == "mysql"):
            self.get_col_names_mysql(table_str)


    def get_col_names_psql(self, table_str):

        self.db_lock.acquire()
        col_names = []
        try:
            cur = self.con.cursor()
            cur.execute("select * from " + table_str + " LIMIT 0")
            col_names = [desc[0] for desc in cur.description]
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n" % e)

        self.db_lock.release()
        return col_names


    def get_col_names_mysql(self, table_str):

        self.db_lock.acquire()
        col_names = []
        
        # todo fill in

        self.db_lock.release()
        return col_names


    def establish_tables(self, table_str_arr):
        for table_str in table_str_arr:
            # Ensures table_str is in ops_ namespace
            if table_str.startswith("ops_"):
                self.establish_table(table_str)


    def establish_all_tables(self):
        self.establish_tables(self.schema_dict.keys())

    def purge_outdated_resources_from_info_tables(self):
        pass # TODO fill in


    def establish_table(self, table_str):

        schema_str = self.translate_table_schema_to_schema_str(self.schema_dict[table_str], table_str)
        
        if self.table_exists(table_str):
            if self.debug:
                print "INFO: table " + table_str + " already exists with schema:"
                print "Current schema_str " + schema_str
                print "Skipping creation of " + table_str
            
        else:
            self.db_lock.acquire()
        
            try:
                cur = self.con.cursor()
                print "create table " + table_str + schema_str
                cur.execute("create table " + table_str + schema_str)
                self.con.commit()

                cur.close()
            except Exception, e:
                sys.stderr.write("%s\n" % e)
                sys.stderr.write("Exception while creating table %s %s" % (table, schema_str))
            
            self.db_lock.release()


    def drop_tables(self, table_str_arr):
        for table_str in table_str_arr:
            self.drop_table(table_str)


    def drop_table(self, table_str):

        self.db_lock.acquire()        

        try:
            cur = self.con.cursor() 
            if self.debug:
                print "drop table if exists " + table_str
            cur.execute("drop table if exists " + table_str)
            self.con.commit()
            if self.debug:
                print "Dropping table", table_str
            cur.close()
        except Exception, e:
            sys.stderr.write("%s\n%s" % (e, table_str))

        self.db_lock.release()


    def get_all_ids_from_table(self, table_str):
        cur = self.con.cursor()
        res = [];
        self.db_lock.acquire()
        try:
            cur.execute("select distinct id from " + table_str + ";") 
            q_res = cur.fetchall()
            if self.debug:
                print q_res
            self.con.commit()
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0]) # gets first of single tuple

        except Exception, e:
            sys.stderr.write("%s\n" % e)
            self.con.commit()

        cur.close()
        self.db_lock.release()

        return res



    def translate_table_schema_to_schema_str(self, table_schema_dict, table_str):
    
        schema_str = "("
        if self.database_program == "postgres":
            for col_i in range(len(table_schema_dict)):
                schema_str += "\"" +table_schema_dict[col_i][0] + "\" " + table_schema_dict[col_i][1] + "," 
        else:
            for col_i in range(len(table_schema_dict)):
                if table_schema_dict[col_i][1] == "varchar":
                    schema_str += table_schema_dict[col_i][0] + " " + table_schema_dict[col_i][1] + "(512)," 
                else:
                    schema_str += table_schema_dict[col_i][0] + " " + table_schema_dict[col_i][1] + "," 

        # remove , and add )
        return schema_str[:-1] + ")"


# used only if arguments passed to program
# gets each argument as a table name
def arg_parser(argv, dict_keys):
    if (len(argv) == 1):
        sys.exit(1)

    table_str_arr = []

    for arg in argv[1:]:
        
        try:
            table_str = str(arg)
        except ValueError:
            sys.stderr.write("%s Not a string.\n" % arg)
            sys.exit(1)
        if table_str not in dict_keys:
            print "Argument " + arg + " converted to string " + table_str + " was not found in schema dictionary keys:"
            print dict_keys.keys()
            sys.exit(1)
        else:
            table_str_arr.append(table_str)

    return table_str_arr

def test_mysql(con):
    
    cur = con.cursor()
    cur.execute("select version()")
    ver = cur.fetchone()
    print ver,"is the db version"


    cur.execute("drop table if exists ops_swap_free")
    con.commit()
    cur.execute("create table ops_swap_free(id varchar(128),ts int8,v float4)")
    con.commit()


def main():
    print "no unit test"
  

if __name__ == "__main__":

    main()
