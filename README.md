# marksix-tool
香港六合彩参考号码生成工具（Streamlit）
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="香港六合彩参考工具",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 波色定义 ====================
RED = {1,2,7,8,12,13,18,19,23,24,29,30,34,35,40,45,46}
BLUE = {3,4,9,10,14,15,20,25,26,31,36,37,41,42,47,48}
GREEN = {5,6,11,16,17,21,22,27,28,32,33,38,39,43,44,49}

def get_color(n):
    if n in RED: return "红"
    if n in BLUE: return "蓝"
    return "绿"

# ==================== 内置近期数据（截至26/116） ====================
DEFAULT_DRAWS = [
    {"period": "26/116", "date": "2026-10-31", "main": [10,11,19,27,37,43], "special": 8},
    {"period": "26/115", "date": "2026-10-27", "main": [2,4,18,21,24,47], "special": 31},
    {"period": "26/114", "date": "2026-10-24", "main": [9,25,26,28,44,45], "special": 20},
    {"period": "26/113", "date": "2026-10-22", "main": [4,11,12,16,38,48], "special": 5},
    {"period": "26/112", "date": "2026-10-20", "main": [2,5,7,8,21,29], "special": 31},
    {"period": "26/111", "date": "2026-10-17", "main": [3,13,27,29,30,40], "special": 9},
    {"period": "26/110", "date": "2026-10-15", "main": [3,7,8,10,36,42], "special": 20},
    {"period": "26/109", "date": "2026-10-13", "main": [3,5,9,17,21,26], "special": 38},
    {"period": "26/108", "date": "2026-10-10", "main": [12,14,20,33,34,37], "special": 31},
    {"period": "26/107", "date": "2026-10-08", "main": [18,19,24,31,40,44], "special": 5},
    {"period": "26/106", "date": "2026-10-06", "main": [9,29,31,34,36,41], "special": 28},
    {"period": "26/105", "date": "2026-10-03", "main": [8,23,29,31,34,43], "special": 48},
    {"period": "26/104", "date": "2026-09-26", "main": [4,28,31,44,47,48], "special": 19},
    {"period": "26/103", "date": "2026-09-22", "main": [2,34,35,43,45,46], "special": 41},
    {"period": "26/102", "date": "2026-09-19", "main": [5,8,11,14,19,31], "special": 21},
    {"period": "26/101", "date": "2026-09-17", "main": [4,17,31,41,47,48], "special": 8},
    {"period": "26/100", "date": "2026-09-15", "main": [2,5,6,9,29,30], "special": 19},
    {"period": "26/099", "date": "2026-09-12", "main": [9,18,24,33,40,47], "special": 11},
    {"period": "26/098", "date": "2026-09-10", "main": [22,23,31,32,35,45], "special": 34},
    {"period": "26/097", "date": "2026-09-08", "main": [9,23,28,29,35,41], "special": 38},
]

# ==================== 工具函数 ====================
def get_frequency(draws, include_special=True):
    counter = Counter()
    for d in draws:
        for n in d["main"]:
            counter[n] += 1
        if include_special:
            counter[d["special"]] += 1
    return counter

def generate_numbers(strategy, freq, n_main=6):
    all_nums = list(range(1, 50))
    
    if strategy == "热号优先":
        candidates = [num for num, _ in freq.most_common(25)]
        main = sorted(random.sample(candidates, n_main))
    
    elif strategy == "冷号回归":
        cold = [num for num, _ in sorted(freq.items(), key=lambda x: x[1])][:30]
        if len(cold) < n_main:
            cold = all_nums
        main = sorted(random.sample(cold, n_main))
    
    elif strategy == "热冷混合":
        hot = [num for num, _ in freq.most_common(18)]
        cold = [num for num, _ in sorted(freq.items(), key=lambda x: x[1])][:18]
        main = sorted(random.sample(hot, 3) + random.sample(cold, 3))
    
    elif strategy == "奇偶平衡":
        odds = [i for i in all_nums if i % 2 == 1]
        evens = [i for i in all_nums if i % 2 == 0]
        main = sorted(random.sample(odds, 3) + random.sample(evens, 3))
    
    elif strategy == "大小平衡":
        small = list(range(1, 25))
        big = list(range(25, 50))
        main = sorted(random.sample(small, 3) + random.sample(big, 3))
    
    elif strategy == "波色均衡":
        r = random.sample(list(RED), 2)
        b = random.sample(list(BLUE), 2)
        g = random.sample(list(GREEN), 2)
        main = sorted(r + b + g)
    
    elif strategy == "和值控制":
        # 尝试生成和值在 140~190 的组合
        for _ in range(50):
            main = sorted(random.sample(all_nums, 6))
            if 140 <= sum(main) <= 190:
                break
        else:
            main = sorted(random.sample(all_nums, 6))
    
    else:  # 综合随机（默认）
        main = sorted(random.sample(all_nums, 6))
    
    # 特别号：从剩余号码中选
    remaining = [x for x in all_nums if x not in main]
    special = random.choice(remaining)
    
    return main, special

def format_numbers(main, special):
    main_str = "  ".join(f"{n:02d}" for n in main)
    return f"{main_str}  +  {special:02d}"

# ==================== 侧边栏 ====================
st.sidebar.title("🎱 设置面板")

st.sidebar.markdown("### 生成参数")
num_sets = st.sidebar.slider("生成组数", 1, 10, 6)
strategy = st.sidebar.selectbox(
    "生成策略",
    ["热号优先", "冷号回归", "热冷混合", "奇偶平衡", "大小平衡", "波色均衡", "和值控制", "综合随机"],
    index=2
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 数据来源")
use_builtin = st.sidebar.checkbox("使用内置近期数据（推荐）", value=True)

uploaded_file = st.sidebar.file_uploader("或上传自己的历史数据", type=["csv", "xlsx"])

st.sidebar.markdown("---")
st.sidebar.info("上传格式建议：包含「正码」和「特别号」列，或直接用内置数据即可。")

# ==================== 主界面 ====================
st.title("🎱 香港六合彩参考号码生成工具")
st.caption("仅供娱乐与数据参考 | 开奖结果完全随机 | 请理性对待，量力而行")

# 数据准备
draws = DEFAULT_DRAWS.copy()
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success(f"成功读取 {len(df)} 条记录")
        # 这里可以后续扩展解析逻辑
    except Exception as e:
        st.sidebar.error(f"读取失败：{e}")

freq = get_frequency(draws)

# 统计展示
with st.expander("📊 查看近期热号 / 冷号统计（基于内置数据）", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**出现较多的号码（热号）**")
        hot_list = freq.most_common(12)
        for num, cnt in hot_list:
            st.write(f"{num:02d}  →  {cnt} 次")
    with col_b:
        st.markdown("**出现较少的号码（冷号）**")
        cold_list = sorted(freq.items(), key=lambda x: x[1])[:12]
        for num, cnt in cold_list:
            st.write(f"{num:02d}  →  {cnt} 次")

st.markdown("---")

# 生成按钮
if st.button("🎯 立即生成参考号码", type="primary", use_container_width=True):
    results = []
    for i in range(num_sets):
        main, special = generate_numbers(strategy, freq)
        results.append({
            "组别": i + 1,
            "正选号码": " ".join(f"{n:02d}" for n in main),
            "特别号": f"{special:02d}",
            "完整": format_numbers(main, special),
            "和值": sum(main),
            "奇偶": f"{sum(1 for x in main if x%2==1)}奇{sum(1 for x in main if x%2==0)}偶",
            "波色": "".join(get_color(x)[0] for x in main)
        })
    
    # 保存到 session
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "strategy": strategy,
        "results": results
    })
    
    st.success(f"已使用【{strategy}】策略生成 {num_sets} 组号码")
    
    # 展示结果
    for r in results:
        st.code(r["完整"], language=None)
        st.caption(f"和值 {r['和值']}  |  {r['奇偶']}  |  波色分布：{r['波色']}")
    
    # 下载按钮
    df_result = pd.DataFrame(results)
    csv = df_result.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="⬇️ 下载本次结果 (CSV)",
        data=csv,
        file_name=f"marksix_ref_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

# 历史记录
if "history" in st.session_state and st.session_state.history:
    st.markdown("---")
    st.subheader("🕒 本次会话生成记录")
    for idx, item in enumerate(st.session_state.history[:5]):
        with st.expander(f"{item['time']}  |  策略：{item['strategy']}"):
            for r in item["results"]:
                st.text(r["完整"])

# 底部说明
st.markdown("---")
st.markdown("""
**使用提示**
- 推荐先用「热冷混合」或「波色均衡」试试看
- 手机访问时建议横屏或使用桌面模式查看更清晰
- 部署到 Streamlit Cloud 后，用手机浏览器打开链接即可随时使用

**免责声明**  
本工具仅根据历史数据进行统计组合与随机生成，**不具备任何预测能力**。六合彩每期开奖均为独立随机事件，过往数据不影响未来结果。请理性娱乐，勿过度投入。
""")
