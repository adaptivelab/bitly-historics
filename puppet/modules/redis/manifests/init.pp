class redis {

  $version = '2.4.15'
  $download = "http://redis.googlecode.com/files/redis-${version}.tar.gz"
  $dest = "/opt/redis-${version}"
  $bin = '/usr/local/bin'

  exec { 'download-redis':
    cwd     => '/tmp',
    command => "/usr/bin/wget -q ${download} -O redis-${version}.tar.gz",
    timeout => 300,
    unless => "/usr/bin/test -f /tmp/redis-${version}.tar.gz"
  }

  exec { 'extract-redis':
    cwd     => '/tmp',
    command => "/bin/tar xzf /tmp/redis-${version}.tar.gz",
    creates => "/tmp/redis-${version}",
    require => Exec[download-redis]
  }

  exec { "make-redis":
    command => "/usr/bin/make && /usr/bin/make install PREFIX=${dest}",
    cwd     => "/tmp/redis-${version}",
    creates => "${dest}/src/redis-server",
    require => Exec[extract-redis],
  }

  exec { "chown-redis-binaries":
    command => "/bin/chown ${id} redis-*",
    cwd     => "${dest}/bin",
    require => Exec[make-redis],
  }

  exec { "symlink-redis-binaries":
    command => "ln -sf ${dest}/bin/redis-server redis-server && ln -sf ${dest}/bin/redis-cli redis-cli && ln -sf ${dest}/bin/redis-benchmark redis-benchmark && ln -sf ${dest}/bin/redis-check-dump redis-check-dump",
    cwd     => "/usr/local/bin",
    path    => "/bin/",
    require => Exec[chown-redis-binaries],
  }

  file { '/etc/redis':
    ensure => directory
  }

  file { ['/mnt', '/mnt/redis', '/mnt/log', '/mnt/log/redis']:
    ensure => directory
  }

  exec { 'chown-mnt':
    command => "/bin/chown -R ${id} /mnt",
    require => File[['/mnt', '/mnt/redis', '/mnt/log', '/mnt/log/redis']],
  }

  file { '/etc/redis/redis.conf':
    ensure  => present,
    content => template("redis/redis.conf"),
    owner => root,
    group => root,
  }

  file { "/etc/circus.d/redis.ini":
    ensure => present,
    content => template("redis/circus.ini"),
    require => File["/etc/circus.d"],
  }

}
