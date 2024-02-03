
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Datos de ejemplo
V = np.array([[3, 2], [-2, 2], [4, 5]])
nombres_canciones = ['Canción A', 'Canción B', 'Canción C']

origin = np.array([[0, 0, 0], [0, 0, 0]])  # Punto de origen

fig, ax = plt.subplots()
ax.quiver(*origin, V[:, 0], V[:, 1], color=['mediumturquoise', 'coral', 'coral'], scale=21)

for i, nombre in enumerate(nombres_canciones):
    print("A")
    ax.annotate(nombre, xy=(V[i, 0], V[i, 1]))

ax.set_xlabel('Energía')
ax.set_ylabel('Instrumentalidad')

plt.show()


