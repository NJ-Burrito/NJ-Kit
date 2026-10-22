import json,base64,subprocess,hashlib,os,sys,time,urllib.request,unicodedata,re
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__))
TOK=os.environ['OPENROUTER_API_KEY']  # from the environment; never stored in the repo
URL='https://openrouter.ai/api/v1'
MODEL='google/gemini-3.1-flash-tts-preview'
DIRECTION="Say this warmly and confidently with a smile in your voice, calm and clear, unhurried, like a friendly expert guiding someone step by step: "
def post(path,body,t=180):
    r=urllib.request.Request(URL+path,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+TOK,'Content-Type':'application/json'})
    return urllib.request.urlopen(r,timeout=t).read()
def tts(text,direction=DIRECTION,tag=None):
    key=hashlib.sha1((direction+text).encode()).hexdigest()[:16]
    wav=os.path.join(HERE,'audio',(tag or key)+'.wav')
    if os.path.exists(wav): return wav
    pcm=post('/audio/speech',{'model':MODEL,'input':direction+text,'voice':'Kore','response_format':'pcm'})
    open(wav+'.pcm','wb').write(pcm)
    subprocess.run(['ffmpeg','-y','-v','error','-f','s16le','-ar','24000','-ac','1','-i',wav+'.pcm',wav],check=True)
    os.remove(wav+'.pcm'); return wav
ASR_PROMPT=("Transcribe this Arabic speech. Output ONLY the transcript, in Arabic script, with FULL tashkeel (fatha, damma, kasra, sukun, shadda, tanween) "
"written EXACTLY as the speaker pronounced each word, including the final case-ending vowel of every word spoken. Do not correct grammar, do not normalize, do not guess what the speaker should have said; "
"transcribe the vowels actually heard. If a word is pronounced with a sukun/pause at its end, mark sukun. No commentary.")
def asr(wav,model='google/gemini-3-flash-preview'):
    b=base64.b64encode(open(wav,'rb').read()).decode()
    out=post('/chat/completions',{'model':model,'temperature':0,'messages':[{'role':'user','content':[{'type':'text','text':ASR_PROMPT},{'type':'input_audio','input_audio':{'data':b,'format':'wav'}}]}]})
    j=json.loads(out); return j['choices'][0]['message']['content'].strip()
if __name__=='__main__':
    w=tts(sys.argv[1],tag='probe'); print(w); print(asr(w))
