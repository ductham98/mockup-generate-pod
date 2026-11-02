
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def load_rgb(path):
    return np.array(Image.open(path).convert("RGB"))

def detect_nails(design_rgb, threshold=238, min_area=700, padding=8):
    """Detect isolated nail tips on a light background using connected components.
    Returns RGB crops, sorted top-to-bottom then left-to-right.
    For images with touching shadows/backgrounds, use the manual crop controls in UI.
    """
    img = design_rgb
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Exclude near-white background. Adaptive saturation also catches colored nails.
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    mask = ((gray < threshold) | (hsv[:,:,1] > 22)).astype(np.uint8) * 255
    # Remove isolated speckles and bridge tiny holes.
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    comps=[]
    for i in range(1,n):
        x,y,w,h,area = stats[i]
        if area < min_area or h < 30 or w < 15:
            continue
        # Filter large watermark/text/background artifacts.
        if w > img.shape[1]*0.35 or h > img.shape[0]*0.55:
            continue
        x0=max(0,x-padding); y0=max(0,y-padding)
        x1=min(img.shape[1],x+w+padding); y1=min(img.shape[0],y+h+padding)
        crop=img[y0:y1,x0:x1].copy()
        # Build alpha from connected component, softly feather edge.
        alpha=(labels[y0:y1,x0:x1] == i).astype(np.uint8)*255
        alpha=cv2.GaussianBlur(alpha,(3,3),0.6)
        comps.append({"box":(x,y,w,h),"crop":crop,"alpha":alpha,"area":area})
    # The sample layout has two rows. Group by center-y then sort x.
    if not comps:
        raise ValueError("Không tìm thấy móng. Hãy dùng ảnh nền sáng, các móng không chạm nhau.")
    comps.sort(key=lambda c: c["box"][1] + c["box"][3]/2)
    rows=[]
    for c in comps:
        cy=c["box"][1]+c["box"][3]/2
        if not rows or abs(cy-rows[-1]["mean_y"]) > max(35, c["box"][3]*0.55):
            rows.append({"mean_y":cy,"items":[c]})
        else:
            rows[-1]["items"].append(c)
            rows[-1]["mean_y"]=np.mean([x["box"][1]+x["box"][3]/2 for x in rows[-1]["items"]])
    for r in rows:
        r["items"].sort(key=lambda c:c["box"][0])
    return [c for r in rows for c in r["items"]]

def order_quad(q):
    q=np.array(q,dtype=np.float32)
    # Input points are [top-left, top-right, bottom-right, bottom-left] around nail
    return q

def warp_nail(nail, target_quad, canvas_shape, preserve_gloss=True):
    h,w=canvas_shape[:2]
    crop=nail["crop"]
    alpha=nail["alpha"]
    ch,cw=crop.shape[:2]
    # Map the entire isolated nail crop directly to the calibrated nail quadrilateral.
    # The alpha mask keeps the light background transparent during compositing.
    q=order_quad(target_quad)
    src=np.array([[0,0],[cw-1,0],[cw-1,ch-1],[0,ch-1]],np.float32)
    H=cv2.getPerspectiveTransform(src,q)
    warped=cv2.warpPerspective(crop,H,(w,h),flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
    wa=cv2.warpPerspective(alpha,H,(w,h),flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    wa=cv2.GaussianBlur(wa,(5,5),1.0)
    return warped, wa

def composite(base_rgb, nails, target_quads, gloss_strength=0.28):
    out=base_rgb.copy().astype(np.float32)
    for nail,quad in zip(nails,target_quads):
        warped, alpha=warp_nail(nail,quad,base_rgb.shape)
        a=(alpha.astype(np.float32)/255.0)
        # Preserve base light/shade variation inside the target nail area.
        # This is a restrained luminance transfer, not AI regeneration.
        if gloss_strength > 0:
            base_gray=cv2.cvtColor(base_rgb,cv2.COLOR_RGB2GRAY).astype(np.float32)
            # Normalize local base luminance to keep original specular highlights.
            lum=np.clip((base_gray-128)/110.0,-0.35,0.55)
            shade=(1.0 + gloss_strength*lum)
            warped=np.clip(warped.astype(np.float32)*shade[:,:,None],0,255)
        out=out*(1-a[:,:,None])+warped*a[:,:,None]
    return np.clip(out,0,255).astype(np.uint8)
