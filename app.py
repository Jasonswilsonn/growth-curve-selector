import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROWS = list("ABCDEFGH")
COLS = list(range(1, 13))

st.title("96-Well Growth Curve Replicate Selector")

uploaded_file = st.file_uploader("Upload Growth Curve CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Time [s]" not in df.columns:
        st.error("CSV must contain a 'Time [s]' column.")
    else:
        timepoints = df["Time [s]"].values
        well_data = {col: df[col].values for col in df.columns if col != "Time [s]"}

        all_wells = [f"{r}{c}" for r in ROWS for c in COLS if f"{r}{c}" in well_data]

        if "selected_wells" not in st.session_state:
            st.session_state.selected_wells = set()
        if "replicate_sets" not in st.session_state:
            st.session_state.replicate_sets = []

        def toggle_well_selection(clicked_well):
            if clicked_well in st.session_state.selected_wells:
                st.session_state.selected_wells.remove(clicked_well)
            else:
                st.session_state.selected_wells.add(clicked_well)

        st.markdown("### Plate Map (Click wells to select)")
        fig = go.Figure()
        colors = ["lightblue", "lightgreen", "plum", "orange", "khaki", "lightpink", "lightcyan", "wheat"]

        color_map = {}
        for i, block in enumerate(st.session_state.replicate_sets):
            for well in block:
                color_map[well] = colors[i % len(colors)]
        for well in st.session_state.selected_wells:
            color_map[well] = "gray"

        for i, row in enumerate(ROWS):
            for j, col in enumerate(COLS):
                well = f"{row}{col}"
                if well not in well_data:
                    continue
                fillcolor = color_map.get(well, "white")
                fig.add_shape(
                    type="rect", x0=j, x1=j+1, y0=-i, y1=-(i+1),
                    line=dict(color="black"), fillcolor=fillcolor
                )
                fig.add_annotation(
                    x=j+0.5, y=-(i+0.5), text=well, showarrow=False,
                    font=dict(color="black"),
                    hovertext=f"Click to select {well}",
                )

        fig.update_layout(
            height=500, width=1000,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(visible=False, fixedrange=True, range=[0, 12]),
            yaxis=dict(visible=False, fixedrange=True, range=[-8, 0]),
            dragmode=False
        )

        click_data = st.plotly_chart(fig, use_container_width=False)

        clicked = st.experimental_get_query_params().get("clicked", [None])[0]
        if clicked and clicked in all_wells:
            toggle_well_selection(clicked)

        if st.button("Add Replicate Set"):
            if st.session_state.selected_wells:
                st.session_state.replicate_sets.append(list(st.session_state.selected_wells))
                st.session_state.selected_wells.clear()

        if st.button("Reset All Selections"):
            st.session_state.selected_wells.clear()
            st.session_state.replicate_sets = []

        if st.button("Export Tidy CSV"):
            rows = []
            for block in st.session_state.replicate_sets:
                if not block:
                    continue
                num_reps = len(block)
                data_matrix = np.array([well_data[w] for w in block if w in well_data])
                if data_matrix.shape[0] != num_reps:
                    st.warning("Mismatch in replicate data size.")
                    continue
                mean = np.mean(data_matrix, axis=0)
                std = np.std(data_matrix, axis=0)
                label = block[0]
                for i, t in enumerate(timepoints):
                    rows.append({"Time": round(t, 3), "Condition": label, "Mean": mean[i], "SD": std[i]})

            tidy_df = pd.DataFrame(rows)
            csv = tidy_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Tidy CSV", csv, "tidy_output.csv", "text/csv")
