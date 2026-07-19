import json
from collections import Counter, defaultdict
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))

def mun_counts(filter_fn):
    c=Counter()
    for a in arr:
        if filter_fn(a):
            c[str(a.get('municipality') or 'UNINCORPORATED').upper()]+=1
    return c

print('total',len(arr))
print('total per municipality')
print(Counter([str(a.get('municipality') or 'UNINCORPORATED').upper() for a in arr]))

filters={
 'over_occupancy>0': lambda a: float(a.get('over_occupancy') or 0)>0,
 'rental_type entire': lambda a: ('entire' in str(a.get('rental_type') or '').lower()),
 'rental_type entire or entire home/condo': lambda a: ('entire' in str(a.get('rental_type') or '').lower()),
 'guests>=3': lambda a: float(a.get('guests') or 0)>=3,
 'beds>=2': lambda a: float(a.get('beds') or 0)>=2,
 'percent_over>0': lambda a: float(a.get('percent_over') or 0)>0,
}

for name,fn in filters.items():
    c=mun_counts(fn)
    total=sum(c.values())
    print('\nFilter:',name,'total',total)
    print('sample:', {k:c.get(k,0) for k in ['BLOOMINGDALE','GARDEN CITY','POOLER','PORT WENTWORTH','SAVANNAH','THUNDERBOLT','TYBEE ISLAND','UNINCORPORATED']})
