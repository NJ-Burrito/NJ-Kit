import json,corpus as C,collections,re
M1,M2='google/gemini-3.6-flash','google/gemini-3.5-flash-lite'
R1=json.load(open('json/run1.json',encoding='utf-8')); R2=json.load(open('json/run2.json',encoding='utf-8'))
# A. demo/hard variants, both models, excl-final (waqf-tolerant) and exact
def tab(rows,title):
    print('##',title)
    for m in (M1,M2):
        agg=collections.defaultdict(lambda:[0,0,0,0])
        for r in rows:
            h=r.get('asr:'+m,'ERR')
            if h.startswith('ERR'): continue
            n,ex,exf,lt,lo,d=C.score(r['base'],h); a=agg[(r['group'],r['variant'])]
            a[0]+=n;a[1]+=ex;a[2]+=exf;a[3]+=1
        for k,a in sorted(agg.items()): print(m.split('/')[1],k,'exact %d/%d (%.0f%%)  excl-final %d/%d (%.0f%%)  clips %d'%(a[1],a[0],100*a[1]/a[0],a[2],a[0],100*a[2]/a[0],a[3]))
tab([r for r in R1+R2 if r['group'] in('demo',)],'demo, 3 TTS reps (run1 + 2 more) x 2 ASR')
tab([r for r in R1 if r['group']=='hard'],'hard run1')
# B. keyword pairs: does ASR report the sent vowels on the key word (frame word 2)
print('## keyword (frame: قَالَ الْمُدِيرُ X فِي الْمَكْتَبِ), key = word 3')
tot=collections.Counter(); sets=collections.defaultdict(dict)
for r in R2:
    if r['group']!='keyword': continue
    k=r['id'][2:]
    for m in (M1,M2):
        h=r['asr:'+m]
        if h.startswith('ERR'): continue
        ref=C.parse(r['sent']); hy=C.parse(h)
        if len(hy)<3: tot[(m,'bad')]+=1; continue
        key_ref=ref[2]; key_h=hy[2]
        same_letters=[C.norm_letter(c) for c,_ in key_ref]==[C.norm_letter(c) for c,_ in key_h]
        ok=same_letters and all(a[1]==b[1] for a,b in zip(key_ref,key_h))
        # ignore final letter
        okf=same_letters and all(a[1]==b[1] for a,b in zip(key_ref[:-1],key_h[:-1]))
        tot[(m,'n')]+=1; tot[(m,'exact')]+=ok; tot[(m,'nofinal')]+=okf
        sets[(m,r['rep'],k)]=(key_ref,key_h)
for m in (M1,M2): print(m.split('/')[1],'key word exact %d/%d, excluding final letter %d/%d'%(tot[(m,'exact')],tot[(m,'n')],tot[(m,'nofinal')],tot[(m,'n')]))
# which keys fail
fl=collections.Counter()
for r in R2:
    if r['group']!='keyword': continue
    for m in (M1,M2):
        h=r['asr:'+m]; hy=C.parse(h); ref=C.parse(r['sent'])
        if len(hy)>=3:
            a,b=ref[2],hy[2]
            if [(c,frozenset(x)) for c,x in a[:-1]]!=[(c,frozenset(x)) for c,x in b[:-1]]:
                fl[(r['id'][2:],''.join(c+''.join(sorted(x)) for c,x in b))]+=1
for k,v in sorted(fl.items()): print('MISS',k,v)
json.dump({'tot':{str(k):v for k,v in tot.items()}},open('json/an2.json','w'))
