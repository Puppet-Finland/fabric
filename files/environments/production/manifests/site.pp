### Run stages

# Pre stage is useful for things that we need to do before anything else,
# e.g. setup apt/yum repositories
stage { 'pre': before => Stage['main'] }

# This is useful mostly for firewall rules: we want to make sure that
# reject rules get applied last. For details, see:
#
# https://github.com/puppetlabs/puppetlabs-firewall
stage { 'post': require => Stage['main'] }

### Manual node categorization

# Save server role defined in the node's yaml into a top-scope variable. These
# top-scope variables are then used in the Hiera hierarchy to configure a node
# according to it's role.
$role = hiera('role', undef)

### Default email addresses

$serveradmin = hiera('serveradmin', undef)
$servermonitor = hiera('servermonitor', undef)

### Read classes from hiera. This needs to be at the bottom.
hiera_include('classes')
