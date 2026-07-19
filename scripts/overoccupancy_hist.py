import json
from collections import Counter
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))
vals=[float(a.get('over_occupancy') or 0) for a in arr]
# compute counts of over_occupancy >= k for k from 0..10
for k in range(0,11):
    cnt=sum(1 for v in vals if v>=k)
    print('>=',k, cnt)
