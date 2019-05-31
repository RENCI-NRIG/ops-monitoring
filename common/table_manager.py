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

import sys
import threading
import opsconfig_loader

class DBManager(object):
    """
    Base Database Manager class.
    Defines the "base" methods to be implemented by subclasses
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        """
        Base constructor, capturing the arguments as attributes of the class.
        """
        self.dbname = dbnm
        self.username = usernm
        self.passwd = pw
        self.hostname = hostnm
        self.port = prt
        self.poolsize = poolsize
        self.logger = logger

    def get_column_name(self, column):
        """
        Method to return a column name with the proper quotation for a given DB engine.
        :param column: the name of the column
        :return: the column name with the proper quotation for the DB engine represented by the class.
        """
        raise NotImplementedError();

    def get_connection(self):
        """
        Method to get a connection. This class functions as a connection pool. Once the caller is done 
        using its connection, it should return it to the pool, using the return_connection() method.
        :return: a connection to the DB specified by the arguments passed in the constructor
        """
        raise NotImplementedError();

    def return_connection(self, conn):
        """
        Method to return a connection after it's been used.
        :param conn: the connection that was once obtained via get_connection()
        """
        raise NotImplementedError();

    def get_import_module_name(self):
        """
        Method to get the DB module name used by this class.
        This is useful for example when trying to catch exception that are defined by the DB API, but truly
        provided by the DB driver module. 
        """
        raise NotImplementedError();
    
    def get_table_schema_string(self, table_schema):
        """
        Method to get a schema string, i.e. "( col1Name, col2Name, .... , colnName)"
        from a "usual" table schema list of tuples containing (column name, column type, required)
        :param table_schema: A table schema in the usual format
        :return: the corresponding schema string
        """
        schema_str = "("
        for col in range(len(table_schema)):
            if col > 0:
                schema_str += ", "
            schema_str += self.get_column_name(table_schema[col][0])
        schema_str += ")"
        return schema_str
    
    def get_table_values_string(self, row):
        """
        Method to get a string of value, i.e. "'value1', 'value2', ... , 'valuen'"
        from a list of values.
        :param row: the list of values
        :return: the string of all the values.
        """
        values_str = ""
        for col in range(len(row)):
            if col > 0:
                values_str += ", "
            if row[col] is None:
                values_str += "NULL"
            else:
                values_str += "'" + str(row[col]) + "'"
        return values_str

    def get_table_field_values_string(self, table_schema, row):
        """
        Method to get a string of field/values, i.e. "field1='value1', field2='value2', ... , fieldn='valuen'"
        from the table schema and a list of values.
        :param table_schema: A table schema in the usual format
        :param row: the list of values
        return the string of field/values
        """
        field_value_str = ""
        for col in range(len(table_schema)):
            if col > 0:
                field_value_str += ", "
            field_value_str += self.get_column_name(table_schema[col][0])
            if row[col] is None:
                field_value_str += "=NULL"
            else:
                field_value_str += "='" + str(row[col]) + "'"
        return field_value_str

    def get_upsert_statements(self, table_name, table_schema, row, id_column):
        """
        Method to provide the insert or update (aka merge or upsert) SQL statements for a row of data into a table.
        :param table_name: the name of the table to modify
        :param table_schema:the schema of the table
        :param row: the row to insert or update (i.e. a list of values)
        :param id_column: the position of the column in the table that can act as a key.
        :return: The proper upsert SQL statements.
        """
        raise NotImplementedError();


class MySQLDBManager (DBManager):
    """
    Database Manager class for MySQL. 
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        super(MySQLDBManager, self).__init__(dbnm, usernm, pw, hostnm, prt, poolsize, logger)

    def get_column_name(self, column):
        return column

    def get_connection(self):
        # TODO implement poolsize restrictions
        import MySQLdb
        try:
            con = MySQLdb.connect(db=self.dbname, user=self.username, passwd=self.passwd, host=self.hostname, port=int(self.port))
        except Exception, e:
            self.logger.critical("%s \nCannot open a mysql connection to database %s. \n Exiting.\n" % (e, self.dbname))
            sys.exit(1)
        return con

    def return_connection(self, conn):
        conn.close()

    def get_import_module_name(self):
        import MySQLdb
        return MySQLdb

    def get_upsert_statements(self, table_name, table_schema, row, id_columns):
        statements = []
        # for MySql, the statement executed has the following syntax:
        # INSERT INTO table (field1, field2, ... fieldn) VALUES ( value1, value2, ... , valuen )
        # ON DUPLICATE KEY UPDATE field1=value1, field2=value2, ... , fieldn=valuen
        # NOTE: this works only on tables which have a primary key defined.
        #      (Possibly NOT NULL UNIQUE column as well)
        statement = "INSERT INTO " + table_name + " " + self.get_table_schema_string(table_schema) + \
                    " VALUE (" + self.get_table_values_string(row) + ") ON DUPLICATE KEY UPDATE " + \
                    self.get_table_field_values_string(table_schema, row)
        statements.append(statement)
        return statements


class PostgreSQLDBManager (DBManager):
    """
    Database Manager class for postgreSQL. 
    """
    def __init__(self, dbnm, usernm, pw, hostnm, prt, poolsize, logger):
        super(PostgreSQLDBManager, self).__init__(dbnm, usernm, pw, hostnm, prt, poolsize, logger)
        import psycopg2.pool
        self.pool = psycopg2.pool.ThreadedConnectionPool(1, poolsize, database=dbnm, user=usernm, password=pw, host=hostnm, port=prt)

    def get_column_name(self, column):
        return "\"" + column + "\""

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def get_import_module_name(self):
        import psycopg2
        return psycopg2

    def get_upsert_statements(self, table_name, table_schema, row, id_columns):
        statements = []
        # for postgres there are 2 statements executed in the same transaction.
        # The syntax used is as follows:
        # UPDATE table SET field1=value1, field2=value2, ... , fieldn=valuen WHERE id_field=id_value;
        # INSERT INTO table (field1, field2, ... fieldn)
        #    SELECT value1, value2, ... , valuen WHERE NOT EXISTS(SELECT 1 FROM table WHERE id_field=id_value);
        # the UPDATE will succeed if a row with id_field=id_value exists, otherwise has no effect.
        # the INSERT will succeed only if a row with id_field=id_value does not already exists.

        # Convert id_columns to a list if it is not one already.
        try:
            _ = iter(id_columns) # attempt to access it as an iterable
        except TypeError:
            id_columns = [id_columns]

        # Build the WHERE clause of the SQL statement using the column indices in id_columns.
        where_clause = " WHERE "
        and_str = ""
        for col in id_columns:
            where_clause += and_str + '"' + table_schema[col][0] + "\"='" + str(row[col]) + "'"
            and_str = " AND "

        statement = "UPDATE \"" + table_name + "\" SET " + self.get_table_field_values_string(table_schema, row) + \
                    where_clause
        statements.append(statement)
        statement = "INSERT INTO \"" + table_name + "\" " + self.get_table_schema_string(table_schema) + \
                    " SELECT " + self.get_table_values_string(row) + " WHERE NOT EXISTS ( SELECT 1 from " + \
                    table_name + where_clause + ")"
        statements.append(statement)
        return statements


class TableManager:

    def __init__(self, db_type, config_path):

        self.config_path = config_path
        import logger
        self.logger = logger.get_logger(config_path)

        # load a 2-function package for reading database connection config
        sys.path.append(config_path)
        import database_conf_loader

        self.conf_loader = database_conf_loader  # clarify naming conventions

        [db_prog] = self.conf_loader.main(config_path, db_type)

        self.database_type = db_type  # local or collector
        self.database_program = db_prog  # postgres or mysql

        self.dbmanager = self.init_dbmanager()

        self.db_lock = threading.Lock()


    # fetches DB schemas from config local datastore
    def poll_config_store(self):

        ocl = opsconfig_loader.OpsconfigLoader(self.config_path)

        # parses the DB schemas
        info_schema = ocl.get_info_schema()
        self.data_schema = ocl.get_data_schema()
        info_constraints = ocl.get_info_constraints()
        info_dependencies = ocl.get_info_dependencies()
        self.event_types = ocl.get_event_types()

        # hold the DB schemas in the schema dictionary
        self.schema_dict = self.__create_schema_dict__(self.data_schema, info_schema)
        # hold the DB constraints in the constraints dictionary
        self.contraints_dict = self.__create_constraints_dict__(self.data_schema, info_constraints)

        all_dependencies_dict = self.__create_dependencies_dict__(self.data_schema, info_dependencies)

        self.tables = self.__create_ordered_table_list__(all_dependencies_dict)

        self.logger.debug("Schema loaded with keys:\n" + str(self.schema_dict.keys()))



    def init_dbmanager(self):
        """
        Method to initialize the Database Manager based on the settings from the configuration file.
        :return: The correct instance of a concrete class inheriting from DBManager
        :note: This method will cause the program to exit if the specified DB engine is not recognized.
        """
        [database_, username_, password_, host_, port_, poolsize_] = self.conf_loader.get_db_parameters(self.config_path, \
                                                                                             self.database_program, \
                                                                                             self.database_type)

        if self.database_program == "postgres":
            return PostgreSQLDBManager(database_, username_, password_, host_, port_, poolsize_, self.logger)
        elif self.database_program == "mysql":
            return MySQLDBManager(database_, username_, password_, host_, port_, poolsize_, self.logger)
        else:
            self.logger.critical("%s is not a valid database program\n" % self.database_program)
            sys.exit(1)

    def __create_schema_dict__(self, data_schema, info_schema):
        """
        Creates a unified dictionary of the DB schema, containing both the 
        tables supporting the "information" and the tables supporting the 
        "data" (i.e. measurements)
        :param data_schema: the schema dictionary for the data tables
        :param info_schema: the schema dictionary for the information tables
        :return: a unified dictionary of the DB schema for all the tables.
        :note: The returned dictionary has the tables names as keys, and a list
        for value. That list contains the name of the DB column, the DB type of
        the column, and whether a value for that column is required.
        """
        schema_dict = {}
        schema_dict["units"] = {}
        if (len(dict(data_schema.items() + info_schema.items())) != len(data_schema) + len(info_schema)):
            self.logger.warning("Error: table namespace collision\n")
            return None

        for ds_k in data_schema.keys():
            # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            if self.database_type == "local":
                schema_dict[ds_k] = data_schema[ds_k][:-1]
            elif self.database_type == "collector":
                l = data_schema[ds_k][:-1]
                # The ops_experiment_XXX tables are coming from external check stores.
                # and so is ops_aggregate_is_available
                # The rest of the data are coming from aggregate stores.
                if ds_k.startswith("ops_experiment") or ds_k == "ops_aggregate_is_available":
                    l.insert(0, ["externalcheck_id", "varchar"])
                else:
                    l.insert(0, ["aggregate_id", "varchar"])
                schema_dict[ds_k] = l
            # All fields of the data table are required...
            for k in range(len(schema_dict[ds_k])):
                schema_dict[ds_k][k].append(True)
            schema_dict["units"][ds_k] = data_schema[ds_k][-1][1]

        for is_k in info_schema.keys():
            schema_dict[is_k] = info_schema[is_k]

        return schema_dict

    def __create_constraints_dict__(self, data_schema, info_constraints):
        """
        Creates a unified dictionary of the DB constraints, containing both the 
        tables supporting the "information" and the tables supporting the "data"
        (i.e. measurements)
        :param data_schema: the schema dictionary for the data tables
        :param info_schema: the constraint dictionary for the information tables
        :return: a unified dictionary of the DB constraints for all the tables.
        :note: The returned dictionary has the tables names as keys, and a list
        for value. That list contains a constraint format string as the first 
        object and a list as a second object, which contains column names and 
        or table names. The constraint string is meant to be "merged" via the 
        python % operator with the list.
        """
        constraints_dict = {}

        for ds_k in data_schema.keys():
            # last of list is units
            # 2nd of tuple is a string of what unit type is (i.e., percent)
            if self.database_type == "local":
                constraints_dict[ds_k] = [["PRIMARY KEY (%s, %s)", ["id", "ts"]]]
            elif self.database_type == "collector":
                # The ops_experiment_XXX tables are coming from external check stores.
                # and so is ops_aggregate_is_available
                # The rest of the data are coming from aggregate stores.
                if ds_k.startswith("ops_experiment") or ds_k == "ops_aggregate_is_available":
                    constraints_dict[ds_k] = [["PRIMARY KEY (%s, %s, %s)", ["externalcheck_id", "id", "ts"]],
                                             ["FOREIGN KEY (%s) REFERENCES %s(%s)", ["externalcheck_id", "ops_externalcheck", "id"]]
                                            ]
                else:
                    constraints_dict[ds_k] = [["PRIMARY KEY (%s, %s, %s)", ["aggregate_id", "id", "ts"]],
                                             ["FOREIGN KEY (%s) REFERENCES %s(%s)", ["aggregate_id", "ops_aggregate", "id"]]
                                            ]
            if ds_k.startswith("ops_node"):
                constraints_dict[ds_k].append(["FOREIGN KEY (%s) REFERENCES %s(%s)", ["id", "ops_node", "id"]])
            elif ds_k.startswith("ops_interfacevlan"):
                constraints_dict[ds_k].append(["FOREIGN KEY (%s) REFERENCES %s(%s)", ["id", "ops_interfacevlan", "id"]])
            elif ds_k.startswith("ops_interface"):
                constraints_dict[ds_k].append(["FOREIGN KEY (%s) REFERENCES %s(%s)", ["id", "ops_interface", "id"]])
            elif ds_k.startswith("ops_aggregate"):
                constraints_dict[ds_k].append(["FOREIGN KEY (%s) REFERENCES %s(%s)", ["id", "ops_aggregate", "id"]])
            elif ds_k.startswith("ops_experiment"):
                constraints_dict[ds_k].append(["FOREIGN KEY (%s) REFERENCES %s(%s)", ["id", "ops_experiment", "id"]])

        for ic_k in info_constraints.keys():
            constraints_dict[ic_k] = info_constraints[ic_k]

        return constraints_dict

    def __create_dependencies_dict__(self, data_schema, info_dependencies):
        """
        Creates a unified dictionary of the DB table dependencies, containing 
        both the tables supporting the "information" and the tables supporting 
        the "data" (i.e. measurements)
        :param data_schema: the schema dictionary for the data tables
        :param info_schema: the dependencies dictionary for the information tables
        :return: a unified dictionary of the DB dependencies for all the tables.
        :note: The returned dictionary has the tables names as keys, and a list
        for value. That list contains the names of the tables the table 
        (identified via the key) is dependent upon.
        """
        dependencies_dict = {}

        for ds_k in data_schema.keys():
            if self.database_type == "collector":
                # The ops_experiment_XXX tables are coming from external check stores.
                # and so is ops_aggregate_is_available
                # The rest of the data are coming from aggregate stores.
                if ds_k.startswith("ops_experiment") or ds_k == "ops_aggregate_is_available":
                    dependencies_dict[ds_k] = ["ops_externalcheck"]
                else:
                    dependencies_dict[ds_k] = ["ops_aggregate"]
            else:
                dependencies_dict[ds_k] = []

            if ds_k.startswith("ops_node"):
                dependencies_dict[ds_k].append("ops_node")
            elif ds_k.startswith("ops_interfacevlan"):
                dependencies_dict[ds_k].append("ops_interfacevlan")
            elif ds_k.startswith("ops_interface"):
                dependencies_dict[ds_k].append("ops_interface")
            elif ds_k.startswith("ops_aggregate"):
                dependencies_dict[ds_k].append("ops_aggregate")
            elif ds_k.startswith("ops_experiment"):
                dependencies_dict[ds_k].append("ops_experiment")

        for id_k in info_dependencies.keys():
            dependencies_dict[id_k] = info_dependencies[id_k]

        return dependencies_dict

    def add_table_schema(self, table_name, table_schema):
        """
        Adds a table schema to the dictionary of known table schemas. Dictionary key is the table name
        @param table_name: the name of the table, which will become the key to the table schemas dictionary.
        @param table_schema: the schema of the table in its usual form, i.e. a list of tuples containing 
        the name of a table column, the type of that column, and whether a value for that column is required.
        @return: True if the addition was successful, False if the schema for such a table name was already 
        existing
        """
        if self.schema_dict.has_key(table_name):
            return False
        # TODO validate that table_schema fits the expected format
        self.schema_dict[table_name] = table_schema
        return True

    def add_table_constraints(self, table_name, table_constraints):
        """
        Adds constraints for a table to the dictionary of known table constraints. Dictionary key is the table name
        @param table_name: the name of the table, which will become the key to the table schemas dictionary.
        @param table_constraints: the constraints of the table in its usual form, i.e. a list of tuples, each containing 
        the constraint string in the form of a string format and a list of columns or tables names to 
        be inserted in the constraint string with the python operator %.
        @return: True if the addition was successful, False if the constraints for such a table name was already 
        existing
        """
        if self.contraints_dict.has_key(table_name):
            return False
        # TODO validate that table_constraints fits the expected format
        self.contraints_dict[table_name] = table_constraints
        return True

    def __create_ordered_table_list__(self, dependencies_dict):
        """
        Creates a list of DB table names ordered by their dependencies, in the 
        order needed for table creation.
        :param dependencies_dict: a dependency dictionary such as the one created by 
        create_dependencies_dict().
        :return: a list of DB table names ordered by their dependencies, in the 
        order needed for table creation.
        """
        table_list = dependencies_dict.keys()
        # no absolutely necessary but so that we always end up with the same order.
        table_list.sort()

        keepGoing = True
        iterNb = 0
        while keepGoing:
            keepGoing = False
            iterNb += 1
            for idx in range(len(table_list)):
                deps = dependencies_dict[table_list[idx]]
                if len(deps) > 0:
                # we want to move that table after all its dependencies
                    maxIdx = 0
                    for j in range(idx + 1, len(table_list)):
                        if table_list[j] in deps:
                            if j > maxIdx:
                                maxIdx = j
                    if maxIdx > 0:
                        # switch tables
                        tmp = table_list[idx]
                        table_list[idx] = table_list[maxIdx]
                        table_list[maxIdx] = tmp
                        keepGoing = True
            if iterNb > 1000:
                self.logger.critical("Sorting table dependencies is taking more than 1000 iterations... circular dependencies?")
                self.logger.critical("exiting")
                sys.exit(-1)

        return table_list

    def purge_old_tsdata(self, table_name, delete_older_than_ts):
        """
        Method to delete data older than a given timestamp from a specific table.
        :param table_name: the table to delete from
        :param delete_older_than_ts: the timestamp with which to compare the data in the table.
        :return: True if there was no problem deleting the data (even if no data was deleting 
            according to the criteria), False otherwise.
        """
        ok = True
        self.db_lock.acquire()

        del_str = "delete from " + table_name + " where ts < " + str(delete_older_than_ts)
        self.logger.debug(del_str)

        if not self.execute_sql(del_str):
            self.logger.warning("Trouble deleting data to %s.\n" % table_name)
            self.logger.warning("delete_older_than_ts %s\n" % delete_older_than_ts)
            ok = False

        self.db_lock.release()
        return ok

    # inserts done here to handle cursor write locking
    def insert_stmt(self, table_name, val_str):
        """
        Method to insert values in a table.
        :param table_name: the name of the table to insert values in.
        :param val_str: a string listing (exhaustively) the values to be inserted.
            It is expected to be in the form "( val1, val2, val3, ..., valn)" if the 
            table has n columns.
        :return: True if there no issue inserting the data, false otherwise.
        """
        ret = True
        self.db_lock.acquire()
        ins_str = "insert into " + table_name + " values " + val_str
        self.logger.debug(ins_str)

        if not self.execute_sql(ins_str):
            self.logger.warning("Trouble inserting data to %s.\n" % table_name)
            self.logger.warning("val str %s\n" % val_str)
            ret = False
        self.db_lock.release()

        return ret

    # deletes done here to handle cursor write locking
    def delete_stmt(self, table_name, obj_id):
        """
        Method to delete a specific row from a table
        :param table_name: the name of the table to delete from.
        :param obj_id: the id of the object to delete. (It is assumed that the table has a column named id)
        :return: True if the delete statement executed correctly, False otherwise.
        """

        ok = True
        self.db_lock.acquire()
        del_str = "delete from " + table_name + " where id = '" + obj_id + "'"
        self.logger.debug(del_str)

        if not self.execute_sql(del_str):
            self.logger.warning("Trouble deleting %s as id from %s.\n" % (obj_id, table_name))
            ok = False

        self.db_lock.release()
        return ok


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
            return self.__table_exists_psql__(table_str)
        elif self.database_program == "mysql":
            return self.__table_exists_mysql__(table_str)
        return False

    def __table_exists_mysql__(self, table_str):
        exists = False
        self.db_lock.acquire()
        q_res = self.query("show tables like '" + table_str + "'")
        if q_res is not None and len(q_res) > 0:
            exists = True
        self.db_lock.release()

        return exists

    def __table_exists_psql__(self, table_str):
        exists = False
        self.db_lock.acquire()
        q_res = self.query("select exists(select relname from pg_class where relname='" + table_str + "')")
        if q_res is not None and len(q_res) > 0 and len(q_res[0]) > 0:
            exists = q_res[0][0]
        self.db_lock.release()

        return exists


    def get_column_name(self, column):
        """
        Method to return the column name properly quoted, or not, for the DB engine currently used.
        :param column: the name of the column
        :return: the column string to be inserted into a SQL statement 
        """
        return self.dbmanager.get_column_name(column)


    def get_col_names(self, table_str):
        if (self.database_program == "postgres"):
            self.get_col_names_psql(table_str)
        if (self.database_program == "mysql"):
            self.get_col_names_mysql(table_str)


    def get_col_names_psql(self, table_str):
        # using cursor description not cursor.fetchall(), so have to kinda duplicate the query() code here...
        self.db_lock.acquire()
        err = True
        con = self.dbmanager.get_connection()
        cur = con.cursor()
        col_names = []
        try:
            cur.execute("select * from " + table_str + " LIMIT 0")
            err = False
        except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
            cur.close()
            self.dbmanager.return_connection(con)
            con = self.dbmanager.get_connection()
            cur = con.cursor()
            try:
                cur.execute("select * from " + table_str + " LIMIT 0")
                err = False
            except Exception, e:
                self.logger.warning("%s\n" % e)
        except Exception, e:
            self.logger.warning("%s\n" % e)

        if not err:
            col_names = [desc[0] for desc in cur.description]
        cur.close()

        self.dbmanager.return_connection(con)
        self.db_lock.release()
        return col_names


    def get_col_names_mysql(self, table_str):

        self.db_lock.acquire()
        con = self.dbmanager.get_connection()
        col_names = []

        # todo fill in

        self.dbmanager.return_connection(con)
        self.db_lock.release()
        return col_names


    def __establish_tables__(self, table_str_arr):
        """
        Creates a list of tables
        :param table_str_arr: the list of tables to create.
        :return: True if the tables were successfully created, False otherwise
        """
        ok = True
        for table_str in table_str_arr:
            # Ensures table_str is in ops_ namespace
            if table_str.startswith("ops_"):
                if not self.establish_table(table_str):
                    ok = False
        return ok

    def establish_all_tables(self):
        """
        Creates all the DB tables
        :return: True if the tables were successfully created, False otherwise
        """
        return self.__establish_tables__(self.tables)

    def purge_outdated_resources_from_info_tables(self):
        pass  # TODO fill in


    def establish_table(self, table_str):
        """
        Creates a specific table
        :param table_str: the name of the table to create.
        :return: True if the table was successfully created, False otherwise
        """
        ok = True
        if self.table_exists(table_str):
            self.logger.debug("table " + table_str + " already exists.")
            self.logger.debug("Skipping creation of " + table_str)

        else:
            schema_str = self.translate_table_schema_to_schema_str(self.schema_dict[table_str], self.contraints_dict[table_str], table_str)
            self.db_lock.acquire()
            self.logger.info("create table " + table_str + schema_str)
            if not self.execute_sql("create table " + table_str + schema_str):
                self.logger.warning("Exception while creating table %s %s" % (table_str, schema_str))
                ok = False
            self.db_lock.release()
        return ok

    def drop_all_tables(self):
        """
        Drops all the DB tables
        :return: True if the tables were dropped, false if there was any kind of issue.
        """
        reverse_table_order = self.tables[:]
        reverse_table_order.reverse()
        return self.__drop_tables__(reverse_table_order)

    def drop_data_tables(self):
        """
        Drops the DB data tables (not the info ones)
        :return: True if the tables were dropped, false if there was any kind of issue.
        """
        # no need to consider the tables order because the data tables only depend on info tables.
        return self.__drop_tables__(self.data_schema.keys())

    def __drop_tables__(self, table_str_arr):
        """
        Drops a list of tables
        :param table_str_arr: the list of tables to be dropped.
        :return: True if the tables were dropped, false if there was any kind of issue.
        """
        ok = True
        for table_str in table_str_arr:
            if not self.__drop_table__(table_str):
                ok = False

        return ok


    def __drop_table__(self, table_str):
        """
        Drops a specific table
        :param table_str: the name of the table to be dropped
        :return: True if the tables was dropped, false if there was any kind of issue.
        """
        self.db_lock.acquire()
        self.logger.debug("drop table if exists " + table_str)

        if self.execute_sql("drop table if exists " + table_str):
            self.logger.info("Dropped table: " + table_str)
            ok = True
        else:
            self.logger.warning("Error while dropping table %s" % (table_str))
            ok = False

        self.db_lock.release()
        return ok

    def get_all_ids_from_table(self, table_str):

        res = [];
        self.db_lock.acquire()
        q_res = self.query("select distinct id from " + table_str)
        self.logger.debug(q_res)

        if q_res is not None:
            for res_i in range(len(q_res)):
                res.append(q_res[res_i][0])  # gets first of single tuple

        self.db_lock.release()

        return res



    def translate_table_schema_to_schema_str(self, table_schema_dict, table_constraint_dict, table_str):
        schema_str = "("
        for col_i in range(len(table_schema_dict)):
            schema_str += self.get_column_name(table_schema_dict[col_i][0]) + " " + table_schema_dict[col_i][1]
            # for mysql varchar are not unlimited
            if self.database_program == "mysql":
                if table_schema_dict[col_i][1] == "varchar":
                    schema_str += "(512)"
            if table_schema_dict[col_i][2]:
                schema_str += " NOT NULL"
            schema_str += ","

        for const_i in range(len(table_constraint_dict)):
            col_names = []
            for col_i in range(len(table_constraint_dict[const_i][1])):
                col_names.append(self.get_column_name(table_constraint_dict[const_i][1][col_i]))
            try:
                schema_str += table_constraint_dict[const_i][0] % tuple(col_names)
            except TypeError, e:
                self.logger.warning(str(e))
                self.logger.critical("Could not create table " + table_str +
                                     "\n error building constraint statement with % operator\n" +
                                     table_constraint_dict[const_i][0] + "\n" +
                                     str(col_names))
                self.logger.critical("Exiting")
                sys.exit(-1)

            schema_str += ","
        # remove , and add )
        return schema_str[:-1] + ")"

    def get_column_from_schema(self, schema, column_name):
        """
        Method to find the index of a column in the schema
        :param schema: a table schema
        :param column_name: the name of a column
        return the index of the column in the schema, or None if it was not found
        """
        for col in range(len(schema)):
            if schema[col][0] == column_name:
                return col
        return None

    def query(self, querystr):
        """
        Execute a query and returns the results.
        :param querystr:  the query to be executed
        :return: a tuple containing the tuples of all the records selected, themselves in the form of tuples.
                 None if there was an issue executing the query.
        """
#         if self.database_program == "postgres":
#             import psycopg2 as dbengine
#         elif self.database_program == "mysql":
#             import MySQLdb as dbengine

        con = self.dbmanager.get_connection()
        cur = con.cursor()
        q_res = None
        try:
            self.logger.debug("About to execute: %s" % (querystr))
            cur.execute(querystr)
            self.logger.debug("Modified row count: %d " % (cur.rowcount))
            if cur.rowcount > 0:
                q_res = cur.fetchall()
        except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
            self.logger.info("Trying to reconnect")
            con.rollback()
            cur.close()
            self.dbmanager.return_connection(con)
            con = self.dbmanager.get_connection()
            cur = con.cursor()
            try:
                cur.execute(querystr)
                if cur.rowcount > 0:
                    q_res = cur.fetchall()
            except Exception, e:
                # TODO replace with logging statement
                self.logger.warning("Error while executing the following query: " + querystr)
                self.logger.warning(str(e))
        except Exception, e:
            # TODO replace with logging statement
            self.logger.warning("Error while executing the following query: " + querystr)
            self.logger.warning(e)

        finally:
            con.commit()

        cur.close()
        self.dbmanager.return_connection(con)

        return q_res

    def execute_sql(self, sqlstatement):
        """
        Execute one or more SQL statements and returns True if the statement(s) executed correctly.
        :param querystr:  the statement or statements to be executed. No results are expected.
        :return: True if all the statement executed correctly, False if there was an issue. 
        As soon as an issue is encountered, no more statements are executed and a DB rollback is issued.
        """
#         if self.database_program == "postgres":
#             import psycopg2 as dbengine
#         elif self.database_program == "mysql":
#             import MySQLdb as dbengine

        con = self.dbmanager.get_connection()
        cur = con.cursor()
        res = False

        if isinstance(sqlstatement, basestring):
            statements = (sqlstatement,)
        elif isinstance(sqlstatement, list):
            statements = sqlstatement
        elif isinstance(sqlstatement, tuple):
            statements = sqlstatement
        else:
            self.logger.critical("Unexpected type for sqlstatement argument %s.\n Exiting.\n" % (sqlstatement,))
            sys.exit(1)


        tryNumber = 1
        fatalErr = False
        while True:
            err = False
            for statement in statements:
                err = True
                try:
                    self.logger.debug("About to execute: %s" % (statement))
                    cur.execute(statement)
                    self.logger.debug("Modified row count: %d " % (cur.rowcount))
                    err = False
                except (AttributeError, self.dbmanager.get_import_module_name().OperationalError):
                    self.logger.info("Trying to reconnect")
                    # since we're dealing with mutilple statements, in case of a disconnection, we need to reissue them all.
                    con.rollback()
                    cur.close()
                    self.dbmanager.return_connection(con)
                    con = self.dbmanager.get_connection()
                    cur = con.cursor()
                    tryNumber += 1
                except Exception, e:
                    # TODO replace with logging statement
                    self.logger.warning("Error while executing the following SQL statement: " + statement)
                    self.logger.warning(str(e))
                    con.rollback()
                    # we don't want to retry after this
                    fatalErr = True
                if err:
                    break
            else:  # for loop else
                # so we had no issue.
                con.commit()
                res = True
                break;
            if fatalErr or (tryNumber > 2):
                res = False
                break

        cur.close()
        self.dbmanager.return_connection(con)

        return res

    def upsert(self, table_name, table_schema, row, id_columns):
        """
        Method to insert or update (aka merge or upsert) a row of data into a table.
        :param table_name: the name of the table to modify
        :param table_schema:the schema of the table
        :param row: the row to insert or update (i.e. a list of values)
        :param id_columns: the position of the column in the table that can act as a key 
           or a list of positions of the columns that act as a key.
        :return: True if the insert or update happened successfully, False otherwise.
        :note: With a postgres engine, this method only works for tables which have 
            primary keys defined.
        """
        if (len(table_schema) != len(row)):
            self.logger.warning("Problem with data for table %s: schema has %d fields, row has %d!\n %s\n %s" % \
                                (table_name, len(table_schema), len(row), str(table_schema), str(row)))
            return False
        ok = True
        statements = self.dbmanager.get_upsert_statements(table_name, table_schema, row, id_columns)
        if not self.execute_sql(statements):
            ok = False
        return ok

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


def main():
    print "no unit test"


if __name__ == "__main__":

    main()
