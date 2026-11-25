# Leotio Studios Puder-Simulation v3.0 · 25.11.2026: echt = Pigment stroemt mit dem Wasser (Advektion entlang der Rillen); 25.11.2026: WMODE=...,echt schreibt Wasserhoehe (wat_) und Faerbung (wtn_) fuer einen echten Wasserkoerper in Blender; takt.json 'pulse' = Zeiten der Wasser-Stoesse; 25.11.2026: WMODE=schwall,schaum,aufprall|flut (Wasser-Varianten); SOFT = feinerer Puder (kleinere Koerner, weichere Ablage), MW = Masse je Korn, WSRC = Wasser aus 2 oder 4 Ecken; Takt-Treffer mit fl (flaechig: Startbreite) und el [Streckung, Winkel Grad]; DUST = Schwebstaub, HT = Aufhellung mit der Hoehe; TAKT=takt.json steuert Zeiten/Orte; VAR=welle|wasser|licht raeumt die Rillen; 12 Explosionen aus der Hoehe, Luftwiderstand, Absetzen in Rillen, Ablage-Karten
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
GS=np.clip(gaussian_filter(G.astype(np.float32),1.5)*1.3,0,1); XS=np.linspace(0,1,R,dtype=np.float32)[None,:]
def hgt(x,y):
    i=np.clip(((1-y)/2*R).astype(int),0,R-1); j=np.clip(((x+1)/2*R).astype(int),0,R-1)
    return np.where(G[i,j],-D,0.0)
# Explosionen: jitter-Raster 4x3, zeitlich gestaffelt
cells=[(cx,cy) for cy in (-0.6,0.0,0.6) for cx in (-0.66,-0.22,0.22,0.66)]
order=rng.permutation(len(cells))
EX=[]
NEX=int(os.environ.get('NEX','12')); SC=float(os.environ.get('SCALE','1.0'))
for n,ci in enumerate(order[:NEX]):
    cx,cy=cells[ci]
    t0=1.1+n*float(os.environ.get('GAP','0.33'))*12/NEX+rng.uniform(-0.08,0.08)
    EX.append(dict(p=np.array([cx+rng.uniform(-0.2,0.2),cy+rng.uniform(-0.2,0.2)]),t=t0,c=n%len(pal),lob=int(rng.integers(5,11)),phi=rng.uniform(0,6.3)))
VAR=os.environ.get('VAR','')
if VAR=='schlag':      # alle Pakete fast gleichzeitig
    for e in EX: e['t']=1.0+float(rng.uniform(0,0.35))
if VAR=='farben':      # Farbe fuer Farbe, je 2 Pakete
    for n,e in enumerate(EX): e['c']=(n//2)%len(pal); e['t']=1.0+(n//2)*0.75+(n%2)*0.12
if os.environ.get('ONE'):   # Einzelne Explosion fuer Nahaufnahme: ONE=x,y,t,farbindex
    x_,y_,t_,c_=os.environ['ONE'].split(',')
    EX=[dict(p=np.array([float(x_),float(y_)]),t=float(t_),c=int(c_),lob=7,phi=0.4)]
if os.environ.get('FUENF'):   # 5 grosse Pakete, jede Farbe einmal: 4 Viertel, zuletzt die Mitte
    G5=float(os.environ.get('GAP','0.9'))
    EX=[dict(p=np.array(p_),t=1.0+n*G5,c=c_,lob=int(rng.integers(6,10)),phi=rng.uniform(0,6.3)) for n,(p_,c_) in enumerate((((-0.42,0.42),0),((0.42,-0.42),1),((-0.42,-0.42),4),((0.42,0.42),3),((0.0,0.0),2)))]
TCLR=None
if os.environ.get('TAKT'):    # Takt-Datei: Zeiten in Video-Sekunden, hier in Simulationszeit umgerechnet
    import json; TK=json.load(open(os.environ['TAKT'])); SL=TK.get('slow',1.5)
    EX=[dict(p=np.array(h['p'],float),t=h['t']/SL,c=h['c'],sc=h.get('sc',1.0),fl=h.get('fl',0.02),el=h.get('el',[1.0,0.0]),lob=int(rng.integers(6,10)),phi=rng.uniform(0,6.3)) for h in TK['hits']]
    TCLR=TK['clear']/SL
print('Explosionen', [(round(e['t'],2),e['c']) for e in EX])
NE=len(EX); N=NE*NP
pos=np.zeros((N,3),np.float32); vel=np.zeros((N,3),np.float32)
eid=np.repeat(np.arange(NE),NP); col_i=np.array([EX[e]['c'] for e in eid])
# Farbstreuung je Teilchen (leicht heller/dunkler, Nachbarfarbe beigemischt)
CH=float(os.environ.get('CHALK','0.0'))
pcol=(pal[col_i]*(1-CH)+CH)*rng.uniform(0.96,1.04,(N,1)).astype(np.float32)
FINE=float(os.environ.get('FINE','0.55'))
k=np.where(rng.random(N)<1-FINE, rng.uniform(2.5,10,N), rng.uniform(14,34,N)).astype(np.float32)          # Luftwiderstand: grob .. fein
DUST=float(os.environ.get('DUST','0')); HT=float(os.environ.get('HT','0'))
dm=rng.random(N)<DUST; k[dm]=rng.uniform(50,120,int(dm.sum()))   # Schwebstaub: haengt lange in der Luft
state=np.zeros(N,np.int8)   # 0 wartet, 1 fliegt, 2 liegt
SOFT=float(os.environ.get('SOFT','0')); MW=float(os.environ.get('MW','1'))
rad=np.where(k>12, rng.uniform(0.0012,0.0024,N), rng.uniform(0.0009,0.0016,N)).astype(np.float32)*(1-0.45*SOFT)
# Ablage
acc=np.zeros((R,R,3),np.float32); thick=np.zeros((R,R),np.float32)
def deposit(idx):
    if len(idx)==0: return
    x=pos[idx,0]; y=pos[idx,1]
    i=np.clip(((1-y)/2*R).astype(int),0,R-1); j=np.clip(((x+1)/2*R).astype(int),0,R-1)
    m=(0.6+k[idx]*0.04)*MW
    np.add.at(thick,(i,j),m)
    for q in range(3): np.add.at(acc[...,q],(i,j),pcol[idx,q]*m)
def turb(p,t):
    x,y,z=p[:,0],p[:,1],p[:,2]
    return np.stack([np.sin(3.1*y+1.7*z+t*1.3)+0.5*np.sin(7.3*z-2*t),
                     np.sin(2.7*x-1.9*z-t*1.1)+0.5*np.sin(6.1*x+t*1.7),
                     0.4*np.sin(2.3*x+3.1*y+t)],1).astype(np.float32)
CAMZ0=2.0*1920/560*50/36
# --- Rillen raeumen: Hilfsfelder
YY=np.linspace(1,-1,R,dtype=np.float32)[:,None]; XX=np.linspace(-1,1,R,dtype=np.float32)[None,:]
gi,gj=np.nonzero(G); NS=int(os.environ.get('NSPARK','26000'))
sk=rng.integers(0,len(gi),NS); SPI=gi[sk]; SPJ=gj[sk]
SPX=(SPJ+rng.random(NS))/R*2-1; SPY=1-(SPI+rng.random(NS))/R*2
SPR=rng.random(NS).astype(np.float32); SPA=rng.uniform(0,6.283,NS).astype(np.float32)
GD=None; WN=None
if VAR=='wasser':   # Weg des Wassers: Laufweite entlang der Rillen ab der Ecke oben links
    from collections import deque
    GD=np.full((R,R),-1,np.int32); q=deque()
    for a,b in (((2,2),(R-3,R-3),(2,R-3),(R-3,2)) if os.environ.get('WSRC','4')=='4' else ((2,2),(R-3,R-3))):
        GD[a,b]=0; q.append((a,b))
    while q:
        a,b=q.popleft(); d=GD[a,b]+1
        for da,db in (((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)) if 'echt' in os.environ.get('WMODE','') else ((1,0),(-1,0),(0,1),(0,-1))):   # echt: Front steht quer zur Rille
            x,y=a+da,b+db
            if 0<=x<R and 0<=y<R and G[x,y] and GD[x,y]<0: GD[x,y]=d; q.append((x,y))
    from scipy.ndimage import maximum_filter
    GDM=float(GD.max()); GD=maximum_filter(np.where(GD<0,0,GD).astype(np.float32),9)
    GDH=maximum_filter(GD,25); HAL=np.clip(gaussian_filter(G.astype(np.float32),5)*2.2,0,1)          # Saum neben der Rille (Flut)
    SPM=((maximum_filter(GD,81)-GD<10)&(GD>0.3*GDM))[SPI,SPJ]                                       # Treffpunkte der Stroeme (Aufprall)
    WM=os.environ.get('WMODE','')
    _g=gaussian_filter(GD,3); FY,FX=np.gradient(_g); _n=np.maximum(np.sqrt(FX*FX+FY*FY),1e-4); FX=(FX/_n*G).astype(np.float32); FY=(FY/_n*G).astype(np.float32)   # Fliessrichtung
    WT=np.zeros((R,R,4),np.float32); WON=np.zeros((R,R),bool); II,JJ=np.mgrid[0:R,0:R].astype(np.float32)
    from scipy.ndimage import map_coordinates
    MEET=gaussian_filter(((maximum_filter(GD,81)-GD<10)&(GD>0.3*GDM)&G).astype(np.float32),14); MEET/=max(MEET.max(),1e-6)   # Naehe zu den Treffpunkten
def sparks(t0s,birth,vx,vy,vz,life,colr,white,g):
    age=t-t0s-birth; on=(age>0)&(age<life)
    if not on.any(): return None
    a=age[on]; u=a/life
    p=np.stack([np.clip(SPX[on]+vx[on]*a,-0.985,0.985),np.clip(SPY[on]+vy[on]*a,-0.985,0.985),0.005+vz[on]*a-g*a*a],1).astype(np.float32)
    p[:,2]=np.maximum(p[:,2],0.004)
    c=colr[SPI[on],SPJ[on]]*(1-white)+white
    return p,np.clip(c,0,1).astype(np.float32),(0.0032*(1-u*0.8)).astype(np.float32)
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
                reach=rng.gamma(2.5,0.09,n)*spike*SC*E.get('sc',1.0)                          # Reichweite in m
                sp=reach*k[sl]
                up=rng.gamma(2.0,0.06,n)*k[sl]
                FLW=E.get('fl',0.02); ELS,ELA=E.get('el',[1.0,0.0]); ca,sa=np.cos(np.radians(ELA)),np.sin(np.radians(ELA))
                ux=np.cos(th)*sp*ELS; uy=np.sin(th)*sp/np.sqrt(ELS)                                   # gestreckte Wolke, gedreht um ELA
                vel[sl,0]=ux*ca-uy*sa; vel[sl,1]=ux*sa+uy*ca; vel[sl,2]=up
                vel[sl,2]+= -FALL*0.15
                qx=rng.normal(0,FLW*ELS,n); qy=rng.normal(0,FLW/np.sqrt(ELS),n)                       # flaechiger Start statt Punkt
                pos[sl,0]=np.clip(E['p'][0]+qx*ca-qy*sa,-0.97,0.97); pos[sl,1]=np.clip(E['p'][1]+qx*sa+qy*ca,-0.97,0.97); pos[sl,2]=0.01
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
            if ts>DUR-0.8: landed=idx   # Rest-Schwebstaub legt sich: am Ende liegt alles
            deposit(landed); state[landed]=2
    # Ausgabe: fliegende Teilchen + fallende Pakete
    fl=np.nonzero(state==1)[0]
    zc=np.clip(pos[fl,2:3]/0.25,0,1)*HT; P=[pos[fl]]; C=[pcol[fl]*(1-zc)+zc]; RR=[rad[fl]]
    for e,E in enumerate(EX):
        dtm=E['t']-t
        if 0<dtm<0.7 and not os.environ.get('NOFALL'):   # NOFALL: kein sichtbares fallendes Paket vor dem Einschlag
            m=int(2500*SC*SC); sl=np.arange(e*NP,e*NP+m)
            jit=rng.normal(0,1,(m,3)).astype(np.float32)*np.array([0.03*SC,0.03*SC,0.03*SC+dtm*0.08],np.float32)
            zz=FALL*dtm; CAMZ=2.0*1920/560*50/36
            pp=np.concatenate([np.tile(E['p']*(1-zz/CAMZ),(m,1)),np.full((m,1),zz)],1).astype(np.float32)+jit   # faellt auf der Sichtachse: Einschlag genau an der Stelle
            P.append(pp); C.append(pcol[sl]); RR.append(np.full(m,0.004,np.float32))
    # Ablage-Karten
    S1=1.4+2.4*SOFT; S2=14+8*SOFT; th=gaussian_filter(thick,S1)+0.6*gaussian_filter(thick,S2); cc=np.stack([gaussian_filter(acc[...,q],S1)+0.6*gaussian_filter(acc[...,q],S2) for q in range(3)],-1)
    colr=cc/np.maximum(th,1e-4)[...,None]
    cov=1-np.exp(-th/0.10)
    fxw=np.zeros((R,R),np.float32); fxg=np.zeros((R,R),np.float32); thick_show=1.0; ext=None
    if VAR=='rillen':   # am Ende wird der Puder von links nach rechts aus den Rillen geblasen
        prog=np.clip((t-(DUR-2.4))/1.6,0,1); wipe=np.clip((prog*1.4-XS)/0.4,0,1)
        cov=cov*(1-GS*wipe); thick_show=1-GS*wipe
    elif VAR=='welle':  # 1 Druckwelle des letzten Pakets: unregelmaessige, koernige Front statt Kreis, feiner Staub
        E_=EX[-1]; WS=float(os.environ.get('WSPEED','0.85'))
        if WN is None:
            r_=np.random.default_rng(21)
            WN=gaussian_filter(r_.standard_normal((R,R)).astype(np.float32),60); WN/=np.abs(WN).max()      # grobe Verformung der Front
            WF=gaussian_filter(r_.standard_normal((R,R)).astype(np.float32),1.2); WF/=WF.std()            # Korn an der Kante
            ang=np.arctan2(YY-E_['p'][1],XX-E_['p'][0]); WA=0.10*np.sin(5*ang+1.3)+0.07*np.sin(9*ang+4.0)+0.05*np.sin(14*ang+2.2)
        dist=np.sqrt((XX-E_['p'][0])**2+(YY-E_['p'][1])**2)*(1+WA)+0.16*WN
        wipe=np.clip(((t-E_['t'])*WS-dist)/0.10+0.5+0.45*WF,0,1)
        cov=cov*(1-GS*wipe); thick_show=1-GS*wipe
        dx=SPX-E_['p'][0]; dy=SPY-E_['p'][1]; dd=np.maximum(np.sqrt(dx*dx+dy*dy),1e-3)
        dsp=dist[SPI,SPJ]
        ext=sparks(E_['t'],dsp/WS+0.12*SPR,dx/dd*0.16,dy/dd*0.16,0.28+0.3*SPR,0.8,colr,0.25,0.5)
        if ext is not None: ext=(ext[0],ext[1],ext[2]*0.55)
    elif VAR=='wasser' and TCLR is not None and WM:   # Wasser-Varianten: schwall (im Takt), schaum (helle Front), aufprall (Spritzer am Treffpunkt), flut (fuellen und Sog)
        a_=t-TCLR; BT=60.0/TK.get('bpm',90)/SL; gsp=GD[SPI,SPJ]
        if 'flut' in WM:
            sp=GDM/0.7; arr=GD/sp; arrH=GDH/sp; TS=(TK['pulse'][-1]/SL-TCLR) if TK.get('pulse') else 3*BT
            f1=np.clip((a_-arr)/0.05,0,1); r=np.clip((a_-TS)/0.25,0,1)
            keep=np.clip((GDM*(1-r*r)-GD)/40+0.5,0,1)*(1-np.clip((a_-TS-0.25)/0.1,0,1))
            b=np.clip((a_-0.7)/0.4,0,1); dry=np.clip((a_-TS-0.3)/0.6,0,1)
            covg=cov*(1-f1)+0.6*f1*keep
            cov=cov*(1-GS)+covg*GS; thick_show=1-GS*f1
            fxw=np.maximum(GS*f1*keep,np.clip(HAL-GS,0,1)*b*np.clip((a_-arrH)/0.05,0,1)*(1-dry))
            if a_>TS:   # Sog: feine Tropfen, wo sich das Wasser zurueckzieht
                e_=sparks(TCLR+TS,0.25*np.sqrt(np.clip(1-gsp/GDM,0,1)),0.10*np.cos(SPA),0.10*np.sin(SPA),0.25+0.35*SPR,0.5,colr,0.8,0.9)
                if e_ is not None: P.append(e_[0]); C.append(e_[1]); RR.append(e_[2]*0.7)
        else:
            if 'schwall' in WM:   # 3 Stoesse, je einer pro Schlag
                FR=GDM+80; seg=FR/3; PD=0.16
                PT=np.array([p_/SL-TCLR for p_ in TK['pulse']],np.float32) if TK.get('pulse') else np.arange(3,dtype=np.float32)*BT   # Stoesse auf den Schlaegen der Musik
                kk=np.clip(np.floor(GD/seg),0,2).astype(int); arr=PT[kk]+PD*(GD-kk*seg)/seg
                kq=np.clip(np.floor(gsp/seg),0,2).astype(int); arrs=PT[kq]+PD*(gsp-kq*seg)/seg
            else:
                sp=GDM/1.25; fr=a_*sp; arr=GD/sp; arrs=gsp/sp
            f1=np.clip((a_-arr)/0.05,0,1); f2=np.clip((a_-arr-0.10)/0.5,0,1); dr=np.clip((a_-arr-0.7)/0.4,0,1)
            cov0=cov.copy()
            covg=cov*(1-f1)+(0.0 if 'echt' in WM else 0.6)*f1*(1-f2)
            cov=cov*(1-GS)+covg*GS; thick_show=1-GS*f1
            fxw=GS*f1*(1-dr)
            if 'echt' in WM:   # echter Wasserkoerper: Spiegelhoehe (0..1 = Rillentiefe) mit Schwallkamm, Nachschwappen, Aufprall; Puder loest sich als Farbe im Wasser
                ag=np.clip(a_-arr,0,None); on=((a_-arr)>0)&G
                TD=(float(PT[-1]) if 'schwall' in WM else 1.25)+0.8; dn=np.clip((a_-TD)/0.6,0,1)
                hw=0.78*(1-np.exp(-ag/0.07))+0.55*np.exp(-ag/0.07)+0.10*np.sin(6.283*(GD/60.0-a_*2.6))*np.exp(-ag/0.7)+0.45*MEET*np.exp(-ag/0.35)*np.cos(6.283*ag*2.2)
                hw=gaussian_filter(np.where(on,np.clip(hw,0,1.02)*(1-dn)**1.5,0).astype(np.float32),1.2)
                np.save(f'{OUT}/wat_{f:04d}.npy',hw.reshape(R//2,2,R//2,2).mean((1,3)).astype(np.float16))   # 512 x 512
                vv=(520*np.exp(-ag/0.22)+45)*on/FPS                                   # Stroemung: schnell hinter der Front, dann ruhiges Nachlaufen
                src=[II-FY*vv,JJ-FX*vv]
                WT=np.stack([map_coordinates(WT[...,q],src,order=1,mode='nearest') for q in range(4)],-1)*G[...,None]
                new=on&~WON; WON=on.copy()
                WT[new,:3]+=colr[new]*cov0[new,None]; WT[new,3]+=cov0[new]                # Puder loest sich an der Front und wird mitgenommen
                WT=np.stack([gaussian_filter(WT[...,q],2.2) for q in range(4)],-1)*G[...,None]; WT*=1-0.9/FPS   # mischt sich und wird klarer
                tn=WT[...,:3]/np.maximum(WT[...,3:4],1e-3); ta=np.clip(WT[...,3]*0.8,0,0.8)*(1-dn)*on
                Image.fromarray((np.concatenate([np.clip(tn,0,1),ta[...,None]],-1)*255).astype(np.uint8),'RGBA').save(f'{OUT}/wtn_{f:04d}.png')
                fxw=GS*f1*0.55*(1-np.clip((a_-TD-0.3)/0.6,0,1))
            if 'schaum' in WM and a_>0:   # helle Schaumkante an der Front, schleudert feinen Puder aus der Rille
                fb=np.clip(1-np.abs(a_-arr-0.03)/0.05,0,1)*GS*(GD>0)
                colr=colr*(1-fb[...,None])+fb[...,None]; cov=np.maximum(cov,0.92*fb)
                e_=sparks(TCLR,arrs+0.02*SPR,0.14*np.cos(SPA),0.14*np.sin(SPA),0.25+0.45*SPR,0.55,colr,0.45,0.9)
                if e_ is not None: P.append(e_[0]); C.append(e_[1]); RR.append(e_[2]*0.6)
            if 'aufprall' in WM and a_>0:  # wo sich die Stroeme treffen, spritzt es hoch
                rr_=np.maximum(np.sqrt(SPX*SPX+SPY*SPY),1e-3); jx=-SPX/rr_*0.10+0.10*np.cos(SPA); jy=-SPY/rr_*0.10+0.10*np.sin(SPA)   # feine Tropfen, leicht nach innen: aussen bleibt es sauber
                e_=sparks(TCLR,np.where(SPM&(SPA<2.2),arrs,1e9),jx*SPR,jy*SPR,0.35+0.5*SPR,0.6,colr,0.9,1.3)
                if e_ is not None: P.append(e_[0]); C.append(e_[1]); RR.append(e_[2]*0.45)
    elif VAR=='wasser' and TCLR is not None:  # 8 klares Wasser laeuft durch die Rillen und spuelt den Puder aus
        sp=GDM/1.25; fr=(t-TCLR)*sp
        f1=np.clip((fr-GD)/60,0,1); f2=np.clip((fr-GD-60)/420,0,1); dr=np.clip(((t-TCLR-1.45)*sp-GD)/500,0,1)
        covg=cov*(1-f1)+0.6*f1*(1-f2)
        cov=cov*(1-GS)+covg*GS; thick_show=1-GS*f1
        fxw=GS*f1*(1-dr)
    elif VAR=='licht' and TCLR is not None:   # 9 die Rillen leuchten von innen, der Puder loest sich in Funken auf
        a_=t-TCLR; glow=np.clip(a_/0.45,0,1)*np.clip(1-(a_-1.0)/0.7,0,1) if a_>0 else 0.0
        burn=np.clip((a_-0.25)/0.75,0,1)
        cov=cov*(1-GS*burn); thick_show=1-GS*burn
        gf=G.astype(np.float32); fxg=np.clip(gaussian_filter(gf,5)*1.3+gaussian_filter(gf,22)*0.9,0,1)**1.5*glow
        ext=sparks(TCLR,0.2+SPR*0.8,0.05*np.cos(SPA),0.05*np.sin(SPA),0.25+0.35*SPR,0.9,colr,0.65,0.0)
    if ext is not None: P.append(ext[0]); C.append(ext[1]); RR.append(ext[2])
    P=np.concatenate(P); C=np.concatenate(C); RR=np.concatenate(RR)
    np.savez(f'{OUT}/pts_{f:04d}.npz',p=P.astype(np.float32),c=C.astype(np.float16),r=RR.astype(np.float16))
    rgba=np.concatenate([np.clip(colr,0,1),cov[...,None]],-1)
    Image.fromarray((rgba*255).astype(np.uint8),'RGBA').save(f'{OUT}/dep_{f:04d}.png')
    hh=np.clip(gaussian_filter(thick,1.2)/6.0,0,1)*thick_show
    Image.fromarray((hh*65535).astype(np.uint16)).save(f'{OUT}/hgt_{f:04d}.png')
    Image.fromarray((np.stack([fxw,fxg,np.zeros_like(fxw)],-1)*255).astype(np.uint8)).save(f'{OUT}/fx_{f:04d}.png')
    if f%24==0: print(f,'fliegt',len(fl),'liegt',int((state==2).sum()),'bedeckt',float((cov>0.9).mean()),flush=True)
print('fertig')
