import re,unicodedata,sys,importlib.util
sys.stdout.reconfigure(encoding='utf-8')
M="ً-ْٰ"
SH="ّ"
def demo_lines():
    s=open('../kore-demo/demo-flow.ts',encoding='utf-8').read()
    return re.findall(r"^\s+'([a-z\-]+)':\s*\n\s+'(.+?)',$",s,re.M)
def nfc(t): return unicodedata.normalize('NFC',t)
def shadda_first(t): return re.sub("([ً-ِْ])ّ",lambda m:"ّ"+m.group(1),t)
def bare(t): return re.sub("["+M+"]","",t)
def nocase(t):
    # drop the mark(s) on the last letter of every word (pausal / internal-marks-only)
    out=[]
    for w in t.split(' '):
        out.append(re.sub("(?<=[ء-ي])["+M+"]+(?=[^ء-ي]*$)","",w) if re.search("[ء-ي]",w) else w)
    return ' '.join(out)
def waqf(t):
    # clause ends (before ، . : ؛ or end of text): final non-tanween vowel -> sukun
    out=[]
    toks=t.split(' ')
    for i,tok in enumerate(toks):
        m=re.match("^(.*?)([»\"]*[،.:؛]*[»\"]*)$",tok)
        w,p=m.group(1),m.group(2)
        if (re.search("[،.:؛]",p) or i==len(toks)-1) and w and not re.search("[ًٌٍ]",w[-3:]):
            w2=re.sub("[َُِ]+$","",w)
            if not w2.endswith("ّ") and w2!=w: w=w2+"ْ"
        out.append(w+p)
    return ' '.join(out)
CORPUS=[]  # (id, group, base_marked, keyed_note)
for i,(k,t) in enumerate(demo_lines()): CORPUS.append(('demo-'+k,'demo',t))
PAIRS=[
 ('p-katab1','pair','كَتَبَ الطَّالِبُ الرِّسَالَةَ'),('p-katab2','pair','كُتِبَتِ الرِّسَالَةُ'),('p-katab3','pair','كَتَّبَ الْمُعَلِّمُ الطُّلَّابَ'),
 ('p-alima1','pair','عَلِمَ الطَّالِبُ الْخَبَرَ'),('p-alima2','pair','عُلِمَ الْخَبَرُ'),('p-alima3','pair','عَلَّمَ الْمُعَلِّمُ الطَّالِبَ'),
 ('p-mud1','pair','قَابَلْتُ الْمُدِيرَ'),('p-mud2','pair','قَابَلَنِي الْمُدِيرُ'),('p-mud3','pair','سَلَّمْتُ عَلَى الْمُدِيرِ'),
 ('p-bad1','pair','ذَهَبَ الطَّالِبَ إِلَى الْمَدْرَسَةُ'),  # counter-grammar: marks wrong on purpose
 ('p-bad2','pair','قَرَأَ الْمُعَلِّمُ الْكِتَابُ الْجَدِيدِ'),
]
HARD=[
 ('h-num-digit','hard','تُعْرَضُ الْخِدْمَةُ لِمُدَّةِ ٣٠ يَوْمًا'),
 ('h-num-word','hard','تُعْرَضُ الْخِدْمَةُ لِمُدَّةِ ثَلَاثِينَ يَوْمًا'),
 ('h-lat-pdf','hard','اِضْغَطْ عَلَى زِرِّ PDF ثُمَّ اخْتَرِ الْمِلَفَّ'),
 ('h-lat-ar','hard','اِضْغَطْ عَلَى زِرِّ بِي دِي إِفْ ثُمَّ اخْتَرِ الْمِلَفَّ'),
 ('h-wasl-a','hard','وَاخْتَارَ ابْنُ الْمُدِيرِ اسْمَهُ'),
 ('h-wasl-b','hard','وَٱخْتَارَ ٱبْنُ الْمُدِيرِ ٱسْمَهُ'),
 ('h-sun','hard','الشَّمْسُ وَالْقَمَرُ وَالنَّهْرُ وَالْبَابُ'),
 ('h-tamarb','hard','هَذِهِ الْخِدْمَةُ مَجَّانِيَّةٌ، وَالْخِدْمَةُ الْمَجَّانِيَّةُ مُتَاحَةٌ'),
 ('h-maqsura','hard','انْتَقَلْتُ إِلَى الْمَبْنَى عَلَى الْمُسْتَوَى الثَّانِي'),
 ('h-proper','hard','الْمُؤَسَّسَةُ الْعَامَّةُ لِلْغِذَاءِ وَالدَّوَاءِ فِي الْأُرْدُنِّ'),
 ('h-hamza','hard','سُئِلَ الْمُسْؤُولُ عَنْ الْمَسْؤُولِيَّةِ'),
]
CORPUS+=PAIRS+HARD
VARIANTS={'asis':lambda t:t,'nfc':nfc,'bare':bare,'nocase':nocase,'waqf':waqf}
# --- scoring ---
def parse(t):
    t=nfc(t); t=re.sub("ـ","",t)
    t=re.sub("([ا])([ً])", lambda m: "ً"+m.group(1) if False else m.group(0), t)
    words=[]
    for tok in re.split(r"\s+",t):
        w=[]
        for ch in tok:
            if re.match("[ء-يٱ]",ch): w.append([ch,set()])
            elif re.match("["+M+"]",ch) and w: w[-1][1].add(ch)
        if w: words.append(w)
    # tanween-fatha written after alif -> move to previous letter
    for w in words:
        for i in range(1,len(w)):
            if w[i][0]=="ا" and "ً" in w[i][1] and i>=1 and not w[i-1][1]-{"ّ"} :
                pass
        for i in range(1,len(w)):
            if w[i][0] in "اى" and "ً" in w[i][1]:
                w[i][1].discard("ً"); w[i-1][1].add("ً")
    return words
def norm_letter(c): return {"ٱ":"ا","أ":"ا","إ":"ا","آ":"ا","ى":"ي"}.get(c,c)
def score(ref,hyp):
    """returns (words_total, exact, exact_ignoring_final, letter_marks_total, letter_marks_ok, diffs)"""
    R,H=parse(ref),parse(hyp)
    n=len(R); ex=exf=0; lt=lo=0; diffs=[]
    for i,r in enumerate(R):
        h=H[i] if i<len(H) else []
        rl=[norm_letter(c) for c,_ in r]; hl=[norm_letter(c) for c,_ in h]
        if rl!=hl: diffs.append((''.join(c+''.join(sorted(m)) for c,m in r),'LETTERS≠'+''.join(c+''.join(sorted(m)) for c,m in h))); continue
        ok=all(r[j][1]==h[j][1] for j in range(len(r)))
        okf=all(r[j][1]==h[j][1] for j in range(len(r)-1))
        for j in range(len(r)): 
            lt+=1; lo+= r[j][1]==h[j][1]
        ex+=ok; exf+=okf
        if not ok: diffs.append((''.join(c+''.join(sorted(m)) for c,m in r),''.join(c+''.join(sorted(m)) for c,m in h)))
    return n,ex,exf,lt,lo,diffs
if __name__=='__main__':
    print(len(CORPUS)); print(demo_lines()[0][0]); 
    t=CORPUS[1][2]; print(nocase(t)[:60]); print(waqf(t)[-50:]); print(score(t,t)[:5], score(t,nfc(t))[:5], score(t,bare(t))[:5])
