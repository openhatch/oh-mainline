class openhatch_database {
  # Create the oh_milestone_a database
  exec { "/usr/bin/mysql -uroot < /vagrant/mysite/scripts/database_01_create.sql":
    creates => '/var/lib/mysql/oh_milestone_a',
    user => 'root',
    group => 'root',
    cwd => '/root/',
  }

  exec { "/vagrant/manage.py syncdb --noinput":
    user => 'vagrant',
    timeout => 0,
    group => 'vagrant',
    cwd => '/vagrant/',
    logoutput => on_failure,
    require => [Exec["/usr/bin/python2.6 /vagrant/bootstrap.py"],
                Exec['/usr/bin/mysql -uroot < /vagrant/mysite/scripts/database_01_create.sql'],
                Exec['/vagrant/bin/buildout']],
  }

  exec { "/vagrant/manage.py migrate":
    user => 'vagrant',
    timeout => 0,
    group => 'vagrant',
    cwd => '/vagrant/',
    logoutput => on_failure,
    require => [Exec["/usr/bin/python2.6 /vagrant/bootstrap.py"],
                Exec["/vagrant/manage.py syncdb --noinput"]],
  }

}
