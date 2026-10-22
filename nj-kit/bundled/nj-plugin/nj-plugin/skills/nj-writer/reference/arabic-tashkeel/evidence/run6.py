import h,corpus as C,json,re,concurrent.futures as cf
from sent import SENT
M1='google/gemini-3.6-flash'
def split(t):  # vowel-first text: X + vowel? + shadda -> X sukun X vowel   (shadda in NFC order: letter, vowel, shadda)
    return re.sub("([ء-ي])([ً-ِ]?)ّ", lambda m: m.group(1)+"ْ"+m.group(1)+m.group(2), C.nfc(t))
def job(a):
    cid,base,rep=a; txt=split(base)
    w=h.tts(txt,tag=f'v6-{cid}-split-r{rep}')
    return {'id':cid,'variant':'split','rep':rep,'sent':txt,'base':C.nfc(base),'asr':h.asr(w,M1)}
lines=[(cid,t) for cid,g,t in C.CORPUS if g=='demo']+[(f's{i}',t) for i,t in enumerate(SENT)]
jobs=[(c,t,r) for c,t in lines for r in range(1,6)]
print(split(SENT[1]))
with cf.ThreadPoolExecutor(8) as ex: res=list(ex.map(job,jobs))
json.dump(res,open('json/run6.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
