import ttkbootstrap as ttk

# Crear una ventana temporal para acceder a los estilos
root = ttk.Window()
style = ttk.Style()

# Imprimir todos los nombres de temas
print("Temas disponibles en tu versión:")
for nombre in style.theme_names():
    print(f"  - {nombre}")

root.destroy()