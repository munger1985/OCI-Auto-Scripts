fo = open("install-config.yaml", "r+")
var=open("pullsecret.txt","r")
pubkeyfile=open('sshkey.pub',"r")

string=var.read()
all=fo.read()
string=string.replace('\n',"")
all=all.replace('ppllss',string)
keystring=pubkeyfile.read()
keystring=keystring.replace('\n',"")
all=all.replace('sshpubkey',keystring)

fo.seek(0)
fo.write(all)
