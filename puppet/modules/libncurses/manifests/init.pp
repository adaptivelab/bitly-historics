class libncurses {
  package { ['libncurses5-dev']:
    ensure => present,
  }
}
