---
layout: post
title:  "HTB-Arkham"
description: Hack the Box - Arkham Machine.
tags: HTB Arkham
---
# Brief Summary

Arkham machine is typical and fairly popular. The environment set up mimics real-life scenarios.

![machine](/assets/arkham/machine.png)

# Nmap 
As usual, starting off with nmap tool and selecting the option '-A'.
```nmap
# Nmap 7.91 scan initiated Fri Mar 26 04:32:41 2021 as: nmap -A -oN scan-A.txt 10.10.10.130
Nmap scan report for 10.10.10.130
Host is up (0.095s latency).
Scanned at 2021-03-26 04:32:42 EDT for 64s
Not shown: 995 filtered ports
PORT     STATE SERVICE       VERSION
80/tcp   open  http          Microsoft IIS httpd 10.0
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
|_http-title: IIS Windows Server
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp  open  microsoft-ds?
8080/tcp open  http          Apache Tomcat 8.5.37
| http-methods: 
|_  Potentially risky methods: PUT DELETE
|_http-open-proxy: Proxy might be redirecting requests
|_http-title: Mask Inc.
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 28s
| p2p-conficker: 
|   Checking for Conficker.C or higher...
|   Check 1 (port 29094/tcp): CLEAN (Timeout)
|   Check 2 (port 58554/tcp): CLEAN (Timeout)
|   Check 3 (port 50812/udp): CLEAN (Timeout)
|   Check 4 (port 22737/udp): CLEAN (Timeout)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2021-03-26T08:33:36
|_  start_date: N/A

Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Fri Mar 26 04:33:46 2021 -- 1 IP address (1 host up) scanned in 65.24 seconds
```


# Enumeration

Let's pick on port 8080 and scan for web objects using gobuster and open up dirbuter to manually surf the application served via tomcat. 

```sh
gobuster dir --url 'http://10.10.10.130:8080' -w ~/wordlists/big.txt -x .jsp
```
-x for extensions. (we know we probably should look for jsp, since it is apache tomcat server)

The results are not disappointing. 

```sh
2021/07/18 04:18:19 Starting gobuster in directory enumeration mode
===============================================================
/]                    (Status: 400) [Size: 0]
/[                    (Status: 400) [Size: 0]
/].jsp                (Status: 400) [Size: 0]
/[.jsp                (Status: 400) [Size: 0]
/css                  (Status: 302) [Size: 0] [--> /css/]
/favicons             (Status: 302) [Size: 0] [--> /favicons/]
/fonts                (Status: 302) [Size: 0] [--> /fonts/]   
/images               (Status: 302) [Size: 0] [--> /images/]  
/js                   (Status: 302) [Size: 0] [--> /js/]      
/plain]               (Status: 400) [Size: 0]                 
/plain].jsp           (Status: 400) [Size: 0]                 
/quote]               (Status: 400) [Size: 0]                 
/quote].jsp           (Status: 400) [Size: 0]                 
/thankyou.jsp         (Status: 500) [Size: 2513]              
                                                              
===============================================================
```

Looking are /images directory, we see that we get '404' Not Found...

Let's jump to port 445 and take a look at what SMB has hidden for us.

Using smbclient tools to be able to enumerate the directories and files on the remote host.
```sh
smbclient -L 10.10.10.130
```

Here is the output of this command. (when prompted for password just press enter)
```sh     
Enter WORKGROUP\GUEST's password: 

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        BatShare        Disk      Master Wayne's secrets
        C$              Disk      Default share
        IPC$            IPC       Remote IPC
        Users           Disk      
```
Take a look at BatShare folder.
```sh
smbclient //10.10.10.130/BatShare
smb: \> ls
  .                                   D        0  Sun Feb  3 13:00:10 2019
  ..                                  D        0  Sun Feb  3 13:00:10 2019
  appserver.zip                       A  4046695  Fri Feb  1 06:13:37 2019

                5158399 blocks of size 4096. 2128121 blocks available
smb: \> get appserver.zip
getting file \appserver.zip of size 4046695 as appserver.zip (1113.5 KiloBytes/sec) (average 1113.5 KiloBytes/sec)
smb: \> exit
```



# Cryptography 

Decompressing the archive appserver.zip after downloading it, we found two files. 'IMPORTANT.TXT' which has a message to Alfred with content "Alfred, this is the backup image from our linux server. Please see that The Joker or anyone else doesn't have unauthenticated access to it. - Bruce". The other file 'backup.img' is encrypted, we can tell from executing ```file``` command against it.
```sh 
$ file backup.img 
backup.img: LUKS encrypted file, ver 1 [aes, xts-plain64, sha256] UUID: d931ebb1-5edc-4453-8ab1-3d23bb85b38e
```
The encryption type is 'Linux Unified Key Setup' short for LUKS. This type of encryption requires 'cryptsetup' tools to be installed if not already there in kali linux. (if cryptsetup is not installed hashcat will not be able to display the correct password)

It is time to break in and see what inside. Using 'hashcat' tool to brute-force the password. First, we need to determine the Hash modes.

```sh
$ hashcat -h | grep -i LUKS
  14600 | LUKS                                             | Full-Disk Encryption (FDE)
```

It is good idea to minimize our dictionary list to speed up the cracking process. Specially when the cipher is 'aes' because it longer time to complete the full operation.

Since the box is all about batman, lets grep for batman word in rockyou.txt dictionary list.

```sh
$ cat rockyou.txt | grep -i batman >> batman.txt
$ nl batman.txt
...(output was shortened)
  1073  1-batman-2
  1074  0batman
  1075  0907fairylovesbatman$
  1076  00BATman
  1077  -batman-
  1078  *batman7*
  1079  $batman4
  1080  #9batman
  1081  #1Batman
```
-i case-insensitive 

Now lets run **hashcat**

```sh
hashcat -a 0 -m 14600 backup.img batman.txt
```
-m to select hash mode option

after a while, finally got the correct word 'batmanforever'

####

Looking at web.xml.bak found a string That looks like a secret.
```
<param-value>SnNGOTg3Ni0=</param-value>
```



# Initial Foothold, Sqli & Bypass File Upload Restriction 


# Post Exploitation & Root Own

- thanks for reading



