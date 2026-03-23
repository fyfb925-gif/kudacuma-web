import streamlit as st
import pandas as pd
import datetime
import os
import html
import re
import shutil
import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from html2image import Html2Image

# --- 1. 基础配置 ---
st.set_page_config(page_title="果熊俱乐部-KuDaKuMaClub V11.8.1", layout="wide")

DB_FILE = "kudacuma_history.csv"
QR_DIR = "qr_codes"
EXPORT_DIR = "exports"

# Google Sheets 配置 (请确保 st.secrets 中已配置 gcp_service_account)
SHEET_ID = "1YiCSICtstqZRjkdpRpQsgS3jLC-t1BFIY6kQuxRfHho"
HISTORY_WORKSHEET = "history"

BASE_COLUMNS = [
    "日期", "客户", "单号", "状态", "运费状态", "总收入", "总利润", "利润率",
    "版本", "来源单号", "根单号", "是否修订版", "商品明细", "汇率", "有效期",
    "服务费%", "手续费%", "重量KG", "报价运费JPY", "成本运费JPY", "额外杂费",
    "收款通道", "Payment1JPY", "Payment2JPY", "商品原价合计", "商品折后合计",
    "优惠金额", "图片路径"
]

# 目录初始化
for d in [QR_DIR, EXPORT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=BASE_COLUMNS).to_csv(DB_FILE, index=False, encoding="utf-8-sig")

# =========================
# 工具函数
# =========================

def get_next_quote_id():
    """生成不带秒的单号，减少页面刷新频率"""
    return f"KDKM-{datetime.datetime.now().strftime('%m%d%H%M')}"

def make_empty_items_df():
    return pd.DataFrame([{
        "商品": "",
        "数量": 1,
        "售价": 0,
        "折扣": 100.0,
        "成本": 0
    }])

def clean_number_series(series: pd.Series) -> pd.Series:
    if series is None: return pd.Series(dtype="float64")
    s = series.astype(str).str.strip().replace({"": None, "None": None, "nan": None, "NaN": None})
    s = s.str.replace("¥", "", regex=False).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
    return pd.to_numeric(s, errors="coerce")

def parse_items_json(raw) -> pd.DataFrame:
    if not raw or str(raw).strip() in ["nan", "None", "[]"]:
        return make_empty_items_df()
    try:
        df = pd.read_json(str(raw))
        if df.empty: return make_empty_items_df()
        # 补全缺失列
        for col in ["商品", "数量", "售价", "折扣", "成本"]:
            if col not in df.columns: df[col] = "" if col == "商品" else 0
        return df[["商品", "数量", "售价", "折扣", "成本"]]
    except:
        return make_empty_items_df()

# --- 核心状态维护 ---

def init_form_state():
    """初始化所有表单状态"""
    if "editor_df" not in st.session_state:
        st.session_state["editor_df"] = make_empty_items_df()
    
    defaults = {
        "client_input": "新客户",
        "rate_input": 0.0450,
        "valid_time_input": "48 Hours",
        "quote_id_input": get_next_quote_id(),
        "service_pct_input": 10.0,
        "pay_fee_pct_input": 3.0,
        "freight_status_input": "已确认",
        "pay_method_input": "微信支付",
        "weight_input": 1.0,
        "quote_freight_input": 2200,
        "cost_freight_input": 1400,
        "other_cost_input": 0,
        "edit_mode": False,
        "edit_source_quote_id": "",
        "edit_root_quote_id": "",
        "edit_version": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_form_state():
    """彻底重置表单"""
    for key in list(st.session_state.keys()):
        if key not in ["history_df"]: # 保留历史缓存
            del st.session_state[key]
    init_form_state()
    st.rerun()

def load_record_into_form(record: dict):
    """从历史记录加载到表单"""
    st.session_state["client_input"] = str(record.get("客户", "新客户"))
    st.session_state["rate_input"] = float(pd.to_numeric(record.get("汇率", 0.0450), errors="coerce") or 0.0450)
    st.session_state["editor_df"] = parse_items_json(record.get("商品明细"))
    
    # 关键：清除编辑器组件的内部缓存，强制重新渲染新数据
    if "items_editor" in st.session_state:
        del st.session_state["items_editor"]
    
    st.session_state["edit_mode"] = True
    st.session_state["edit_version"] = int(pd.to_numeric(record.get("版本", 1), errors="coerce") or 1) + 1
    st.session_state["quote_id_input"] = get_next_quote_id()
    st.rerun()

# --- Google Sheets 交互 ---

@st.cache_resource
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scope)
        return gspread.authorize(creds)
    except:
        return None

def load_history():
    client = get_gsheet_client()
    if client:
        try:
            ws = client.open_by_key(SHEET_ID).worksheet(HISTORY_WORKSHEET)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except:
            pass
    return pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=BASE_COLUMNS)

# =========================
# 主界面
# =========================
init_form_state()

st.title("🍎 果熊报价系统 V11.8.1")

# --- 侧边栏：订单参数 ---
with st.sidebar:
    st.header("⚙️ 订单配置")
    client_name = st.text_input("客户姓名", value=st.session_state["client_input"])
    quote_id = st.text_input("单号", value=st.session_state["quote_id_input"])
    exchange_rate = st.number_input("参考汇率 (JPY->RMB)", value=st.session_state["rate_input"], format="%.4f", step=0.0001)
    
    col_a, col_b = st.columns(2)
    service_fee_pct = col_a.number_input("服务费 %", value=st.session_state["service_pct_input"])
    pay_fee_pct = col_b.number_input("通道费 %", value=st.session_state["pay_fee_pct_input"])
    
    if st.button("🔄 重置表单", use_container_width=True):
        reset_form_state()

# --- 主区域：商品录入 ---
st.markdown("### 📝 商品录入")
st.info("💡 提示：输入完成后请点击表格外任意位置或按回车，以确保数据保存。")

# 核心：使用固定的 key 来锁定编辑器状态
edited_df = st.data_editor(
    st.session_state["editor_df"],
    num_rows="dynamic",
    key="items_editor", 
    use_container_width=True,
    column_config={
        "商品": st.column_config.TextColumn("商品名称", width="large", required=True),
        "数量": st.column_config.NumberColumn("数量", min_value=1, step=1, default=1),
        "售价": st.column_config.NumberColumn("售价(JPY)", min_value=0, format="¥ %d"),
        "折扣": st.column_config.NumberColumn("折扣(%)", min_value=0, max_value=100, default=100),
        "成本": st.column_config.NumberColumn("成本(JPY)", min_value=0, format="¥ %d"),
    }
)

# 实时将编辑器的变动同步回 session_state，防止因侧边栏操作导致丢失
if edited_df is not None:
    st.session_state["editor_df"] = edited_df

# --- 计算逻辑 ---
df = st.session_state["editor_df"].copy()
df["数量"] = pd.to_numeric(df["数量"], errors="coerce").fillna(0)
df["售价"] = pd.to_numeric(df["售价"], errors="coerce").fillna(0)
df["折扣"] = pd.to_numeric(df["折扣"], errors="coerce").fillna(100.0)

# 计算单行
df["项原价"] = df["数量"] * df["售价"]
df["项折后"] = df["项原价"] * (df["折扣"] / 100.0)

p_rev_original = int(df["项原价"].sum())
p_rev_discounted = int(df["项折后"].sum())
discount_total = p_rev_original - p_rev_discounted

# 服务费与通道费
service_fee = int(p_rev_discounted * (service_fee_pct / 100.0))
pay_fee = int(p_rev_discounted * (pay_fee_pct / 100.0))

# --- 展示与保存 ---
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("商品原价总计", f"¥ {p_rev_original:,}")
c2.metric("折后应付 (P1)", f"¥ {p_rev_discounted:,}", delta=f"-{discount_total}" if discount_total > 0 else None)
c3.metric("预估服务费", f"¥ {service_fee + pay_fee:,}")

if st.button("💾 保存并生成报价单", type="primary", use_container_width=True):
    # 此处添加您原有的导出图片和保存到 Google Sheets 的逻辑
    # 使用 st.session_state["editor_df"] 作为最终数据源
    st.success(f"订单 {quote_id} 已准备就绪！")
    # ... 原有保存逻辑 ...
