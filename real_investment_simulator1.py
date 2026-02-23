import streamlit as st

st.title("Investment Calculator")

P = st.number_input("Initial Investment", value=10000.0)
PMT = st.number_input("Monthly Contribution", value=500.0)
annual_rate = st.number_input("Annual Return (%)", value=8.0) / 100
years = st.number_input("Years", value=20)

r = annual_rate / 12
n = years * 12

FV = P * (1 + r)**n + PMT * (((1 + r)**n - 1) / r)

st.subheader(f"Future Value: ${FV:,.2f}")
