import os
import threading
import time

# CONFIGURACION GLOBAL

DB_FILE = "fat_db.txt"

# GPWD = directorio actual
GPWD = 0

# Lock para evitar problemas de concurrencia
lock = threading.Lock()


# FUNCIONES BASE

def inicializar_sistema():
    """
    Inicializa el sistema FAT.
    Si el archivo no existe, crea el directorio raiz.
    """

    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as archivo:
            archivo.write("0|/|DIR|-1|rwx|-\n")

    print("Sistema FAT inicializado correctamente.")
    print("Directorio actual: /")


def leer_db():
    """
    Lee todos los registros del archivo fat_db.txt
    """

    with lock:
        with open(DB_FILE, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()

    registros = []

    for linea in lineas:
        linea = linea.strip()

        if linea:
            partes = linea.split("|")

            registro = {
                "id": int(partes[0]),
                "nombre": partes[1],
                "tipo": partes[2],
                "padre": int(partes[3]),
                "permisos": partes[4],
                "tamano": partes[5]
            }

            registros.append(registro)

    return registros


def escribir_db(registros):
    """
    Sobrescribe completamente la base de datos
    """

    with lock:
        with open(DB_FILE, "w", encoding="utf-8") as archivo:

            for r in registros:
                linea = (
                    f"{r['id']}|"
                    f"{r['nombre']}|"
                    f"{r['tipo']}|"
                    f"{r['padre']}|"
                    f"{r['permisos']}|"
                    f"{r['tamano']}\n"
                )

                archivo.write(linea)


def obtener_nuevo_id(registros):
    """
    Genera un nuevo ID unico
    """

    if not registros:
        return 0

    return max(r["id"] for r in registros) + 1


def buscar_por_nombre(nombre, padre):
    """
    Busca un archivo/directorio por nombre y padre
    """

    registros = leer_db()

    for r in registros:
        if r["nombre"] == nombre and r["padre"] == padre:
            return r

    return None


def obtener_ruta_actual():
    """
    Construye la ruta actual usando GPWD
    """

    registros = leer_db()

    if GPWD == 0:
        return "/"

    ruta = []

    actual = GPWD

    while actual != -1:

        nodo = next((r for r in registros if r["id"] == actual), None)

        if nodo:
            ruta.append(nodo["nombre"])
            actual = nodo["padre"]
        else:
            break

    ruta.reverse()

    return "/" + "/".join(ruta[1:])


# COMANDOS FAT

def mkdir(nombre):
    registros = leer_db()

    existente = buscar_por_nombre(nombre, GPWD)

    if existente:
        print(f"Error: '{nombre}' ya existe.")
        return

    nuevo = {
        "id": obtener_nuevo_id(registros),
        "nombre": nombre,
        "tipo": "DIR",
        "padre": GPWD,
        "permisos": "rwx",
        "tamano": "-"
    }

    registros.append(nuevo)

    escribir_db(registros)

    print(f"Directorio '{nombre}' creado correctamente.")


def touch(nombre):
    registros = leer_db()

    existente = buscar_por_nombre(nombre, GPWD)

    if existente:
        print(f"Error: '{nombre}' ya existe.")
        return

    nuevo = {
        "id": obtener_nuevo_id(registros),
        "nombre": nombre,
        "tipo": "FILE",
        "padre": GPWD,
        "permisos": "rw-",
        "tamano": "0"
    }

    registros.append(nuevo)

    escribir_db(registros)

    print(f"Archivo '{nombre}' creado correctamente.")


def ls():
    registros = leer_db()

    encontrados = False

    for r in registros:
        if r["padre"] == GPWD:
            print(r["nombre"])
            encontrados = True

    if not encontrados:
        print("Directorio vacio.")


def ls_l():
    registros = leer_db()

    print("ID | TIPO | PERMISOS | TAMAÑO | NOMBRE")

    encontrados = False

    for r in registros:
        if r["padre"] == GPWD:

            print(
                f"{r['id']} | "
                f"{r['tipo']} | "
                f"{r['permisos']} | "
                f"{r['tamano']} | "
                f"{r['nombre']}"
            )

            encontrados = True

    if not encontrados:
        print("Directorio vacio.")


def cd(nombre):
    global GPWD

    registros = leer_db()

    if nombre == "..":

        if GPWD == 0:
            print("Ya estas en el directorio raiz.")
            return

        actual = next((r for r in registros if r["id"] == GPWD), None)

        if actual:
            GPWD = actual["padre"]

        print(f"Directorio actual cambiado a: {obtener_ruta_actual()}")
        return

    destino = None

    for r in registros:
        if (
            r["nombre"] == nombre and
            r["padre"] == GPWD and
            r["tipo"] == "DIR"
        ):
            destino = r
            break

    if destino:
        GPWD = destino["id"]
        print(f"Directorio actual cambiado a: {obtener_ruta_actual()}")
    else:
        print(f"Error: directorio '{nombre}' no encontrado.")


def chmod(permisos, nombre):
    registros = leer_db()

    encontrado = False

    for r in registros:
        if r["nombre"] == nombre and r["padre"] == GPWD:
            r["permisos"] = permisos
            encontrado = True
            break

    if encontrado:
        escribir_db(registros)
        print(f"Permisos de '{nombre}' cambiados a {permisos}.")
    else:
        print(f"Error: '{nombre}' no encontrado.")


def rm(nombre):
    registros = leer_db()

    nuevo_registros = []

    eliminado = False

    for r in registros:

        if (
            r["nombre"] == nombre and
            r["padre"] == GPWD and
            r["tipo"] == "FILE"
        ):
            eliminado = True
            continue

        nuevo_registros.append(r)

    if eliminado:
        escribir_db(nuevo_registros)
        print(f"Archivo '{nombre}' eliminado correctamente.")
    else:
        print(f"Error: archivo '{nombre}' no encontrado.")


# HILOS

def crear_archivo_hilo(numero):
    nombre = f"hilo_{numero}.txt"

    print(f"Hilo {numero} creando archivo {nombre}")

    # Pequeña pausa para simular concurrencia real
    time.sleep(0.2)

    with lock:

        registros = leer_db()

        existente = buscar_por_nombre(nombre, GPWD)

        if not existente:

            nuevo = {
                "id": obtener_nuevo_id(registros),
                "nombre": nombre,
                "tipo": "FILE",
                "padre": GPWD,
                "permisos": "rw-",
                "tamano": "0"
            }

            registros.append(nuevo)

            escribir_db(registros)


def test_hilos():
    print("Iniciando prueba concurrente con hilos...")

    hilos = []

    for i in range(1, 6):

        hilo = threading.Thread(
            target=crear_archivo_hilo,
            args=(i,)
        )

        hilos.append(hilo)

        hilo.start()

    for hilo in hilos:
        hilo.join()

    print("Todos los hilos finalizaron correctamente.")


# MENU PRINCIPAL

def mostrar_comandos():

    print("\nComandos disponibles:")
    print("mkdir <nombre_directorio>")
    print("cd <nombre_directorio>")
    print("cd ..")
    print("touch <nombre_archivo>")
    print("ls")
    print("ls -l")
    print("chmod <permisos> <nombre>")
    print("rm <nombre_archivo>")
    print("test_hilos")
    print("exit")


def main():

    inicializar_sistema()

    print("=" * 40)
    print(" SIMULADOR FAT EN PYTHON")
    print("=" * 40)

    mostrar_comandos()

    while True:

        comando = input("\n> ").strip()

        if not comando:
            continue

        partes = comando.split()

        cmd = partes[0]

        try:

            if cmd == "mkdir":

                if len(partes) != 2:
                    print("Uso: mkdir <nombre>")
                else:
                    mkdir(partes[1])

            elif cmd == "touch":

                if len(partes) != 2:
                    print("Uso: touch <nombre>")
                else:
                    touch(partes[1])

            elif cmd == "ls":

                if len(partes) == 1:
                    ls()

                elif len(partes) == 2 and partes[1] == "-l":
                    ls_l()

                else:
                    print("Uso: ls o ls -l")

            elif cmd == "cd":

                if len(partes) != 2:
                    print("Uso: cd <directorio>")
                else:
                    cd(partes[1])

            elif cmd == "chmod":

                if len(partes) != 3:
                    print("Uso: chmod <permisos> <nombre>")
                else:
                    chmod(partes[1], partes[2])

            elif cmd == "rm":

                if len(partes) != 2:
                    print("Uso: rm <archivo>")
                else:
                    rm(partes[1])

            elif cmd == "test_hilos":
                test_hilos()

            elif cmd == "exit":
                print("Saliendo del simulador FAT...")
                break

            else:
                print("Comando no reconocido.")

        except Exception as e:
            print(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()
