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

#!/usr/bin/bash

old_date=20140131
new_date=20140501
schema_server="ekron.gpolab.bbn.com"
base_path="/srv/www/monitoring/schema"

# Master ssh session
#screen -d -m ssh -M -S ~/.ssh/%h%p%r%u $schema_server &

# Create directory if not exists
ssh $schema_server "if [ ! -d $base_path/$new_date ]; then echo schema dir dne ; mkdir $base_path/$new_date  ;  fi;"


for schema_file in $(ls *.schema)
do
    echo "Editing $schema_file from $old_date to $new_date"
    sed "s/$old_date/$new_date/" "$schema_file" > "$schema_file.tmp"
    mv "$schema_file.tmp" "$schema_file"
    schema_name=`echo $schema_file| cut -d'.' -f 1`
    cp $schema_file $schema_name
    echo "Copying file $schema_name to $schema_server"
    scp $schema_name $schema_server:$base_path/$new_date
done

# update permissions
ssh $schema_server "chgrp -R gpo $base_path/$new_date ; chmod -R g+w $base_path/$new_date ;"
