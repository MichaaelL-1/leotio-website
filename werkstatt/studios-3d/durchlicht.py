# Leotio Studios Durchlicht v1.1 · 26.11.2026: DL_MIN Grundlicht fuer dunkle Farben; v1.0 Nachbearbeitung "Papier von hinten durchleuchtet" nur im Quadrat; helle/duenne Stellen lassen viel Licht durch, dunkle kaum
# Aufruf: python3 durchlicht.py ein.mp4 aus.mp4 [erstes_bild=195] ; Umgebung: DL_PEAK=223 DL_A=208 DL_TAU=10 DL_G=1.6 DL_K=2.2
import numpy as np, os, sys, subprocess
from PIL import Image
src,dst=sys.argv[1],sys.argv[2]; F0=int(sys.argv[3]) if len(sys.argv)>3 else 195
PK=float(os.environ.get('DL_PEAK','223')); LA=float(os.environ.get('DL_A','208')); TAU=float(os.environ.get('DL_TAU','10'))
G=float(os.environ.get('DL_G','1.2')); K=float(os.environ.get('DL_K','2.2'))
tmp=dst+'_f'; os.makedirs(tmp,exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',src,f'{tmp}/i_%04d.png'],check=True)
fs=sorted(f for f in os.listdir(tmp) if f.startswith('i_'))
h,w=np.asarray(Image.open(f'{tmp}/{fs[0]}')).shape[:2]
half=w*560/1920/2*0.995; cx,cy=w/2,h/2
yy,xx=np.mgrid[0:h,0:w]; M=((np.abs(xx-cx)<half)&(np.abs(yy-cy)<half)).astype(np.float32)
from scipy.ndimage import gaussian_filter; M=gaussian_filter(M,0.7)[...,None]
warm=np.array([1.0,0.93,0.80],np.float32)
for i,f in enumerate(fs):
    v=F0+i
    if v<LA: g=0.0
    elif v<PK: x=(v-LA)/(PK-LA); g=(x*x*(3-2*x))**2
    else: g=np.exp(-(v-PK)/TAU)
    a=np.asarray(Image.open(f'{tmp}/{f}').convert('RGB')).astype(np.float32)/255
    lin=a**2.2
    lum=(0.2126*lin[...,0]+0.7152*lin[...,1]+0.0722*lin[...,2])[...,None]
    lum=gaussian_filter(lum[...,0],1.5)[...,None]           # Korn nicht mitverstaerken
    T0=np.clip((lum-0.04)/0.42,0,1)**K; MN=float(os.environ.get('DL_MIN','0.3'))
    T=MN+(1-MN)*T0                                         # helle Farbe/duenner Puder: viel Licht; dunkle Pigmente: weniger
    light=lin*(1+G*g*T*3*warm)                            # Lampe hinter dem Papier, durch die Farbe gefiltert
    light=np.where(light>0.6,0.6+0.4*np.tanh((light-0.6)/0.4),light)            # weiche Schulter statt hartem Ausbrennen
    out=(lin*(1-M)+light*M)
    Image.fromarray((np.clip(out,0,1)**(1/2.2)*255+0.5).astype(np.uint8)).save(f'{tmp}/o_{i:04d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',f'{tmp}/o_%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','16',dst],check=True)
import shutil; shutil.rmtree(tmp)
print('fertig',dst)
