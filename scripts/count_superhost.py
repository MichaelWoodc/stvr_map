import json
from collections import Counter
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))
print('total',len(arr))
print('superhost counts:')
for k in ['Superhost','']:
    print(k, sum(1 for a in arr if (a.get('superhost') or '')==k))
# per municipality Superhost count
for k in ['BLOOMINGDALE','GARDEN CITY','POOLER','PORT WENTWORTH','SAVANNAH','THUNDERBOLT','TYBEE ISLAND','UNINCORPORATED']:
    print(k, sum(1 for a in arr if (a.get('superhost') or '')=='Superhost' and str((a.get('municipality') or 'UNINCORPORATED')).upper()==k))
