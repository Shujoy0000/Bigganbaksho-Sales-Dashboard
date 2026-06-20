import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import datetime
import json
import re
import time

# =========================
# Bigganbaksho Sales Dashboard
# =========================

st.set_page_config(
    page_title="Bigganbaksho Sales Dashboard",
    layout="wide",
    page_icon="📊"
)

# Live CSV links
MONTH_WISE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2ZQeYDz1JAycFqu8N3iTyW4qgiAHbPphOFc7sR10TNUhyjyXTXI8fMs9_g8DYL6HDc-BpXKTQWQuR/pub?output=csv"

# Product Wise Report-এর published CSV link পেলে এখানে বসাবেন
# উদাহরণ: PRODUCT_WISE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxxx/pub?gid=xxxx&single=true&output=csv"
PRODUCT_WISE_CSV_URL = ""

AUTO_REFRESH_SECONDS = 10

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_SHORT = {
    "January": "Jan",
    "February": "Feb",
    "March": "Mar",
    "April": "Apr",
    "May": "May",
    "June": "Jun",
    "July": "Jul",
    "August": "Aug",
    "September": "Sep",
    "October": "Oct",
    "November": "Nov",
    "December": "Dec"
}

GROUP_ROWS = [
    "Physical Sales",
    "Customer Care & Tele Sales",
    "Digital Sales",
    "Rokomari"
]

TOTAL_ROWS = ["Total", "Grand Total"]


# =========================
# CSS
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    color: #111827 !important;
    font-family: 'Segoe UI', sans-serif;
}

.main-title {
    text-align: center;
    color: #FF6600;
    font-size: 52px;
    font-weight: 900;
    margin-top: -80px;
    margin-bottom: 8px;
}

.sub-title {
    text-align: center;
    font-size: 18px;
    color: #666;
    margin-bottom: 22px;
}

.metric-card {
    background: #FFFFFF;
    padding: 12px 8px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.10);
    text-align: center;
    border-top: 8px solid #FF6600;
    height: 125px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.metric-label {
    font-size: 18px;
    color: #444444;
    margin: 0 0 10px 0;
    font-weight: 900;
    text-transform: uppercase;
    white-space: nowrap;
    line-height: 1;
}

.metric-value {
    font-size: 34px;
    color: #2b2b2b;
    font-weight: 900;
    margin: 0;
    line-height: 1;
    white-space: nowrap;
}

.section-header {
    font-size: 28px;
    color: #333;
    background-color: #F0F2F6;
    padding: 12px 20px;
    border-radius: 8px;
    border-left: 10px solid #FF6600;
    margin-top: 42px;
    margin-bottom: 22px;
    font-weight: 800;
}

.copy-note {
    font-size: 13px;
    color: #666;
    margin-top: -4px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# Helper functions
# =========================
def clean_key(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def clean_number_value(value):
    if pd.isna(value):
        return 0
    text = str(value).replace(",", "").replace("৳", "").strip()
    if text == "":
        return 0
    return pd.to_numeric(text, errors="coerce") if pd.notna(pd.to_numeric(text, errors="coerce")) else 0


def money(value):
    return f"৳{int(round(float(value))):,}"


def whole(value):
    return f"{int(round(float(value))):,}"


def pct(value):
    return f"{float(value):.1f}%"


def show_copyable_table(df_display, key_name):
    if df_display.empty:
        st.info("No data found.")
        return

    table_height = min(620, max(180, 38 * (len(df_display) + 1)))

    st.markdown(
        '<div class="copy-note">Table থেকে cell, row বা full table copy করা যাবে। নিচের button দিয়ে full table copy হবে।</div>',
        unsafe_allow_html=True
    )

    safe_key = clean_key(key_name)
    table_text = df_display.to_csv(sep="\t", index=False)
    table_json = json.dumps(table_text, ensure_ascii=False)
    html_table = df_display.to_html(index=False, escape=False)

    components.html(f"""
        <style>
            .table-wrap-{safe_key} {{
                max-height: {table_height}px;
                overflow: auto;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                background: white;
                margin-bottom: 8px;
            }}

            .table-wrap-{safe_key} table {{
                width: 100%;
                border-collapse: collapse;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #111827;
            }}

            .table-wrap-{safe_key} thead th {{
                font-weight: 900 !important;
                color: #000000 !important;
                background: #F8F9FB;
                border: 1px solid #E0E0E0;
                padding: 9px 10px;
                text-align: left;
                position: sticky;
                top: 0;
                z-index: 2;
                white-space: nowrap;
            }}

            .table-wrap-{safe_key} tbody td {{
                border: 1px solid #E8E8E8;
                padding: 8px 10px;
                text-align: left;
                white-space: nowrap;
            }}

            .table-wrap-{safe_key} tbody tr:last-child td {{
                font-weight: 900 !important;
                color: #000000 !important;
            }}

            .copy-btn-{safe_key} {{
                background: #FF6600;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 14px;
                font-weight: 700;
                cursor: pointer;
                font-size: 14px;
                margin-top: 4px;
            }}
        </style>

        <div class="table-wrap-{safe_key}">
            {html_table}
        </div>

        <button class="copy-btn-{safe_key}" id="copy_btn_{safe_key}">
            📋 Copy full table
        </button>

        <script>
        const btn = document.getElementById("copy_btn_{safe_key}");
        const tableText = {table_json};

        btn.onclick = async function() {{
            try {{
                await navigator.clipboard.writeText(tableText);
                btn.innerText = "✅ Copied!";
                setTimeout(() => btn.innerText = "📋 Copy full table", 1300);
            }} catch (err) {{
                btn.innerText = "Copy failed";
                setTimeout(() => btn.innerText = "📋 Copy full table", 1300);
            }}
        }};
        </script>
    """, height=table_height + 72)


def add_total_row(df, label_col, amount_col="Sales Amount", cost_col="Total Cost"):
    if df.empty:
        return df

    total_sales = df[amount_col].sum() if amount_col in df.columns else 0
    total_cost = df[cost_col].sum() if cost_col in df.columns else 0
    total_net = df["Net Sales"].sum() if "Net Sales" in df.columns else total_sales - total_cost

    out = df.copy()
    total_row = {col: "" for col in out.columns}
    total_row[label_col] = "Total"

    if amount_col in out.columns:
        total_row[amount_col] = total_sales
    if cost_col in out.columns:
        total_row[cost_col] = total_cost
    if "Net Sales" in out.columns:
        total_row["Net Sales"] = total_net
    if "%" in out.columns:
        total_row["%"] = "100.0%"

    out = pd.concat([out, pd.DataFrame([total_row])], ignore_index=True)
    return out


def format_sales_table(df, label_col):
    out = df.copy()

    for col in ["Sales Amount", "Total Cost", "Net Sales", "Qty", "Quantity", "Amount"]:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: money(x) if pd.notna(x) and str(x) != "" else "")

    if "%" in out.columns:
        out["%"] = out["%"].apply(lambda x: x if isinstance(x, str) and x.endswith("%") else pct(x))

    return out


# =========================
# Data loading
# =========================
@st.cache_data(ttl=5)
def load_month_wise_data(cache_buster):
    # cache_buster parameter forces Streamlit/browser to request fresh data regularly
    url = f"{MONTH_WISE_CSV_URL}&v={cache_buster}"
    raw = pd.read_csv(url, header=None, dtype=str).fillna("")

    # Find main matrix header
    header_row = None
    for idx in range(min(10, len(raw))):
        if str(raw.iloc[idx, 0]).strip() == "Sales Channel":
            header_row = idx
            break

    if header_row is None:
        raise ValueError("Sales Channel header not found in Month Wise Sales Report CSV.")

    subheader_row = header_row + 1
    data_start = subheader_row + 1

    # Month positions in the first matrix
    month_positions = {}
    for col in range(raw.shape[1] - 1):
        value = str(raw.iloc[header_row, col]).strip()
        if value in MONTH_ORDER:
            month_positions[value] = {"amount_col": col, "cost_col": col + 1}

    rows = []
    current_group = ""

    for i in range(data_start, len(raw)):
        channel = str(raw.iloc[i, 0]).strip()

        if channel == "":
            continue

        # stop after the first main total row; below part is pivot area
        if channel == "Total":
            total_row = raw.iloc[i]
            break

        if channel in GROUP_ROWS:
            current_group = channel
            row_type = "Group"
        else:
            row_type = "Source"

        grand_total = clean_number_value(raw.iloc[i, 1]) if raw.shape[1] > 1 else 0

        for month in MONTH_ORDER:
            if month not in month_positions:
                continue

            amount_col = month_positions[month]["amount_col"]
            cost_col = month_positions[month]["cost_col"]

            sales_amount = clean_number_value(raw.iloc[i, amount_col]) if amount_col < raw.shape[1] else 0
            total_cost = clean_number_value(raw.iloc[i, cost_col]) if cost_col < raw.shape[1] else 0

            rows.append({
                "Group": channel if row_type == "Group" else current_group,
                "Source": channel,
                "Level": row_type,
                "Month": month,
                "Month No": MONTH_ORDER.index(month) + 1,
                "Sales Amount": float(sales_amount),
                "Total Cost": float(total_cost),
                "Net Sales": float(sales_amount) - float(total_cost),
                "Sales Grand Total": float(grand_total)
            })

    df = pd.DataFrame(rows)

    if df.empty:
        return df, raw

    return df, raw


@st.cache_data(ttl=5)
def load_product_data(cache_buster):
    if PRODUCT_WISE_CSV_URL.strip() == "":
        return pd.DataFrame()

    url = f"{PRODUCT_WISE_CSV_URL}&v={cache_buster}"
    df = pd.read_csv(url, dtype=str).fillna("")
    df.columns = df.columns.astype(str).str.strip()

    # Flexible column detection
    source_col = next((c for c in df.columns if c.lower() in ["source", "sales channel", "channel"]), None)
    product_col = next((c for c in df.columns if "product" in c.lower()), None)
    month_col = next((c for c in df.columns if c.lower() in ["month", "month name"]), None)
    qty_col = next((c for c in df.columns if "qty" in c.lower() or "quantity" in c.lower()), None)
    amount_col = next((c for c in df.columns if "amount" in c.lower() or "sales" in c.lower() or "revenue" in c.lower()), None)

    if not source_col or not product_col:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["Source"] = df[source_col].astype(str).str.strip()
    out["Product"] = df[product_col].astype(str).str.strip()
    out["Month"] = df[month_col].astype(str).str.strip() if month_col else ""
    out["Qty"] = df[qty_col].apply(clean_number_value) if qty_col else 0
    out["Amount"] = df[amount_col].apply(clean_number_value) if amount_col else 0

    out = out[
        (out["Source"] != "") &
        (out["Product"] != "") &
        (out["Source"].str.lower() != "nan") &
        (out["Product"].str.lower() != "nan")
    ]

    return out


# =========================
# Auto refresh
# =========================
if "last_auto_refresh" not in st.session_state:
    st.session_state.last_auto_refresh = time.time()

if time.time() - st.session_state.last_auto_refresh > AUTO_REFRESH_SECONDS:
    st.session_state.last_auto_refresh = time.time()
    st.rerun()


try:
    cache_buster = int(time.time() // 5)
    month_df, raw_df = load_month_wise_data(cache_buster)
    product_df = load_product_data(cache_buster)

    st.markdown('<div class="main-title">Bigganbaksho Sales Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Live month-wise and source-wise sales analytics</div>', unsafe_allow_html=True)

    # Sidebar
    st.sidebar.header("📅 Filter Panel")

    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    available_months = [m for m in MONTH_ORDER if m in month_df["Month"].unique()]
    default_months = [m for m in available_months if month_df.loc[month_df["Month"] == m, "Sales Amount"].sum() > 0]
    if not default_months:
        default_months = available_months

    selected_months = st.sidebar.multiselect(
        "Select Month",
        available_months,
        default=default_months,
        format_func=lambda x: MONTH_SHORT.get(x, x)
    )

    report_level = st.sidebar.radio(
        "Report Type",
        ["Group", "Source"],
        index=1,
        horizontal=False
    )

    level_df = month_df[month_df["Level"] == report_level].copy()

    source_options = sorted(level_df["Source"].dropna().unique().tolist())
    selected_sources = st.sidebar.multiselect(
        "Select Sales Channel / Source",
        source_options,
        default=source_options
    )

    show_cost = st.sidebar.checkbox("Show Total Cost", value=True)

    st.sidebar.caption(f"Auto-refresh: every {AUTO_REFRESH_SECONDS} seconds")
    st.sidebar.caption("Google published CSV may still have a short delay.")

    filtered_df = level_df[
        level_df["Month"].isin(selected_months) &
        level_df["Source"].isin(selected_sources)
    ].copy()

    # Summary values
    total_sales = filtered_df["Sales Amount"].sum()
    total_cost = filtered_df["Total Cost"].sum()
    net_sales = filtered_df["Net Sales"].sum()

    top_source = ""
    if not filtered_df.empty:
        top_source = (
            filtered_df.groupby("Source")["Sales Amount"]
            .sum()
            .sort_values(ascending=False)
            .index[0]
        )

    c1, c2, c3, c4, c5 = st.columns(5)

    cards = [
        ("Total Sales", money(total_sales)),
        ("Total Cost", money(total_cost)),
        ("Net Sales", money(net_sales)),
        ("Selected Months", str(len(selected_months))),
        ("Top Source", top_source if top_source else "-")
    ]

    for col, (label, value) in zip([c1, c2, c3, c4, c5], cards):
        col.markdown(
            f"<div class='metric-card'><div><p class='metric-label'>{label}</p><p class='metric-value'>{value}</p></div></div>",
            unsafe_allow_html=True
        )

    # Month wise section
    st.markdown('<div class="section-header">Month-wise Sales Report</div>', unsafe_allow_html=True)

    month_summary = (
        filtered_df.groupby(["Month", "Month No"], as_index=False)
        .agg({
            "Sales Amount": "sum",
            "Total Cost": "sum",
            "Net Sales": "sum"
        })
        .sort_values("Month No")
    )

    month_summary["Month Short"] = month_summary["Month"].map(MONTH_SHORT)

    if not month_summary.empty:
        chart_cols = ["Sales Amount"]
        if show_cost:
            chart_cols.append("Total Cost")

        chart_data = month_summary.melt(
            id_vars=["Month Short", "Month No"],
            value_vars=chart_cols,
            var_name="Metric",
            value_name="Amount"
        )

        fig_month = px.bar(
            chart_data,
            x="Month Short",
            y="Amount",
            color="Metric",
            barmode="group",
            text_auto=True
        )

        fig_month.update_traces(
            textposition="outside",
            texttemplate="৳%{y:,}"
        )

        fig_month.update_layout(
            height=430,
            margin=dict(t=20, b=40, l=10, r=20),
            yaxis=dict(tickformat=",d", title="Amount"),
            xaxis=dict(title="Month"),
            legend_title_text="",
        )

        st.plotly_chart(fig_month, use_container_width=True)

        month_table = month_summary[["Month", "Sales Amount", "Total Cost", "Net Sales"]].copy()
        month_table["%"] = month_table["Sales Amount"] / (total_sales if total_sales > 0 else 1) * 100
        month_table = add_total_row(month_table, "Month")
        show_copyable_table(format_sales_table(month_table, "Month"), "month_wise_table")
    else:
        st.info("No month-wise data found for selected filters.")

    # Source wise section
    st.markdown('<div class="section-header">Source-wise Sales Report</div>', unsafe_allow_html=True)

    source_summary = (
        filtered_df.groupby("Source", as_index=False)
        .agg({
            "Sales Amount": "sum",
            "Total Cost": "sum",
            "Net Sales": "sum"
        })
        .sort_values("Sales Amount", ascending=False)
    )

    if not source_summary.empty:
        source_summary["%"] = source_summary["Sales Amount"] / (total_sales if total_sales > 0 else 1) * 100

        fig_source = px.bar(
            source_summary.head(20),
            x="Sales Amount",
            y="Source",
            orientation="h",
            color="Source",
            text_auto=True
        )

        fig_source.update_traces(
            textposition="outside",
            texttemplate="৳%{x:,}"
        )

        fig_source.update_layout(
            height=max(420, len(source_summary.head(20)) * 42 + 80),
            margin=dict(t=20, b=40, l=10, r=90),
            yaxis={
                "type": "category",
                "categoryorder": "array",
                "categoryarray": source_summary["Source"].tolist()
            },
            xaxis=dict(showticklabels=False, title=""),
            showlegend=False
        )

        st.plotly_chart(fig_source, use_container_width=True)

        source_table = add_total_row(source_summary, "Source")
        show_copyable_table(format_sales_table(source_table, "Source"), "source_wise_table")
    else:
        st.info("No source-wise data found for selected filters.")

    # Product-wise section
    st.markdown('<div class="section-header">Product-wise Report</div>', unsafe_allow_html=True)

    if PRODUCT_WISE_CSV_URL.strip() == "":
        st.info(
            "Product Wise Report-এর CSV URL এখনো set করা নেই। "
            "Product Wise Report tab publish করে URL-টা code-এর PRODUCT_WISE_CSV_URL-এ বসালে এখানে product-wise chart এবং table live দেখাবে।"
        )
    elif product_df.empty:
        st.info("Product data পাওয়া যায়নি বা expected column পাওয়া যায়নি.")
    else:
        p_df = product_df.copy()

        if selected_months and "Month" in p_df.columns and p_df["Month"].astype(str).str.strip().ne("").any():
            p_df = p_df[p_df["Month"].isin(selected_months)]

        if selected_sources:
            p_df = p_df[p_df["Source"].isin(selected_sources)]

        if p_df.empty:
            st.info("Selected filter অনুযায়ী product data নেই.")
        else:
            product_source_summary = (
                p_df.groupby(["Source", "Product"], as_index=False)
                .agg({
                    "Qty": "sum",
                    "Amount": "sum"
                })
                .sort_values(["Source", "Amount"], ascending=[True, False])
            )

            for source in sorted(product_source_summary["Source"].unique()):
                src_df = product_source_summary[product_source_summary["Source"] == source].copy()
                st.markdown(f"### {source} - Product-wise Sales")

                fig_product = px.bar(
                    src_df.head(10),
                    x="Amount",
                    y="Product",
                    orientation="h",
                    color="Product",
                    text_auto=True
                )

                fig_product.update_traces(
                    textposition="outside",
                    texttemplate="৳%{x:,}"
                )

                fig_product.update_layout(
                    height=max(360, len(src_df.head(10)) * 42 + 80),
                    margin=dict(t=20, b=40, l=10, r=90),
                    yaxis={
                        "type": "category",
                        "categoryorder": "array",
                        "categoryarray": src_df["Product"].tolist()
                    },
                    xaxis=dict(showticklabels=False, title=""),
                    showlegend=False
                )

                st.plotly_chart(fig_product, use_container_width=True)

                total_amount = src_df["Amount"].sum()
                src_df["%"] = src_df["Amount"] / (total_amount if total_amount > 0 else 1) * 100

                table_df = src_df.rename(columns={"Amount": "Sales Amount", "Qty": "Qty"})
                table_df = add_total_row(table_df, "Product", amount_col="Sales Amount", cost_col="Total Cost")
                show_copyable_table(format_sales_table(table_df[["Source", "Product", "Qty", "Sales Amount", "%"]], "Product"), f"product_table_{source}")

except Exception as e:
    st.error(f"Error: {e}")
