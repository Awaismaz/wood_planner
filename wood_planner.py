import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from rectpack import newPacker

SHEET_WIDTH = 1220
SHEET_HEIGHT = 2440

def load_panels(csv_path):
    df = pd.read_csv(csv_path)
    panels = []
    for _, row in df.iterrows():
        for _ in range(row['Quantity']):
            panels.append((row['Width_mm'], row['Height_mm'], row['PanelID']))
    return panels

def pack_panels(panels):
    packer = newPacker(rotation=False)

    # Add all rectangles
    for w, h, _id in panels:
        packer.add_rect(w, h, rid=_id)

    # Add bin(s) (4x8 sheet size)
    for _ in range(100):  # Max 100 sheets
        packer.add_bin(SHEET_WIDTH, SHEET_HEIGHT)

    packer.pack()

    layouts = []
    for i, abin in enumerate(packer):
        layout = []
        for rect in abin:
            x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
            layout.append({'x': x, 'y': y, 'width': w, 'height': h, 'id': rid})
        layouts.append(layout)

    return layouts

def draw_layout(sheets):
    for idx, sheet in enumerate(sheets):
        fig, ax = plt.subplots()
        ax.set_xlim(0, SHEET_WIDTH)
        ax.set_ylim(0, SHEET_HEIGHT)
        ax.set_title(f'Sheet {idx + 1}')
        ax.set_aspect('equal')

        for panel in sheet:
            rect = patches.Rectangle(
                (panel['x'], panel['y']),
                panel['width'],
                panel['height'],
                linewidth=1,
                edgecolor='black',
                facecolor='lightgray'
            )
            ax.add_patch(rect)
            ax.text(panel['x'] + 10, panel['y'] + 10, panel['id'], fontsize=8)

        plt.gca().invert_yaxis()
        plt.show()

if __name__ == '__main__':
    panels = load_panels('test.csv')
    layouts = pack_panels(panels)
    draw_layout(layouts)
    print(f"Total Sheets Required: {len(layouts)}")
