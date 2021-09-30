import os
import subprocess
if os.path.exists('/dev/sda1'):
    if os.path.exists('/media/external'):
        subprocess.run(["sudo","mount","-t","vfat","/dev/sda1","/media/external","-o","uid=1000,gid=1000,utf8,dmask=027,fmask=137"])  

    else:
        subprocess.run(["sudo","mkdir","/media/external"])  
        subprocess.run(["sudo","mount","-t","vfat","/dev/sda1","/media/external","-o","uid=1000,gid=1000,utf8,dmask=027,fmask=137"])  
        
#check_output(["sudo","mount","-t","vfat","/dev/sda1","/media/external","-o","uid=1000,gid=1000,utf8,dmask=027,fmask=137"], shell=True)   
else:

    if os.path.exists('/dev/sdb1'):
        subprocess.run(["sudo","reboot"])
    else:
        try:
            check_output(["sudo","rm","-r","/media/external"], shell=True)  
        except:
            subprocess.run(["sudo","reboot"])   