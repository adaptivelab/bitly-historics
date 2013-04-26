class hotworker {
  package { 'hotworker':
    provider => 'pip',
    ensure   => '0.2.0',
    require => Package['python-dev'],
  }
}
