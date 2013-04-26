class zeromq {
  package { ['libzmq-dev']:
    ensure => present,
  }
}
