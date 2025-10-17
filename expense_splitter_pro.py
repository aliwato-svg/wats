
# ==========================================
# 💰 Smart Expense Splitter App (Enhanced)
# ==========================================
# Run using:
#   streamlit run expense_splitter_pro.py
#
# Features:
# ✅ Add/remove participants
# ✅ Add equal or unequal expenses
# ✅ Editable table of expenses
# ✅ Automatic balance & settlement calculation
# ✅ Pie chart + summary
# ✅ CSV export
# ==========================================

import streamlit as st
import pandas as pd
import os

# ---------------------------
# Setup and Initialization
# ---------------------------
st.set_page_config(page_title="💰 Expense Splitter Pro", layout="wide")

file_name = "expenses.csv"

def load_expenses():
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    else:
        return pd.DataFrame(columns=["Participant", "Amount"])

def save_expenses(df):
    df.to_csv(file_name, index=False)

if "expenses" not in st.session_state:
    st.session_state.expenses = load_expenses()

expenses_df = st.session_state.expenses

tab1, tab2, tab3 = st.tabs(["👥 Participants", "💵 Add Expense", "📊 Summary"])

# 👥 TAB 1: Manage Participants
with tab1:
    st.header("👥 Add or Remove Participants")
    col1, col2 = st.columns([3, 1])
    new_participant = col1.text_input("Enter participant name")
    add_btn = col2.button("➕ Add")

    if add_btn and new_participant:
        if new_participant not in expenses_df["Participant"].values:
            new_row = pd.DataFrame({"Participant": [new_participant], "Amount": [0.0]})
            expenses_df = pd.concat([expenses_df, new_row], ignore_index=True)
            save_expenses(expenses_df)
            st.session_state.expenses = expenses_df
            st.success(f"✅ Added {new_participant}")
        else:
            st.warning("⚠ Participant already exists!")

    st.subheader("Current Participants")
    edited_df = st.data_editor(expenses_df, num_rows="dynamic", key="participants_table")
    if st.button("💾 Save Changes"):
        save_expenses(edited_df)
        st.session_state.expenses = edited_df
        st.success("✅ Saved successfully!")

# 💵 TAB 2: Add Expense
with tab2:
    st.header("💵 Add a New Expense")

    if len(expenses_df) == 0:
        st.warning("⚠ Please add participants first.")
    else:
        payer = st.selectbox("Who paid?", expenses_df["Participant"].tolist())
        amount = st.number_input("Total amount", min_value=0.0, format="%.2f")
        description = st.text_input("Expense description (e.g. Dinner, Taxi, Movie)")
        split_type = st.radio("Split type", ["Equal", "Unequal"], horizontal=True)

        if split_type == "Unequal":
            st.info("Enter share percentages (must sum to 100%)")
            cols = st.columns(len(expenses_df))
            shares = []
            for i, person in enumerate(expenses_df["Participant"]):
                share = cols[i].number_input(f"{person}'s %", min_value=0.0, max_value=100.0, step=1.0, key=f"share_{i}")
                shares.append(share)

        if st.button("💰 Add Expense"):
            if amount <= 0:
                st.warning("⚠ Enter a valid amount.")
            else:
                if split_type == "Equal":
                    share_per_person = amount / len(expenses_df)
                    expenses_df["Amount"] += share_per_person
                else:
                    if abs(sum(shares) - 100) > 0.01:
                        st.error("❌ Percentages must sum to 100!")
                        st.stop()
                    expenses_df["Amount"] += [(amount * (s / 100)) for s in shares]

                save_expenses(expenses_df)
                st.session_state.expenses = expenses_df
                st.success(f"✅ {payer} paid {amount:.2f} for {description}")

# 📊 TAB 3: Summary and Balances
with tab3:
    st.header("📊 Expense Summary")

    if len(expenses_df) == 0:
        st.warning("⚠ No data available.")
    else:
        total_spent = expenses_df["Amount"].sum()
        per_person = total_spent / len(expenses_df)
        balances = expenses_df.copy()
        balances["Balance"] = balances["Amount"] - per_person

        st.subheader("💰 Balances")
        for _, row in balances.iterrows():
            name, balance = row["Participant"], row["Balance"]
            if balance > 0:
                st.success(f"✅ {name} should receive {balance:.2f}")
            elif balance < 0:
                st.error(f"❌ {name} owes {-balance:.2f}")
            else:
                st.info(f"✔ {name} is settled.")

        st.divider()
        st.subheader("📈 Spending Overview")
        st.bar_chart(expenses_df.set_index("Participant")["Amount"])
        st.caption(f"Total Spent: {total_spent:.2f} | Fair Share: {per_person:.2f} per person")

        st.subheader("🤝 Settlement Suggestions")
        debtors = balances[balances["Balance"] < 0].copy()
        creditors = balances[balances["Balance"] > 0].copy()
        suggestions = []
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor = debtors.iloc[i]
            creditor = creditors.iloc[j]
            pay = min(-debtor["Balance"], creditor["Balance"])
            suggestions.append(f"{debtor['Participant']} → {creditor['Participant']}: {pay:.2f}")
            debtors.at[debtor.name, "Balance"] += pay
            creditors.at[creditor.name, "Balance"] -= pay
            if abs(debtors.at[debtor.name, "Balance"]) < 1e-6: i += 1
            if abs(creditors.at[creditor.name, "Balance"]) < 1e-6: j += 1

        if suggestions:
            for s in suggestions:
                st.write("💸", s)
        else:
            st.info("All settled!")

        csv = expenses_df.to_csv(index=False).encode("utf-8")
        st.download_button("📂 Download CSV", data=csv, file_name="expenses.csv", mime="text/csv")
