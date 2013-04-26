class vagrant {

  line { 'line-venv-activate':
    ensure => absent,
    file   => '/home/vagrant/.bashrc',
    line   => 'cd /vagrant && source env/bin/activate',
  }

  line { 'cd-vagrant':
    ensure => present,
    file   => '/home/vagrant/.bashrc',
    line   => 'cd /vagrant',
  }

}
