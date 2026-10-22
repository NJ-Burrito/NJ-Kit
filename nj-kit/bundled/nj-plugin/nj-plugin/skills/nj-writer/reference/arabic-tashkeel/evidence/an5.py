import json,corpus as C,collections,statistics as st
R=json.load(open('json/run5.json',encoding='utf-8'))
SH="ّ"
def sc(r,pick=lambda i,w:True):
    ref,hy=C.parse(r['base']),C.parse(r['asr']); n=ok=okf=0
    for i,w in enumerate(ref):
        if not pick(i,w): continue
        n+=1
        if i<len(hy) and [C.norm_letter(a) for a,_ in w]==[C.norm_letter(a) for a,_ in hy[i]]:
            ok+=all(p[1]==q[1] for p,q in zip(w,hy[i])); okf+=all(p[1]==q[1] for p,q in zip(w[:-1],hy[i][:-1]))
    return n,ok,okf
for name,pick in (('all words',lambda i,w:True),('shadda words',lambda i,w:any(SH in m for _,m in w))):
    print('##',name)
    for v in ('vf','sf','bare'):
        n=ok=okf=0; per=collections.defaultdict(lambda:[0,0])
        for r in R:
            if r['variant']!=v: continue
            a,b,c=sc(r,pick); n+=a;ok+=b;okf+=c; per[r['rep']][0]+=a; per[r['rep']][1]+=c
        reps=[100*x[1]/x[0] for x in per.values() if x[0]]
        print(v,'internal-exact %d/%d (%.1f%%)  final-incl %d/%d  per-rep range %.0f-%.0f%% (sd %.1f)'%(okf,n,100*okf/n,ok,n,min(reps),max(reps),st.pstdev(reps)))
# paired by line: sf vs vf
d=collections.defaultdict(lambda:collections.defaultdict(list))
for r in R: d[r['id']][r['variant']].append(sc(r)[2]/max(1,sc(r)[0]))
print('per-line mean internal acc  vf / sf / bare')
for k,v in d.items(): print(k,*['%.2f'%st.mean(v[x]) for x in('vf','sf','bare')])
