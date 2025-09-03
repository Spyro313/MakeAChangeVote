import streamlit as st
import pandas as pd
import os
import time  # ✅ for sleep
import json

# ----- Config -----
POINTS_LIMIT = 10
NUM_SLIDERS = 7
PROJECT_NAMES = ["1.\u00A0P", "2.\u00A0F", "3.\u00A0A", "4.\u00A0S", "5.\u00A0M", "6.\u00A0Q", "7.\u00A0C"]
logins = {"941": ("", False), "890": ("", False), "307": ("", False), "241": ("", False), "808": ("", False), "153": ("", False), "594": ("", False), "638": ("", False), "168": ("", False), "925": ("", False), "376": ("", False), "000": ("", True)}
CSV_FILE = "votes.csv"
JSON_FILE = "logins.json"


st.set_page_config(page_title="Make a Change Vote", layout="centered")

# ----- Title -----
st.title("🗳️ Allocate 10 Points Across 7 Projects")

# ----- Initialize session state -----
if "login" not in st.session_state:
    st.session_state.login = ""
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as file:
            file.write(json.dumps(logins))

for i in range(NUM_SLIDERS):
    slider_key = f"slider_{i}"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = 0

with open(JSON_FILE, 'r') as file:
    logins = json.load(file)

# ----- Slider change constraint -----
def total_excluding(index):
    return sum(
        st.session_state[f"slider_{j}"]
        for j in range(NUM_SLIDERS)
        if j != index
    )

def handle_slider_change(index):
    key = f"slider_{index}"
    current_value = st.session_state[key]
    other_total = total_excluding(index)
    max_allowed = POINTS_LIMIT - other_total

    if current_value > max_allowed:
        st.warning(
            f"Total exceeds {POINTS_LIMIT}. "
            f"Reducing Project {index + 1} to {max_allowed}."
        )
        st.session_state[key] = max_allowed
# ----- Login UI -----
if st.session_state.login == "":
    user_login = st.text_input("Enter your code")
    if st.button("Log in"):
        if user_login in logins.keys():
            st.session_state.login = user_login
            st.rerun()
        else:
            st.error("Incorrect login")

# ----- Voting UI -----
elif logins[st.session_state.login][1] == False:
    for i in range(NUM_SLIDERS):
        st.slider(
            PROJECT_NAMES[i],
            min_value=0,
            max_value=10,
            key=f"slider_{i}",
            on_change=handle_slider_change,
            args=(i,)
        )

    total = sum(st.session_state[f"slider_{i}"] for i in range(NUM_SLIDERS))
    st.markdown(f"**Total allocated:** {total} / {POINTS_LIMIT}")

    if st.button("✅ Submit and Show Results"):
        if total != POINTS_LIMIT:
            st.error(f"Please allocate exactly {POINTS_LIMIT} points before submitting.")
        else:
            vote_data = {
                f"{PROJECT_NAMES[i]}": st.session_state[f"slider_{i}"]
                for i in range(NUM_SLIDERS)
            }
            df_new = pd.DataFrame([vote_data])

            if os.path.exists(CSV_FILE):
                df_existing = pd.read_csv(CSV_FILE)
                df_all = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_all = df_new

            df_all.to_csv(CSV_FILE, index=False)

            logins[st.session_state.login][1] = True
            with open(JSON_FILE, 'w') as file:
                file.write(json.dumps(logins))
            st.rerun()

# ----- Results UI -----
else:
    st.success("✅ Your vote has been submitted.")

    if os.path.exists(CSV_FILE):
        df_results = pd.read_csv(CSV_FILE)
        totals = df_results.sum()

        st.markdown("## 📊 Aggregated Results")
        st.bar_chart(totals)

        with st.expander("📄 See all submissions"):
            st.dataframe(df_results)
    else:
        st.info("No votes submitted yet.")

    if st.button("Reload data"):
        st.rerun()

    # ✅ Manual refresh every 10 seconds
    #time.sleep(10)
    #st.rerun()

# ----- Admin Reset Button -----
#with st.expander("⚙️ Admin Controls"):
#    if st.button("🗑️ Reset All Votes"):
#        if os.path.exists(CSV_FILE):
#            os.remove(CSV_FILE)
#            st.success("✅ All votes have been reset.")
#            st.session_state.submitted = False
#            st.rerun()
#        else:
#            st.info("ℹ️ No vote file found to reset.")
