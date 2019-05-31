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

node default {

  ## Defaults

  # Always run apt-get update before trying to install packages
  Package {
    require => Exec["apt_client_update"],
  }

  $database_type = "mysql"

  # exactly one of these should be true
  $populate_data = false
  $populate_config_store = true
  $init_collector = false

  $database_name = "local"
  $config_store_url = "http://starkville.bbn.com/info/opsconfig/geni-prod"

  # since these passwords are being committed to a repo, never use
  # them anywhere outside a vagrant instance running on localhost
  $postgres_superuser_password = "d86LJY278htqSkrP2oNx"
  $postgres_localstore_password = "yz9nQxB9TbF74jmMQbXs"
  $mysql_localstore_password = "JU63p3MBGjnUmzbv3apQ"

  include "local"
}

class local {

  include "apt::client"
  include "apache::server"
  include "flask::server"
  include "local::server"
  include "${database_type}::server"

  # if you want to populate the fake data, you need psutil
  if $populate_data {
    include "psutil::base"
  }
}
