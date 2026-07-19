import json
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))
from collections import Counter
print('total entries',len(arr))
over=[a for a in arr if float(a.get('over_occupancy') or 0)>0]
print('over-occupancy total',len(over))
co=Counter([str(a.get('municipality') or 'UNINCORPORATED').upper() for a in over])
for k in ['BLOOMINGDALE','GARDEN CITY','POOLER','PORT WENTWORTH','SAVANNAH','THUNDERBOLT','TYBEE ISLAND','UNINCORPORATED','VERNONBURG']:
    print(k, co.get(k,0))
