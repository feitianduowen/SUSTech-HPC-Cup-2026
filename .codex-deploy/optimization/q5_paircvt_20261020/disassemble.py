import subprocess
import sys

library=sys.argv[1]
symbol='ggml_vec_dot_q5_1_q8_1'
p=subprocess.run(['nm','-D','-S',library],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,check=True)
matches=[line.split() for line in p.stdout.splitlines() if line.split() and line.split()[-1]==symbol]
assert len(matches)==1 and len(matches[0])==4,matches
start=int(matches[0][0],16);size=int(matches[0][1],16)
assert start>0 and size>0
subprocess.run(['objdump','-d','--start-address='+hex(start),'--stop-address='+hex(start+size),library],check=True)
