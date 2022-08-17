
import io, base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


def PieChart():
    # Generate plot, setting the axes at the centre
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    labels = 'Green', 'Red'
    sizes = [918, 931]
    explode = (0, 0.1)  # only "explode" the 2nd slice (i.e. 'Hogs')
    colours = ('#5cb85c','#d9534f')

    fig1, ax1 = plt.subplots()

    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90, colors=colours)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # plt.show()

    # Convert plot to PNG image
    pngImage = io.BytesIO()
    FigureCanvas(ax1).print_png(pngImage)

    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    return pngImageB64String
