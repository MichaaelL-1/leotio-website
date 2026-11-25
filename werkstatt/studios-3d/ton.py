# Leotio Studios Ton v1.0 · 25.11.2026: Einschlaege aus der Simulation + Jingle (modern | klassisch), alles synthetisch
import numpy as np, sys
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
MODE=sys.argv[1]; OUT=sys.argv[2]
SR=48000; DUR=12.0; N=int(SR*DUR); SLOW=1.5
# Explosionszeiten wie sim.py (Seed 3, NEX=10, GAP=0.28)
rng=np.random.default_rng(3)
cells=[(cx,cy) for cy in (-0.6,0.0,0.6) for cx in (-0.66,-0.22,0.22,0.66)]
order=rng.permutation(12); EX=[]
for n,ci in enumerate(order[:10]):
    cx,cy=cells[ci]; t0=1.1+n*0.28*12/10+rng.uniform(-0.08,0.08)
    x=cx+rng.uniform(-0.2,0.2); rng.uniform(-0.2,0.2); rng.integers(5,11); rng.uniform(0,6.3)
    EX.append((t0*SLOW,x,n%5))
print([(round(t,2),c) for t,x,c in EX])
r2=np.random.default_rng(11)
L=np.zeros(N); R=np.zeros(N)
def add(sig,t,pan=0.0,g=1.0):
    i=int(t*SR); 
    if i>=N: return
    s=sig[:N-i]*g; a=(pan+1)/2*np.pi/2
    L[i:i+len(s)]+=s*np.cos(a); R[i:i+len(s)]+=s*np.sin(a)
def bp(x,lo,hi):
    return sosfilt(butter(2,[lo,hi],btype='band',fs=SR,output='sos'),x)
def thud():
    t=np.arange(int(0.7*SR))/SR; f=45+60*np.exp(-t*18)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*6)*np.minimum(t/0.004,1)
def puff():
    t=np.arange(int(1.8*SR))/SR; n=r2.standard_normal(len(t))
    a=bp(n,900,5000)*np.exp(-t*2.6)+bp(n,200,900)*np.exp(-t*5)*0.8
    return a*np.minimum(t/0.012,1)
def fall():
    t=np.arange(int(0.55*SR))/SR; n=r2.standard_normal(len(t))
    return bp(n,500,2500)*(t/0.55)**3*0.5
def tone(f,d,kind):
    t=np.arange(int(d*SR))/SR
    if kind=='pluck':   # klavier-/harfenartig
        s=sum(np.sin(2*np.pi*f*k*t*(1+0.0004*k*k))*np.exp(-t*(1.6+0.9*k))/k**1.3 for k in range(1,9))
        return s*np.minimum(t/0.003,1)
    if kind=='bell':
        s=sum(a*np.sin(2*np.pi*f*r*t)*np.exp(-t*dc) for r,a,dc in ((1,1,1.5),(2.0,0.5,2.5),(3.01,0.25,4),(4.2,0.12,6)))
        return s*np.minimum(t/0.004,1)
    if kind=='pad':
        s=sum(np.sin(2*np.pi*f*dt*t+ph)*(1/k) for dt,ph,k in ((1,0,1),(1.004,1,1),(0.996,2,1),(2.002,0.5,3),(3.0,1.5,6)))
        env=np.minimum(t/(d*0.35),1)*np.minimum((d-t)/(d*0.3),1)
        return s*env
    if kind=='sub':
        return np.sin(2*np.pi*f*t)*np.exp(-t*1.2)*np.minimum(t/0.01,1)
m=lambda n: 440*2**((n-69)/12)
for t,x,c in EX:
    add(fall(),t-0.55,x,0.35); add(thud(),t,x*0.5,0.9); add(puff(),t,x,0.22)
END=11.0
if MODE=='modern':
    # jede Farbe hat ihren Ton (D-Dur-Pentatonik): Gelb D, Coelin E, Ultramarin F#, Violett A, Rot H
    PENT=[62,64,66,69,71]
    for t,x,c in EX: add(tone(m(PENT[c]+12),2.5,'bell'),t,x,0.16)
    for n_,g in ((38,0.5),(50,0.35),(57,0.3),(62,0.22),(66,0.18),(69,0.12)): add(tone(m(n_),10.6,'pad'),0.2,0,g*0.16)
    # Motiv am Ende: A - F# - E - D (Auflösung), darunter Sub
    for k,(n_,dt) in enumerate(((69,0),(66,0.32),(64,0.64),(74,1.02))):
        add(tone(m(n_),3.0,'bell'),END-1.4+dt,(-0.3,0.3,-0.15,0)[k],0.34)
        add(tone(m(n_-12),3.0,'pluck'),END-1.4+dt,0,0.22)
    add(tone(m(26),2.6,'sub'),END-0.38,0,0.8); add(thud(),END-0.38,0,0.8)
    for n_ in (50,57,62,66,69,76): add(tone(m(n_),1.6,'pad'),END-0.38,0,0.06)
else:
    # Bach, Praeludium C-Dur BWV 846 (gemeinfrei), Takte 1-4, neu gesetzt
    BARS=[(60,64,67,72,76),(60,62,69,74,77),(59,62,67,74,77),(60,64,67,72,76)]
    BAR=2.5; st=BAR/16; t0=0.35
    for b,ch in enumerate(BARS):
        for h in range(2):
            for i,k in enumerate((0,1,2,3,4,2,3,4)):
                tt=t0+b*BAR+h*BAR/2+i*st
                add(tone(m(ch[k]),2.8 if i<2 else 1.6,'pluck'),tt,(-0.25,-0.1,0.05,0.15,0.25)[k],0.30 if i<2 else 0.22)
    te=t0+4*BAR+0.1
    for i,n_ in enumerate((36,48,55,60,64,67,72)): add(tone(m(n_),3.2,'pluck'),te+i*0.035,0,0.3)
    add(tone(m(24),2.4,'sub'),te,0,0.5)
    for n_,g in ((36,0.4),(48,0.3),(55,0.2)): add(tone(m(n_),11,'pad'),0.2,0,g*0.08)
# Hall
tl=np.arange(int(2.2*SR))/SR
def rev(x,seed):
    ir=np.random.default_rng(seed).standard_normal(len(tl))*np.exp(-tl*2.8); ir=bp(ir,150,7000)
    return fftconvolve(x,ir)[:N]*0.012
L2=L+rev(L,1)*1.0; R2=R+rev(R,2)*1.0
S=np.stack([L2,R2],1)
f=np.ones(N); k=int(0.9*SR); f[-k:]=np.linspace(1,0,k)**2; S*=f[:,None]
S=np.tanh(S/np.abs(S).max()*1.6)/np.tanh(1.6)*0.89
wavfile.write(OUT,SR,(S*32767).astype(np.int16)); print(OUT)
