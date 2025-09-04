import streamlit as st
import pandas as pd
import os
import json

# ----- Config -----
CSV_FILE = "votes.csv"
JSON_LOGINS = "logins.json"
JSON_CONFIG = "config.json"

with open(JSON_CONFIG, 'r') as file:
    config = json.load(file)
    PROJECT_NAMES = config["project_names"]
    NUM_SLIDERS = len(PROJECT_NAMES)
    POINTS_LIMIT = config["points"]
    logins = config["logins"]
    logins["results_only"] = ["View Results", True]


st.set_page_config(page_title="Make a Change Vote", layout="centered")

# ----- Title -----
st.title(f"🗳️ Allocate {POINTS_LIMIT} Points Across {NUM_SLIDERS} Projects")

# ----- Initialize session state -----
if "login" not in st.session_state:
    st.session_state.login = ""
    if not os.path.exists(JSON_LOGINS):
        with open(JSON_LOGINS, 'w') as file:
            file.write(json.dumps(logins))

for i in range(NUM_SLIDERS):
    slider_key = f"slider_{i}"
    if slider_key not in st.session_state:
        st.session_state[slider_key] = 0

with open(JSON_LOGINS, 'r') as file:
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
    if st.button("View Results"):
        st.session_state.login = "results_only"
        st.rerun()

# ----- Voting UI -----
elif logins[st.session_state.login][1] == False:
    for i in range(NUM_SLIDERS):
        st.slider(
            PROJECT_NAMES[i],
            min_value=0,
            max_value=POINTS_LIMIT,
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
            with open(JSON_LOGINS, 'w') as file:
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
