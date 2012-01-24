class openhatch_code {
  # Run bootstrap.py to make sure buildout can run
  exec { "/usr/bin/python2.6 /vagrant/bootstrap.py":
    creates => '/vagrant/bin/buildout',
    user => 'vagrant',
    group => 'vagrant',
    cwd => '/vagrant/',
  }

  exec { "/vagrant/bin/buildout":
    creates => '/vagrant/manage.py',
    user => 'vagrant',
    timeout => 0,
    group => 'vagrant',
    cwd => '/vagrant/',
    logoutput => true,
    require => [Exec["/usr/bin/python2.6 /vagrant/bootstrap.py"]],
  }

}
