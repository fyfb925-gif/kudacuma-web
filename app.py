import streamlit as st
import pandas as pd
import datetime
import os
import html
from pathlib import Path

from html2image import Html2Image

# --- 1. 基础配置 ---
st.set_page_config(page_title="果熊俱乐部-KuDaKuMaClub V11.8", layout="wide")
DB_FILE = "kudacuma_history.csv"
QR_DIR = "qr_codes"
EXPORT_DIR = "exports"

BASE_COLUMNS = [
    "日期", "客户", "单号", "状态", "运费状态", "总收入", "总利润", "利润率"
]

if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

if not os.path.exists(EXPORT_DIR):
    os.makedirs(EXPORT_DIR)

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=BASE_COLUMNS).to_csv(
        DB_FILE, index=False, encoding="utf-8-sig"
    )


def load_history():
    try:
        df = pd.read_csv(DB_FILE, encoding="utf-8-sig")
    except Exception:
        df = pd.DataFrame(columns=BASE_COLUMNS)

    for col in BASE_COLUMNS:
        if col not in df.columns:
            if col == "状态":
                df[col] = "成交"
            elif col == "运费状态":
                df[col] = "已确认"
            else:
                df[col] = ""

    return df[BASE_COLUMNS].copy()


def save_history(df: pd.DataFrame):
    df = df.copy()
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[BASE_COLUMNS]
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")


def prepare_history_for_analysis(df):
    if df.empty:
        return df

    temp = df.copy()
    temp["日期"] = pd.to_datetime(temp["日期"], errors="coerce")
    temp["客户"] = temp["客户"].fillna("未知客户").astype(str)
    temp["单号"] = temp["单号"].fillna("").astype(str)
    temp["状态"] = temp["状态"].fillna("报价").astype(str)
    temp["运费状态"] = temp["运费状态"].fillna("已确认").astype(str)
    temp["总收入"] = pd.to_numeric(temp["总收入"], errors="coerce").fillna(0)
    temp["总利润"] = pd.to_numeric(temp["总利润"], errors="coerce").fillna(0)
    temp["利润率"] = pd.to_numeric(temp["利润率"], errors="coerce").fillna(0)

    temp = temp.dropna(subset=["日期"]).copy()
    temp["年月"] = temp["日期"].dt.strftime("%Y-%m")
    temp["日期文本"] = temp["日期"].dt.strftime("%Y-%m-%d")
    return temp


def format_jpy(v):
    return f"¥ {int(v):,}"
def _build_item_cards_html(valid_df: pd.DataFrame) -> str:
    if valid_df.empty:
        return "<div style='color:#bbb; padding:12px 0; font-size:0.92rem;'>等待录入...</div>"

    cards = []
    two_col = len(valid_df) >= 6
    grid_class = "items-grid two-col" if two_col else "items-grid"

    for _, r in valid_df.iterrows():
        item_name = html.escape(str(r["商品"]))
        qty = int(r["数量"])
        orig_price = int(r["项原价"])
        discounted_price = int(r["项折后"])
        disc_pct = float(r["折扣"])

        disc_tag = ""
        if disc_pct < 100:
            disc_tag = f" <span style='font-size:16px; color:#E74C3C; font-weight:700;'>(折扣: {disc_pct:.1f}%)</span>"

        card_html = (
            "<div class='item-card'>"
            f"<div class='item-main-row'>"
            f"<span>• {item_name} x{qty}{disc_tag}</span>"
            f"<span>¥ {orig_price:,}</span>"
            "</div>"
        )

        if disc_pct < 100 and discounted_price != orig_price:
            card_html += (
                "<div class='item-sub-row'>"
                "<span>折后金额</span>"
                f"<span>¥ {discounted_price:,}</span>"
                "</div>"
            )

        card_html += "</div>"
        cards.append(card_html)

    return f"<div class='{grid_class}'>" + "".join(cards) + "</div>"


def build_quote_export_html(
    client,
    quote_id,
    valid_time,
    rate,
    valid_df,
    payment1_jpy,
    p_rev_original,
    p_rev,
    discount_amount,
    service_pct,
    disp_service_fee,
    pay_fee_pct,
    disp_pay_fee,
    freight_status,
    w,
    ship_total_quote,
    p2_total,
    grand_total_jpy,
    grand_total_rmb,
    qr_abs_path
):
    items_html = _build_item_cards_html(valid_df)

    summary_html = (
        f"<div class='summary-row subtle'><span>商品原价合计</span><span>¥ {p_rev_original:,}</span></div>"
    )

    if discount_amount > 0:
        summary_html += (
            f"<div class='summary-row strong'><span>折后金额合计</span><span>¥ {p_rev:,}</span></div>"
            f"<div class='summary-row discount'><span>优惠折扣总计</span><span>-¥ {discount_amount:,}</span></div>"
        )

    if freight_status == "已确认":
        payment2_html = (
            f"<div class='fee-row'><span>代购服务费 ({service_pct}%)</span><span>¥ {disp_service_fee:,}</span></div>"
            f"<div class='fee-row'><span>跨境支付通道费 ({pay_fee_pct}%)</span><span>¥ {disp_pay_fee:,}</span></div>"
            f"<div class='fee-row'><span>国际物流费用 ({w:.1f} KG)</span><span>¥ {ship_total_quote:,}</span></div>"
            f"<div class='total-label-jpy'>¥ {p2_total + ship_total_quote:,} JPY</div>"
            f"<div class='rmb-price-ref'>参考 RMB：{round((p2_total + ship_total_quote) * rate, 2):,}</div>"
            f"<div class='rmb-note'>※ 实际人民币金额按支付时即时汇率折算</div>"
        )
        grand_title = "两笔支付合计"
    else:
        payment2_html = (
            f"<div class='fee-row'><span>代购服务费 ({service_pct}%)</span><span>¥ {disp_service_fee:,}</span></div>"
            f"<div class='fee-row'><span>跨境支付通道费 ({pay_fee_pct}%)</span><span>¥ {disp_pay_fee:,}</span></div>"
            f"<div class='fee-row'><span>国际物流费用</span><span>到货后结算</span></div>"
            f"<div class='total-label-jpy'>¥ {p2_total:,} JPY</div>"
            f"<div class='rmb-price-ref'>参考 RMB：{round(p2_total * rate, 2):,}</div>"
            f"<div class='rmb-note'>※ 国际物流费用将在商品到货后按实际重量结算</div>"
        )
        grand_title = "当前已确认金额"

    qr_src = Path(qr_abs_path).resolve().as_uri() if qr_abs_path and os.path.exists(qr_abs_path) else ""

    html_code = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            background: #f5f5f5;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
            color: #222;
        }}

        .page {{
            width: 1500px;
            margin: 0 auto;
            padding: 24px 24px 36px 24px;
            box-sizing: border-box;
        }}

        .quote-container {{
            background: white;
            padding: 30px;
            border-radius: 22px;
            border: 1px solid #ececec;
            box-shadow: 0 4px 18px rgba(0,0,0,0.04);
        }}

        .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}

        .club-title {{
            font-size: 56px;
            font-weight: 800;
            color: #111;
            line-height: 1.1;
        }}

        .client-info {{
            font-size: 28px;
            color: #555;
            font-weight: 700;
            margin-top: 12px;
            line-height: 1.6;
        }}

        .top-right {{
            text-align: right;
            color: #777;
            font-size: 24px;
            line-height: 1.7;
        }}

        .valid-text {{
            color: #E74C3C;
            font-weight: 700;
        }}

        .hr {{
            margin: 26px 0 22px 0;
            border-top: 1px solid #eee;
        }}

        .main-grid {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 18px;
            align-items: start;
        }}

        .payment-header {{
            padding: 18px 24px;
            color: white;
            border-radius: 16px 16px 0 0;
            font-weight: 700;
            font-size: 30px;
        }}

        .detail-box {{
            padding: 22px;
            border-radius: 0 0 16px 16px;
            border: 1px solid #eee;
            border-top: none;
            background: #fcfcfc;
        }}

        .left-card {{
            margin-bottom: 18px;
        }}

        .items-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 0 18px;
        }}

        .items-grid.two-col {{
            grid-template-columns: 1fr 1fr;
        }}

        .item-card {{
            padding: 10px 0;
            border-bottom: 1px dashed #eee;
        }}

        .item-main-row {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            font-size: 24px;
            font-weight: 700;
            color: #2c3e50;
            line-height: 1.5;
        }}

        .item-sub-row {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            margin-top: 4px;
            font-size: 20px;
            color: #777;
            line-height: 1.5;
        }}

        .summary-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px dashed #eee;
            font-size: 24px;
            font-weight: 700;
        }}

        .summary-row.subtle {{
            color: #555;
        }}

        .summary-row.strong {{
            color: #2c3e50;
        }}

        .summary-row.discount {{
            color: #E74C3C;
        }}

        .fee-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px dashed #eee;
            font-size: 24px;
            font-weight: 700;
            line-height: 1.5;
        }}

        .grand-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
        }}

        .grand-row-title {{
            font-size: 26px;
            font-weight: 800;
            color: #2C3E50;
        }}

        .total-label-jpy {{
            font-size: 54px;
            font-weight: 800;
            color: #222;
            text-align: right;
            margin-top: 14px;
            line-height: 1.2;
        }}

        .rmb-price-ref {{
            color: #E74C3C;
            font-size: 32px;
            font-weight: 800;
            text-align: right;
            margin-top: 6px;
            line-height: 1.2;
        }}

        .rmb-note {{
            font-size: 20px;
            color: #aaa;
            text-align: right;
            margin-top: 4px;
            line-height: 1.5;
        }}

        .qr-instruction-header {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-bottom: none;
            padding: 14px;
            border-radius: 18px 18px 0 0;
            text-align: center;
        }}

        .pay-warning {{
            color: #E74C3C;
            font-weight: 800;
            font-size: 30px;
            margin-bottom: 6px;
        }}

        .pay-sub {{
            font-size: 25px;
            font-weight: 700;
            color: #333;
        }}

        .qr-box {{
            border: 1px solid #e9ecef;
            border-top: none;
            padding: 18px 20px 16px 20px;
            border-radius: 0 0 18px 18px;
            text-align: center;
            background: white;
        }}

        .qr-box img {{
            width: 72%;
            max-width: 340px;
            display: block;
            margin: 0 auto;
        }}

        .qr-footer-note {{
            margin-top: 10px;
            text-align: center;
            font-size: 20px;
            color: #999;
            line-height: 1.45;
        }}

        .service-guarantee {{
            margin-top: 18px;
            padding: 16px 18px;
            border-radius: 16px;
            border: 1px dashed #ccc;
            background: #fafafa;
        }}

        .guarantee-title {{
            font-size: 26px;
            font-weight: 800;
            color: #444;
            margin-bottom: 10px;
        }}

        .guarantee-item {{
            font-size: 21px;
            color: #777;
            line-height: 1.65;
            margin-bottom: 4px;
        }}
    </style>
    </head>
    <body>
        <div class="page">
            <div class="quote-container">
                <div class="topbar">
                    <div>
                        <div class="club-title">果熊俱乐部-KuDaKuMaClub</div>
                        <div class="client-info">客户姓名：{html.escape(str(client))} | 日期：{datetime.date.today()}</div>
                    </div>
                    <div class="top-right">
                        <div>单号：{html.escape(str(quote_id))}</div>
                        <div>有效期：<span class="valid-text">{html.escape(str(valid_time))}</span></div>
                    </div>
                </div>

                <div class="hr"></div>

                <div class="main-grid">
                    <div>
                        <div class="left-card">
                            <div class="payment-header" style="background:#E74C3C;">第一笔支付：商品订购款项 (Payment 1)</div>
                            <div class="detail-box" style="border-left:5px solid #E74C3C;">
                                {items_html}
                                {summary_html}
                                <div class="total-label-jpy">¥ {payment1_jpy:,} JPY</div>
                                <div class="rmb-price-ref">参考 RMB：{round(payment1_jpy * rate, 2):,}</div>
                            </div>
                        </div>

                        <div class="left-card">
                            <div class="payment-header" style="background:#3498DB;">第二笔支付：国际物流与服务 (Payment 2)</div>
                            <div class="detail-box" style="border-left:5px solid #3498DB;">
                                {payment2_html}
                            </div>
                        </div>

                        <div class="left-card">
                            <div class="payment-header" style="background:#2C3E50;">🧾 订单总计 (Grand Total)</div>
                            <div class="detail-box" style="border-left:5px solid #2C3E50; background:#f8f9fa;">
                                <div class="grand-row">
                                    <span class="grand-row-title">{grand_title}</span>
                                    <div style="text-align:right;">
                                        <div class="total-label-jpy" style="color:#2C3E50; margin-top:0;">¥ {grand_total_jpy:,} JPY</div>
                                        <div class="rmb-price-ref" style="color:#2C3E50;">参考 RMB：{grand_total_rmb:,}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="service-guarantee">
                            <div class="guarantee-title">📦 订单处理流程</div>
                            <div class="guarantee-item">1. 确认订单信息无误并完成付款后，我方将尽快联系店铺安排采购。</div>
                            <div class="guarantee-item">2. 如遇店铺暂时缺货，我方会第一时间与您沟通，可选择退款或等待补货后再安排下单。</div>
                        </div>
                    </div>

                    <div>
                        <div class="qr-instruction-header">
                            <div class="pay-warning">⚠️ 订单需分两笔金额支付</div>
                            <div class="pay-sub">请扫码并输入对应日元金额完成支付</div>
                        </div>

                        <div class="qr-box">
                            {"<img src='" + qr_src + "'>" if qr_src else "<div style='color:#999;padding:80px 0;'>未找到二维码</div>"}
                            <div class="qr-footer-note">
                                <b>[ 完成支付后请截屏回传此对话框 ]</b><br>
                                当前结算参考汇率：1 JPY = {rate:.4f} RMB<br>
                                果熊俱乐部 | 感谢您的信任
                            </div>
                        </div>

                        <div class="service-guarantee">
                            <div class="guarantee-title">🛡️ 果熊服务须知 / Service Notes:</div>
                            <div class="guarantee-item">1. 所有商品均通过日本正规渠道采购，确保正品。</div>
                            <div class="guarantee-item">2. 国际物流预计14–21个工作日送达，具体到达时间以实际物流情况为准。</div>
                            <div class="guarantee-item">3. 国际物流时间可能受天气、航班及海关查验等因素影响，请以实际情况为准。</div>
                            <div class="guarantee-item">4. 代购商品确认付款后即安排采购，非质量问题原则上不支持取消或退换。</div>
                            <div class="guarantee-item">5. 商品尺寸、版型等信息仅供参考，具体适配情况因个人体型差异可能存在不同，尺码选择需客户自行确认。</div>
                            <div class="guarantee-item">6. 人民币金额仅供参考，最终以支付时银行或支付平台实时汇率为准。</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_code


def export_quote_png(
    client,
    quote_id,
    valid_time,
    rate,
    valid_df,
    payment1_jpy,
    p_rev_original,
    p_rev,
    discount_amount,
    service_pct,
    disp_service_fee,
    pay_fee_pct,
    disp_pay_fee,
    freight_status,
    w,
    ship_total_quote,
    p2_total,
    grand_total_jpy,
    grand_total_rmb,
    qr_abs_path
):
    item_count = len(valid_df) if not valid_df.empty else 0
    base_height = 1600
    extra_height = max(0, item_count - 4) * 70
    img_height = min(3200, base_height + extra_height)

    html_code = build_quote_export_html(
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
        qr_abs_path=qr_abs_path,
    )

    file_name = f"{quote_id}.png"
    hti = Html2Image(output_path=EXPORT_DIR)

    hti.screenshot(
        html_str=html_code,
        save_as=file_name,
        size=(1500, img_height)
    )

    return os.path.join(EXPORT_DIR, file_name)


# --- 2. CSS ---
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
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
    font-size: 0 .92rem;
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

# --- 3. 菜单 ---
with st.sidebar:
    st.title("🐻 KDKM V11.8")
    menu = st.radio("导航", ["新建报价", "历史订单", "运营分析", "系统设置"])


# --- 4. 新建报价 ---
if menu == "新建报价":
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        client = c1.text_input("客户姓名", "新客户")
        rate = c2.number_input("结算汇率", value=0.0450, format="%.4f")
        valid_time = c3.selectbox("有效期", ["48 Hours", "24 Hours", "3 Days"])
        quote_id = c4.text_input("单号", f"KDKM-{datetime.datetime.now().strftime('%m%d%H%M')}")

        d1, d2, d3, d4 = st.columns(4)
        service_pct = d1.number_input("服务费 %", value=10.0, step=0.5)
        pay_fee_pct = d2.number_input("手续费 %", value=3.0, step=0.1)
        freight_status = d3.selectbox("运费状态", ["已确认", "待确认"])

        qr_list = [f.replace(".png", "") for f in os.listdir(QR_DIR) if f.endswith(".png")]
        pay_method = d4.selectbox("收款通道", ["微信支付"] + qr_list)

    st.markdown('<div class="control-title">📦 商品录入与成本控制</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)

    if freight_status == "已确认":
        w = f1.number_input("重量 (KG)", min_value=0.0, value=1.0, step=0.1)
        u_q = f2.number_input("报价运费 (JPY)", min_value=0, value=2200, step=1)
        u_c = f3.number_input("成本运费 (JPY)", min_value=0, value=1400, step=1)
    else:
        w = f1.number_input("重量 (KG)", min_value=0.0, value=0.0, step=0.1)
        u_q = f2.number_input("报价运费 (JPY)", min_value=0, value=0, step=1)
        u_c = f3.number_input("成本运费 (JPY)", min_value=0, value=0, step=1)

    other_c = f4.number_input("额外杂费", min_value=0, value=0, step=100)

    ship_total_quote = int(w * u_q)
    ship_total_cost = int(w * u_c)

    st.info("💡 可在【折扣】列为不同商品单独设置折扣，100 即为不打折。按 Tab 键可更快录入。")

    df_input = st.data_editor(
        pd.DataFrame([{
            "商品": "",
            "数量": 1,
            "售价": 0,
            "折扣": 100.0,
            "成本": 0
        }]),
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

    # 第一笔
    payment1_jpy = p_rev

    # 第二笔逻辑：服务费 + 通道费先收，国际运费到货后再结算
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
                "</div>"
            )

            if discount_amount > 0:
                summary_html += (
                    f"<div class='summary-row strong'>"
                    f"<span>折后金额合计</span><span>¥ {p_rev:,}</span>"
                    "</div>"
                    f"<div class='summary-row discount'>"
                    f"<span class='discount-text'>优惠折扣总计</span><span class='discount-text'>-¥ {discount_amount:,}</span>"
                    "</div>"
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

        qr_p = os.path.join(QR_DIR, f"{pay_method}.png")
        if os.path.exists(qr_p):
            st.markdown('<div class="qr-image-wrap">', unsafe_allow_html=True)
            st.image(qr_p)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("请在系统设置中上传收款码")

        st.markdown(f"""
            <div class="qr-footer-note">
                <b>[ 完成支付后请截屏回传此对话框 ]</b><br>
                当前结算参考汇率：1 JPY = {rate:.4f} RMB<br>
                果熊俱乐部 | 感谢您的信任
            </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)

    with s1:
        if st.button("💾 保存为报价", use_container_width=True):
            if valid_df.empty:
                st.error("无法保存：请先录入商品信息")
            else:
                margin = (net_profit_jpy / grand_total_jpy * 100) if grand_total_jpy else 0
                new_row = pd.DataFrame([[
                    datetime.date.today(),
                    client,
                    quote_id,
                    "报价",
                    freight_status,
                    grand_total_jpy,
                    net_profit_jpy,
                    round(margin, 2)
                ]], columns=BASE_COLUMNS)

                history = load_history()
                history = pd.concat([history, new_row], ignore_index=True)
                save_history(history)
                st.success("已保存为报价")

    with s2:
        if st.button("✅ 保存为成交", use_container_width=True):
            if valid_df.empty:
                st.error("无法保存：请先录入商品信息")
            else:
                margin = (net_profit_jpy / grand_total_jpy * 100) if grand_total_jpy else 0
                new_row = pd.DataFrame([[
                    datetime.date.today(),
                    client,
                    quote_id,
                    "成交",
                    freight_status,
                    grand_total_jpy,
                    net_profit_jpy,
                    round(margin, 2)
                ]], columns=BASE_COLUMNS)

                history = load_history()
                history = pd.concat([history, new_row], ignore_index=True)
                save_history(history)
                st.success("已保存为成交")
    with s3:
        if st.button("🖼️ 导出报价图片", use_container_width=True):
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

            with open(export_path, "rb") as f:
                st.download_button(
                    "⬇️ 下载报价图片",
                    data=f,
                    file_name=os.path.basename(export_path),
                    mime="image/png",
                    use_container_width=True
                )


# --- 5. 历史订单 ---
elif menu == "历史订单":
    st.subheader("📚 历史订单")
    history = load_history()

    if history.empty:
        st.info("暂无历史订单。")
    else:
        show_df = history.copy()
        st.dataframe(show_df, use_container_width=True, hide_index=True)

        st.markdown("### 报价转成交")
        quote_df = history[history["状态"].astype(str) == "报价"].copy()

        if quote_df.empty:
            st.caption("当前没有可转换的报价记录。")
        else:
            quote_df["展示"] = (
                quote_df["日期"].astype(str) + " | "
                + quote_df["客户"].astype(str) + " | "
                + quote_df["单号"].astype(str) + " | "
                + quote_df["状态"].astype(str)
            )

            selected_quote = st.selectbox("选择一条报价记录改为成交", quote_df["展示"].tolist())

            if st.button("🔄 改为成交"):
                idx = quote_df[quote_df["展示"] == selected_quote].index[0]
                history.loc[idx, "状态"] = "成交"
                save_history(history)
                st.success("该记录已改为成交，请刷新或切换页面查看最新结果。")

        st.markdown("### 删除订单记录")
        delete_df = history.copy()
        delete_df["展示"] = (
            delete_df["日期"].astype(str)
            + " | "
            + delete_df["客户"].astype(str)
            + " | "
            + delete_df["单号"].astype(str)
            + " | "
            + delete_df["状态"].astype(str)
            + " | "
            + delete_df["总收入"].fillna(0).astype(float).map(lambda x: f"¥{int(x):,}")
        )

        selected_labels = st.multiselect("选择要删除的报价/订单记录", delete_df["展示"].tolist())

        if st.button("🗑️ 删除选中记录", type="primary"):
            if not selected_labels:
                st.warning("请先选择要删除的记录。")
            else:
                remaining = delete_df[~delete_df["展示"].isin(selected_labels)].copy()
                remaining = remaining[BASE_COLUMNS]
                save_history(remaining)
                st.success(f"已删除 {len(selected_labels)} 条记录，请刷新或切换页面查看最新结果。")


# --- 6. 运营分析 ---
elif menu == "运营分析":
    st.subheader("📊 运营分析仪表盘")

    history = load_history()
    df = prepare_history_for_analysis(history)

    # 只统计成交
    df = df[df["状态"] == "成交"].copy()

    if df.empty:
        st.info("暂无成交数据。保存成交订单后，这里会自动生成运营分析。")
    else:
        today = pd.Timestamp.today().normalize()
        month_start = today.replace(day=1)
        last_30_start = today - pd.Timedelta(days=29)

        df_month = df[df["日期"] >= month_start].copy()
        df_30 = df[df["日期"] >= last_30_start].copy()

        total_orders = len(df)
        total_revenue = df["总收入"].sum()
        total_profit = df["总利润"].sum()
        avg_margin = df["利润率"].mean() if total_orders else 0
        avg_order_value = df["总收入"].mean() if total_orders else 0

        month_orders = len(df_month)
        month_revenue = df_month["总收入"].sum()
        month_profit = df_month["总利润"].sum()
        month_avg_margin = df_month["利润率"].mean() if month_orders else 0

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("总成交单数", f"{total_orders}")
        a2.metric("总销售额", format_jpy(total_revenue))
        a3.metric("总利润", format_jpy(total_profit))
        a4.metric("平均利润率", f"{avg_margin:.2f}%")

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("本月成交单数", f"{month_orders}")
        b2.metric("本月销售额", format_jpy(month_revenue))
        b3.metric("本月利润", format_jpy(month_profit))
        b4.metric("客单价", format_jpy(avg_order_value))

        st.caption(f"本月平均利润率：{month_avg_margin:.2f}%")
        st.markdown("---")

        st.markdown("### 最近30天趋势")
        if not df_30.empty:
            daily = (
                df_30.groupby(df_30["日期"].dt.strftime("%Y-%m-%d"))
                .agg(
                    成交单数=("单号", "count"),
                    销售额=("总收入", "sum"),
                    利润=("总利润", "sum"),
                )
                .reset_index()
                .rename(columns={"日期": "日期"})
            )

            st.dataframe(daily, use_container_width=True, hide_index=True)

            chart_daily = daily.set_index("日期")
            st.line_chart(chart_daily[["销售额", "利润"]], use_container_width=True)
        else:
            st.caption("最近30天暂无成交订单。")

        st.markdown("---")

        left, right = st.columns(2)

        with left:
            st.markdown("### 客户贡献排行")
            customer_rank = (
                df.groupby("客户")
                .agg(
                    成交单数=("单号", "count"),
                    销售额=("总收入", "sum"),
                    利润=("总利润", "sum"),
                    平均利润率=("利润率", "mean"),
                )
                .reset_index()
                .sort_values(by="销售额", ascending=False)
            )

            customer_rank["销售额"] = customer_rank["销售额"].map(format_jpy)
            customer_rank["利润"] = customer_rank["利润"].map(format_jpy)
            customer_rank["平均利润率"] = customer_rank["平均利润率"].map(lambda x: f"{x:.2f}%")

            st.dataframe(customer_rank, use_container_width=True, hide_index=True)

        with right:
            st.markdown("### 月度汇总")
            monthly_summary = (
                df.groupby("年月")
                .agg(
                    成交单数=("单号", "count"),
                    销售额=("总收入", "sum"),
                    利润=("总利润", "sum"),
                    平均利润率=("利润率", "mean"),
                )
                .reset_index()
                .sort_values(by="年月", ascending=False)
            )

            monthly_summary["销售额"] = monthly_summary["销售额"].map(format_jpy)
            monthly_summary["利润"] = monthly_summary["利润"].map(format_jpy)
            monthly_summary["平均利润率"] = monthly_summary["平均利润率"].map(lambda x: f"{x:.2f}%")

            st.dataframe(monthly_summary, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("### 最近成交订单")
        recent_orders = (
            df.sort_values(by="日期", ascending=False)[
                ["日期文本", "客户", "单号", "总收入", "总利润", "利润率", "运费状态"]
            ]
            .head(20)
            .copy()
        )

        recent_orders = recent_orders.rename(columns={"日期文本": "日期"})
        recent_orders["总收入"] = recent_orders["总收入"].map(format_jpy)
        recent_orders["总利润"] = recent_orders["总利润"].map(format_jpy)
        recent_orders["利润率"] = recent_orders["利润率"].map(lambda x: f"{x:.2f}%")

        st.dataframe(recent_orders, use_container_width=True, hide_index=True)


# --- 7. 系统设置 ---
elif menu == "系统设置":
    up_qr = st.file_uploader("上传收款二维码", type=["png", "jpg", "jpeg"])
    if up_qr and st.button("更新微信支付码"):
        with open(os.path.join(QR_DIR, "微信支付.png"), "wb") as f:
            f.write(up_qr.getbuffer())
        st.success("二维码保存成功")
        
