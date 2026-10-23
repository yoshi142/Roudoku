import json,os,numpy as np,cv2

out={}
for f in os.listdir('thm'):
    p='thm/'+f
    if os.path.getsize(p)<1500: continue
    im=cv2.imread(p)
    if im is None: continue
    im=cv2.resize(im,(320,180))
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(float)/255
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    sat=hsv[...,1].astype(float)/255
    edges=cv2.Canny((g*255).astype('uint8'),100,200)
    q=(im//32).reshape(-1,3); uniq=len(np.unique(q[:,0]*64+q[:,1]*8+q[:,2]))

    out[f[:-4]]=dict(contrast=float(g.std()),bright=float(g.mean()),dark=float((g<0.2).mean()),white=float(((g>0.85)&(sat<0.25)).mean()),
        sat=float(sat.mean()),edge=float((edges>0).mean()),colors=int(uniq))
json.dump(out,open('thfeat.json','w'),indent=0); print(len(out))
