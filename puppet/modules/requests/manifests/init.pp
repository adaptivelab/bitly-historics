class requests {

  package { 'requests':
    provider => 'pip',
    ensure   => '1.1',
    require => Package['python-dev'],
  }

}
