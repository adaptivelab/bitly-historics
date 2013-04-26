#
# Standalone manifest - for dev Vagrant box.
#
node precise64 {

  $cron_username = "vagrant"
  include common
  include vagrant
  include vagrant::puppet

}

node 'openresty-pypi.vagrant' {

  $cron_username = "ubuntu"
  include common

}
