import streamlit as st
import math
import base64
import numpy as np
import pandas as pd
from zhipuai import ZhipuAI

# --- 1. 页面配置与工业风 UI ---
st.set_page_config(page_title="国网标准-全特性数字化实验室", layout="wide")


def get_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""


img_base64 = get_base64("my_background.png")

st.markdown(
    f"""
    <style>
    .stApp {{ background-image: url("data:image/png;base64,{img_base64}"); background-size: cover; background-attachment: fixed; }}
    .main .block-container {{ background: rgba(0, 20, 20, 0.94); backdrop-filter: blur(15px); border-radius: 15px; color: #FFFFFF; border: 1px solid #00A380; padding: 1.5rem; }}
    .formula-box {{ background: rgba(0, 163, 128, 0.2); border: 1px solid #00A380; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-family: 'Courier New', Courier, monospace; }}
    .stMetric {{ background: rgba(0, 163, 128, 0.1); border-left: 5px solid #00A380; border-radius: 5px; padding: 10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 2. 顶部全局导航 (手机端优化) ---
st.title("⚡ 国网标准数字化综合实验室")

# 全局电压滑块：新增 20kV
u_hv_global = st.select_slider(
    "⚡ 设定系统高压侧额定电压 (kV)", options=[0.4, 6, 10, 20, 35, 110], value=10.0
)

# 实验工位切换：确保逻辑唯一，不套娃
lab_mode = st.selectbox(
    "🧪 请选择实验工位",
    [
        "1. 变压器双侧参数与线路压降",
        "2. 绝缘电阻与接地系统判定",
        "3. 断路器机械特性与弹跳仿真",
        "4. 载流温升在线模拟",
        "5. AI 专家综合诊断报告",
    ],
)

st.divider()

# --- 3. 核心实验逻辑 ---

# --- 模块 1：变压器双侧 + 压降 (全参数不删减版) ---
if "1." in lab_mode:
    st.subheader("📐 变压器参数计算与长线路压降")

    # 公式展示
    st.markdown('<div class="formula-box">', unsafe_allow_html=True)
    st.latex(
        r"I_{hv} = \frac{S}{\sqrt{3} \cdot U_{hv}} \quad | \quad I_{lv} = \frac{S}{\sqrt{3} \cdot U_{lv}} \quad | \quad \Delta U\% = \frac{S \cdot L \cdot \rho}{U_{hv}^2 \cdot A \cdot 10}"
    )
    st.write("注：$U_{hv}$ 由顶部滑块控制，$U_{lv}$ 支持自定义调节。")
    st.markdown("</div>", unsafe_allow_html=True)

    # 第一行：变压器计算
    st.write("#### 1️⃣ 变压器双侧额定电流")
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        s_kva = st.number_input("变压器额定容量 (kVA)", value=1250, step=50)
        u_lv = st.number_input(
            "低压侧额定电压 (kV)", value=0.4, step=0.01
        )  # 新增低压侧自定义
    with c2:
        i_hv = s_kva / (math.sqrt(3) * u_hv_global)
        st.metric(f"高压侧电流 ({u_hv_global}kV)", f"{i_hv:.2f} A")
    with c3:
        i_lv = s_kva / (math.sqrt(3) * u_lv)
        st.metric(f"低压侧电流 ({u_lv}kV)", f"{i_lv:.2f} A", delta="大电流侧")

    st.divider()

    # 第二行：线路压降
    st.write("#### 2️⃣ 长线路末端压降校验")
    d1, d2, d3 = st.columns(3)
    dist = d1.number_input("线路长度 (m)", value=500, step=50)
    sect = d2.number_input("电缆截面 (mm²)", value=95, step=1)
    # 压降计算
    v_drop = (s_kva * dist * 0.0175) / (u_hv_global * u_hv_global * sect * 10)
    d3.metric(
        "末端电压压降率",
        f"{v_drop:.2f}%",
        delta="符合规范" if v_drop < 5 else "严重超标",
        delta_color="normal" if v_drop < 5 else "inverse",
    )

# --- 模块 2：绝缘与接地 (国网标准 GB 50150) ---
elif "2." in lab_mode:
    st.subheader("🛡️ 绝缘与接地安全性判定")
    st.info(f"当前系统电压: {u_hv_global} kV | 执行标准: GB 50150")

    r1, r2, r3 = st.columns(3)
    ir_val = r1.number_input("绝缘电阻实测 (MΩ)", value=2500)
    ir_ground = r2.number_input("接地电阻实测 (Ω)", value=0.8)
    loop_res = r3.number_input("回路电阻实测 (μΩ)", value=60)

    # 动态判定标准
    if u_hv_global >= 10:
        min_ir = 2500
    elif u_hv_global >= 6:
        min_ir = 1000
    else:
        min_ir = 0.5

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric(
        "绝缘状态", "合格" if ir_val >= min_ir else "告警", delta=f"标准:{min_ir}MΩ"
    )
    res2.metric(
        "接地系统", f"{ir_ground}Ω", delta="合格" if ir_ground <= 4.0 else "超标"
    )
    res3.metric(
        "回路电阻", f"{loop_res}μΩ", delta="优良" if loop_res <= 120 else "超标"
    )

# --- 模块 3：断路器机械特性 (DL/T 403 仿真) ---
elif "3." in lab_mode:
    st.subheader("⏱️ 断路器机械特性动态波形仿真")
    m1, m2 = st.columns([1, 2])
    with m1:
        close_t = st.slider("合闸时长设定 (ms)", 30, 80, 45)
        bounce_t = st.slider("合闸弹跳仿真 (ms)", 0.0, 5.0, 1.2)
        travel = st.number_input("动触头行程 (mm)", value=11.0)
    with m2:
        t = np.linspace(0, 100, 400)
        y = np.where(t < close_t, 0, travel)
        if bounce_t > 0:
            b_idx = (t >= close_t) & (t <= close_t + bounce_t * 5)
            y[b_idx] += np.sin((t[b_idx] - close_t) * 6) * np.exp(
                -(t[b_idx] - close_t) * 0.6
            )
        st.line_chart(
            pd.DataFrame({"时间(ms)": t, "行程(mm)": y}), x="时间(ms)", y="行程(mm)"
        )

    if bounce_t > 2.0:
        st.error(f"❌ 警告：合闸弹跳 ({bounce_t}ms) 超过国网标准(≤2ms)")

# --- 模块 4：载流温升试验 ---
elif "4." in lab_mode:
    st.subheader("🔥 载流温升在线模拟 (GB/T 11022)")
    t1, t2 = st.columns(2)
    load_i = t1.slider("模拟运行电流 (A)", 0, 2000, 1250)
    # 温升模拟逻辑
    rise = (load_i / 1250) ** 2 * 45
    total_temp = 25 + rise
    t2.metric("预测触头温度", f"{total_temp:.1f} °C", delta=f"温升 {rise:.1f} K")
    if total_temp > 105:
        st.error("⚠️ 警告：温度超过绝缘耐受极限！")

# --- 模块 5：AI 专家诊断 ---
else:
    st.subheader("🤖 AI 专家综合诊断报告")
    api_key = st.text_input("智谱 API Key", type="password")
    if st.button("🚀 生成全项数字化报告", use_container_width=True):
        if api_key:
            client = ZhipuAI(api_key=api_key)
            with st.spinner("AI 正在根据国网标准研判数据..."):
                prompt = f"评价变压器容量(s_kva if 's_kva' in locals() else '未知')kVA在{u_hv_global}kV下的状态..."
                response = client.chat.completions.create(
                    model="glm-4", messages=[{"role": "user", "content": prompt}]
                )
                st.markdown(response.choices[0].message.content)
        else:
            st.warning("请在侧边栏或此处输入 API Key")
