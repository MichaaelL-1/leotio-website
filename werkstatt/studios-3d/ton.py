# Leotio Studios Ton v2.0 · 25.11.2026: Takt (takt.json) steuert Ton und Animation. Varianten: trommel | klavier | puls. Alles synthetisch, rechtefrei.
import numpy as np, sys, json, os
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
MODE=sys.argv[1]; OUT=sys.argv[2]
TK=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'takt.json')))
SR=48000; DUR=TK['dauer']; N=int(SR*DUR); HITS=TK['hits']; TC=TK['clear']; TE=TK['schluss']; BEAT=60/TK['bpm']
r2=np.random.default_rng(11); L=np.zeros(N); R=np.zeros(N)
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR)
    if i<0: sig=sig[-i:]; i=0
    if i>=N: return
    s=sig[:N-i]*g; a=(pan+1)/2*np.pi/2
    L[i:i+len(s)]+=s*np.cos(a); R[i:i+len(s)]+=s*np.sin(a)
def bp(x,lo,hi): return sosfilt(butter(2,[lo,hi],btype='band',fs=SR,output='sos'),x)
def lp(x,f): return sosfilt(butter(2,f,btype='low',fs=SR,output='sos'),x)
def T(d): return np.arange(int(d*SR))/SR
m=lambda n: 440*2**((n-69)/12)
def thud(f0=42,dec=5,d=1.2):
    t=T(d); f=f0+70*np.exp(-t*22); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*dec)*np.minimum(t/0.003,1)
def taiko(f0=70):
    t=T(1.6); f=f0*(1+0.6*np.exp(-t*30)); b=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*4)
    sk=bp(r2.standard_normal(len(t)),300,3000)*np.exp(-t*35)*0.5
    return (b+0.4*np.sin(2*np.pi*np.cumsum(f*1.59)/SR)*np.exp(-t*7)+sk)*np.minimum(t/0.002,1)
def puff(d=2.2):
    t=T(d); n=r2.standard_normal(len(t))
    return (bp(n,900,5000)*np.exp(-t*2.2)+bp(n,200,900)*np.exp(-t*4)*0.8)*np.minimum(t/0.012,1)
def riser(d=0.6,lo=400,hi=3000):
    t=T(d); return bp(r2.standard_normal(len(t)),lo,hi)*(t/d)**3
def air(d):       # Raeumen der Rillen: Luft, die aufgeht
    t=T(d); n=r2.standard_normal(len(t)); u=t/d
    return (bp(n,1500,9000)*np.sin(np.pi*u)**2*0.6+bp(n,300,1500)*np.sin(np.pi*u)**1.5*0.5)
def pluck(f,d=3.0):
    t=T(d); s=sum(np.sin(2*np.pi*f*k*t*(1+0.0004*k*k))*np.exp(-t*(1.2+0.8*k))/k**1.25 for k in range(1,10))
    return s*np.minimum(t/0.003,1)
def bell(f,d=3.0):
    t=T(d); return sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t*dc) for r,a,dc in ((1,1,1.4),(2.0,0.5,2.4),(3.01,0.25,4),(4.2,0.12,6)))*np.minimum(t/0.004,1)
def pad(f,d,att=0.35,rel=0.3):
    t=T(d); s=sum(np.sin(2*np.pi*f*dt*t+ph)/k for dt,ph,k in ((1,0,1),(1.004,1,1),(0.996,2,1),(2.002,0.5,3),(3.0,1.5,6)))
    return s*np.minimum(t/(d*att),1)*np.minimum((d-t)/(d*rel),1)
def saw(f,d,cut=900,dec=3):
    t=T(d); s=sum(np.sin(2*np.pi*f*k*t)/k for k in range(1,14)); return lp(s,cut)*np.exp(-t*dec)*np.minimum(t/0.005,1)
def sub(f,d=2.6): t=T(d); return np.sin(2*np.pi*f*t)*np.exp(-t*1.1)*np.minimum(t/0.01,1)
PAN=[h['p'][0]*0.7 for h in HITS]
# gemeinsam: jedes Paket = fallendes Rauschen, das genau auf dem Schlag endet, dann der Puder
for h,p in zip(HITS,PAN):
    g=h.get('sc',1.5)/2.0
    add(riser(0.62),h['t']-0.62,p,0.30*g); add(puff(),h['t'],p,0.20*g)
add(air(TE-TC),TC,0,0.16)
if MODE=='trommel':     # episch: grosse Trommeln, tiefer Bass, Streicherflaeche in d-Moll
    for i,(h,p) in enumerate(zip(HITS,PAN)):
        g=h.get('sc',1.5)/2.0
        add(taiko(62 if i<4 else 50),h['t'],p*0.5,1.0*g); add(thud(),h['t'],0,0.7*g)
    add(taiko(80),HITS[3]['t']-BEAT/4,0.2,0.35)                         # Vorschlag vor dem 4. Schlag
    for k in range(4): add(taiko(90),HITS[4]['t']-BEAT*(4-k)/4,(-0.4,0.4,-0.2,0.2)[k],0.18+0.08*k)   # Wirbel zum 5.
    CH=[(38,50,57,62,65),(34,46,53,58,62),(41,53,57,60,65),(36,48,55,60,64),(38,50,57,62,65,69)]     # d - B - F - C - d
    for i,h in enumerate(HITS):
        te=HITS[i+1]['t'] if i<4 else TE
        for n_ in CH[i]: add(pad(m(n_),te-h['t']+0.6,0.15,0.4),h['t'],0,0.05)
    for n_ in (38,50,57,62,66,69,74): add(pad(m(n_),DUR-TE,0.08,0.6),TE,0,0.07)      # Schluss: D-Dur, hell
    add(taiko(50),TE,0,0.9); add(sub(m(26)),TE,0,0.7)
    for k,n_ in enumerate((62,69,74,78)): add(bell(m(n_)),TE+k*0.09,(-0.3,0.3,-0.1,0.1)[k],0.12)
elif MODE=='klavier':   # klassisch: Fluegel, jeder Schlag ein Akkord, Kadenz in C-Dur, dazu Kontrabass
    CH=[(36,48,55,60,64),(33,45,57,60,64),(29,41,53,57,60),(31,43,55,59,62),(31,43,53,59,62,65)]     # C - a - F - G - G7
    for i,(h,p) in enumerate(zip(HITS,PAN)):
        g=0.75+0.25*h.get('sc',1.5)/2.0
        for n_ in CH[i]: add(pluck(m(n_),3.5),h['t'],p*0.3,0.26*g)
        add(thud(38,7,0.8),h['t'],0,0.45*g)
    # Lauf zwischen den Schlaegen (Sechzehntel aus dem Akkord), leise
    for i in range(4):
        t0=HITS[i]['t']; t1=HITS[i+1]['t']; st=BEAT/4; k=1
        while t0+k*st<t1-0.05:
            n_=CH[i][1+(k%4)]+12; add(pluck(m(n_),1.2),t0+k*st,(-0.3,0.3)[k%2],0.07); k+=1
    for k in range(int((TE-HITS[4]['t'])/(BEAT/2))):                    # Aufstieg zum Schluss
        add(pluck(m((67,71,74,77,79,83,86,89)[k%8]),1.5),HITS[4]['t']+BEAT/2*(k+1)-BEAT/2,0,0.08+0.012*k)
    for k,n_ in enumerate((24,36,48,55,60,64,67,72,76)): add(pluck(m(n_),4.0),TE+k*0.03,0,0.3)       # C-Dur
    add(sub(m(24)),TE,0,0.5)
else:                    # puls: elektronisch, trocken, jede Farbe ihr Ton (D-Dur-Pentatonik), Bass und Klatscher
    PENT=[62,64,66,69,71]
    def kick():
        t=T(0.5); f=48+120*np.exp(-t*40); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*9)
    def clap():
        t=T(0.35); return bp(r2.standard_normal(len(t)),900,6000)*(np.exp(-t*30)+0.5*np.exp(-np.abs(t-0.02)*200))
    for i,(h,p) in enumerate(zip(HITS,PAN)):
        g=h.get('sc',1.5)/2.0
        add(kick(),h['t'],0,1.0); add(clap(),h['t'],p,0.35*g)
        add(saw(m(PENT[h['c']]-24),1.6,700,2.5),h['t'],0,0.35); add(bell(m(PENT[h['c']]+12),2.5),h['t'],p,0.2)
    k=0; t=HITS[0]['t']                                                  # leiser Achtel-Puls
    while t<TE-0.05:
        add(bp(r2.standard_normal(int(0.05*SR)),5000,11000)*np.exp(-T(0.05)*90),t,(-0.5,0.5)[k%2],0.10 if k%2 else 0.05); t+=BEAT/2; k+=1
    for n_ in (38,50,57,62,66): add(pad(m(n_),TE-0.2,0.5,0.1),0.2,0,0.035)
    add(riser(TE-TC,800,8000),TC,0,0.22)
    add(kick(),TE,0,1.0); add(sub(m(26)),TE,0,0.8)
    for k,n_ in enumerate((69,66,64,74)): add(bell(m(n_)),TE+k*BEAT/4,(-0.3,0.3,-0.15,0)[k],0.3)       # Motiv A-Fis-E-D
    for n_ in (50,57,62,66,69): add(pad(m(n_),DUR-TE,0.05,0.7),TE,0,0.06)
tl=T(2.4)
def rev(x,seed):
    ir=bp(np.random.default_rng(seed).standard_normal(len(tl))*np.exp(-tl*(4.5 if MODE=='puls' else 2.4)),150,7000)
    return fftconvolve(x,ir)[:N]*0.012
S=np.stack([L+rev(L,1),R+rev(R,2)],1)
f=np.ones(N); k=int(1.0*SR); f[-k:]=np.linspace(1,0,k)**2; S*=f[:,None]
S=np.tanh(S/np.abs(S).max()*1.7)/np.tanh(1.7)*0.89
wavfile.write(OUT,SR,(S*32767).astype(np.int16)); print(OUT)
