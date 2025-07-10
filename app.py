import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
        grid = np.array(all_wells).reshape(8, 12)

        st.markdown("### Select Replicate Sets")

        if "replicate_sets" not in st.session_state:
            st.session_state.replicate_sets = []

        selected_wells = st.multiselect("Select wells for a replicate set (hold Ctrl/Shift to multi-select):", all_wells)
        if st.button("Add Replicate Set"):
            if selected_wells:
                st.session_state.replicate_sets.append(selected_wells)

        if st.button("Reset All Selections"):
            st.session_state.replicate_sets = []

        st.markdown("### Plate Map")
        z = [[f"{r}{c}" if f"{r}{c}" in well_data else "" for c in COLS] for r in ROWS]

        colors = ["lightblue", "lightgreen", "plum", "orange", "khaki", "lightpink", "lightcyan", "wheat"]
        well_color_map = {}
        for i, block in enumerate(st.session_state.replicate_sets):
            for well in block:
                well_color_map[well] = colors[i % len(colors)]

        fig = go.Figure()
        for i, row in enumerate(ROWS):
            for j, col in enumerate(COLS):
                well = f"{row}{col}"
                fillcolor = well_color_map.get(well, "white")
                fig.add_shape(type="rect", x0=j, x1=j+1, y0=-i, y1=-(i+1), line=dict(color="black"), fillcolor=fillcolor)
                fig.add_annotation(x=j+0.5, y=-(i+0.5), text=well, showarrow=False)

        fig.update_layout(height=400, width=800, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(visible=False), yaxis=dict(visible=False))
        st.plotly_chart(fig)

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
                label = block[0]  # Use first well as condition label
                for i, t in enumerate(timepoints):
                    rows.append({"Time": round(t, 3), "Condition": label, "Mean": mean[i], "SD": std[i]})

            tidy_df = pd.DataFrame(rows)
            csv = tidy_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Tidy CSV", csv, "tidy_output.csv", "text/csv")
