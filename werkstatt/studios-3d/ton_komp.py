# Leotio Studios Kompositionen v1.0 · 25.11.2026: 10 Fassungen aus Orchester-Bausteinen auf dem Takt (takt.json). Aufruf: ton_komp.py <Bausteine> <Zielordner>
import numpy as np, sys, json, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
SRC=sys.argv[1]; OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
TK=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'takt.json')))
SR=48000; DUR=TK['dauer']; N=int(SR*DUR); HITS=TK['hits']; TC=TK['clear']; TE=TK['schluss']
HT=[h['t'] for h in HITS]
def load(k):
    sr,a=wavfile.read(f'{SRC}/{k}.wav'); assert sr==SR; a=a.astype(np.float64)/32768; return a/np.abs(a).max()
B={k:load(k) for k in ('strmin','strmaj','vln','horn','bell','pauke','chor','hit','chord','rise')}
# gemessene Tonhoehen der Bausteine: strmin/strmaj = D-Dur, vln/horn = C4, bell = A4, pauke = C2, chor/chord/rise = A
def pitch(a,st):
    f=2**(st/12); n=int(len(a)/f); x=np.linspace(0,len(a)-1,n); i=np.arange(len(a))
    return np.stack([np.interp(x,i,a[:,c]) for c in range(2)],1)
def env(a,att,rel,cres=0.0):
    n=len(a); t=np.arange(n)/SR; e=np.minimum(t/max(att,1e-3),1)*np.minimum((n/SR-t)/max(rel,1e-3),1)
    if cres: e=e*(1-cres+cres*(t/(n/SR))**1.5)
    return a*np.clip(e,0,1)[:,None]
def cut(a,t0,d): return a[int(t0*SR):int((t0+d)*SR)]
class Mix:
    def __init__(s): s.S=np.zeros((N,2))
    def add(s,sig,t,g=1.0,pan=0.0):
        i=int(t*SR)
        if i<0: sig=sig[-i:]; i=0
        x=sig[:max(0,N-i)]*g
        s.S[i:i+len(x),0]+=x[:,0]*(1-max(pan,0)*0.5); s.S[i:i+len(x),1]+=x[:,1]*(1+min(pan,0)*0.5)
def major(root,d,cres=0.3):     # echter Streicherakkord (D-Dur) auf anderen Grundton verschoben; root = Halbtoene ueber/unter D
    a=pitch(B['strmin'],root); return env(cut(a,0.6/2**(root/12),d),0.22,0.55,cres)
def note(inst,midi,d,att=0.02,rel=0.25):
    base={'vln':60,'horn':60,'bell':69}[inst]; a=pitch(B[inst],midi-base)
    off=0.0 if inst=='bell' else 0.08
    return env(cut(a,off,d),att,rel)
def minor(root_midi,d,cres=0.3):  # Mollakkord aus einzelnen Streichertoenen geschichtet
    out=np.zeros((int(d*SR),2))
    for st,g in ((-12,0.9),(0,0.8),(3,0.6),(7,0.6),(12,0.45)):
        x=env(cut(pitch(B['vln'],root_midi+st-60),0.25,d),0.22,0.55,cres); out[:len(x)]+=x*g
    return out*0.55
RT={'D':0,'G':5,'A':-5,'Bb':-4,'C':-2,'F':3,'E':2}; RM={'Dm':50,'Bm':47,'Em':52,'Gm':55,'F#m':54,'Am':57}
def chordsig(name,d,cres=0.3): return major(RT[name],d,cres) if name in RT else minor(RM[name],d,cres)
rng=np.random.default_rng(4)
def build(K):
    M=Mix()
    seq=K['bed']; times=[0.25]+HT[1:]+[K.get('pre_t',TC+0.5),TE]     # Akkordwechsel: Anfang, Schlag 2..5, Vorhalt, Schluss
    names=seq+[K['pre']]
    for i,nm in enumerate(names):
        t0=times[i]; t1=times[i+1]; d=t1-t0+0.45
        M.add(chordsig(nm,d,0.35),t0-0.12,K.get('bedg',0.5))
    # Schlaege: weich und tief, grosser Schlag staerker
    for i,h in enumerate(HITS):
        g=h.get('sc',1.5)/2.0; big=(i==4)
        M.add(pitch(B['pauke'],2),h['t']-0.004,(0.75 if big else 0.5)*g*K.get('hitg',1.0),h['p'][0]*0.4)
        M.add(B['hit'],h['t']-0.004,(0.5 if big else 0.16)*K.get('hitg',1.0),h['p'][0]*0.4)
        t=np.arange(int(1.8*SR))/SR; n=sosfilt(butter(2,[900,5000],btype='band',fs=SR,output='sos'),rng.standard_normal(len(t)))*np.exp(-t*2.4)*np.minimum(t/0.012,1)
        M.add(np.stack([n,n],1),h['t'],0.035,h['p'][0]*0.7)
    # Aufschwung (auf A) in den Schluss, Chor als Dominante
    r=B['rise'][int(3.4*SR):]; r=r/np.abs(r).max(); r=r*(np.linspace(0,1,len(r))**1.5)[:,None]
    M.add(pitch(r,RT[K['pre']]+5) if K['pre'] in RT else r,TE-len(r)/SR/2**((RT.get(K['pre'],-5)+5)/12),0.4)
    if K.get('chor',True):
        c=pitch(B['chor'],RT.get(K['pre'],-5)+5); c=env(cut(c,1.0,2.9),1.2,0.35,0.5); M.add(c,TE-2.75,0.5)
    # Schlussakkord D-Dur: Streicher + volles Orchester + Chor
    M.add(env(cut(B['strmaj'],1.7,DUR-TE+0.2),0.05,1.4),TE-0.02,0.8)
    M.add(env(cut(B['strmin'],0.6,DUR-TE+0.2),0.05,1.4),TE-0.02,0.5)
    co=pitch(B['chord'],-7); M.add(env(cut(co,1.15*2**(7/12),DUR-TE+0.2),0.03,1.4),TE-0.02,0.55*K.get('tutti',1.0))
    if K.get('chorend',True): M.add(env(cut(pitch(B['chor'],5),1.9/2**(5/12),DUR-TE),0.25,1.3),TE,0.4)
    M.add(pitch(B['pauke'],2),TE-0.004,0.6)
    # Motiv
    for inst,g in K['inst']:
        for (dt,midi,d) in K['motiv']:
            M.add(note(inst,midi+(0 if inst!='horn' else -12),d,0.015 if inst!='vln' else 0.05,min(0.3,d*0.5)),TE+dt,g*K.get('motg',1.0))
    S=M.S
    tl=np.arange(int(2.2*SR))/SR; out=S.copy()
    for c,sd in ((0,1),(1,2)):
        ir=sosfilt(butter(2,[200,6000],btype='band',fs=SR,output='sos'),np.random.default_rng(sd).standard_normal(len(tl))*np.exp(-tl*2.6))
        out[:,c]+=fftconvolve(S[:,c],ir)[:N]*0.006
    f=np.ones(N); k=int(1.3*SR); f[-k:]=np.linspace(1,0,k)**2; out*=f[:,None]
    return np.tanh(out/np.abs(out).max()*1.4)/np.tanh(1.4)*0.89
# Motive: (Zeit relativ zum Schlussakkord, MIDI-Ton, Dauer). D4=62, A4=69, D5=74, F#5=78, A5=81
KOMP=[
 dict(nr=1,name='Leotio Studios',text='Das Motiv spricht den Namen: 4 Töne für Le-o-ti-o, 3 für Stu-di-os. Warm, D-Dur.',bed=['D','Bm','G','A','G'],pre='A',inst=[('bell',0.5),('vln',0.35)],
      motiv=[(-0.90,69,0.5),(-0.60,66,0.5),(-0.30,64,0.5),(0.0,62,0.9),(0.55,62,0.5),(0.85,69,0.5),(1.15,74,1.5)]),
 dict(nr=2,name='Aufgang',text='Große Kino-Wendung über B und C nach D. Motiv steigt in vier Tönen auf, Horn und Streicher.',bed=['D','D','Bb','C','Bb'],pre='C',inst=[('horn',0.55),('vln',0.4)],
      motiv=[(0.0,62,0.6),(0.33,69,0.6),(0.66,74,0.6),(0.99,78,1.6)]),
 dict(nr=3,name='Heimkehr',text='Ruhig und warm. Motiv fällt und kehrt zurück, mit Glocke.',bed=['D','G','Bm','G','Em'],pre='A',inst=[('bell',0.55)],
      motiv=[(0.0,78,0.6),(0.3,76,0.6),(0.6,74,0.6),(0.9,69,0.6),(1.2,74,1.5)]),
 dict(nr=4,name='Ins Licht',text='Beginnt in Moll, öffnet sich am Schluss nach Dur. Motiv: Hornruf in drei Tönen.',bed=['Dm','Bb','F','C','Gm'],pre='A',inst=[('horn',0.6),('vln',0.3)],
      motiv=[(0.0,62,0.7),(0.45,69,0.7),(0.9,74,1.6)]),
 dict(nr=5,name='Weite',text='Viel Ruhe, lange Streicherflächen. Motiv in fünf Tönen, hell und schwebend.',bed=['D','G','D','G','Bb'],pre='C',inst=[('bell',0.45),('vln',0.3)],hitg=0.8,
      motiv=[(0.0,69,0.5),(0.28,71,0.5),(0.56,74,0.5),(0.84,78,0.6),(1.25,74,1.5)]),
 dict(nr=6,name='Feier',text='Hell und festlich. Motiv ist eine kurze Fanfare im Dreiklang.',bed=['D','A','Bm','G','D'],pre='A',inst=[('horn',0.6),('bell',0.3)],
      motiv=[(0.0,62,0.35),(0.2,66,0.35),(0.4,69,0.35),(0.6,74,1.7)]),
 dict(nr=7,name='Kino',text='Ernst und spannungsvoll, der große Schlag sitzt auf der Dominante. Motiv: drei Töne nach Hause.',bed=['Dm','Dm','Bb','Gm','A'],pre='A',inst=[('vln',0.55),('horn',0.35)],
      motiv=[(0.0,78,0.7),(0.42,76,0.7),(0.84,74,1.7)]),
 dict(nr=8,name='Schwebend',text='Beginnt offen auf G, findet erst am Schluss den Grundton. Glockenmotiv in vier Tönen.',bed=['G','D','Em','Bm','C'],pre='A',inst=[('bell',0.55)],hitg=0.85,
      motiv=[(0.0,74,0.5),(0.3,81,0.5),(0.6,78,0.5),(0.9,74,1.6)]),
 dict(nr=9,name='Signal',text='Am nächsten am Telekom-Prinzip: fünf klare Töne, kurz und merkbar, aber weich gespielt.',bed=['D','D','G','G','A'],pre='A',inst=[('bell',0.6)],chor=False,chorend=False,tutti=0.7,
      motiv=[(0.0,74,0.4),(0.22,74,0.4),(0.44,69,0.4),(0.75,78,0.5),(1.05,74,1.5)]),
 dict(nr=10,name='Hymne',text='Getragen, wie ein Schlusschoral. Motiv steigt in Schritten und landet auf dem Grundton.',bed=['D','Bm','F#m','G','Em'],pre='A',inst=[('vln',0.5),('horn',0.4)],
      motiv=[(0.0,69,0.55),(0.33,74,0.55),(0.66,76,0.55),(0.99,78,0.6),(1.4,74,1.5)]),
]
if __name__=='__main__':
    for K in KOMP:
        S=build(K); wavfile.write(f"{OUT}/komp{K['nr']:02d}.wav",SR,(S*32767).astype(np.int16)); print(K['nr'],K['name'],flush=True)
    json.dump([{k:K[k] for k in ('nr','name','text')} for K in KOMP],open(f'{OUT}/komp.json','w'),ensure_ascii=False)
