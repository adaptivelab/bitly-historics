class libssl {
  package { ['libssl-dev']:
    ensure => present,
  }
}
