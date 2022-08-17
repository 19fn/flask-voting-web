from matplotlib import pyplot as plt
from io import StringIO
import base64

def PieChart(x,y):
    # Generate plot
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    labels = 'Green', 'Red'
    sizes = [x, y]
    explode = (0, 0.1)  # only "explode" the 2nd slice (i.e. 'Hogs')
    colours = ('#5cb85c','#d9534f')

    img = StringIO.StringIO()
    fig1, ax1 = plt.subplots()

    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90, colors=colours)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)

    plot_url = base64.b64encode(img.getvalue())

    # plt.savefig("./web/imgs/plt.png",dpi=300, bbox_inches='tight')

    return plot_url
