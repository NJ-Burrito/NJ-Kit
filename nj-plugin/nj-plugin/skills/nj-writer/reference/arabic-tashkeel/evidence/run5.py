import h,corpus as C,json,re,concurrent.futures as cf
from sent import SENT
M1='google/gemini-3.6-flash'
V={'vf':lambda t:C.nfc(t),'sf':lambda t:C.shadda_first(C.nfc(t)),'bare':C.bare}
def job(a):
    cid,base,vn,rep=a; txt=V[vn](base)
    w=h.tts(txt,tag=f'v5-{cid}-{vn}-r{rep}')
    return {'id':cid,'variant':vn,'rep':rep,'sent':txt,'base':C.shadda_first(C.nfc(base)),'asr':h.asr(w,M1)}
lines=[(cid,t) for cid,g,t in C.CORPUS if g=='demo']+[(f's{i}',t) for i,t in enumerate(SENT)]
jobs=[(c,t,v,r) for c,t in lines for v in V for r in range(1,6)]
print(len(jobs))
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(job,jobs))
json.dump(res,open('json/run5.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
