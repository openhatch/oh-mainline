# The classes that we 'include' are actually
# each defined in their own file. We must import
# them to have access to them.
import "classes/*"

class openhatch_code {
  # Run bootstrap.py to make sure buildout can run
  exec { "/usr/bin/python2.6 /vagrant/bootstrap.py":
    creates => '/vagrant/bin/buildout',
    user => 'vagrant',
    group => 'vagrant',
    cwd => '/vagrant/',
    require => [Package['python2.6-dev']],
  }

  exec { "/vagrant/bin/buildout":
    creates => '/vagrant/bin/mysite',
    user => 'vagrant',
    group => 'vagrant',
    cwd => '/vagrant/',
    logoutput => true,
    require => [Exec["/usr/bin/python2.6 /vagrant/bootstrap.py"]],
  }

}

node default {
  include apt_get_update
  include openhatch_dependencies
  include openhatch_code
}
