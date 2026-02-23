import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("Real Market Investment Simulator")

# Inputs
initial = st.number_input("Initial Investment", value=10000.0)
monthly = st.number_input("Monthly Contribution", value=500.0)
years = st.number_input("Years", value=30)
avg_return = st.number_input("Expected Average Annual Return (%)", value=7.0) / 100
volatility = st.number_input("Market Volatility (%)", value=15.0) / 100
simulations = 1000

months = years * 12
results = []

for _ in range(simulations):
    value = initial
    for m in range(months):
        monthly_return = np.random.normal(avg_return/12, volatility/np.sqrt(12))
        value = value * (1 + monthly_return) + monthly
    results.append(value)

results = np.array(results)

st.subheader("Results After Simulation")

st.write(f"Median Outcome: ${np.median(results):,.0f}")
st.write(f"Best 10% Outcome: ${np.percentile(results,90):,.0f}")
st.write(f"Worst 10% Outcome: ${np.percentile(results,10):,.0f}")
st.write(f"Probability of Ending Below Total Invested: {np.mean(results < (initial + monthly*months)) * 100:.1f}%")

fig, ax = plt.subplots()
ax.hist(results, bins=40)
ax.set_title("Distribution of Outcomes")
st.pyplot(fig)
