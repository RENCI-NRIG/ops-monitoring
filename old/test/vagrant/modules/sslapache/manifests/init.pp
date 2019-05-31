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

class sslapache::server {

  package {
    "apache2": ensure => installed;
    "libapache2-mod-wsgi": ensure => installed;
  }

  file {
    "/etc/apache2/sites-enabled/default-ssl":
      content => template("sslapache/site_enabled_default.erb"),
      notify => Service["apache2"],
      require => Exec["a2ensite"]; 
  }

  file {
    "/etc/ssl/certs/ch.geni.net-ca.pem":
      content => template("sslapache/ch.geni.net-ca.pem"),
      notify => Service["apache2"];
  }

  service {
    "apache2":
      ensure => running,
      enable => true,
      require => Package["libapache2-mod-wsgi"];
  }

  exec {
    "a2enmod":
      command => "/bin/rm /etc/apache2/sites-enabled/*; /usr/sbin/a2enmod ssl",
      require => Package["apache2"];
    }

  exec {
    "a2ensite":
      command => "/usr/sbin/a2ensite default-ssl",
      require => Package["apache2"];
  }
}
