#!/usr/bin/env python3
"""
BullBear Dashboard - 加密市场状态机可视化
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# 配置页面
st.set_page_config(
    page_title="BullBear Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义样式
st.markdown("""
<style>
    .main {padding-top: 1rem;}
    h1 {font-weight: 300; font-size: 2.5rem; color: #1f77b4;}
    h2 {font-weight: 400; font-size: 1.6rem; margin-top: 2rem; margin-bottom: 1rem;}
    .state-box {
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .state-bull-offensive {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
    }
    .state-bull-defensive {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        color: white;
    }
    .state-bear-offensive {
        background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
        color: white;
    }
    .state-bear-defensive {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: white;
    }
    .metric-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 配置
BACKEND_URL = st.sidebar.text_input(
    "后端API地址",
    value="http://localhost:8000",
    help="BullBear Backend API地址"
)

# 标题
st.title("📊 BullBear Dashboard")
st.markdown("**加密市场状态机 - 四象限状态可视化**")

# 状态映射
STATE_STYLES = {
    "牛市进攻": "state-bull-offensive",
    "牛市修复": "state-bull-defensive",
    "熊市反弹": "state-bear-offensive",
    "熊市消化": "state-bear-defensive",
}

RISK_COLORS = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

# 获取数据
@st.cache_data(ttl=60)  # 缓存60秒
def fetch_state():
    """从后端获取市场状态"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/state", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"无法连接到后端: {e}")
        return None

@st.cache_data(ttl=60)
def fetch_all_data():
    """从后端获取所有数据"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/data", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"无法获取数据: {e}")
        return None

# 主界面
if st.button("🔄 刷新数据", type="primary"):
    st.cache_data.clear()

# 获取状态
state_data = fetch_state()
all_data = fetch_all_data()

if state_data and state_data.get("ok"):
    state_info = state_data
    state_name = state_info.get("state", "未知")
    trend = state_info.get("trend", "未知")
    funding = state_info.get("funding", "未知")
    risk_level = state_info.get("risk_level", "未知")
    confidence = state_info.get("confidence", 0.0)
    metadata = state_info.get("metadata", {})
    
    # 显示当前状态
    col1, col2 = st.columns([2, 1])
    
    with col1:
        state_class = STATE_STYLES.get(state_name, "state-box")
        st.markdown(f"""
        <div class="state-box {state_class}">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{state_name}</div>
            <div style="font-size: 1rem; opacity: 0.9;">
                {trend} | {funding}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("风险等级", f"{RISK_COLORS.get(risk_level, '⚪')} {risk_level}")
        st.metric("置信度", f"{confidence:.1%}")
        st.caption(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 四象限图
    st.markdown("---")
    st.subheader("📈 四象限状态图")
    
    # 创建四象限可视化
    fig = go.Figure()
    
    # 定义象限位置
    quadrants = {
        "牛市进攻": {"x": 1, "y": 1, "color": "#ff6b6b"},
        "牛市修复": {"x": -1, "y": 1, "color": "#4ecdc4"},
        "熊市反弹": {"x": 1, "y": -1, "color": "#feca57"},
        "熊市消化": {"x": -1, "y": -1, "color": "#a8edea"},
    }
    
    # 绘制所有象限
    for name, pos in quadrants.items():
        fig.add_trace(go.Scatter(
            x=[pos["x"]],
            y=[pos["y"]],
            mode="markers+text",
            marker=dict(
                size=100 if name == state_name else 50,
                color=pos["color"],
                opacity=1.0 if name == state_name else 0.3,
                line=dict(width=3 if name == state_name else 1, color="white"),
            ),
            text=[name],
            textposition="middle center",
            textfont=dict(size=14 if name == state_name else 10, color="white" if name == state_name else "gray"),
            name=name,
            showlegend=False,
        ))
    
    # 当前状态高亮
    current_pos = quadrants.get(state_name, {"x": 0, "y": 0})
    fig.add_trace(go.Scatter(
        x=[current_pos["x"]],
        y=[current_pos["y"]],
        mode="markers",
        marker=dict(size=120, color="white", opacity=0.5, line=dict(width=2, color="black")),
        name="当前状态",
        showlegend=False,
    ))
    
    fig.update_layout(
        title="市场状态四象限图",
        xaxis=dict(
            title="资金姿态",
            range=[-1.5, 1.5],
            tickmode="array",
            tickvals=[-1, 1],
            ticktext=["资金防守", "资金进攻"],
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            title="趋势方向",
            range=[-1.5, 1.5],
            tickmode="array",
            tickvals=[-1, 1],
            ticktext=["趋势空", "趋势多"],
            showgrid=True,
            gridcolor="lightgray",
        ),
        height=500,
        showlegend=False,
        plot_bgcolor="white",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 详细数据
    st.markdown("---")
    st.subheader("📊 详细数据")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("BTC价格", f"${metadata.get('btc_price', 0):,.2f}")
    
    with col2:
        st.metric("MA50", f"${metadata.get('ma50', 0):,.2f}")
    
    with col3:
        st.metric("MA200", f"${metadata.get('ma200', 0):,.2f}")
    
    with col4:
        st.metric("稳定币占比", f"{metadata.get('stablecoin_ratio', 0):.2f}%")
    
    # 原始数据表格
    if all_data and all_data.get("ok"):
        st.markdown("---")
        st.subheader("🔍 原始数据")
        
        data_dict = all_data.get("data", {})
        if data_dict:
            import pandas as pd
            df_data = []
            for key, value in data_dict.items():
                df_data.append({
                    "数据类型": key,
                    "数值": value.get("value", 0),
                    "数据源": value.get("provider", "unknown"),
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
    
else:
    st.warning("⚠️ 无法获取市场状态数据。请确保后端服务正在运行。")
    st.info(f"后端地址: {BACKEND_URL}")
    st.code(f"""
# 启动后端服务:
cd backend
python -m uvicorn bullbear_backend.main:app --reload --port 8000
    """)

# 侧边栏信息
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 关于")
st.sidebar.markdown("""
**BullBear Dashboard** 是加密市场状态机的可视化界面。

**四象限状态:**
- 🔥 **牛市进攻**: 趋势多 + 资金进攻
- 📈 **牛市修复**: 趋势多 + 资金防守
- ⚡ **熊市反弹**: 趋势空 + 资金进攻
- 🩸 **熊市消化**: 趋势空 + 资金防守
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 链接")
st.sidebar.markdown(f"""
- [API文档]({BACKEND_URL}/docs)
- [健康检查]({BACKEND_URL}/api/health)
""")

