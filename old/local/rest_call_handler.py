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

### Main query handler functions

# Main handle for data queries
def handle_ts_data_query(tm, filters):

    schema_dict = tm.schema_dict
    try:
        q_dict = eval(filters) # try to make a dictionary

    except Exception, e:
        return "query: " + filters + "<br><br>had error: " + str(e) + "<br><br> failed to evaluate as dictionary"

    # check for necessary keys
    (ok, fail_str) = check_data_query_keys(q_dict)
    if ok == True:
        ts_filters = q_dict["filters"]["ts"]
        event_types = q_dict["filters"]["eventType"]
        objects = q_dict["filters"]["obj"]
    else:
        return fail_str # returns why filters failed

    ts_where_str = build_ts_where_str(ts_filters)

    # ts
    if ts_where_str == "":
        return "[]"

    resp_arr = []    
    
    for event_type in event_types:
        et_split = event_type.split(':')
        if et_split[0] == "ops_monitoring":
            event_type = et_split[1]
            obj_type = objects["type"]
            for obj_id in objects["id"]:
                resp_i = {}
                        
                ts_arr = get_tsdata(tm, event_type, obj_type, obj_id, ts_where_str)
                obj_schema = get_object_schema(tm, obj_type, obj_id)
            
                if (ts_arr != None):
                    resp_i["$schema"] = "http://www.gpolab.bbn.com/monitoring/schema/20140131/data#"
                    resp_i["id"] = event_type + ":" + obj_id
                    resp_i["subject"] = {"href":obj_schema}
                    resp_i["eventType"] = "ops_monitoring:" + event_type
                    resp_i["description"] = "ops_monitoring:" + event_type + " for " + obj_id + " of type " + obj_type
                    resp_i["units"] = schema_dict["units"]["ops_" + obj_type + "_" + event_type]
                    resp_i["tsdata"] = ts_arr
                    resp_arr.append(resp_i)
        else:
            print "event ", event_type, "not recognized", "missing namespace 'ops_monitoring:' ?"
    return json.dumps(resp_arr)


# Main handle for node queries
def handle_node_info_query(tm, node_id):
    table_str = "ops_node"
    node_schema = tm.schema_dict[table_str]
    con = tm.con

    iface_refs = []

    node_info = get_object_info(tm, table_str, node_id)

    if node_info is not None:
        ifaces = get_related_objects(tm, "ops_node_interface", "node_id", node_id)
        for iface_id in ifaces:
            iface_refs.append(get_refs(tm, "ops_interface", iface_id))

        return json.dumps(get_node_info_dict(node_schema, node_info, iface_refs))

    else:
        return "resource not found"


# Main handle interface queries
def handle_interface_info_query(tm, iface_id):
    table_str = "ops_interface"
    iface_schema = tm.schema_dict[table_str]
    con = tm.con

    iface_info = get_object_info(tm, table_str, iface_id)

    if iface_info is not None:
        return json.dumps(get_interface_info_dict(iface_schema, iface_info))
    else:
        return "interface not found"


# Main handle interface queries
def handle_interfacevlan_info_query(tm, ifacevlan_id):
    table_str = "ops_interfacevlan"
    iface_schema = tm.schema_dict[table_str]
    con = tm.con

    ifacevlan_info = get_object_info(tm, table_str, ifacevlan_id)

    if ifacevlan_info is not None:
        return json.dumps(get_interfacevlan_info_dict(iface_schema, ifacevlan_info))
    else:
        return "interfacevlan not found"


# Main handle for sliver queries
def handle_sliver_info_query(tm, sliver_id):
    table_str = "ops_sliver"
    sliver_schema = tm.schema_dict[table_str]
    con = tm.con

    res_refs = []

    sliver_info = get_object_info(tm, table_str, sliver_id)

    if sliver_info is not None:

        resources = get_related_objects(tm, "ops_sliver_resource", "sliver_id", sliver_id);

        for res_i in resources:
            # not sure if resource is a node or link.  Query for both add proper result.
            node_ref = get_refs(tm, "ops_node", res_i)
            link_ref = get_refs(tm, "ops_link", res_i)
            if len(node_ref) > 0:
                res_refs.append(node_ref)
            elif len(link_ref) > 0:
                res_refs.append(link_ref)
            
        return json.dumps(get_sliver_info_dict(sliver_schema, sliver_info, res_refs))

    else:
        return "sliver not found"


# Main handle aggregate for info queries
def handle_aggregate_info_query(tm, agg_id):
    table_str = "ops_aggregate"
    agg_schema = tm.schema_dict[table_str]
    con = tm.con

    res_refs = []    
    slv_refs = []

    agg_info = get_object_info(tm, table_str, agg_id)
    if agg_info is not None:

        resources = get_related_objects(tm, "ops_aggregate_resource", "aggregate_id", agg_id)

        for res_i in resources: 
            # not sure if resource is a node or link.  Query for both add proper result.
            node_ref = get_refs(tm, "ops_node", res_i)
            link_ref = get_refs(tm, "ops_link", res_i)
            if len(node_ref) > 0:
                res_refs.append(node_ref)
            elif len(link_ref) > 0:
                res_refs.append(link_ref)

        slivers = get_related_objects(tm, "ops_aggregate_sliver", "aggregate_id", agg_id)
        for slv_i in slivers:
            slv_refs.append(get_refs(tm, "ops_sliver", slv_i))

        return json.dumps(get_aggregate_info_dict(agg_schema, agg_info, res_refs, slv_refs))

    else:
        return "aggregate not found"


def handle_externalcheck_info_query(tm, extck_id):
    table_str = "ops_externalcheck"
    extck_schema = tm.schema_dict[table_str]
    con = tm.con

    exp_refs = []    

    extck_info = get_object_info(tm, table_str, extck_id)
    if extck_info is not None:

        monitored_aggregates = get_monitored_aggregates(tm, extck_id)

        experiments = get_related_objects(tm, "ops_externalcheck_experiment", "externalcheck_id", extck_id)

        for exp_i in experiments: 
            exp_ref = get_self_ref(tm, "ops_experiment", exp_i)
            if exp_ref:
                exp_refs.append(exp_ref)

        return json.dumps(get_externalcheck_info_dict(extck_schema, extck_info, exp_refs, monitored_aggregates))

    else:
        return "external check store not found"


# Main handle aggregate for info queries
def handle_authority_info_query(tm, auth_id):
    table_str = "ops_authority"
    auth_schema = tm.schema_dict[table_str]
    con = tm.con

    user_refs = []    
    slice_refs = []

    auth_info = get_object_info(tm, table_str, auth_id)
    if auth_info is not None:

        users = get_related_objects(tm, "ops_authority_user", "authority_id", auth_id)
        for user_i in users:
            user_refs.append(get_refs(tm, "ops_user", user_i))

        slices = get_related_objects(tm, "ops_authority_slice", "authority_id", auth_id)
        for slice_i in slices:
            slice_refs.append(get_refs(tm, "ops_slice", slice_i))

        return json.dumps(get_authority_info_dict(auth_schema, auth_info, user_refs, slice_refs))

    else:
        return "authority not found"


# Main handle slice info queries
def handle_slice_info_query(tm, slice_id):
    table_str = "ops_slice"
    slice_schema = tm.schema_dict[table_str]
    con = tm.con

    user_refs = []    

    slice_info = get_object_info(tm, table_str, slice_id)
    if slice_info is not None:

        users = get_related_objects(tm, "ops_slice_user", "slice_id", slice_id)

        for user_i in users:
            user_refs.append(get_slice_user_refs(tm, "ops_slice_user", user_i))

        return json.dumps(get_slice_info_dict(slice_schema, slice_info, user_refs))

    else:
        return "slice not found"


# Main handle user info queries
def handle_user_info_query(tm, user_id):
    table_str = "ops_user"
    user_schema = tm.schema_dict[table_str]
    con = tm.con

    user_info = get_object_info(tm, table_str, user_id)
    if user_info is not None:
        return json.dumps(get_user_info_dict(user_schema, user_info))
    else:
        return "user not found"


# Main handle for link info queries
def handle_link_info_query(tm, link_id):
    table_str = "ops_link"
    link_schema = tm.schema_dict[table_str]
    con = tm.con

    endpt_refs = []    

    link_info = get_object_info(tm, table_str, link_id)
    if link_info is not None:

        endpts = get_related_objects(tm, "ops_link_interfacevlan", "link_id", link_id)
        for endpt_i in endpts:
            endpt_refs.append(get_refs(tm, "ops_interfacevlan", endpt_i))

        return json.dumps(get_link_info_dict(link_schema, link_info, endpt_refs))

    else:
        return "link not found"


# Main handle for experiment queries
def handle_experiment_info_query(tm, exp_id):
    table_str = "ops_experiment"
    exp_schema = tm.schema_dict[table_str]
    con = tm.con

    iface_refs = []

    exp_info = get_object_info(tm, table_str, exp_id)

    if exp_info is not None:
        return json.dumps(get_experiment_info_dict(exp_schema, exp_info))
    else:
        return "experiment not found"



# Main handle opsconfig info queries
def handle_opsconfig_info_query(tm, opsconfig_id):

    # simply spit out the config file until its contents converges
    return json.dumps(json.load(open(tm.config_path + "opsconfig.json")))

    '''
    table_str = "ops_opsconfig"
    opsconfig_schema = tm.schema_dict[table_str]
    con = tm.con

    agg_refs = []
    auth_refs = []

    opsconfig_info = get_object_info(tm, table_str, opsconfig_id)
    if opsconfig_info is not None:
        
        aggs = get_related_objects(tm, "ops_opsconfig_aggregate", "opsconfig_id", opsconfig_id)

        for agg_i in aggs:
            agg_refs.append(get_opsconfig_aggregate_refs(tm, "ops_opsconfig_aggregate", agg_i))

        auths = get_related_objects(tm, "ops_opsconfig_authority", "opsconfig_id", opsconfig_id)
        for auth_i in auths:
            auth_refs.append(get_refs(tm, "ops_opsconfig_authority", auth_i))

        events_list = get_events_list(tm)

        info_list = get_info_list(tm)
            
        return json.dumps(get_opsconfig_info_dict(opsconfig_schema, opsconfig_info, agg_refs, auth_refs, events_list, info_list))
    else:
        return "opsconfig not found"
    '''

### Argument checker for tsdata queries

# Checks the filters for data queies. It needs a filters dictionary
# with ts, eventType, and obj keys
def check_data_query_keys(q_dict):

    if "filters" not in q_dict:
        return (False, "query: " + str(q_dict) + "<br><br>has dictionary error.  It is missing filters key")
        
    missing_keys = []
    if "ts" not in q_dict["filters"]:
        missing_keys.append("ts")
    if "eventType" not in q_dict["filters"]:
        missing_keys.append("eventType")
    if "obj" not in q_dict["filters"]:
        missing_keys.append("obj")

    if len(missing_keys) > 0:
        return (False, "query: " + str(q_dict) + "<br><br>has dictionary error.  It is missing keys: " + str(missing_keys))

    return (True, None)


### Form response dictionary functions

# Forms interface info dictionary (to be made to JSON)
def get_interface_info_dict(schema, info_row):

    json_dict = {}
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "address_address":
            addr = info_row[col_i]
        elif schema[col_i][0] == "address_type":
            addr_type = info_row[col_i]
        elif schema[col_i][0].startswith("properties$"):
            # parse off properties$
            json_dict["ops_monitoring:" + schema[col_i][0].split("$")[1]] = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["address"] = {"address":addr,"type":addr_type}

    return json_dict


# Forms experiment info dictionary (to be made to JSON)
def get_experiment_info_dict(schema, info_row):

    json_dict = {}
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "source_aggregate_urn":
            src_agg_urn = info_row[col_i]
        elif schema[col_i][0] == "source_aggregate_href":
            src_agg_href = info_row[col_i]
        elif schema[col_i][0] == "destination_aggregate_urn":
            dest_agg_urn = info_row[col_i]
        elif schema[col_i][0] == "destination_aggregate_href":
            dest_agg_href = info_row[col_i]
        else: # top level keys are equal to what is in DB
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["source_aggregate"] = {"urn":src_agg_urn,"href":src_agg_href}
    json_dict["destination_aggregate"] = {"urn":dest_agg_urn,"href":dest_agg_href}

    return json_dict


# Forms interfacevlan info dictionary (to be made to JSON)
def get_interfacevlan_info_dict(schema, info_row):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "interface_urn":
            iface_urn = info_row[col_i]
        elif schema[col_i][0] == "interface_href":
            iface_href = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["port"] = {"urn":iface_urn,"href":iface_href}

    return json_dict


# Forms user info dictionary (to be made to JSON)
def get_user_info_dict(schema, info_row):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "authority_urn":
            auth_urn = info_row[col_i]
        elif schema[col_i][0] == "authority_href":
            auth_href = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["authority"] = {"urn":auth_urn,"href":auth_href}

    return json_dict


# Forms node info dictionary (to be made to JSON)
def get_node_info_dict(schema, info_row, port_refs):

    json_dict = {}

    # Not all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0].startswith("properties$"):
            # parse off properties$ 
            json_dict["ops_monitoring:" + schema[col_i][0].split("$")[1]] = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]        

    if port_refs:
        json_dict["ports"] = []
        for port_ref in port_refs:
            if len(port_ref) > 0:
                json_dict["ports"].append({"href":port_ref[0],"urn":port_ref[1]})
            
    return json_dict


# Forms opsconfig info dictionary (to be made to JSON)
def get_opsconfig_info_dict(schema, info_row, agg_refs, auth_refs, events_list, info_list):

    json_dict = {}

    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]

    if agg_refs:
        json_dict["aggregates"] = []
        for agg_ref in agg_refs:
            if len(agg_ref) > 0:
                json_dict["aggregates"].append({"href":agg_ref[0],"urn":agg_ref[1],"amtype":agg_ref[2]})

    if auth_refs:
        json_dict["authorities"] = []
        for auth_ref in auth_refs:
            if len(auth_ref) > 0:
                json_dict["authorities"].append({"href":auth_ref[0],"urn":auth_ref[1]})
            
    if events_list:
        json_dict["events"] = {}
        json_dict["events"]["node"] = []
        json_dict["events"]["interface"] = []
        json_dict["events"]["interfacevlan"] = []
        for ev_i in events_list:
            if ev_i[0] == "node":
                json_dict["events"]["node"].append({"name":ev_i[1], "id":ev_i[2], "ts":ev_i[3], "v":ev_i[4], "units":ev_i[5]})
            elif ev_i[0] == "interface":
                json_dict["events"]["interface"].append({"name":ev_i[1], "id":ev_i[2], "ts":ev_i[3], "v":ev_i[4], "units":ev_i[5]})
            elif ev_i[0] == "interfacevlan":
                json_dict["events"]["interfacevlan"].append({"name":ev_i[1], "id":ev_i[2], "ts":ev_i[3], "v":ev_i[4], "units":ev_i[5]})

    if info_list:
        json_dict["info"] = []
        for if_i in info_list:
            table_dict = {}
            table_dict["name"] = if_i[0]
            table_dict["db_schema"] = eval(if_i[1])
            json_dict["info"].append(table_dict)

    return json_dict


# Forms sliver info dictionary (to be made to JSON)
def get_sliver_info_dict(schema, info_row, res_refs):

    json_dict = {}

    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "aggregate_urn":
            agg_urn = info_row[col_i]
        elif schema[col_i][0] == "aggregate_href":
            agg_href = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]
            
    json_dict["aggregate"] = {"urn":agg_urn,"href":agg_href}

    if res_refs:
        json_dict["resources"] = []
        for res_ref in res_refs:
            if len(res_ref) > 0:
                json_dict["resources"].append({"href":res_ref[0],"urn":res_ref[1]})
            
    return json_dict


# Forms aggregate info dictionary (to be made to JSON)
def get_aggregate_info_dict(schema, info_row, res_refs, slv_refs):

    json_dict = {}
    
    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]

    if res_refs:
        json_dict["resources"] = []
        for res_ref in res_refs:
            if len(res_ref) > 0:
                json_dict["resources"].append({"href":res_ref[0],"urn":res_ref[1]})

    if slv_refs:
        json_dict["slivers"] = []
        for slv_ref in slv_refs:
            if len(slv_ref) > 0:
                json_dict["slivers"].append({"href":slv_ref[0],"urn":slv_ref[1]})  
    return json_dict

# Forms external check store info dictionary (to be made to JSON)
def get_externalcheck_info_dict(schema, info_row, exp_refs, mon_agg_refs):

    json_dict = {}
    
    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]

    if exp_refs:
        json_dict["experiments"] = []
        for exp_ref in exp_refs:
            if len(exp_ref) > 0:
                json_dict["experiments"].append({"href":exp_ref[0]})

    if mon_agg_refs:
        json_dict["monitored_aggregates"] = []
        for mon_agg_ref in mon_agg_refs:
            if len(exp_ref) > 0:
                json_dict["monitored_aggregates"].append({"id":mon_agg_ref[0],"href":mon_agg_ref[1]})

    return json_dict


# Forms link info dictionary (to be made to JSON)
def get_link_info_dict(schema, info_row, endpt_refs):

    json_dict = {}
    
    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]

    if endpt_refs:
        json_dict["endpoints"] = []
        for endpt_ref in endpt_refs:
            if len(endpt_ref) > 0:
                json_dict["endpoints"].append({"href":endpt_ref[0],"urn":endpt_ref[1]})

    return json_dict


# Forms slice info dictionary (to be made to JSON)
def get_slice_info_dict(schema, info_row, user_refs):

    json_dict = {}
                
    # NOT all of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        if schema[col_i][0] == "authority_href":
            auth_href = info_row[col_i]
        elif schema[col_i][0] == "authority_urn":
            auth_urn = info_row[col_i]
        else:
            json_dict[schema[col_i][0]] = info_row[col_i]

    json_dict["authority"] = {"href":auth_href,"urn":auth_urn}

    if user_refs:
        json_dict["members"] = []
        for member_ref in user_refs:
            if len(member_ref) > 0:
                json_dict["members"].append({"href":member_ref[0],"urn":member_ref[1],"role":member_ref[2]})
            
    return json_dict


# Forms authority info dictionary (to be made to JSON)
def get_authority_info_dict(schema, info_row, user_refs, slice_refs):

    json_dict = {}
    
    # All of info_row goes into top level dictionary
    for col_i in range(len(schema)):
        json_dict[schema[col_i][0]] = info_row[col_i]

    if user_refs:
        json_dict["users"] = []
        for user_ref in user_refs:
            if len(user_ref) > 0:
                json_dict["users"].append({"href":user_ref[0],"urn":user_ref[1]})

    if slice_refs:
        json_dict["slices"] = []
        for slice_ref in slice_refs:
            if len(slice_ref) > 0:
                json_dict["slices"].append({"href":slice_ref[0],"urn":slice_ref[1]})
            
    return json_dict


### SQL query functions

# Gets object info where an object can be anything (node, aggregate,
# interface, sliver
def get_object_info(tm, table_str, obj_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    res = None;

    try:
        cur.execute("select * from " + table_str + " where id = '" + obj_id + "' order by ts desc limit 1")
        res = cur.fetchone()
        tm.con.commit()
    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res

# Gets event types for an object
def get_events_list(tm):
    cur = tm.con.cursor()
    res = [];
    tm.db_lock.acquire()
    try:
        # explicit selecting preserves order of results set
        cur.execute("select object_type, name, id, ts, v, units from ops_opsconfig_event") 
        res = cur.fetchall()
       
    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res


# Gets info for an object
def get_info_list(tm):
    cur = tm.con.cursor()
    res = [];
    tm.db_lock.acquire()
    try:
        # explicit selecting preserves order of results set
        cur.execute("select tablename, schemaarray from ops_opsconfig_info") 
        res = cur.fetchall()
    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res


# Gets related objects
def get_related_objects(tm, table_str, colname_str, id_str):
    cur = tm.con.cursor()
    res = [];
    tm.db_lock.acquire()
    try:
        cur.execute("select distinct id from " + table_str + " where " + colname_str + " = '" + id_str + "'") 
        q_res = cur.fetchall()
        tm.con.commit()
        for res_i in range(len(q_res)):
            res.append(q_res[res_i][0]) # gets first of single tuple

    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res


# Get references of objects TODO refactor similar functions
def get_refs(tm, table_str, object_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    refs = [];
    
    try:

        # two queries avoids regex split with ,
        if tm.database_program == "postgres":
            cur.execute("select \"selfRef\" from " + table_str + " where id = '" + object_id + "' limit 1")
        elif tm.database_program == "mysql":
            cur.execute("select selfRef from " + table_str + " where id = '" + object_id + "' limit 1")
        q_res = cur.fetchone()
        tm.con.commit()
        self_ref = None
        if q_res is not None:
            self_ref = q_res[0] # gets first of single tuple

        cur.execute("select urn from " + table_str + " where id = '" + object_id + "' limit 1")
        q_res = cur.fetchone()
        tm.con.commit()
        if q_res is not None and self_ref is not None:
            urn = q_res[0] # gets first of single tuple
            refs = [self_ref, urn] 

    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()
    
    return refs


# Get self reference only TODO refactor similar functions
def get_self_ref(tm, table_str, object_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    self_ref = None
    
    try:

        # two queries avoids regex split with ,
        if tm.database_program == "postgres":
            cur.execute("select \"selfRef\" from " + table_str + " where id = '" + object_id + "' limit 1")
        elif tm.database_program == "mysql":
            cur.execute("select selfRef from " + table_str + " where id = '" + object_id + "' limit 1")
        q_res = cur.fetchone()
        tm.con.commit()
        self_ref = None
        if q_res is not None:
            self_ref = q_res # gets first of single tuple

    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()
    
    return self_ref


# Get self reference only TODO refactor similar functions
def get_monitored_aggregates(tm, extck_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    res = None
        
    try:

        if tm.database_program == "postgres":
            cur.execute("select id, \"selfRef\" from ops_externalcheck_monitoredaggregate where externalcheck_id = '" + extck_id + "'")
        elif tm.database_program == "mysql":
            cur.execute("select id, selfRef from ops_externalcheck_monitoredaggregate where externalcheck_id = '" + extck_id + "'")
 
        q_res = cur.fetchall()
        tm.con.commit()

        if q_res is not None:
            res = []
            for q_res_idx in range(len(q_res)):
                res.append([q_res[q_res_idx][0], q_res[q_res_idx][1]])

    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()
    
    return res


# special get of refs for slice users which includes role TODO refactor similar functions
def get_slice_user_refs(tm, table_str, slice_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    refs = [];

    try:
        # three queries avoids regex split with ,
        if tm.database_program == "postgres":
            cur.execute("select distinct \"selfRef\" from " + table_str + " where id = '" + slice_id + "'")
        elif tm.database_program == "mysql":
            cur.execute("select distinct selfRef from " + table_str + " where id = '" + slice_id + "'")

        q_res = cur.fetchone()
        tm.con.commit()
        href = q_res[0] # gets first of single tuple

        cur.execute("select distinct urn from " + table_str + " where id = '" + slice_id + "'")
        q_res = cur.fetchone()
        tm.con.commit()
        urn = q_res[0] # gets first of single tuple

        cur.execute("select distinct role from " + table_str + " where id = '" + slice_id + "'")
        q_res = cur.fetchone()
        tm.con.commit()
        role = q_res[0] # gets first of single tuple

        refs = [href, urn, role] 

    except Exception, e:
        print e
        tm.con.commit()
    
    cur.close()
    tm.db_lock.release()

    return refs


# special get of refs for opsconfig aggregates which includes amtype  
# TODO refactor similar functions
def get_opsconfig_aggregate_refs(tm, table_str, opsconfig_id):

    tm.db_lock.acquire()
    cur = tm.con.cursor()
    refs = [];

    try:
        
        # three queries avoids regex split with ,
        if tm.database_program == "postgres":
            cur.execute("select distinct \"selfRef\" from " + table_str + " where id = '" + opsconfig_id + "'")
        elif tm.database_program == "mysql":
            cur.execute("select distinct selfRef from " + table_str + " where id = '" + opsconfig_id + "'")

        q_res = cur.fetchone()
        tm.con.commit()
        href = q_res[0] # gets first of single tuple

        cur.execute("select distinct urn from " + table_str + " where id = '" + opsconfig_id + "'")
        q_res = cur.fetchone()
        tm.con.commit()
        urn = q_res[0] # gets first of single tuple

        cur.execute("select distinct amtype from " + table_str + " where id = '" + opsconfig_id + "'")
        q_res = cur.fetchone()
        tm.con.commit()
        role = q_res[0] # gets first of single tuple

        refs = [href, urn, role] 

    except Exception, e:
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return refs


# builds timestamp filter as a where clause for SQL statement
def build_ts_where_str(ts_dict):
    ts_where_str = ""
    ts_filters = []

    if 'gte' not in ts_dict and 'gt' not in ts_dict:
        print "must past a ts filter for (lt or lte) and (gt or gte)"
        print "missing gt or gte filter"
        return ts_where_str

    if 'lte' not in ts_dict and 'lt' not in ts_dict:
        print "must past a ts filter for (lt or lte) and (gt or gte)"
        print "missing lt or lte filter"
        return ts_where_str

    try:
        for ts_k in ts_dict:
            ts_v = ts_dict[ts_k]
            if ts_k == 'gte':
                ts_filters.append("ts >= " + str(ts_v))
            elif ts_k == 'gt':
                ts_filters.append("ts > " + str(ts_v))
            elif ts_k == 'lte':
                ts_filters.append("ts <= " + str(ts_v))
            elif ts_k == 'lt':
                ts_filters.append("ts < " + str(ts_v))
    except Exception, e:
        print str(e), "ts filters has invalid key or value:"
    
    try:
        ts_where_str = ts_filters[0] + " and " +  ts_filters[1]
    except Exception, e:
        print str(e), "must past a ts filter for (lt or lte) and (gt or gte)"

    return ts_where_str

def get_tsdata(tm, event_type, obj_type, obj_id, ts_where_str):
     
    tm.db_lock.acquire()
    cur = tm.con.cursor()
    res = None
    try:
    
        # assumes an id for obj_id in table event_type with ops_ prepended
        cur.execute("select ts,v from ops_" + obj_type + "_" + event_type + " where id = '" + obj_id + "' and " + ts_where_str)
        q_res = cur.fetchall()
        tm.con.commit()

        if len(q_res) > 0:
            res = []
            for q_res_i in xrange(len(q_res)): # parsing result "<ts>,<v>"
                res.append({"ts":q_res[q_res_i][0],"v":q_res[q_res_i][1]})
        
    except Exception, e:
        print "query failed: select ts,v from ops_" + obj_type + "_" + event_type + " where id = '" + obj_id + "' and " + ts_where_str
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res


def get_object_schema(tm, obj_type, obj_id):
     
    tm.db_lock.acquire()
    cur = tm.con.cursor()
    res = None
    try:
    
        # assumes an id for obj_id in table event_type with ops_ prepended
        if tm.database_program == "postgres":
            cur.execute("select \"$schema\" from ops_" + obj_type + " where id = '" + obj_id + "'")
        elif tm.database_program == "mysql":
            cur.execute("select $schema from ops_" + obj_type + " where id = '" + obj_id + "'")

        q_res = cur.fetchall()
        tm.con.commit()

        if len(q_res) > 0:
            res = q_res[0][0]
        
    except Exception, e:
        print "query failed: select $schema from ops_" + obj_type + " where id = '" + obj_id + "'"
        print e
        tm.con.commit()

    cur.close()
    tm.db_lock.release()

    return res

def main():
    print "no unit test"

if __name__ == "__main__":
    main()
