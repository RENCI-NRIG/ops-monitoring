#!/usr/bin/env python
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
import sys
import time
import json
import ConfigParser
import subprocess
import os
from string import digits
from pprint import pprint as pprint

common_path = "../common/"
config_path = "/home/amcanary/"
# input file with short-names and Urls aggregates 
inputFile=open('/home/amcanary/src/gcf/agg_nick_cache.base')

# Dic to store short name and corresponding url 
# Format: shortname [fqdn]=[aggShortName,amtype,urn]
# where state is 0 for up and 1 for down
shortName={}

# Dic to store slice info for campus and core
# monitoring slices.
# 
slices={}
sys.path.append(common_path)
import table_manager

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr 
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path
        config = ConfigParser.ConfigParser()
        config.read(config_path+ "ips.conf")
        self.ip_campus = dict(config.items("campus"))
        self.ip_core = dict(config.items("core"))

    def populateInfoTables(self, shortName, slices, srcPing, ipList):
        fileLoc1="/home/amcanary/ops_externalcheck_experiment_Registry"
        fileLoc2="/home/amcanary/ops_experiment_Registry"
        dataStoreBaseUrl="https://extckdatastore.gpolab.bbn.com"
        dataStoreSite="gpo"
        for srcSite in srcPing: 
            for dstSite in ipList:
                passFlag = 0 
                if srcSite != dstSite: # A site must not ping itself
                    dstSiteFlag=dstSite.strip().split('-') 
                     
                    if len(dstSiteFlag) ==2:
                        exp_id= srcSite + "_to_" +  dstSite + "_campus"
                        sliceUrn=slices["sitemon"][0]
                        sliceUuid=slices["sitemon"][1]
                    else:                        
                        exp_id= srcSite + "_to_" +  dstSite   
                        srcSiteFlag=srcSite.strip().split('-')
                        if srcSiteFlag[2] != dstSiteFlag[2]:
                           passFlag=1
                           pass # Can't ping between hosts in different networks
                        else:
                            if dstSiteFlag[2]=="3715_core":# Get slice info for core VLAN 3715
                               sliceUrn=slices["gpoI15"][0]
                               sliceUuid=slices["gpoI15"][1]
                            else:
                                sliceUrn=slices["gpoI16"][0]# Get slice info for core VLAN 3716
                                sliceUuid=slices["gpoI16"][1] 
                     
                    if passFlag ==1:
                       pass 
                    else:
                        # Routine for "ops_externalcheck_experiment" Table  
                        extck_exp = [exp_id, dataStoreSite, dataStoreBaseUrl + "/info/experiment/" + exp_id]
                        dataInsert(self.tbl_mgr, fileLoc1, exp_id, extck_exp, "ops_externalcheck_experiment")
                   
                        urnHrefs=getSiteInfo(srcSite, dstSite, shortName)# [srcUrn, srcHref, dstUrn, dstHref]
                        ts = str(int(time.time()*1000000))    
                        exp=["http://www.gpolab.bbn.com/monitoring/schema/20140828/experiment#", exp_id, 
                            dataStoreBaseUrl + "/info/experiment/"+  exp_id, ts, sliceUrn, sliceUuid,    
                            urnHrefs[0], urnHrefs[1], urnHrefs[2], urnHrefs[3]]
                        dataInsert(self.tbl_mgr, fileLoc2, exp_id, exp, "ops_experiment")   

    def insert_externalcheck_monitoredaggregate(self,fqdn, aggRow):
        extck_id = aggRow[0] # agg_id
        dataStoreSite="gpo"
        ts = str(int(time.time()*1000000))
        dataStore_url_base="https://datastore."+ fqdn
        mon_agg = [extck_id, dataStoreSite, dataStore_url_base + "/info/aggregate/" + extck_id]
        fileLoc="/home/amcanary/ops_externalcheck_monitoredaggregate_Registry"
        dataInsert(self.tbl_mgr, fileLoc, mon_agg[2], mon_agg, "ops_externalcheck_monitoredaggregate")
  
    def insert_externalcheck(self):
        dataStoreSite="gpo"
        dataStore_url_base="https://extckdatastore.gpolab.bbn.com"
        ts = str(int(time.time()*1000000))
        extck = ["http://www.gpolab.bbn.com/monitoring/schema/20140828/externalcheck#", dataStoreSite, dataStore_url_base + "/info/externalcheck/" + dataStoreSite, ts, dataStore_url_base + "/data/"]
        fileLoc="/home/amcanary/ops_externalcheck_Registry"
        dataInsert(self.tbl_mgr, fileLoc, extck[0], extck, "ops_externalcheck")
        
def dataInsert (tbl_mgr, fileLoc, exp_id, data, table):
    regFile=open(fileLoc,"r+")
    if os.stat(fileLoc).st_size > 0: # If file is not empty
        exp_aggFlag=0 # Check if an entry is registered
        for line in regFile:
            line=line.strip().split(" ") # Remove white spaces
            if line[0] == exp_id:
                exp_aggFlag=1
                break # Item registered already
        if exp_aggFlag==0: # Register new item                         
            regFile.write(exp_id)
            regFile.write('\n')
            db_insert(tbl_mgr, table, data)
    else: # Empty file
        regFile.write(exp_id)
        regFile.write('\n')
        db_insert(tbl_mgr, table , data) 

def getSiteInfo(srcSite, dstSite, shortName):
    srcUrn = srcHref = dstUrn = dstHref = ''
    for key in shortName:
        if shortName[key][0] == srcSite:
            srcUrn=shortName[key][2]
            srcHref = "https://datastore."+ key + "/info/aggregate/" + srcSite
        elif shortName[key][0] == dstSite:
           dstUrn=shortName[key][2]
           dstHref = "https://datastore."+ key + "/info/aggregate/" + dstSite
  
    return [srcUrn, srcHref, dstUrn, dstHref]    

def db_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:        
        val_str += val + "','" # join won't do this

    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )

    tbl_mgr.insert_stmt(table_str, val_str)

def getShortName():
    i=1
    for line in inputFile: # Read in line
        if line[0]!='#' and line[0]!='[' and line[0]!='\n': # Don't read comments/junk
            cols = line.strip().split('=')
            aggShortName=cols[0]
            if aggShortName == "plcv3" or aggShortName == "plc3": # Only grab fqdn for aggShortName=plc
               continue
            aggShortName=formatShortName(aggShortName) # Grab shortname and convert to current format
            cols1=cols[1].strip().split(',')
            urn = cols1[0] # Grab urn
            cols2=cols1[1].strip().split('/')
            cols3=cols2[2].strip().split(':')
            fqdn=cols3[0] # Grab fqdn

            if aggShortName == "plc" or aggShortName=="ion":
                amtype="myplc"
            else:
                amtype=cols2[3] # Grab amtype

            if is_empty(shortName) == "True": # If dic is empty
                shortName[fqdn]= [aggShortName,amtype,urn]
            else:
                if shortName.has_key(fqdn): # If we have the shortName move to next line
                   continue
                else:
                    shortName[fqdn]=[aggShortName,amtype,urn]
    return shortName

def formatShortName(shortName):
    if len(shortName)>5:# Aggregate with 2 chars: ignore
        shortName = shortName.translate(None, digits) # Remove all #s froms shortName
    oldFormat = shortName.strip().split('-')
    suffix=['ig','eg', 'of', 'pg']
    if len(oldFormat)==1: # For cases like "ion"
       return shortName
    for id in suffix:
        if oldFormat[0]==id and len(oldFormat) == 2: # For cases like gpo-ig
            newFormat= oldFormat[1]+"-"+id
            break
        elif oldFormat[1]==id and len(oldFormat) == 2: # For cases like ig-gpo
            newFormat=shortName
            break
        elif oldFormat[0]==id and len(oldFormat) == 3: # For cases like ig-of-gpo
            newFormat= oldFormat[2] + '-' + id + '-' + oldFormat[1]
            break
        elif oldFormat[1]==id and len(oldFormat) == 3: # For cases like gpo-ig-of
            newFormat= shortName
            break

    if newFormat == "i-of": # For i2-of case
        return "i2-of"
    else:
        return newFormat
def is_empty(any_structure): # Determine if "any_structure" is empty
    if any_structure:
       # print('Structure is not empty.')
        return False
    else:
       # print('Structure is empty.')
        return True
def getAMState(output):
    cols=output.strip().split(':')
    if cols[2] == " Timed out after 60 seconds": # Occurs if subprocess hangs 
        result =0
    elif cols[3]==" 0": # check for "returned: 0" output
        result="1" # Good result
    else:
        result="0" # Bad result   
    return result

def getSlices():
    slices={'sitemon':['urn:publicid:IDN+ch.geni.net:gpoamcanary+slice+sitemon','f42d1c94-506a-4247-a8af-40f5760d7750'], 'gpoI15': ['urn:publicid:IDN+ch.geni.net:gpo-infra+slice+gpoI15','35e195e0-430a-488e-a0a7-8314326346f4'], 'gpoI16':['urn:publicid:IDN+ch.geni.net:gpo-infra+slice+gpoI16','e85a5108-9ea3-4e01-87b6-b3bc027aeb8f']}
    return slices

def main():

    db_name = "local"
    config_path = "../config/"
    debug = False
    tbl_mgr = table_manager.TableManager(db_name, config_path, debug)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr,"")
    # read list of urls (or short-names)
    shortName=getShortName()
    slices=getSlices()
    srcPingCampus=['gpo-ig','utah-ig']
    srcPingCore=['gpo-ig-3715_core','gpo-ig-3716_core']   
    # Populate "ops_externalcheck_experiment" and "ops_experiment" tables 
    ip.populateInfoTables(shortName, slices, srcPingCampus, ip.ip_campus)
    ip.populateInfoTables(shortName, slices, srcPingCore, ip.ip_core)
    # Populate "ops_externalCheck" table
    ip.insert_externalcheck()    
    for fqdn in shortName:
        shortName[fqdn]
        # Populate "ops_externalcheck_monitoredaggregate" table 
        ip.insert_externalcheck_monitoredaggregate(fqdn, shortName[fqdn])
    tbl_mgr.close_con();

if __name__ == "__main__":
    main()
    
