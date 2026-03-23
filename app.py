def init_form_state():
    defaults = {
        "client_input": "新客户",
        "rate_input": 0.0450,
        "valid_time_input": "48 Hours",
        "quote_id_input": f"KDKM-{datetime.datetime.now().strftime('%m%d%H%M')}",
        "service_pct_input": 10.0,
        "pay_fee_pct_input": 3.0,
        "freight_status_input": "已确认",
        "pay_method_input": "微信支付",
        "weight_input": 1.0,
        "quote_freight_input": 2200,
        "cost_freight_input": 1400,
        "other_cost_input": 0,
        "editor_df": make_empty_items_df(),
        "edit_mode": False,
        "edit_source_quote_id": "",
        "edit_root_quote_id": "",
        "edit_version": 1,

        # 新增：保存后延迟重置
        "pending_reset_after_save": False,
        "pending_success_message": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_form_state():
    st.session_state["client_input"] = "新客户"
    st.session_state["rate_input"] = 0.0450
    st.session_state["valid_time_input"] = "48 Hours"
    st.session_state["quote_id_input"] = f"KDKM-{datetime.datetime.now().strftime('%m%d%H%M')}"
    st.session_state["service_pct_input"] = 10.0
    st.session_state["pay_fee_pct_input"] = 3.0
    st.session_state["freight_status_input"] = "已确认"
    st.session_state["pay_method_input"] = "微信支付"
    st.session_state["weight_input"] = 1.0
    st.session_state["quote_freight_input"] = 2200
    st.session_state["cost_freight_input"] = 1400
    st.session_state["other_cost_input"] = 0
    st.session_state["editor_df"] = make_empty_items_df()
    st.session_state["edit_mode"] = False
    st.session_state["edit_source_quote_id"] = ""
    st.session_state["edit_root_quote_id"] = ""
    st.session_state["edit_version"] = 1
    st.session_state["pending_reset_after_save"] = False
    st.session_state["pending_success_message"] = ""

    if "items_editor" in st.session_state:
        del st.session_state["items_editor"]


def apply_pending_reset_if_needed():
    if not st.session_state.get("pending_reset_after_save", False):
        return

    st.session_state["client_input"] = "新客户"
    st.session_state["rate_input"] = 0.0450
    st.session_state["valid_time_input"] = "48 Hours"
    st.session_state["quote_id_input"] = get_next_quote_id()
    st.session_state["service_pct_input"] = 10.0
    st.session_state["pay_fee_pct_input"] = 3.0
    st.session_state["freight_status_input"] = "已确认"
    st.session_state["pay_method_input"] = "微信支付"
    st.session_state["weight_input"] = 1.0
    st.session_state["quote_freight_input"] = 2200
    st.session_state["cost_freight_input"] = 1400
    st.session_state["other_cost_input"] = 0
    st.session_state["editor_df"] = make_empty_items_df()

    st.session_state["edit_mode"] = False
    st.session_state["edit_source_quote_id"] = ""
    st.session_state["edit_root_quote_id"] = ""
    st.session_state["edit_version"] = 1

    if "items_editor" in st.session_state:
        del st.session_state["items_editor"]

    st.session_state["pending_reset_after_save"] = False


def get_next_quote_id():
    return f"KDKM-{datetime.datetime.now().strftime('%m%d%H%M%S')}"


def load_record_into_form(record: dict):
    st.session_state["client_input"] = str(record.get("客户", "新客户") or "新客户")
    st.session_state["rate_input"] = float(pd.to_numeric(record.get("汇率", 0.0450), errors="coerce") or 0.0450)
    st.session_state["valid_time_input"] = str(record.get("有效期", "48 Hours") or "48 Hours")
    st.session_state["service_pct_input"] = float(pd.to_numeric(record.get("服务费%", 10.0), errors="coerce") or 10.0)
    st.session_state["pay_fee_pct_input"] = float(pd.to_numeric(record.get("手续费%", 3.0), errors="coerce") or 3.0)
    st.session_state["freight_status_input"] = str(record.get("运费状态", "已确认") or "已确认")
    st.session_state["pay_method_input"] = str(record.get("收款通道", "微信支付") or "微信支付")
    st.session_state["weight_input"] = float(pd.to_numeric(record.get("重量KG", 0), errors="coerce") or 0)
    st.session_state["quote_freight_input"] = int(pd.to_numeric(record.get("报价运费JPY", 0), errors="coerce") or 0)
    st.session_state["cost_freight_input"] = int(pd.to_numeric(record.get("成本运费JPY", 0), errors="coerce") or 0)
    st.session_state["other_cost_input"] = int(pd.to_numeric(record.get("额外杂费", 0), errors="coerce") or 0)
    st.session_state["editor_df"] = parse_items_json(record.get("商品明细"))
    st.session_state["edit_mode"] = True
    st.session_state["edit_source_quote_id"] = str(record.get("单号", "") or "")
    root_quote_id = str(record.get("根单号", "") or record.get("单号", "") or "")
    st.session_state["edit_root_quote_id"] = root_quote_id
    current_version = int(pd.to_numeric(record.get("版本", 1), errors="coerce") or 1)
    st.session_state["edit_version"] = current_version + 1
    st.session_state["quote_id_input"] = get_next_quote_id()

    if "items_editor" in st.session_state:
        del st.session_state["items_editor"]


# --- 2. CSS ---
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: "Noto Sans CJK SC", "Noto Sans SC", "WenQuanYi Zen Hei", "WenQuanYi Micro Hei", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.quote-container {
    background: white;
    padding: 30px;
    border-radius: 20px;
    border: 1px solid #f0f0f0;
    margin-top: 15px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.club-title {
    font-size: 2.0rem !important;
    font-weight: 700;
    color: #1a1a1a;
    line-height: 1.1;
    letter-spacing: -0.02em;
}

.client-info {
    font-size: 0.94rem;
    color: #555;
    font-weight: 700;
    margin-top: 10px;
    line-height: 1.6;
}

.payment-header {
    padding: 13px 20px;
    color: white;
    border-radius: 12px 12px 0 0;
    font-weight: 600;
    font-size: 0.98rem;
}

.detail-box {
    padding: 18px;
    border-radius: 0 0 12px 12px;
    border: 1px solid #eee;
    border-top: none;
    background-color: #fdfdfd;
}

.qr-instruction-header {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-bottom: none;
    padding: 10px 12px;
    border-radius: 15px 15px 0 0;
    text-align: center;
}

.pay-warning {
    color: #E74C3C;
    font-weight: 800;
    font-size: 0.92rem;
    margin-bottom: 3px;
}

.service-guarantee {
    margin-top: 18px;
    padding: 15px;
    border-radius: 12px;
    border: 1px dashed #ccc;
    background-color: #fafafa;
}

.guarantee-title {
    font-size: 0.90rem;
    font-weight: 700;
    color: #444;
    margin-bottom: 8px;
}

.guarantee-item {
    font-size: 0.80rem;
    color: #777;
    line-height: 1.58;
}

.qr-footer-note {
    margin-top: 14px;
    text-align: center;
    font-size: 0.78rem;
    color: #999;
    line-height: 1.5;
}

.profit-panel {
    background-color: #1e2130;
    padding: 18px;
    border-radius: 12px;
    color: #ecf0f1;
    margin-top: 15px;
}

.profit-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 0.84rem;
    opacity: 0.95;
}

.control-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: #333;
    margin: 18px 0 10px 0;
}

.total-label-jpy {
    font-size: 1.8rem;
    font-weight: 700;
    color: #222;
    text-align: right;
    margin-top: 10px;
    letter-spacing: -0.02em;
}

.rmb-price-ref {
    color: #E74C3C;
    font-size: 1.05rem !important;
    font-weight: 700;
    text-align: right;
}

.rmb-note {
    font-size: 0.76rem;
    color: #aaa;
    text-align: right;
    margin-top: 2px;
}

.discount-text {
    color: #E74C3C;
    font-weight: 700;
}

.items-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0 18px;
}

.items-grid.two-col {
    grid-template-columns: 1fr 1fr;
}

.item-card {
    padding: 8px 0;
    border-bottom: 1px dashed #eee;
    transition: all 0.18s ease;
}

.item-card:hover {
    background: rgba(0,0,0,0.015);
}

.item-main-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.90rem;
    font-weight: 600;
    color: #2c3e50;
    gap: 12px;
}

.item-sub-row {
    display: flex;
    justify-content: space-between;
    margin-top: 3px;
    font-size: 0.76rem;
    color: #777;
    gap: 12px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px dashed #eee;
    font-size: 0.90rem;
    font-weight: 600;
}

.summary-row.subtle {
    color: #555;
}

.summary-row.strong {
    color: #2c3e50;
}

.summary-row.discount {
    color: #E74C3C;
}

.fee-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px dashed #eee;
    font-size: 0.90rem;
    font-weight: 600;
}

.grand-row-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: #2C3E50;
}

.status-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
}

.status-quote {
    background: #fff3cd;
    color: #856404;
}

.status-deal {
    background: #d4edda;
    color: #155724;
}

.qr-image-wrap img {
    width:68% !important;
    max-width: 230px !important;
    margin: 0 auto;
    display: block;
}

/* 录入表格字体保持舒服但稳定 */
div[data-testid="stDataEditor"] [role="columnheader"] {
    font-size: 0.86rem !important;
}

div[data-testid="stDataEditor"] [role="gridcell"] {
    font-size: 0.88rem !important;
}

div[data-testid="stDataEditor"] input,
div[data-testid="stDataEditor"] textarea {
    font-size: 0.88rem !important;
}
</style>
""", unsafe_allow_html=True)

init_form_state()
apply_pending_reset_if_needed()

if st.session_state.get("pending_success_message"):
    st.success(st.session_state["pending_success_message"])
    st.session_state["pending_success_message"] = ""


# --- 3. 菜单 ---
with st.sidebar:
    st.title("🐻 KDKM V12.0")
    menu = st.radio("导航", ["新建报价", "历史订单", "运营分析", "系统设置"], key="menu")


# --- 4. 新建报价 ---
if menu == "新建报价":
    if st.session_state.get("edit_mode", False):
        st.info(
            f"📝 当前为修订模式：将基于来源单号 {st.session_state.get('edit_source_quote_id', '')} "
            f"生成 V{st.session_state.get('edit_version', 1)} 新版本，不会覆盖旧记录。"
        )

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        client = c1.text_input("客户姓名", key="client_input")
        rate = c2.number_input("结算汇率", format="%.4f", key="rate_input")
        valid_time = c3.selectbox("有效期", ["48 Hours", "24 Hours", "3 Days"], key="valid_time_input")
        quote_id = c4.text_input("单号", key="quote_id_input")

        d1, d2, d3, d4 = st.columns(4)
        service_pct = d1.number_input("服务费 %", step=0.5, key="service_pct_input")
        pay_fee_pct = d2.number_input("手续费 %", step=0.1, key="pay_fee_pct_input")
        freight_status = d3.selectbox("运费状态", ["已确认", "待确认"], key="freight_status_input")

        qr_list = [f.replace(".png", "") for f in os.listdir(QR_DIR) if f.endswith(".png")]
        pay_method = d4.selectbox("收款通道", ["微信支付"] + qr_list, key="pay_method_input")

    st.markdown('<div class="control-title">📦 商品录入与成本控制</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)

    w = f1.number_input("重量 (KG)", min_value=0.0, step=0.1, key="weight_input")
    u_q = f2.number_input("报价运费 (JPY)", min_value=0, step=1, key="quote_freight_input")
    u_c = f3.number_input("成本运费 (JPY)", min_value=0, step=1, key="cost_freight_input")
    other_c = f4.number_input("额外杂费", min_value=0, step=100, key="other_cost_input")

    ship_total_quote = int(w * u_q)
    ship_total_cost = int(w * u_c)

    st.info("💡 可在【折扣】列为不同商品单独设置折扣，100 即为不打折。按 Tab 键可更快录入。")

    editor_seed = st.session_state.get("editor_df", make_empty_items_df()).copy()
    if editor_seed.empty:
        editor_seed = make_empty_items_df()

    df_input = st.data_editor(
        editor_seed,
        key="items_editor",
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        row_height=38,
        column_config={
            "商品": st.column_config.TextColumn("商品", width="large", required=True),
            "数量": st.column_config.NumberColumn("数量", min_value=0, step=1, width="small"),
            "售价": st.column_config.NumberColumn("售价", min_value=0, step=100, width="small"),
            "折扣": st.column_config.NumberColumn("折扣", min_value=0.0, max_value=100.0, step=1.0, width="small"),
            "成本": st.column_config.NumberColumn("成本", min_value=0, step=100, width="small"),
        }
    )

    st.session_state["editor_df"] = df_input.copy()

    valid_df = df_input.copy()
    valid_df["商品"] = valid_df["商品"].fillna("").astype(str)
    valid_df = valid_df[valid_df["商品"].str.strip() != ""].copy()

    if not valid_df.empty:
        valid_df["数量"] = pd.to_numeric(valid_df["数量"], errors="coerce").fillna(0).astype(int).clip(lower=0)
        valid_df["售价"] = pd.to_numeric(valid_df["售价"], errors="coerce").fillna(0).astype(float).clip(lower=0)
        valid_df["折扣"] = pd.to_numeric(valid_df["折扣"], errors="coerce").fillna(100.0).astype(float).clip(lower=0, upper=100)
        valid_df["成本"] = pd.to_numeric(valid_df["成本"], errors="coerce").fillna(0).astype(float).clip(lower=0)

        valid_df["项原价"] = valid_df["数量"] * valid_df["售价"]
        valid_df["项折后"] = valid_df["项原价"] * (valid_df["折扣"] / 100.0)

    p_rev_original = int(valid_df["项原价"].sum()) if not valid_df.empty else 0
    p_rev = int(valid_df["项折后"].sum()) if not valid_df.empty else 0
    discount_amount = p_rev_original - p_rev

    p_cost = int((valid_df["数量"] * valid_df["成本"]).sum()) if not valid_df.empty else 0

    payment1_jpy = p_rev
    disp_service_fee = int(p_rev * (service_pct / 100))
    disp_pay_fee = int((p_rev + disp_service_fee) * (pay_fee_pct / 100))
    p2_total = disp_service_fee + disp_pay_fee

    if freight_status == "已确认":
        grand_total_jpy = p_rev + p2_total + ship_total_quote
    else:
        grand_total_jpy = p_rev + p2_total

    grand_total_rmb = round(grand_total_jpy * rate, 2)

    with st.sidebar:
        loss_gap = int(grand_total_jpy * 0.02) if grand_total_jpy > 0 else 0
        net_profit_jpy = (
            (p_rev - p_cost)
            + (ship_total_quote - ship_total_cost)
            + disp_service_fee
            + disp_pay_fee
            - loss_gap
            - other_c
        )
        net_profit_rmb = round(net_profit_jpy * rate, 2)

        st.markdown(f"""
            <div class="profit-panel">
                <div style="font-weight:600; margin-bottom:12px; border-bottom:1px solid #3d4256; padding-bottom:5px;">📊 收益透视图</div>
                <div class="profit-row"><span>商品利</span><span>+¥{p_rev - p_cost:,}</span></div>
                <div class="profit-row"><span>代购费</span><span>+¥{disp_service_fee:,}</span></div>
                <div class="profit-row"><span>运费差</span><span>+¥{ship_total_quote - ship_total_cost:,}</span></div>
                <div class="profit-row"><span>通道差</span><span>+¥{disp_pay_fee:,}</span></div>
                <div class="profit-row" style="color:#e74c3c;"><span>结算损耗(2%)</span><span>-¥{loss_gap:,}</span></div>
                <div class="profit-row" style="color:#f39c12;"><span>额外杂费</span><span>-¥{other_c:,}</span></div>
                <hr style="margin:10px 0; border-top:1px solid #3d4256;">
                <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                    <span style="font-weight:600; padding-bottom: 5px;">预估净利</span>
                    <div style="text-align:right;">
                        <div style="font-size:1.28rem; font-weight:700; color:#27ae60;">¥{net_profit_jpy:,}</div>
                        <div style="font-size:0.86rem; color:#f39c12; font-weight:600; margin-top:2px;">≈ RMB {net_profit_rmb:,}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="quote-container">
        <div style="display:flex; justify-content:space-between; align-items:flex-end;">
            <div>
                <div class="club-title">果熊俱乐部-KuDaKuMaClub</div>
                <div class="client-info">客户姓名：{html.escape(client)} | 日期：{datetime.date.today()}</div>
            </div>
            <div style="text-align:right; color:#777; font-size:0.86rem;">
                <div>单号：{html.escape(quote_id)}</div>
                <div>有效期：<span style="color:#E74C3C; font-weight:600;">{html.escape(valid_time)}</span></div>
            </div>
        </div>
        <hr style="margin: 20px 0; border:0; border-top:1px solid #eee;">
    """, unsafe_allow_html=True)

    ql, qr = st.columns([1.1, 0.9])

    with ql:
        st.markdown(
            '<div class="payment-header" style="background-color: #E74C3C;">第一笔支付：商品订购款项 (Payment 1)</div>',
            unsafe_allow_html=True
        )

        items_html = ""
        summary_html = ""

        if not valid_df.empty:
            item_cards = []

            for _, r in valid_df.iterrows():
                item_name = html.escape(str(r["商品"]))
                qty = int(r["数量"])
                orig_price = int(r["项原价"])
                discounted_price = int(r["项折后"])
                disc_pct = float(r["折扣"])

                disc_tag = ""
                if disc_pct < 100:
                    disc_tag = f" <span style='font-size:0.78rem; color:#E74C3C; font-weight:600;'>(折扣: {disc_pct:.1f}%)</span>"

                card_html = (
                    "<div class='item-card'>"
                    f"<div class='item-main-row'>"
                    f"<span>• {item_name} x{qty}{disc_tag}</span>"
                    f"<span>¥ {orig_price:,}</span>"
                    "</div>"
                )

                if disc_pct < 100 and discounted_price != orig_price:
                    card_html += (
                        f"<div class='item-sub-row'>"
                        "<span>折后金额</span>"
                        f"<span>¥ {discounted_price:,}</span>"
                        "</div>"
                    )

                card_html += "</div>"
                item_cards.append(card_html)

            grid_class = "items-grid two-col" if len(valid_df) >= 6 else "items-grid"
            items_html = f"<div class='{grid_class}'>" + "".join(item_cards) + "</div>"

            summary_html += (
                f"<div class='summary-row subtle'>"
                f"<span>商品原价合计</span><span>¥ {p_rev_original:,}</span>"
                f"</div>"
            )

            if discount_amount > 0:
                summary_html += (
                    f"<div class='summary-row strong'>"
                    f"<span>折后金额合计</span><span>¥ {p_rev:,}</span>"
                    f"</div>"
                    f"<div class='summary-row discount'>"
                    f"<span class='discount-text'>优惠折扣总计</span><span class='discount-text'>-¥ {discount_amount:,}</span>"
                    f"</div>"
                )
        else:
            items_html = "<div style='color:#bbb; padding:12px 0; font-size:0.92rem;'>等待录入...</div>"

        st.markdown(
            f"<div class='detail-box' style='border-left:4px solid #E74C3C;'>"
            f"{items_html}"
            f"{summary_html}"
            f"<div class='total-label-jpy'>¥ {payment1_jpy:,} JPY</div>"
            f"<div class='rmb-price-ref'>参考 RMB：{round(payment1_jpy * rate, 2):,}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="payment-header" style="background-color: #3498DB; margin-top:20px;">第二笔支付：国际物流与服务 (Payment 2)</div>',
            unsafe_allow_html=True
        )

        if freight_status == "已确认":
            second_total = p2_total + ship_total_quote
            st.markdown(
                f"<div class='detail-box' style='border-left:4px solid #3498DB;'>"
                f"<div class='fee-row'><span>代购服务费 ({service_pct}%)</span><span>¥ {disp_service_fee:,}</span></div>"
                f"<div class='fee-row'><span>跨境支付通道费 ({pay_fee_pct}%)</span><span>¥ {disp_pay_fee:,}</span></div>"
                f"<div class='fee-row'><span>国际物流费用 ({w:.1f} KG)</span><span>¥ {ship_total_quote:,}</span></div>"
                f"<div class='total-label-jpy'>¥ {second_total:,} JPY</div>"
                f"<div class='rmb-price-ref'>参考 RMB：{round(second_total * rate, 2):,}</div>"
                f"<div class='rmb-note'>※ 实际人民币金额按支付时即时汇率折算</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='detail-box' style='border-left:4px solid #3498DB;'>"
                f"<div class='fee-row'><span>代购服务费 ({service_pct}%)</span><span>¥ {disp_service_fee:,}</span></div>"
                f"<div class='fee-row'><span>跨境支付通道费 ({pay_fee_pct}%)</span><span>¥ {disp_pay_fee:,}</span></div>"
                f"<div class='fee-row'><span>国际物流费用</span><span>到货后结算</span></div>"
                f"<div class='total-label-jpy'>¥ {p2_total:,} JPY</div>"
                f"<div class='rmb-price-ref'>参考 RMB：{round(p2_total * rate, 2):,}</div>"
                f"<div class='rmb-note'>※ 国际物流费用将在商品到货后按实际重量结算</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.markdown(
            '<div class="payment-header" style="background-color: #2C3E50; margin-top:20px;">🧾 订单总计 (Grand Total)</div>',
            unsafe_allow_html=True
        )

        if freight_status == "已确认":
            st.markdown(
                f"<div class='detail-box' style='border-left:4px solid #2C3E50; background-color:#f8f9fa;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<span class='grand-row-title'>两笔支付合计</span>"
                f"<div style='text-align:right;'>"
                f"<div class='total-label-jpy' style='color:#2C3E50; margin-top:0;'>¥ {grand_total_jpy:,} JPY</div>"
                f"<div class='rmb-price-ref' style='color:#2C3E50;'>参考 RMB：{grand_total_rmb:,}</div>"
                f"</div></div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='detail-box' style='border-left:4px solid #2C3E50; background-color:#f8f9fa;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<span class='grand-row-title'>当前已确认金额</span>"
                f"<div style='text-align:right;'>"
                f"<div class='total-label-jpy' style='color:#2C3E50; margin-top:0;'>¥ {grand_total_jpy:,} JPY</div>"
                f"<div class='rmb-price-ref' style='color:#2C3E50;'>参考 RMB：{grand_total_rmb:,}</div>"
                f"</div></div></div>",
                unsafe_allow_html=True
            )

        st.markdown("""
            <div class="service-guarantee">
                <div class="guarantee-title">📦 订单处理流程</div>
                <div class="guarantee-item">1. 确认订单信息无误并完成付款后，我方将尽快联系店铺安排采购。</div>
                <div class="guarantee-item">2. 如遇店铺暂时缺货，我方会第一时间与您沟通，可选择退款或等待补货后再安排下单。</div>
            </div>
        """, unsafe_allow_html=True)

    with qr:
        st.markdown("""
            <div class="qr-instruction-header">
                <div class="pay-warning">⚠️ 订单需分两笔金额支付</div>
                <b>请扫码并输入对应日元金额完成支付</b>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div style="border: 1px solid #e9ecef; border-top:none; padding:16px 18px 14px 18px; border-radius: 0 0 15px 15px; text-align:center;">',
            unsafe_allow_html=True
        )

        qr_file = os.path.join(QR_DIR, f"{pay_method}.png")
        if os.path.exists(qr_file):
            st.markdown("<div class='qr-image-wrap'>", unsafe_allow_html=True)
            st.image(qr_file)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("未找到对应二维码图片")

        st.markdown(f"""
            <div class="qr-footer-note">
                <b>[ 完成支付后请截屏回传此对话框 ]</b><br>
                当前结算参考汇率：1 JPY = {rate:.4f} RMB<br>
                果熊俱乐部 | 感谢您的信任
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="service-guarantee">
                <div class="guarantee-title">🛡️ 果熊服务须知 / Service Notes:</div>
                <div class="guarantee-item">1. 所有商品均通过日本正规渠道采购，确保正品。</div>
                <div class="guarantee-item">2. 国际物流预计14–21个工作日送达，具体到达时间以实际物流情况为准。</div>
                <div class="guarantee-item">3. 国际物流时间可能受天气、航班及海关查验等因素影响，请以实际情况为准。</div>
                <div class="guarantee-item">4. 代购商品确认付款后即安排采购，非质量问题原则上不支持取消或退换。</div>
                <div class="guarantee-item">5. 商品尺寸、版型等信息仅供参考，具体适配情况因个人体型差异可能存在不同，尺码选择需客户自行确认。</div>
                <div class="guarantee-item">6. 人民币金额仅供参考，最终以支付时银行或支付平台实时汇率为准。</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    b_reset1, b_reset2 = st.columns([1, 5])
    with b_reset1:
        if st.button("🧹 重置表单", use_container_width=True):
            reset_form_state()
            st.rerun()

    st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)

    current_version = int(st.session_state.get("edit_version", 1) or 1)
    source_quote_id = st.session_state.get("edit_source_quote_id", "")
    root_quote_id = st.session_state.get("edit_root_quote_id", "") or quote_id
    is_revision = "是" if st.session_state.get("edit_mode", False) else "否"

    if not st.session_state.get("edit_mode", False):
        current_version = 1
        source_quote_id = ""
        root_quote_id = quote_id

    def build_history_row(save_status, image_path=""):
        margin = (net_profit_jpy / grand_total_jpy * 100) if grand_total_jpy else 0
        payment2_record = p2_total + ship_total_quote if freight_status == "已确认" else p2_total
        row = {
            "日期": datetime.date.today(),
            "客户": client,
            "单号": quote_id,
            "状态": save_status,
            "运费状态": freight_status,
            "总收入": grand_total_jpy,
            "总利润": net_profit_jpy,
            "利润率": round(margin, 2),
            "版本": current_version,
            "来源单号": source_quote_id,
            "根单号": root_quote_id,
            "是否修订版": is_revision,
            "商品明细": serialize_items_df(df_input),
            "汇率": rate,
            "有效期": valid_time,
            "服务费%": service_pct,
            "手续费%": pay_fee_pct,
            "重量KG": w,
            "报价运费JPY": u_q,
            "成本运费JPY": u_c,
            "额外杂费": other_c,
            "收款通道": pay_method,
            "Payment1JPY": payment1_jpy,
            "Payment2JPY": payment2_record,
            "商品原价合计": p_rev_original,
            "商品折后合计": p_rev,
            "优惠金额": discount_amount,
            "图片路径": image_path,
        }
        return pd.DataFrame([[row.get(col, "") for col in BASE_COLUMNS]], columns=BASE_COLUMNS)

    def finalize_after_save(success_message="已保存"):
        st.session_state["pending_reset_after_save"] = True
        st.session_state["pending_success_message"] = success_message
        st.rerun()

    with s1:
        if st.button("💾 保存为报价", use_container_width=True):
            if valid_df.empty:
                st.error("无法保存：请先录入商品信息")
            else:
                history = load_history()
                new_row = build_history_row("报价")
                history = pd.concat([history, new_row], ignore_index=True)
                save_history(history)
                finalize_after_save("已保存为报价")

    with s2:
        if st.button("✅ 保存为成交", use_container_width=True):
            if valid_df.empty:
                st.error("无法保存：请先录入商品信息")
            else:
                history = load_history()
                new_row = build_history_row("成交")
                history = pd.concat([history, new_row], ignore_index=True)
                save_history(history)
                finalize_after_save("已保存为成交")

    with s3:
        if st.button("🖼️ 导出报价图片", use_container_width=True):
            try:
                qr_p = os.path.join(QR_DIR, f"{pay_method}.png")
                export_path = export_quote_png(
                    client=client,
                    quote_id=quote_id,
                    valid_time=valid_time,
                    rate=rate,
                    valid_df=valid_df,
                    payment1_jpy=payment1_jpy,
                    p_rev_original=p_rev_original,
                    p_rev=p_rev,
                    discount_amount=discount_amount,
                    service_pct=service_pct,
                    disp_service_fee=disp_service_fee,
                    pay_fee_pct=pay_fee_pct,
                    disp_pay_fee=disp_pay_fee,
                    freight_status=freight_status,
                    w=w,
                    ship_total_quote=ship_total_quote,
                    p2_total=p2_total,
                    grand_total_jpy=grand_total_jpy,
                    grand_total_rmb=grand_total_rmb,
                    qr_abs_path=qr_p
                )
                st.success(f"报价图片已生成：{export_path}")
            except Exception as e:
                st.error(f"导出失败：{e}")
