class chaussette {

  package { 'chaussette':
    provider => 'pip',
    ensure   => '0.7',
    require => Package['python-dev'],
  }

}
