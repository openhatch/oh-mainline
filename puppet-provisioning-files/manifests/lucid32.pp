# The classes that we 'include' are actually
# each defined in their own file. We must import
# them to have access to them.
import "classes/*"

class openhatch_code {
  package { ['python2.6-dev', 'python-libxml2', 'memcached', 'python-mysqldb',
             'python-setuptools', 'libxml2-dev', 'libxslt-dev', 'mysql-server',
             'mysql-client', 'python-xapian', 'python-imaging', 'subversion',
             'git-core']:
    ensure => installed,
  }

}

node default {
  include apt_get_update
  include openhatch_code
}
