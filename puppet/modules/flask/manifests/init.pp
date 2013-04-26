class flask {

  package { 'flask':
    provider => 'pip',
    ensure   => '0.9',
    require => Package['python-dev'],
  }

  package { 'flask-script':
    provider => 'pip',
    ensure   => '0.5.3',
    require => Package['python-dev'],
  }

}
