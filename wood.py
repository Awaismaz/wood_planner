import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from rectpack import newPacker
import ezdxf
import io
import base64

# Default Sheet Size
DEFAULT_SHEET_WIDTH = 2440
DEFAULT_SHEET_HEIGHT = 1220

st.set_page_config(page_title="Cutlist Optimizer", layout="wide")
st.title("🪚 Sheet Optimizer for Wood Panels")

st.sidebar.header("Input Panels")
uploaded_file = st.sidebar.file_uploader("Upload CSV with PanelID, Width_mm, Height_mm, Quantity", type=["csv"])

sheet_width = st.sidebar.number_input("Sheet Width (mm)", value=DEFAULT_SHEET_WIDTH)
sheet_height = st.sidebar.number_input("Sheet Height (mm)", value=DEFAULT_SHEET_HEIGHT)
sheet_cost = st.sidebar.number_input("Cost per Sheet (PKR)", value=4000)

example = pd.DataFrame({
    "PanelID": ["P1", "P2", "P3"],
    "Width_mm": [600, 800, 1200],
    "Height_mm": [400, 300, 600],
    "Quantity": [4, 2, 1]
})

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = example

st.sidebar.subheader("Current Panel List")
df = st.sidebar.data_editor(df, use_container_width=True, num_rows="dynamic")


if 'layouts' not in st.session_state:
    st.session_state.layouts = []
    st.session_state.dxf_buffers = []
    st.session_state.total_waste = 0

if st.sidebar.button("🧮 Calculate Layout"):
    panels = []
    for _, row in df.iterrows():
        for _ in range(int(row['Quantity'])):
            panels.append((row['Width_mm'], row['Height_mm'], row['PanelID']))

    packer = newPacker(rotation=False)
    for w, h, rid in panels:
        packer.add_rect(w, h, rid=rid)
    for _ in range(100):
        packer.add_bin(sheet_width, sheet_height)
    packer.pack()

    layouts = []
    dxf_buffers = []
    total_used_area = 0
    sheet_area = sheet_width * sheet_height

    for i, abin in enumerate(packer):
        layout = []
        doc = ezdxf.new()
        msp = doc.modelspace()
        for rect in abin:
            x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
            layout.append({'x': x, 'y': y, 'width': w, 'height': h, 'id': rid})
            msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], close=True)
            msp.add_text(rid, dxfattribs={"height": 30}).set_placement((x + 10, y + 10))
            total_used_area += (w * h)
        layouts.append(layout)
        buf = io.StringIO()
        doc.write(buf)
        dxf_buffers.append(buf.getvalue().encode())

    total_sheets = len(layouts)
    total_area = total_sheets * sheet_area
    total_waste = total_area - total_used_area
    waste_cost = (total_waste / total_area) * sheet_cost * total_sheets

    st.session_state.layouts = layouts
    st.session_state.dxf_buffers = dxf_buffers
    st.session_state.total_waste = total_waste
    st.session_state.waste_cost = waste_cost
    st.session_state.total_sheets = total_sheets

if st.session_state.layouts:
    layouts = st.session_state.layouts
    dxf_buffers = st.session_state.dxf_buffers

    st.subheader(f"📐 Total Sheets Used: {st.session_state.total_sheets}")

    col1, col2 = st.columns([1, 4])
    with col1:
        sheet_index = st.number_input("Select Sheet", min_value=1, max_value=len(layouts), value=1, step=1) - 1
    with col2:
        sheet = layouts[sheet_index]
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.set_xlim(0, sheet_width)
        ax.set_ylim(0, sheet_height)
        ax.set_title(f'Sheet {sheet_index + 1}')
        ax.set_aspect('equal')

        for panel in sheet:
            rect = patches.Rectangle(
                (panel['x'], panel['y']),
                panel['width'],
                panel['height'],
                linewidth=1,
                edgecolor='black',
                facecolor='skyblue'
            )
            ax.add_patch(rect)
            ax.text(
                panel['x'] + panel['width'] / 2,
                panel['y'] + panel['height'] / 2,
                panel['id'],
                fontsize=8,
                ha='center',
                va='center'
            )

        ax.invert_yaxis()
        st.pyplot(fig)

    b64 = base64.b64encode(dxf_buffers[sheet_index]).decode()
    href = f'<a href="data:application/dxf;base64,{b64}" download="sheet_{sheet_index + 1}.dxf">Download DWG for Sheet {sheet_index + 1}</a>'
    st.markdown(href, unsafe_allow_html=True)

    st.info(f"🧾 Estimated Waste Area: {st.session_state.total_waste:.0f} mm²")
    st.info(f"💸 Estimated Waste Cost: PKR {st.session_state.waste_cost:.0f}")

    st.success("✅ Done! Upload your own file to test different cutlists.")