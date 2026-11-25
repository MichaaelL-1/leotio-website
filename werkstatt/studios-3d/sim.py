# Leotio Studios Puder-Simulation v1.5 · 25.11.2026: 12 Explosionen aus der Hoehe, Luftwiderstand, Absetzen in Rillen, Ablage-Karten
import numpy as np, os, sys
from PIL import Image
from scipy.ndimage import gaussian_filter
OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True)
PAL=os.environ.get('PAL','#E3A21A,#2F8FC4,#23379A,#7B3F98,#CC2E2A').split(',')
hx=lambda c: np.array([int(c[i:i+2],16) for i in (1,3,5)],np.float32)/255
pal=np.array([hx(c) for c in PAL])
FPS=int(os.environ.get('FPS','24')); DUR=float(os.environ.get('DUR','10')); NF=int(DUR*FPS); SUB=8; dt=1/(FPS*SUB)
NP=int(os.environ.get('NP','130000'))
U=0.01; D=0.035; w=7.881; R=1024
rng=np.random.default_rng(3)
# Hoehenfeld (Rillen = -D) auf [-1,1]^2, Bildzeile 0 = y=+1 (oben)
def grooves():
    g=np.zeros((R,R),bool)
    L=[[0,0,200,w],[0,200-w,200,w],[0,0,w,200],[200-w,0,w,200],[54.638,0,w,145.362],[54.638,137.481,145.362,w]]
    for x,y,ww,hh in L:
        g[int(y/200*R):int((y+hh)/200*R), int(x/200*R):int((x+ww)/200*R)]=True
    return g
G=grooves()
def hgt(x,y):
    i=np.clip(((1-y)/2*R).astype(int),0,R-1); j=np.clip(((x+1)/2*R).astype(int),0,R-1)
    return np.where(G[i,j],-D,0.0)
# Explosionen: jitter-Raster 4x3, zeitlich gestaffelt
cells=[(cx,cy) for cy in (-0.6,0.0,0.6) for cx in (-0.66,-0.22,0.22,0.66)]
order=rng.permutation(len(cells))
EX=[]
for n,ci in enumerate(order):
    cx,cy=cells[ci]
    t0=1.1+n*0.33+rng.uniform(-0.08,0.08)
    EX.append(dict(p=np.array([cx+rng.uniform(-0.2,0.2),cy+rng.uniform(-0.2,0.2)]),t=t0,c=n%len(pal),lob=int(rng.integers(5,11)),phi=rng.uniform(0,6.3)))
if os.environ.get('ONE'):   # Einzelne Explosion fuer Nahaufnahme: ONE=x,y,t,farbindex
    x_,y_,t_,c_=os.environ['ONE'].split(',')
    EX=[dict(p=np.array([float(x_),float(y_)]),t=float(t_),c=int(c_),lob=7,phi=0.4)]
print('Explosionen', [(round(e['t'],2),e['c']) for e in EX])
NE=len(EX); N=NE*NP
pos=np.zeros((N,3),np.float32); vel=np.zeros((N,3),np.float32)
eid=np.repeat(np.arange(NE),NP); col_i=np.array([EX[e]['c'] for e in eid])
# Farbstreuung je Teilchen (leicht heller/dunkler, Nachbarfarbe beigemischt)
pcol=pal[col_i]*rng.uniform(0.96,1.04,(N,1)).astype(np.float32)
k=np.where(rng.random(N)<0.45, rng.uniform(2.5,10,N), rng.uniform(14,34,N)).astype(np.float32)          # Luftwiderstand: grob .. fein
state=np.zeros(N,np.int8)   # 0 wartet, 1 fliegt, 2 liegt
rad=np.where(k>12, rng.uniform(0.0012,0.0024,N), rng.uniform(0.0009,0.0016,N)).astype(np.float32)
# Ablage
acc=np.zeros((R,R,3),np.float32); thick=np.zeros((R,R),np.float32)
def deposit(idx):
    if len(idx)==0: return
    x=pos[idx,0]; y=pos[idx,1]
    i=np.clip(((1-y)/2*R).astype(int),0,R-1); j=np.clip(((x+1)/2*R).astype(int),0,R-1)
    m=(0.6+k[idx]*0.04)
    np.add.at(thick,(i,j),m)
    for q in range(3): np.add.at(acc[...,q],(i,j),pcol[idx,q]*m)
def turb(p,t):
    x,y,z=p[:,0],p[:,1],p[:,2]
    return np.stack([np.sin(3.1*y+1.7*z+t*1.3)+0.5*np.sin(7.3*z-2*t),
                     np.sin(2.7*x-1.9*z-t*1.1)+0.5*np.sin(6.1*x+t*1.7),
                     0.4*np.sin(2.3*x+3.1*y+t)],1).astype(np.float32)
CAMZ0=2.0*1920/560*50/36
FALL=7.0   # Fallgeschwindigkeit des Pakets m/s
for f in range(NF):
    t=f/FPS
    for s in range(SUB):
        ts=t+s*dt
        # Zuendung
        for e,E in enumerate(EX):
            if E['t']<=ts and E['t']>ts-dt:
                sl=slice(e*NP,(e+1)*NP)
                n=NP
                th=rng.uniform(0,2*np.pi,n);
                spike=1+2.5*np.abs(np.sin(E['lob']*th/2+E['phi']))**10      # Strahlen wie bei echtem Puder
                reach=rng.gamma(2.5,0.09,n)*spike                          # Reichweite in m
                sp=reach*k[sl]
                up=rng.gamma(2.0,0.06,n)*k[sl]
                vel[sl,0]=np.cos(th)*sp; vel[sl,1]=np.sin(th)*sp; vel[sl,2]=up
                vel[sl,2]+= -FALL*0.15
                pos[sl,0]=E['p'][0]+rng.normal(0,0.02,n); pos[sl,1]=E['p'][1]+rng.normal(0,0.02,n); pos[sl,2]=0.01
                state[sl]=1
        fl=state==1
        if fl.any():
            v=vel[fl]; p=pos[fl]; kk=k[fl][:,None]
            v=v*np.exp(-kk*dt)
            v[:,2]-=9.81*dt
            v+= turb(p,ts)*0.6*dt*kk*0.3
            p=p+v*dt
            # unsichtbare Wand am Quadratrand: aussen bleibt sauber
            lim=0.99*(1-np.maximum(p[:,2],0)/CAMZ0)     # Rand in Bildprojektion: auch hohe Teilchen bleiben im Quadrat
            for a in (0,1):
                o=np.abs(p[:,a])>lim
                p[o,a]=np.sign(p[o,a])*lim[o]; v[o,a]*=-0.3
            pos[fl]=p; vel[fl]=v
            idx=np.nonzero(fl)[0]
            landed=idx[pos[idx,2]<=hgt(pos[idx,0],pos[idx,1])]
            deposit(landed); state[landed]=2
    # Ausgabe: fliegende Teilchen + fallende Pakete
    fl=np.nonzero(state==1)[0]
    P=[pos[fl]]; C=[pcol[fl]]; RR=[rad[fl]]
    for e,E in enumerate(EX):
        dtm=E['t']-t
        if 0<dtm<0.7:
            m=2500; sl=np.arange(e*NP,e*NP+m)
            jit=rng.normal(0,1,(m,3)).astype(np.float32)*np.array([0.03,0.03,0.03+dtm*0.08],np.float32)
            zz=FALL*dtm; CAMZ=2.0*1920/560*50/36
            pp=np.concatenate([np.tile(E['p']*(1-zz/CAMZ),(m,1)),np.full((m,1),zz)],1).astype(np.float32)+jit   # faellt auf der Sichtachse: Einschlag genau an der Stelle
            P.append(pp); C.append(pcol[sl]); RR.append(np.full(m,0.004,np.float32))
    P=np.concatenate(P); C=np.concatenate(C); RR=np.concatenate(RR)
    np.savez(f'{OUT}/pts_{f:04d}.npz',p=P.astype(np.float32),c=C.astype(np.float16),r=RR.astype(np.float16))
    # Ablage-Karten
    th=gaussian_filter(thick,1.4)+0.6*gaussian_filter(thick,14); cc=np.stack([gaussian_filter(acc[...,q],1.4)+0.6*gaussian_filter(acc[...,q],14) for q in range(3)],-1)
    colr=cc/np.maximum(th,1e-4)[...,None]
    cov=1-np.exp(-th/0.10)
    rgba=np.concatenate([np.clip(colr,0,1),cov[...,None]],-1)
    Image.fromarray((rgba*255).astype(np.uint8),'RGBA').save(f'{OUT}/dep_{f:04d}.png')
    hh=np.clip(gaussian_filter(thick,1.2)/6.0,0,1)
    Image.fromarray((hh*65535).astype(np.uint16)).save(f'{OUT}/hgt_{f:04d}.png')
    if f%24==0: print(f,'fliegt',len(fl),'liegt',int((state==2).sum()),'bedeckt',float((cov>0.9).mean()),flush=True)
print('fertig')
