import csv, json
csvp='data_files/in_process_data/airbnb_master_data_with_type.csv'
jsp='data_files/in_process_data/locations.js'
# count CSV valid lat/lng
valid=0
with open(csvp,encoding='utf-8') as f:
    r=csv.DictReader(f)
    for row in r:
        if row.get('latitude') and row.get('longitude'):
            valid+=1
print('CSV valid coord rows:',valid)
# count locations.js entries
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
start=txt.find('=')
if start!=-1:
    arr=json.loads(txt[start+1:].strip().rstrip(';'))
    print('locations.js entries:',len(arr))
    from collections import Counter
    c=Counter([a.get('municipality','UNINCORPORATED') for a in arr])
    total=sum(c.values())
    print('sum per municipality:',total)
    for k,v in sorted(c.items(), key=lambda t: (-t[1], t[0])):
        print(f'{k}: {v}')
else:
    print('could not parse locations.js')
