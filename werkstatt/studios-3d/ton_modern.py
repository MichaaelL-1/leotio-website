# Leotio Studios Ton modern v1.0 · 25.11.2026: 6 moderne Fassungen (Synth-Flaeche, tiefer Schlag, Bass, Klavier, Glas) auf dem Takt. Aufruf: ton_modern.py <Bausteine modern> <Bausteine Orchester> <Zielordner>
import numpy as np, sys, json, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
SRC,ORC,OUT=sys.argv[1:4]; os.makedirs(OUT,exist_ok=True)
TK=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'takt.json')))
SR=48000; DUR=TK['dauer']; N=int(SR*DUR); HITS=TK['hits']; TC=TK['clear']; TE=TK['schluss']; BEAT=60/TK['bpm']; HT=[h['t'] for h in HITS]
def load(d,k):
    sr,a=wavfile.read(f'{d}/{k}.wav'); assert sr==SR; a=a.astype(np.float64)/32768; return a/np.abs(a).max()
B={k:load(SRC,k) for k in ('pad','drone','boom','piano','riser','bass')}; B['strmaj']=load(ORC,'strmaj')
# gemessen: pad = D-Dur, drone = D, bass = D2 (38), piano = A4 (69)
def pitch(a,st):
    if st==0: return a
    f=2**(st/12); n=int(len(a)/f); x=np.linspace(0,len(a)-1,n); i=np.arange(len(a)); return np.stack([np.interp(x,i,a[:,c]) for c in range(2)],1)
def env(a,att,rel):
    n=len(a); t=np.arange(n)/SR; return a*np.clip(np.minimum(t/max(att,1e-3),1)*np.minimum((n/SR-t)/max(rel,1e-3),1),0,1)[:,None]
def cut(a,t0,d): return a[int(t0*SR):int((t0+d)*SR)]
def hold(a,t0,t1,d,xf=0.5):      # Flaeche beliebig lang halten: Ausschnitt [t0,t1] ueberlappend aneinandersetzen
    seg=cut(a,t0,t1-t0); L=len(seg); out=np.zeros((int(d*SR)+L,2)); step=L-int(xf*SR); pos=0
    while pos<d*SR:
        out[pos:pos+L]+=env(seg,xf,xf); pos+=step
    return out[:int(d*SR)]
def glass(midi,d):               # klarer, glasiger Ton (gerechnet)
    f=440*2**((midi-69)/12); t=np.arange(int(d*SR))/SR
    s=np.sin(2*np.pi*f*t+1.2*np.exp(-t*6)*np.sin(2*np.pi*f*2*t))*np.exp(-t*2.2)+0.3*np.sin(2*np.pi*f*2*t)*np.exp(-t*4)+0.12*np.sin(2*np.pi*f*3.0*t)*np.exp(-t*7)
    s*=np.minimum(t/0.004,1); return np.stack([s,s],1)*0.5
def piano(midi,d): return env(cut(pitch(B['piano'],midi-69),0,d),0.002,min(0.4,d*0.4))
def tick():
    t=np.arange(int(0.05*SR))/SR; n=sosfilt(butter(2,[6000,12000],btype='band',fs=SR,output='sos'),np.random.default_rng(3).standard_normal(len(t)))*np.exp(-t*110); return np.stack([n,n],1)
class Mix:
    def __init__(s): s.S=np.zeros((N,2))
    def add(s,sig,t,g=1.0,pan=0.0):
        i=int(t*SR)
        if i<0: sig=sig[-i:]; i=0
        x=sig[:max(0,N-i)]*g; s.S[i:i+len(x),0]+=x[:,0]*(1-max(pan,0)*0.5); s.S[i:i+len(x),1]+=x[:,1]*(1+min(pan,0)*0.5)
RT={'D':0,'B':-3,'G':-7,'A':-5,'Bb':-4,'C':-2,'F':-9,'E':2}
def build(K):
    M=Mix(); bed=Mix()
    if K.get('drone',0): bed.add(env(hold(B['drone'],1.2,4.2,TE+0.3),1.2,0.6),0,K['drone'])
    if K.get('pad',0): bed.add(env(hold(B['pad'],3.2,5.0,TE+0.3,0.7),1.5,0.6),0,K['pad']*2.2)
    times=[0.3]+HT[1:]+[TC+0.6,TE]
    for i,nm in enumerate(K['bass']+[K['pre']]):
        d=times[i+1]-times[i]+0.2; bed.add(env(cut(pitch(B['bass'],RT[nm]),0.6,d),0.08,0.3),times[i]-0.05,K.get('bassg',0.5))
    S=bed.S
    if K.get('pump'):               # Flaeche atmet im Takt
        t=np.arange(N)/SR; ph=((t-HT[0])%BEAT)/BEAT; S=S*(0.45+0.55*np.minimum(ph/0.6,1)**1.5)[:,None]
        k=0; tt=HT[0]
        while tt<TE-0.05: M.add(tick(),tt,0.10 if k%2 else 0.05,(-0.5,0.5)[k%2]); tt+=BEAT/2; k+=1
    M.S+=S
    rng=np.random.default_rng(4)
    for i,h in enumerate(HITS):
        g=h.get('sc',1.5)/2.0; M.add(B['boom'],h['t']-0.004,(0.95 if i==4 else 0.6)*g*K.get('hitg',1.0),h['p'][0]*0.3)
        t=np.arange(int(1.8*SR))/SR; n=sosfilt(butter(2,[900,5000],btype='band',fs=SR,output='sos'),rng.standard_normal(len(t)))*np.exp(-t*2.4)*np.minimum(t/0.012,1)
        M.add(np.stack([n,n],1),h['t'],0.05,h['p'][0]*0.7)
    r=cut(B['riser'],0.6,1.05); r=r/np.abs(r).max(); M.add(env(r,0.6,0.02),TE-len(r)/SR,0.3*K.get('riseg',1.0))
    # Schluss: D-Dur-Flaeche, Bass, tiefer Schlag; bei Hybrid leise Streicher dazu
    M.add(env(hold(B['pad'],3.2,5.0,DUR-TE+0.2,0.7),0.03,1.5),TE-0.02,2.6*K.get('endpad',1.0))
    M.add(env(cut(B['bass'],0.6,DUR-TE),0.02,1.4),TE-0.02,0.5); M.add(B['boom'],TE-0.004,0.7*K.get('hitg',1.0))
    if K.get('str',0): M.add(env(cut(B['strmaj'],1.7,DUR-TE+0.2),0.05,1.4),TE-0.02,K['str'])
    for (dt,midi,d) in K['motiv']:
        if K.get('pianog',0): M.add(piano(midi,d+0.8),TE+dt,K['pianog'])
        if K.get('glassg',0): M.add(glass(midi+12*K.get('okt',0),d+1.2),TE+dt,K['glassg'])
    S=M.S; tl=np.arange(int(2.6*SR))/SR; out=S.copy()
    for c,sd in ((0,1),(1,2)):
        ir=sosfilt(butter(2,[250,7000],btype='band',fs=SR,output='sos'),np.random.default_rng(sd).standard_normal(len(tl))*np.exp(-tl*K.get('hall',2.4)))
        out[:,c]+=fftconvolve(S[:,c],ir)[:N]*0.007
    f=np.ones(N); k=int(1.3*SR); f[-k:]=np.linspace(1,0,k)**2; out*=f[:,None]
    return np.tanh(out/np.abs(out).max()*1.4)/np.tanh(1.4)*0.89
NAME=[(-0.90,69,0.3),(-0.60,66,0.3),(-0.30,64,0.3),(0.0,62,0.5),(0.55,62,0.3),(0.85,69,0.3),(1.15,74,1.2)]
KOMP=[
 dict(nr=1,name='Klar',text='Ruhige Synth-Fläche, wandernder Bass, tiefe Schläge. Das Motiv spricht den Namen: Le-o-ti-o, Stu-di-os. Klavier und Glaston.',drone=0.25,pad=0.5,bass=['D','B','G','A','G'],pre='A',motiv=NAME,pianog=0.9,glassg=0.35),
 dict(nr=2,name='Signal',text='Fast leer: nur tiefe Schläge und ein Hauch Fläche, dann 5 klare Glastöne. Am nächsten am Telekom-Prinzip.',drone=0.0,pad=0.25,bass=['D','D','D','D','D'],pre='A',bassg=0.25,motiv=[(0.0,74,0.3),(0.22,74,0.3),(0.44,69,0.3),(0.75,78,0.4),(1.05,74,1.2)],glassg=0.7,pianog=0.3,endpad=0.6),
 dict(nr=3,name='Puls',text='Elektronisch: Die Fläche atmet im Takt, feines Ticken. Motiv steigt in 4 Tönen auf.',drone=0.3,pad=0.6,pump=True,bass=['D','D','Bb','C','Bb'],pre='C',motiv=[(0.0,62,0.4),(0.33,69,0.4),(0.66,74,0.4),(0.99,78,1.3)],glassg=0.55,pianog=0.5),
 dict(nr=4,name='Tief',text='Dunkel und schwer, sehr tiefer Bass. Öffnet sich erst am Schluss. Motiv: 3 Töne am Klavier.',drone=0.6,pad=0.0,bass=['D','D','Bb','G','A'],pre='A',bassg=0.7,hitg=1.15,motiv=[(0.0,62,0.6),(0.45,69,0.6),(0.9,74,1.5)],pianog=1.0,glassg=0.15,hall=1.8),
 dict(nr=5,name='Hybrid',text='Moderne Fläche und Schläge, am Schluss kommen leise echte Streicher dazu. Motiv fällt und kehrt zurück.',drone=0.25,pad=0.55,bass=['D','G','B','G','E'],pre='A',str=0.45,motiv=[(0.0,78,0.4),(0.3,76,0.4),(0.6,74,0.4),(0.9,69,0.4),(1.2,74,1.3)],pianog=0.8,glassg=0.3),
 dict(nr=6,name='Weit',text='Viel Raum und Hall, weiche Fläche ohne Dröhnen. Motiv in 5 Tönen, hell und schwebend.',drone=0.0,pad=0.8,bass=['D','G','D','G','Bb'],pre='C',bassg=0.35,hitg=0.8,motiv=[(0.0,69,0.35),(0.28,71,0.35),(0.56,74,0.35),(0.84,78,0.5),(1.25,74,1.3)],pianog=0.6,glassg=0.5,okt=0,hall=1.5),
]
if __name__=='__main__':
    for K in KOMP:
        S=build(K); wavfile.write(f"{OUT}/mod{K['nr']:02d}.wav",SR,(S*32767).astype(np.int16)); print(K['nr'],K['name'],flush=True)
    json.dump([{k:K[k] for k in ('nr','name','text')} for K in KOMP],open(f'{OUT}/mod.json','w'),ensure_ascii=False)
