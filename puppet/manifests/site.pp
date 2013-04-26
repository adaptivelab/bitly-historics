import 'lib/*.pp'
import 'nodes/*.pp'

#
# Modules included for all nodes.
#
#
# ED STONE NOTES:
# many of the following are unnecessary and probably could just be removed:
# hotworker, circus, flask, chaussette, zeromq (but Ian has deployed and does not want to delete stuff this close to delivery)
class common {

    include python
    include hotworker
    include git
    include fabric
    include curl
    include libncurses
    include libpcre
    include libreadline
    include libssl
    include perl
    include openresty
    include circus
    include redis
    include requests
    include flask
    include chaussette
    include zeromq
    include mongodb

    notify {$cron_username:}
    cron {"iantest":
       command => "cd /vagrant && ./run_update_all.sh",
       user => $cron_username,
       hour => "*/5",
     }

}
