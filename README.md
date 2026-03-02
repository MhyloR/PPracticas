# Proyecto de Prácticas

## Descripción  
Generar una interfaz gráfica donde el usuario ingrese un *dataset ID* o un archivo plano, y este le permita seleccionar la variable a trabajar con un filtro de atributos.

---

## Instalación del ambiente virtual y dependencias

### Primer método
1. Abrir **VS Code**.  
2. En la consola instalar *virtualenv*:  
   ```bash
   pip install virtualenv
   ```
   **Nota:** La instalación de esta librería es opcional. Después se explicará otro método para instalar un ambiente virtual.
3. Crear el ambiente virtual:  
   ```bash
   virtualenv -p python <Nombre_del_ambiente>
   ```
4. Activar el ambiente virtual:  
   ```bash
   .\<Nombre_del_ambiente>\Scripts\activate
   ```
5. Si todo salió bien, en la terminal aparecerá algo como:  
   ```
   (<Nombre_del_ambiente>) PS D: ...
   ```
   La letra del disco puede variar dependiendo de tu instalación o particiones.

---

### Segundo método
1. Abrir la consola de **VS Code**.  
2. Crear el ambiente virtual con:  
   ```bash
   python -m venv <Nombre_del_ambiente_virtual>
   ```
3. Activarlo:  
   ```bash
   .\<Nombre_del_ambiente_virtual>\Scripts\Activate.ps1
   ```
4. Si la activación fue exitosa, deberías ver algo similar en la terminal.

---

## TIP
Si no puedes activar el ambiente virtual:
1. Ubica la carpeta creada con el nombre de tu ambiente.  
2. Entra a la carpeta **Scripts**.  
3. Localiza el archivo **Activate.ps1**.  
4. Copia su ruta completa.  
5. Pégala y ejecútala en la terminal.  
6. ¡Listo!

---

## Cómo eliminar el ambiente virtual
Basta con ubicar la carpeta correspondiente al ambiente virtual y eliminarla manualmente desde tu explorador de archivos o desde VS Code.

---

## Instalación de dependencias
1. Ubica el archivo **requirements.txt** (el actual es temporal).  
2. En tu ambiente virtual ejecuta:  
   ```bash
   pip install -r .\requirements.txt
   ```
3. Espera a que termine la instalación.

---
