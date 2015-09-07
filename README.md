# fabric

Generic Fabric scripts to bootstrap and manage Puppet nodes

# Bugs

## Imports need to be inside defs

If imports are placed at the top of the Python files, the task hierarchy gets 
messed up. See message for commit e0d3d79 for details.

## Operating system variables are constantly redefined

Currently each method has to individually (re)determine the OS-specific 
variables. This is suboptimal if a task calls many methods which also need to 
runnable by themselves, i.e. Fabric tasks.
