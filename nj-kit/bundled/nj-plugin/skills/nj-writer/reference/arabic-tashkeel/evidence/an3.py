import json,corpus as C,collections
M1='google/gemini-3.6-flash'
R2=json.load(open('json/run2.json',encoding='utf-8')); R3=json.load(open('json/run3.json',encoding='utf-8'))
SH="ّ"
def wscore(rows,pick):
    agg=collections.defaultdict(lambda:[0,0,0,0])
    for r in rows:
        h=r['asr:'+M1]
        if h.startswith('ERR'): continue
        ref,hy=C.parse(r['base']),C.parse(h)
        for i,w in enumerate(ref):
            if not pick(i,w): continue
            a=agg[(r['group'],r['variant'])]; a[0]+=1
            if i<len(hy):
                x=hy[i]
                if [C.norm_letter(c) for c,_ in w]==[C.norm_letter(c) for c,_ in x]:
                    a[1]+= all(p[1]==q[1] for p,q in zip(w[:-1],x[:-1]))   # internal marks, final letter ignored (waqf)
                    a[2]+= all(p[1]==q[1] for p,q in zip(w,x))
            a[3]+=1
    return agg
key=lambda i,w:i==2
rows=[r for r in R2 if r['group']=='keyword' and r['variant']=='asis']+R3
for k,a in sorted(wscore([r for r in rows if r['group']=='keyword'],key).items()): print('KEYWORD',k,'internal-exact %d/%d (%.0f%%)'%(a[1],a[0],100*a[1]/a[0]))
shw=lambda i,w:any(SH in m for _,m in w)
for k,a in sorted(wscore([r for r in R3 if r['group']=='shadda'],shw).items()): print('SHADDA-WORDS',k,'internal-exact %d/%d (%.0f%%)  full-exact %d'%(a[1],a[0],100*a[1]/a[0],a[2]))
# shadda-bearing key words only, asis vs nfc vs split
shk=lambda i,w:i==2 and any(SH in m for _,m in w)
for k,a in sorted(wscore(rows,shk).items()): print('KEY-with-shadda',k,'%d/%d'%(a[1],a[0]))
# any-word shadda also in demo/run
D=[r for r in json.load(open('json/run1.json',encoding='utf-8'))+R2 if r['group']=='demo' and r['variant'] in('asis','nfc')]
for k,a in sorted(wscore(D,shw).items()): print('DEMO shadda words',k,'%d/%d'%(a[1],a[0]))
# pair discrimination (asis): does ASR give different outputs for different sent words
