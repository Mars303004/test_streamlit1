import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfkit
import os

st.set_page_config(layout="wide", page_title="KPI Dashboard")
st.title("KPI Dashboard")

# Upload file
uploaded_file = st.file_uploader("Upload CSV KPI File", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Preprocess Bulan jadi datetime biar bisa diurut dan dibandingkan
    df['Month'] = pd.to_datetime(df['Month'], format='%b-%y')
    df_feb = df[df['Month'].dt.month == 2]  # Fokus bulan Februari
    df_jan = df[df['Month'].dt.month == 1]  # Buat comparison

    # Tabs
    tabs = st.tabs(["Overall BU Performance", "BU1", "BU2", "BU3", "KPI Raw", "SI"])

    # Tab 1, 3, 4, 5, 6
    for i in [0, 2, 3, 4, 5]:
        with tabs[i]:
            st.warning("Belum ada data yang tersedia")

    # Tab 2: BU1
    with tabs[1]:
        st.header("BU1 Performance")

        perspective = st.radio("Pilih Perspective", ["Financial", "Customer", "Quality", "Employee"], horizontal=True)

        df_persp_feb = df_feb[df_feb['Perspective'] == perspective]
        df_persp_jan = df_jan[df_jan['Perspective'] == perspective]

        # Tab per subdiv/produk
        if perspective == "Customer n Service":
            produk_list = df_persp_feb['Produk'].dropna().unique()
            produk_tabs = st.tabs(produk_list)

            for i, produk in enumerate(produk_list):
                with produk_tabs[i]:
                    df_produk_feb = df_persp_feb[df_persp_feb['Produk'] == produk]
                    df_produk_jan = df_persp_jan[df_persp_jan['Produk'] == produk]

                    # Donut chart: number of customer
                    total_customers = df_produk_feb['Number of customer'].sum()
                    fig_donut = go.Figure(data=[
                        go.Pie(labels=[produk], values=[total_customers], hole=0.5)
                    ])
                    st.plotly_chart(fig_donut, use_container_width=True)

                    # Scorecard + Comparison
                    cust_feb = df_produk_feb['Customer satisfaction'].mean()
                    cust_jan = df_produk_jan['Customer satisfaction'].mean()
                    delta = cust_feb - cust_jan
                    color = "green" if delta >= 0 else "red"
                    arrow = "↑" if delta >= 0 else "↓"
                    st.metric(label=f"Customer Satisfaction ({produk})", value=f"{cust_feb:.2f}", delta=f"{arrow} {abs(delta):.2f}", delta_color=color)

                    # Line chart: comparison
                    temp = df[df['Produk'] == produk][['Month', 'Customer satisfaction']].dropna()
                    temp = temp.groupby('Month').mean().reset_index()
                    fig_line = px.line(temp, x='Month', y='Customer satisfaction', markers=True)
                    st.plotly_chart(fig_line, use_container_width=True)

        else:
            subdiv_list = df_persp_feb['Subdiv'].dropna().unique()
            subdiv_tabs = st.tabs(subdiv_list)

            for i, subdiv in enumerate(subdiv_list):
                with subdiv_tabs[i]:
                    df_sub_feb = df_persp_feb[df_persp_feb['Subdiv'] == subdiv]
                    df_sub_jan = df_persp_jan[df_persp_jan['Subdiv'] == subdiv]

                    if perspective == "Financial":
                        # Bar chart: Budget vs Expense
                        fig_bar = go.Figure(data=[
                            go.Bar(name='Budget', x=df_sub_feb['Subdiv'], y=df_sub_feb['Budget']),
                            go.Bar(name='Expense', x=df_sub_feb['Subdiv'], y=df_sub_feb['Expense'])
                        ])
                        fig_bar.update_layout(barmode='group')
                        st.plotly_chart(fig_bar, use_container_width=True)

                        # Gauge (usage)
                        usage_val = df_sub_feb['Usage'].iloc[0] if not df_sub_feb['Usage'].isna().all() else "0%"
                        st.subheader(f"Usage: {usage_val}")

                        # Scorecard
                        profit = df_sub_feb['Profit'].sum()
                        revenue = df_sub_feb['Revenue'].sum()
                        profit_jan = df_sub_jan['Profit'].sum()
                        revenue_jan = df_sub_jan['Revenue'].sum()
                        st.metric("Profit", f"{profit}", delta=f"{profit - profit_jan}")
                        st.metric("Revenue", f"{revenue}", delta=f"{revenue - revenue_jan}")

                    elif perspective == "Quality":
                        # Bar chart Target vs Realization
                        fig = go.Figure()
                        fig.add_trace(go.Bar(x=df_sub_feb['Subdiv'], y=df_sub_feb['Target'], name='Target'))
                        fig.add_trace(go.Bar(x=df_sub_feb['Subdiv'], y=df_sub_feb['Realization'], name='Realization'))
                        fig.update_layout(barmode='group')
                        st.plotly_chart(fig, use_container_width=True)

                        # Scorecard
                        target_vs_real = df_sub_feb['Target vs Real'].astype(str).str.rstrip('%').astype(float).mean()
                        st.metric("Avg. Target vs Real", f"{target_vs_real:.2f}%")

                    elif perspective == "Employee":
                        current = df_sub_feb['Current MF'].sum()
                        needed = df_sub_feb['Needed MF'].sum()
                        remaining = needed - current
                        fig_donut = go.Figure(data=[
                            go.Pie(labels=['Current', 'Remaining'], values=[current, remaining], hole=0.5)
                        ])
                        st.plotly_chart(fig_donut, use_container_width=True)

                        # Scorecard
                        comp = df_sub_feb['Competency'].mean()
                        turnover = df_sub_feb['Turnover ratio'].astype(str).str.rstrip('%').astype(float).mean()
                        st.metric("Avg. Competency", f"{comp:.2f}%")
                        st.metric("Avg. Turnover Ratio", f"{turnover:.2f}%")

        # Export to PDF
        st.download_button("Export BU1 to PDF (coming soon)", "PDF export belum aktif di demo ini.", file_name="BU1_Dashboard.pdf")
else:
    st.info("Silakan upload file .csv terlebih dahulu.")
