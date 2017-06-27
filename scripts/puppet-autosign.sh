#!/bin/sh
#
# A script than loops forever and signs all certificate requests it receives, 
# without having to turn on real autosigning.
#
# When creating large numbers of nodes this approach may generate invalid 
# certificate/key pairs. The problem may be related to puppet-agent daemon and a 
# manual puppet run doing a certificate request at the same time, which confuses 
# the hell out of Puppet CA. This hypothesis has not been verified, but when the 
# ideal-* nodes (~25) were created, on three occasions the client certificates 
# had to be regenerated because they ended up being useless.
#
x=0
while [ $x -eq 0 ]; do
    puppet cert list|while read LINE; do
        NODE=`echo $LINE|cut -d "\"" -f 2`
        puppet cert sign $NODE
    done 
    sleep 10
done 
