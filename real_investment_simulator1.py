import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Nicholas Reality Investment Simulator", layout="wide")
st.title("Reality-Based Investment Simulator")
st.caption("Shows ranges of outcomes, inflation impact, fees, taxes, crashes, and behavior mistakes.")

# ----------------------------
# Inputs
# ----------------------------
colA, colB, colC = st.columns(3)

with colA:
    initial = st.number_input("Initial investment ($)", min_value=0.0, value=10000.0, step=1000.0)
    monthly = st.number_input("Monthly contribution ($)", min_value=0.0, value=500.0, step=50.0)
    years = st.number_input("Years", min_value=1, value=30, step=1)
    sims = st.slider("Simulations", min_value=200, max_value=10000, value=3000, step=200)

with colB:
    exp_return = st.number_input("Expected annual return (%)", value=7.0, step=0.5) / 100.0
    volatility = st.number_input("Annual volatility (%)", value=15.0, step=1.0) / 100.0
    inflation = st.number_input("Inflation (%)", value=2.5, step=0.1) / 100.0
    fee = st.number_input("Annual fees (expense ratio/advisor) (%)", value=0.20, step=0.05) / 100.0

with colC:
    cap_gains_tax = st.number_input("Capital gains tax (%)", value=15.0, step=1.0) / 100.0
    include_crashes = st.checkbox("Include random crash events", value=True)
    crash_chance_per_year = st.slider("Crash chance per year", 0.0, 0.30, 0.06, 0.01)
    crash_size = st.slider("Crash size (drop)", 0.10, 0.60, 0.35, 0.05)

st.divider()

colD, colE = st.columns(2)
with colD:
    include_behavior = st.checkbox("Include behavior mistakes (panic / missing best days)", value=True)
    panic_sell = st.slider("Panic sell: % of portfolio sold after crash", 0, 100, 25, 5) / 100.0
    months_in_cash = st.slider("Months sitting in cash after panic", 0, 36, 6, 1)
with colE:
    miss_best_days = st.slider("Miss best days per decade", 0, 40, 10, 1)
    cash_return = st.number_input("Cash annual return (%)", value=2.0, step=0.2) / 100.0

# ----------------------------
# Simulation helpers
# ----------------------------
def simulate_path(
    initial, monthly, years, exp_return, vol, inflation, fee,
    include_crashes, crash_chance_per_year, crash_size,
    include_behavior, panic_sell, months_in_cash, miss_best_days, cash_return
):
    months = int(years * 12)
    mu_m = exp_return / 12.0
    sigma_m = vol / np.sqrt(12.0)
    fee_m = fee / 12.0
    infl_m = inflation / 12.0
    cash_m = cash_return / 12.0

    value = initial
    contributed = initial
    # track cost basis (very simplified): contributions are basis
    basis = initial

    # Generate returns
    rets = np.random.normal(mu_m, sigma_m, size=months)

    # Apply “missing best days” by zeroing out the top N monthly returns
    # Convert "per decade" to per simulation horizon
    total_decades = years / 10.0
    miss_n = int(round(miss_best_days * total_decades))
    if include_behavior and miss_n > 0:
        idx = np.argsort(rets)[-miss_n:]  # best months
        rets[idx] = 0.0  # missed those months

    # Crash events: random months with an extra negative shock
    crash_months = np.zeros(months, dtype=bool)
    if include_crashes:
        # approximate monthly probability from annual chance
        p_m = 1 - (1 - crash_chance_per_year) ** (1 / 12.0)
        crash_months = np.random.rand(months) < p_m

    in_cash_months_left = 0

    for m in range(months):
        # contribute at start of month (simple model)
        value += monthly
        contributed += monthly
        basis += monthly

        # crash shock
        if crash_months[m]:
            value *= (1.0 - crash_size)

            # behavior: panic sell a portion, then sit in cash
            if include_behavior and panic_sell > 0 and months_in_cash > 0:
                sold = value * panic_sell
                value -= sold
                # keep sold amount as "cash bucket"
                cash_bucket = sold
                in_cash_months_left = months_in_cash
            else:
                cash_bucket = 0.0
        else:
            cash_bucket = 0.0

        # monthly growth
        if include_behavior and in_cash_months_left > 0:
            # portfolio grows (market) on remaining value
            value *= (1.0 + rets[m] - fee_m)
            # cash bucket grows at cash rate
            cash_bucket *= (1.0 + cash_m)
            # merge cash bucket back only when timer ends
            in_cash_months_left -= 1
            if in_cash_months_left == 0:
                value += cash_bucket
        else:
            value *= (1.0 + rets[m] - fee_m)

        # deflate to "real" dollars alongside nominal
        # We'll return both by applying inflation at the end using (1+infl)^months

    nominal_end = value
    infl_factor = (1.0 + infl_m) ** months
    real_end = nominal_end / infl_factor

    # Simple taxes: tax on gains above basis at the end
    gains = max(0.0, nominal_end - basis)
    taxes = gains * cap_gains_tax
    nominal_after_tax = nominal_end - taxes
    real_after_tax = nominal_after_tax / infl_factor

    return {
        "nominal_end": nominal_end,
        "real_end": real_end,
        "basis": basis,
        "taxes": taxes,
        "nominal_after_tax": nominal_after_tax,
        "real_after_tax": real_after_tax,
        "contributed": contributed
    }

# ----------------------------
# Run simulations
# ----------------------------
run = st.button("Run simulation", type="primary")

if run:
    outcomes = []
    for _ in range(int(sims)):
        outcomes.append(
            simulate_path(
                initial, monthly, years, exp_return, volatility, inflation, fee,
                include_crashes, crash_chance_per_year, crash_size,
                include_behavior, panic_sell, months_in_cash, miss_best_days, cash_return
            )
        )

    nominal_after_tax = np.array([o["nominal_after_tax"] for o in outcomes])
    real_after_tax = np.array([o["real_after_tax"] for o in outcomes])
    taxes = np.array([o["taxes"] for o in outcomes])
    basis = np.array([o["basis"] for o in outcomes])
    contributed = np.array([o["contributed"] for o in outcomes])

    def pct(arr, p): 
        return float(np.percentile(arr, p))

    # ----------------------------
    # Summary cards
    # ----------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Median (Nominal, after tax)", f"${pct(nominal_after_tax, 50):,.0f}")
    c2.metric("10th percentile", f"${pct(nominal_after_tax, 10):,.0f}")
    c3.metric("90th percentile", f"${pct(nominal_after_tax, 90):,.0f}")
    c4.metric("Median (Real $, after tax)", f"${pct(real_after_tax, 50):,.0f}")

    st.write("")
    c5, c6, c7 = st.columns(3)
    total_invested = initial + monthly * int(years * 12)
    c5.metric("Total contributed (planned)", f"${total_invested:,.0f}")
    c6.metric("Median taxes paid (end)", f"${pct(taxes, 50):,.0f}")
    prob_loss_vs_contrib = float(np.mean(nominal_after_tax < total_invested) * 100.0)
    c7.metric("Chance ending below contributions", f"{prob_loss_vs_contrib:.1f}%")

    st.divider()

    # ----------------------------
    # Plots
    # ----------------------------
    left, right = st.columns(2)

    with left:
        fig1, ax1 = plt.subplots()
        ax1.hist(nominal_after_tax, bins=45)
        ax1.set_title("Nominal outcomes (after tax) — distribution")
        ax1.set_xlabel("Ending value ($)")
        ax1.set_ylabel("Frequency")
        st.pyplot(fig1)

    with right:
        fig2, ax2 = plt.subplots()
        ax2.hist(real_after_tax, bins=45)
        ax2.set_title("Real outcomes (inflation-adjusted, after tax) — distribution")
        ax2.set_xlabel("Ending value (today's $)")
        ax2.set_ylabel("Frequency")
        st.pyplot(fig2)

    st.divider()

    # ----------------------------
    # Reality lessons section
    # ----------------------------
    st.subheader("What this teaches (use these as discussion prompts)")
    st.markdown(
        """
- **Ranges beat single numbers:** the market doesn’t owe you the average.
- **Inflation matters:** “$1M” in 30 years is not “$1M today.”
- **Fees compound negatively:** small % fees can erase huge sums over decades.
- **Behavior is the real alpha:** panic + missing best days is devastating.
- **Sequence risk is real:** bad early years can change the whole trajectory.
        """
    )

    st.caption("Tip: Run with behavior OFF vs ON. Your son will immediately see the real enemy is often the investor, not the market.")
else:
    st.info("Set assumptions, then click **Run simulation**.")
