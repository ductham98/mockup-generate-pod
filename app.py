
import streamlit as st
import json, io, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from engine import load_rgb, detect_nails, composite

ROOT=Path(__file__).parent
CFG=json.loads((ROOT/"config.json").read_text())
st.set_page_config(page_title="Nail Mockup Generator",layout="wide")
st.title("Nail Mockup Generator – MVP")
st.caption("Base hand cố định · Thay bộ móng thiết kế · Xử lý local, không watermark")

base_path=ROOT/CFG["base_image"]
base=load_rgb(base_path)
st.sidebar.header("Base template")
st.sidebar.image(base,caption="Base Hand cố định",use_container_width=True)
st.sidebar.info("V1 dùng tọa độ mask được cấu hình sẵn trong config.json. Cần hiệu chỉnh một lần nếu vị trí móng chưa khớp hoàn toàn.")

uploaded=st.file_uploader("Upload ảnh thiết kế (PNG/JPG)",type=["png","jpg","jpeg"])
with st.expander("Cấu hình xử lý",expanded=True):
    gloss=st.slider("Giữ ánh sáng / highlight từ ảnh bàn tay",0.0,0.8,0.28,0.02)
    threshold=st.slider("Ngưỡng tách nền sáng",200,252,CFG["design_detection"]["background_threshold"])
    min_area=st.slider("Diện tích tối thiểu để nhận diện móng",100,5000,CFG["design_detection"]["min_area"],100)

if uploaded:
    design=Image.open(uploaded).convert("RGB")
    design_rgb=np.array(design)
    st.subheader("Ảnh thiết kế đầu vào")
    st.image(design_rgb,use_container_width=True)
    try:
        detected=detect_nails(design_rgb,threshold,min_area,CFG["design_detection"]["padding"])
        st.success(f"Đã phát hiện {len(detected)} vùng móng/đối tượng. Chọn 5 móng dùng cho bàn tay.")
        cols=st.columns(min(5,len(detected)))
        for i,n in enumerate(detected):
            with cols[i%len(cols)]:
                st.image(n["crop"],caption=f"Mẫu {i+1}",use_container_width=True)
        # Default choose first 5 detections. For a 2-row layout, user can choose each nail.
        labels=[f"{i+1}" for i in range(len(detected))]
        defaults=list(range(min(5,len(detected))))
        selected=[]
        st.subheader("Mapping 5 ngón tay")
        names=["Ngón cái","Ngón trỏ","Ngón giữa","Ngón áp út","Ngón út"]
        for i,name in enumerate(names):
            idx=st.selectbox(name,options=list(range(len(detected))),index=defaults[min(i,len(defaults)-1)],format_func=lambda x:f"Mẫu {x+1}",key=f"map_{i}")
            selected.append(detected[idx])
        if st.button("Tạo mockup",type="primary",use_container_width=True):
            if len(detected)<5:
                st.error("Cần tối thiểu 5 móng được nhận diện.")
            else:
                quads=[x["quad"] for x in CFG["nail_targets"]]
                result=composite(base,selected,quads,gloss)
                st.session_state["result"]=result
                st.session_state["result_name"]=Path(uploaded.name).stem+"_mockup.png"
    except Exception as e:
        st.error(f"Lỗi nhận diện: {e}")
        st.info("Ảnh đầu vào nên có nền sáng, các móng tách rời nhau và không có chữ/đồ họa chạm vào móng.")

if "result" in st.session_state:
    st.subheader("Kết quả mockup")
    st.image(st.session_state["result"],use_container_width=True)
    buf=io.BytesIO()
    Image.fromarray(st.session_state["result"]).save(buf,format="PNG")
    st.download_button("Tải mockup PNG",data=buf.getvalue(),file_name=st.session_state["result_name"],mime="image/png",use_container_width=True)
