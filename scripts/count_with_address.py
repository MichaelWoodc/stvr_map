import json
from collections import Counter
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))
with_addr=[a for a in arr if a.get('approximate_address')]
print('with address',len(with_addr))
for k in ['BLOOMINGDALE','GARDEN CITY','POOLER','PORT WENTWORTH','SAVANNAH','THUNDERBOLT','TYBEE ISLAND','UNINCORPORATED']:
    print(k, sum(1 for a in with_addr if str((a.get('municipality') or 'UNINCORPORATED')).upper()==k))
