class openresty {

  $version = '1.2.4.14'
  $download = "http://agentzh.org/misc/nginx/ngx_openresty-${version}.tar.gz"
  $dest = "/opt/ngx_openresty-${version}"
  $bin = '/usr/local/bin'

  exec { 'download-openresty':
    cwd     => '/tmp',
    command => "/usr/bin/wget -q ${download} -O ngx_openresty-${version}.tar.gz",
    timeout => 300,
    unless => "/usr/bin/test -f /tmp/ngx_openresty-${version}.tar.gz"
  }

  exec { 'extract-openresty':
    cwd     => '/tmp',
    command => "/bin/tar xzf /tmp/ngx_openresty-${version}.tar.gz",
    creates => "/tmp/ngx_openresty-${version}",
    require => Exec[download-openresty]
  }

  exec { "make-openresty":
    command => "/tmp/ngx_openresty-${version}/configure --with-luajit && /usr/bin/make && /usr/bin/make install PREFIX=${dest}",
    cwd     => "/tmp/ngx_openresty-${version}",
    creates => "/usr/local/openresty",
    #path    => "/tmp/ngx_openresty-${version}",
    require => [
      Exec[extract-openresty],
      Class['libncurses'],
      Package['libpcre3-dev'],
      Package['libreadline-dev'],
      Package['libssl-dev'],
      Package['perl'],
    ],
  }

  file { ['/var/www', '/var/www/simple']:
    ensure => directory
  }

  file { '/usr/local/openresty/nginx/conf/nginx.conf':
    ensure  => present,
    content => template("openresty/nginx.conf"),
    require => Exec[make-openresty],
  }

  file { '/etc/init/nginx.conf':
    ensure => present,
    content => template("openresty/nginx-upstart.conf"),
  }

  service { 'nginx':
    ensure   => running,
    enable   => true,
    provider => upstart,
    require => [
      File['/etc/init/nginx.conf'],
      File['/usr/local/openresty/nginx/conf/nginx.conf'],
    ]
  }

}
