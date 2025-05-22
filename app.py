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

    # Tambahkan filter bulan
    available_months = df['Month'].dt.strftime('%b-%y').unique()
    selected_month_str = st.selectbox("Pilih Bulan", available_months)
    selected_month = pd.to_datetime(selected_month_str, format='%b-%y')

    df_selected = df[df['Month'] == selected_month]
    df_prev = df[df['Month'] == (selected_month - pd.DateOffset(months=1))]

    # Tabs
    tabs = st.tabs(["Overall BU Performance", "BU1", "BU2", "BU3", "KPI Raw", "SI"])

    # Tab 1, 3, 4, 5, 6
    for i in [0, 2, 3, 4, 5]:
        with tabs[i]:
            st.warning("Belum ada data yang tersedia")

    # Tab 2: BU1
    with tabs[1]:
        st.header("BU1 Performance")

        perspective = st.radio("Pilih Perspective", ["Financial", "Customer n Service", "Quality", "Employee"], horizontal=True)

        df_persp = df_selected[df_selected['Perspective'] == perspective]
        df_prev_persp = df_prev[df_prev['Perspective'] == perspective]

        if perspective == "Customer n Service":
            produk_list = df_persp['Produk'].dropna().unique().tolist()
            if len(produk_list) > 0:
                produk_tabs = st.tabs(produk_list)

                for i, produk in enumerate(produk_list):
                    with produk_tabs[i]:
                        df_produk = df_persp[df_persp['Produk'] == produk]
                        df_produk_prev = df_prev_persp[df_prev_persp['Produk'] == produk]

                        # Donut chart: number of customer
                        total_customers = df_produk['Number of customer'].sum()
                        fig_donut = go.Figure(data=[
                            go.Pie(labels=[produk], values=[total_customers], hole=0.5)
                        ])
                        st.plotly_chart(fig_donut, use_container_width=True)

                        # Scorecard + Comparison
                        cust = df_produk['Customer satisfaction'].mean()
                        cust_prev = df_produk_prev['Customer satisfaction'].mean() if not df_produk_prev.empty else 0
                        delta = cust - cust_prev
                        color = "green" if delta >= 0 else "red"
                        arrow = "↑" if delta >= 0 else "↓"
                        st.metric(label=f"Customer Satisfaction ({produk})", value=f"{cust:.2f}", delta=f"{arrow} {abs(delta):.2f}", delta_color=color)

                        # Line chart: comparison
                        temp = df[df['Produk'] == produk][['Month', 'Customer satisfaction']].dropna()
                        temp = temp.groupby('Month').mean().reset_index()
                        fig_line = px.line(temp, x='Month', y='Customer satisfaction', markers=True)
                        st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning(f"Tidak ada data produk untuk {perspective} di bulan {selected_month_str}")
        else:
            subdiv_list = ["Subdiv 1", "Subdiv 2", "Subdiv 3"]
            subdiv_tabs = st.tabs(subdiv_list)

            for i, subdiv in enumerate(subdiv_list):
                with subdiv_tabs[i]:
                    df_sub = df_persp[df_persp['Subdiv'] == subdiv]
                    df_sub_prev = df_prev_persp[df_prev_persp['Subdiv'] == subdiv]

                    if perspective == "Financial":
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_bar = go.Figure(data=[
                                go.Bar(name='Budget', x=df_sub['Subdiv'], y=df_sub['Budget']),
                                go.Bar(name='Expense', x=df_sub['Subdiv'], y=df_sub['Expense'])
                            ])
                            fig_bar.update_layout(barmode='group')
                            st.plotly_chart(fig_bar, use_container_width=True)
                        with col2:
                            usage_val_str = df_sub['Usage'].iloc[0] if not df_sub['Usage'].isna().all() else "0%"
                            usage_val = float(usage_val_str.strip('%'))
                            usage_prev = float(df_sub_prev['Usage'].iloc[0].strip('%')) if not df_sub_prev['Usage'].isna().all() else 0
                            fig_gauge = go.Figure(go.Indicator(
                                mode="gauge+number+delta",
                                value=usage_val,
                                delta={'reference': usage_prev},
                                gauge={'axis': {'range': [0, 150]}},
                                title={'text': f"Usage (%) - {subdiv}"}
                            ))
                            st.plotly_chart(fig_gauge, use_container_width=True)

                        col3, col4 = st.columns(2)
                        with col3:
                            profit = df_sub['Profit'].sum()
                            profit_prev = df_sub_prev['Profit'].sum()
                            st.markdown("<div style='background-color:#f2f2f2;padding:10px;border-radius:10px'>", unsafe_allow_html=True)
                            st.metric("Profit", f"{profit}", delta=f"{profit - profit_prev}")
                            st.markdown("</div>", unsafe_allow_html=True)
                        with col4:
                            revenue = df_sub['Revenue'].sum()
                            revenue_prev = df_sub_prev['Revenue'].sum()
                            st.markdown("<div style='background-color:#f2f2f2;padding:10px;border-radius:10px'>", unsafe_allow_html=True)
                            st.metric("Revenue", f"{revenue}", delta=f"{revenue - revenue_prev}")
                            st.markdown("</div>", unsafe_allow_html=True)

                    elif perspective == "Quality":
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            fig = go.Figure()
                            fig.add_trace(go.Bar(x=df_sub['Subdiv'], y=df_sub['Target'], name='Target'))
                            fig.add_trace(go.Bar(x=df_sub['Subdiv'], y=df_sub['Realization'], name='Realization'))
                            fig.update_layout(barmode='group')
                            st.plotly_chart(fig, use_container_width=True)
                        with col2:
                            target_vs_real = df_sub['Target vs Real'].astype(str).str.rstrip('%').astype(float).mean()
                            velocity = df_sub['Velocity'].astype(str).str.rstrip('%').astype(float).mean()
                            quality = df_sub['Quality'].astype(str).str.rstrip('%').astype(float).mean()
                            velocity_prev = df_sub_prev['Velocity'].astype(str).str.rstrip('%').astype(float).mean()
                            quality_prev = df_sub_prev['Quality'].astype(str).str.rstrip('%').astype(float).mean()

                            st.markdown("<div style='background-color:#f2f2f2;padding:10px;border-radius:10px'>", unsafe_allow_html=True)
                            st.metric("Avg. Target vs Real", f"{target_vs_real:.2f}%")
                            st.metric("Avg. Velocity", f"{velocity:.2f}%", delta=f"{velocity - velocity_prev:.2f}%")
                            st.metric("Avg. Quality", f"{quality:.2f}%", delta=f"{quality - quality_prev:.2f}%")
                            st.markdown("</div>", unsafe_allow_html=True)

                    elif perspective == "Employee":
                        try:
                            current = df_sub['Current MP'].sum()
                            needed = df_sub['Needed MP'].sum()
                        except KeyError:
                            st.error("Kolom 'Current MP' atau 'Needed MP' tidak ditemukan.")
                            continue
                        remaining = needed - current
                        fig_donut = go.Figure(data=[
                            go.Pie(labels=['Current', 'Remaining'], values=[current, remaining], hole=0.5)
                        ])
                        st.plotly_chart(fig_donut, use_container_width=True)

                        comp = df_sub['Competency'].mean()
                        turnover = df_sub['Turnover ratio'].astype(str).str.rstrip('%').astype(float).mean()
                        st.markdown("<div style='background-color:#f2f2f2;padding:10px;border-radius:10px'>", unsafe_allow_html=True)
                        st.metric("Avg. Competency", f"{comp:.2f}%")
                        st.metric("Avg. Turnover Ratio", f"{turnover:.2f}%")
                        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button("Export BU1 to PDF (coming soon)", "PDF export belum aktif di demo ini.", file_name="BU1_Dashboard.pdf")
else:
    st.info("Silakan upload file .csv terlebih dahulu.")
