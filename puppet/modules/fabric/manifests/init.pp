class fabric {
  package { 'Fabric':
    provider => 'pip',
    ensure   => 'present',
    require => Package['python-dev'],
  }
}
