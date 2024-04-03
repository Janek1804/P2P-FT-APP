## About
QT-Share is a P2P application for sharing files in LAN environment.

## Peer Exchange Protocol and Network Transmissions
<ul>
<li> Peer discovery operates using IPv4 local broadcasts targeting UDP port 7050 every 90 seconds. </li>
<li> File information is exchanged using HTTP on port 8080. </li>
<li> Files are transferred using TCP (port 7050)</li>
</ul>

## File Sharing
FT.conf is used to specify directories of shared files and their pieces.
