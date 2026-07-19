import json
from collections import Counter
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))
processed=[]
for loc in arr:
    try:
        latitude = float(loc.get('latitude') if loc.get('latitude')!='' else 0)
        longitude = float(loc.get('longitude') if loc.get('longitude')!='' else 0)
    except:
        latitude=0; longitude=0
    if not latitude or not longitude:
        continue
    processed.append(loc)
print('arr len',len(arr))
print('processed len',len(processed))
print(Counter([str(a.get('municipality') or 'UNINCORPORATED').upper() for a in processed]))
