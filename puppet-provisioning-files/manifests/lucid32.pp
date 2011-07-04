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

  # We do not use the vcsrepo type because
  # it does not support setting the user
  # who will own the resulting git clone.
  exec { "/usr/bin/git clone git://gitorious.org/openhatch/oh-mainline.git":
    user => 'vagrant',
    group => '',
    require => [User['deploy'], Package['git-core'], File['/home/deploy']],
    cwd => '/home/deploy/',
    logoutput => "on_failure",
    unless => '/usr/bin/test -d /home/deploy/oh-mainline',
    subscribe => [File['/home/deploy']],
  }

}

node default {
  include apt_get_update
  include openhatch_code
}
