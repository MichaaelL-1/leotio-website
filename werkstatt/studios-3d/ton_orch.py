# Leotio Studios Ton Orchester v1.0 · 25.11.2026: Orchester-Bausteine (hit, chord, rise als WAV) werden auf den Takt (takt.json) gesetzt
import numpy as np, sys, json, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SRC=sys.argv[1]; OUT=sys.argv[2]
TK=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'takt.json')))
SR=48000; DUR=TK['dauer']; N=int(SR*DUR); HITS=TK['hits']; TC=TK['clear']; TE=TK['schluss']; BEAT=60/TK['bpm']
def load(k):
    sr,a=wavfile.read(f'{SRC}/{k}.wav'); assert sr==SR; return a.astype(np.float64)/32768
hit=load('hit'); chord=load('chord'); rise=load('rise')
S=np.zeros((N,2))
def add(sig,t,g=1.0,pan=0.0):
    i=int(t*SR)
    if i<0: sig=sig[-i:]; i=0
    s=sig[:max(0,N-i)]*g
    S[i:i+len(s),0]+=s[:,0]*(1-max(pan,0)*0.6); S[i:i+len(s),1]+=s[:,1]*(1+min(pan,0)*0.6)
def pitch(a,f):   # f<1 tiefer und laenger
    n=int(len(a)/f); x=np.linspace(0,len(a)-1,n); return np.stack([np.interp(x,np.arange(len(a)),a[:,c]) for c in range(2)],1)
def onset(a,th=0.1):
    m=np.abs(a).max(1); h=SR//200; e=np.array([m[i:i+h].max() for i in range(0,len(m),h)]); return int(np.argmax(e>th*e.max()))*h
hit=hit[onset(hit,0.05):]; hit/=np.abs(hit).max()
F=[1.0,1.06,1.12,0.97,0.84]; G=[0.85,0.75,0.65,0.72,1.0]
for h,f,g in zip(HITS,F,G): add(pitch(hit,f),h['t']-0.004,g,h['p'][0]*0.5)
for k in range(3): add(pitch(hit,1.35)[:int(0.5*SR)]*np.linspace(1,0,int(0.5*SR))[:,None],HITS[4]['t']-BEAT*(3-k)/4,0.12+0.07*k,(-0.4,0.4,0.0)[k])   # Wirbel zum grossen Schlag
# Aufschwung vor dem Schluss: lauter Teil des Risers endet genau auf dem Schlussakkord
r=rise[int(3.4*SR):]; r=r/np.abs(r).max(); L=len(r); r=r*(np.linspace(0,1,L)**1.5)[:,None]
add(r,TE-L/SR,0.55)
co=onset(chord,0.45); c=chord[max(0,co-int(0.03*SR)):]; c/=np.abs(c).max()
add(c,TE-0.03,0.95)
add(pitch(hit,0.84),TE-0.004,0.55)                          # Pauke unter dem Schlussakkord
# Puder: leises Rauschen nach jedem Schlag
rng=np.random.default_rng(4)
for h in HITS:
    t=np.arange(int(1.8*SR))/SR; n=sosfilt(butter(2,[900,5000],btype='band',fs=SR,output='sos'),rng.standard_normal(len(t)))*np.exp(-t*2.4)*np.minimum(t/0.012,1)
    add(np.stack([n,n],1),h['t'],0.05,h['p'][0]*0.7)
f=np.ones(N); k=int(1.2*SR); f[-k:]=np.linspace(1,0,k)**2; S*=f[:,None]
S=np.tanh(S/np.abs(S).max()*1.5)/np.tanh(1.5)*0.89
wavfile.write(OUT,SR,(S*32767).astype(np.int16)); print(OUT)
