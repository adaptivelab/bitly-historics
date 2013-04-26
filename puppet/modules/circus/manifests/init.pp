class circus {

  package { 'circus':
    provider => 'pip',
    ensure   => '0.6.0',
    require => [Package['python-dev'], Package['libzmq-dev']],
  }

  file { "/etc/circus.ini":
    ensure => present,
    content => template("circus/circus.ini"),
    require => Package["circus"],
  }

  file { '/etc/init/circus.conf':
    ensure => present,
    content => template("circus/upstart.circus.conf"),
    require => File["/etc/circus.ini"],
  }

  service { 'circus':
    ensure   => running,
    enable   => true,
    provider => upstart,
    require => [File['/etc/init/circus.conf'], Class['redis']],
  }

  file { "/etc/circus.d":
    ensure => "directory",
    require => Package[circus],
  }

}
