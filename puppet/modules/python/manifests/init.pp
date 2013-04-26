class python {
  include python::modules
}

#
# Python base system modules
#
class python::modules {
  package { [ 'python-virtualenv', 'python-dev', 'python-pip', 'libfreetype6-dev', 'libpng-dev']:
    ensure => 'installed'
  }
}
