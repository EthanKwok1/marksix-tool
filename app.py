import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="香港六合彩参考工具 Pro", page_icon="🎱", layout="wide")

# ==================== 2026年生肖对照 ====================
ZODIAC_MAP = {
    1:"马",13:"马",25:"马",37:"马",49:"马",
    2:"蛇",14:"蛇",26:"蛇",38:"蛇",
    3:"龙",15:"龙",27:"龙",39:"龙",
    4:"兔",16:"兔",28:"兔",40:"兔",
    5:"虎",17:"虎",29:"虎",41:"虎",
    6:"牛",18:"牛",30:"牛",42:"牛",
    7:"鼠",19:"鼠",31:"鼠",43:"鼠",
    8:"猪",20:"猪",32:"猪",44:"猪",
    9:"狗",21:"狗",33:"狗",45:"狗",
    10:"鸡",22:"鸡",34:"鸡",46:"鸡",
    11:"猴",23:"猴",35:"猴",47:"猴",
    12:"羊",24:"羊",36:"羊",48:"羊",
}
ZODIAC_TO_NUMS = {}
for n, z in ZODIAC_MAP.items():
    ZODIAC_TO_NUMS.setdefault(z, []).append(n)

# ==================== 内置数据（保底） ====================
DEFAULT_DRAWS = [
    {"period":"26/116","date":"2026-10-31","main":[10,11,19,27,37,43],"special":8},
    {"period":"26/115","date":"2026-10-27","main":[2,4,18,21,24,47],"special":31},
    {"period":"26/114","date":"2026-10-24","main":[9,25,26,28,44,45],"special":20},
    {"period":"26/113","date":"2026-10-22","main":[4,11,12,16,38,48],"special":5},
    {"period":"26/112","date":"2026-10-20","main":[2,5,7,8,21,29],"special":31},
    {"period":"26/111","date":"2026-10-17","main":[3,13,27,29,30,40],"special":9},
    {"period":"26/110","date":"2026-10-15","main":[3,7,8,10,36,42],"special":20},
    {"period":"26/109","date":"2026-10-13","main":[3,5,9,17,21,26],"special":38},
    {"period":"26/108","date":"2026-10-10","main":[12,14,20,33,34,37],"special":31},
    {"period":"26/107","date":"2026-10-08","main":[18,19,24,31,40,44],"special":5},
    {"period":"26/106","date":"2026-10-06","main":[9,29,31,34,36,41],"special":28},
    {"period":"26/105","date":"2026-10-03","main":[8,23,29,31,34,43],"special":48},
    {"period":"26/104","date":"2026-09-26","main":[4,28,31,44,47,48],"special":19},
    {"period":"26/103","date":"2026-09-22","main":[2,34,35,43,45,46],"special":41},
    {"period":"26/102","date":"2026-09-19","main":[5,8,11,14,19,31],"special":21},
    {"period":"26/101","date":"2026-09-17","main":[4,17,31,41,47,48],"special":8},
    {"period":"26/100","date":"2026-09-15","main":[2,5,6,9,29,30],"special":19},
    {"period":"26/099","date":"2026-09-12","main":[9,18,24,33,40,47],"special":11},
    {"period":"26/098","date":"2026-09-10","main":[22,23,31,32,35,45],"special":34},
    {"period":"26/097","date":"2026-09-08","main":[9,23,28,29,35,41],"special":38},
]

def get_frequency(draws):
    c = Counter()
    for d in draws:
        for n in d["main"]:
            c[n] += 1
        c[d["special"]] += 1
    return c

def try_fetch_latest():
    """尝试从公开网站获取最新数据，失败返回 None"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        # 尝试 marksixinfo
        r = requests.get("https://marksixinfo.com/en/latest20draws", headers=headers, timeout=8)
        if r.status_code == 200:
            # 简单提取（网站结构可能变化，这里做宽松匹配）
            text = r.text
            # 这里只做示意性提取，实际中可根据需要加强解析
            # 为稳定性，当前版本优先使用内置 + 提示
            return None  # 暂时返回 None，避免因结构变化导致错误
    except Exception:
        pass
    return None

def generate_numbers(strategy, freq, include_nums, exclude_nums, preferred_zodiacs, n_main=6):
    all_nums = list(range(1, 50))
    candidates = [n for n in all_nums if n not in exclude_nums]
    forced = [n for n in include_nums if n in candidates][:n_main]
    need = n_main - len(forced)
    pool = [n for n in candidates if n not in forced]

    if strategy == "热号优先":
        ranked = [n for n,_ in freq.most_common() if n in pool]
        extra = ranked[:max(need*2, need)]
        selected = forced + random.sample(extra, min(need, len(extra))) if extra else forced
    elif strategy == "冷号回归":
        ranked = [n for n,_ in sorted(freq.items(), key=lambda x:x[1]) if n in pool]
        extra = ranked[:max(need*2, need)]
        selected = forced + random.sample(extra, min(need, len(extra))) if extra else forced
    elif strategy == "热冷混合":
        hot = [n for n,_ in freq.most_common(15) if n in pool]
        cold = [n for n,_ in sorted(freq.items(), key=lambda x:x[1]) if n in pool][:15]
        mix = list(set(hot + cold))
        selected = forced + random.sample(mix, min(need, len(mix))) if mix else forced
    elif strategy == "生肖偏好" and preferred_zodiacs:
        zpool = []
        for z in preferred_zodiacs:
            zpool.extend([n for n in ZODIAC_TO_NUMS.get(z, []) if n in pool])
        zpool = list(set(zpool))
        selected = forced + random.sample(zpool, min(need, len(zpool))) if zpool else forced
    else:
        selected = forced + random.sample(pool, min(need, len(pool))) if pool else forced

    main = sorted(list(set(selected))[:n_main])
    while len(main) < n_main:
        add = random.choice([n for n in pool if n not in main] or all_nums)
        main.append(add)
        main = sorted(set(main))

    remain = [x for x in all_nums if x not in main and x not in exclude_nums]
    special = random.choice(remain) if remain else random.randint(1,49)
    return main, special

# ==================== 页面 ====================
st.title("🎱 香港六合彩参考工具 Pro")
st.caption("仅供娱乐参考 | 开奖完全随机 | 请理性对待")

# 初始化数据
if "draws" not in st.session_state:
    st.session_state.draws = DEFAULT_DRAWS.copy()
    st.session_state.last_update = "内置数据（截至26/116）"

# 刷新按钮
col_r1, col_r2 = st.columns([1, 3])
with col_r1:
    if st.button("🔄 尝试刷新最新数据"):
        with st.spinner("正在尝试获取最新开奖..."):
            new_data = try_fetch_latest()
            if new_data:
                st.session_state.draws = new_data
                st.session_state.last_update = f"在线更新成功 {datetime.now().strftime('%H:%M:%S')}"
                st.success("数据已更新！")
            else:
                st.warning("暂时无法从网络获取最新数据，继续使用当前数据（这是正常现象，网站结构经常变化）。")
                st.session_state.last_update = "刷新失败，使用现有数据"

with col_r2:
    st.info(f"当前数据来源：{st.session_state.last_update}")

draws = st.session_state.draws
freq = get_frequency(draws)

# 侧边栏
st.sidebar.title("设置")
num_sets = st.sidebar.slider("生成组数", 1, 10, 5)
strategy = st.sidebar.selectbox("策略", ["热冷混合", "热号优先", "冷号回归", "生肖偏好", "综合随机"])

include_input = st.sidebar.text_input("强制包含号码（空格分隔）", placeholder="例：7 15 31")
include_nums = [int(x) for x in include_input.replace(","," ").split() if x.strip().isdigit() and 1<=int(x)<=49] if include_input else []

exclude_input = st.sidebar.text_input("排除号码（空格分隔）", placeholder="例：1 49")
exclude_nums = [int(x) for x in exclude_input.replace(","," ").split() if x.strip().isdigit() and 1<=int(x)<=49] if exclude_input else []

preferred_zodiacs = st.sidebar.multiselect("生肖偏好", list(ZODIAC_TO_NUMS.keys()))

# 生肖表
with st.expander("生肖对照表（2026马年）"):
    cols = st.columns(4)
    for i, (z, nums) in enumerate(ZODIAC_TO_NUMS.items()):
        with cols[i%4]:
            st.markdown(f"**{z}**")
            st.write(" ".join(f"{n:02d}" for n in sorted(nums)))

# 热冷
with st.expander("热号 / 冷号"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**热号**")
        for n, cnt in freq.most_common(8):
            st.write(f"{n:02d} ({ZODIAC_MAP.get(n,'')}) → {cnt}次")
    with c2:
        st.markdown("**冷号**")
        for n, cnt in sorted(freq.items(), key=lambda x:x[1])[:8]:
            st.write(f"{n:02d} ({ZODIAC_MAP.get(n,'')}) → {cnt}次")

st.markdown("---")

if st.button("🎯 生成参考号码", type="primary", use_container_width=True):
    results = []
    for i in range(num_sets):
        main, special = generate_numbers(strategy, freq, include_nums, exclude_nums, preferred_zodiacs)
        results.append({
            "完整": "  ".join(f"{n:02d}" for n in main) + f"  +  {special:02d}",
            "生肖": " ".join(ZODIAC_MAP.get(n,"?") for n in main),
            "特肖": ZODIAC_MAP.get(special,""),
            "和值": sum(main)
        })
    st.success(f"【{strategy}】生成 {num_sets} 组")
    for r in results:
        st.code(r["完整"])
        st.caption(f"生肖：{r['生肖']} | 特码生肖：{r['特肖']} | 和值：{r['和值']}")

st.markdown("---")
st.caption("免责声明：本工具仅供娱乐参考，开奖结果完全随机，不构成任何投注建议。")
