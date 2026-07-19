import json
jsp='data_files/in_process_data/locations.js'
with open(jsp,encoding='utf-8') as f:
    txt=f.read()
arr=json.loads(txt.split('=',1)[1].strip().rstrip(';'))

def simulate(showViolationsOnly, slider, selectedMunicipalities=None):
    if selectedMunicipalities is None:
        selectedMunicipalities = set([str(a.get('municipality') or 'UNINCORPORATED').upper() for a in arr])
    processed=[a for a in arr if a.get('latitude') and a.get('longitude')]
    # normalized municipality names
    processed=[{**a, 'municipality': str(a.get('municipality') or 'UNINCORPORATED').upper(), 'overOccupancy': float(a.get('over_occupancy') or 0)} for a in processed]
    # effectiveMin logic
    if showViolationsOnly:
        effectiveMin = max(1, slider)
    elif slider>0:
        effectiveMin = slider
    else:
        effectiveMin = None
    filtered=[]
    for loc in processed:
        if loc['municipality'] not in selectedMunicipalities: continue
        if effectiveMin is not None:
            if loc['overOccupancy'] < effectiveMin: continue
        filtered.append(loc)
    return len(filtered), len(processed)

# tests
print('uncheck, slider=0 -> should show all')
print(simulate(False,0)[0])
print('check, slider=0 -> should show over>=1')
print(simulate(True,0)[0])
print('uncheck, slider=1 -> should filter >=1')
print(simulate(False,1)[0])
print('check, slider=2 -> should filter >=2')
print(simulate(True,2)[0])
