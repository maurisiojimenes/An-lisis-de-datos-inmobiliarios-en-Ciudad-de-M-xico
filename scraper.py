from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import unicodedata
import re
import json

def generar_id(prefijo, index):
    return f"{prefijo}-{index:06d}"

def obtener_informacion(driver):#La función solo recibira el driver y devolvera un diccionario
    #Estos son los datos que queremos obtener de cada inmueble
    informacion = {
        "precios": [],
        "delegacion": [],
        "num_habitaciones": [],
        "num_duchas": [],
        "estacionamiento": [],
        "tipo": [],
        "area_terreno": [],
        "area_construida": []
    }

    try:
        # Precio
        precio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "prices-and-fees__price"))
        )
        informacion['precios'].append(precio.text)

        # Ubicación
        ubicacion = driver.find_element(By.CLASS_NAME, "view-map__text")
        informacion['delegacion'].append(ubicacion.text)

        # Habitaciones y baños
        detalles = driver.find_elements(By.CLASS_NAME, "details-item-value")
        habitaciones = "no disponible"
        duchas = "no disponible"

        for detalle in detalles:
            data_test = detalle.get_attribute("data-test")
            if data_test == "bedrooms-value":
                habitaciones = detalle.text
            elif data_test == "full-bathrooms-value":
                duchas = detalle.text

        informacion['num_habitaciones'].append(habitaciones)
        informacion['num_duchas'].append(duchas)


        # Estacionamiento
        try:
            estacionamiento = driver.find_elements(By.XPATH, "//div[@class='facilities__item']//span[text()='Estacionamiento']")
            if estacionamiento:
                informacion['estacionamiento'].append(1)  # Tiene estacionamiento
            else:
                informacion['estacionamiento'].append(0)  # No tiene estacionamiento
        except Exception as e:
            informacion['estacionamiento'].append(0) 


        # Tipo
        try:
            tipo = driver.find_element(By.CSS_SELECTOR, '[data-test="property-type-value"]')
            informacion['tipo'].append(tipo.text)
        except Exception as e:
            informacion['tipo'].append("no disponible")

        # Área del terreno
        try:
            area = driver.find_element(By.CSS_SELECTOR, '[data-test="plot-area-value"]')
            informacion['area_terreno'].append(area.text)
        except Exception as e:
            informacion['area_terreno'].append("no disponible")

        # Área construida
        try:
            area_construida = driver.find_element(By.CSS_SELECTOR, '[data-test="floor-area-value"]')
            informacion['area_construida'].append(area_construida.text)
        except Exception as e:
            informacion['area_construida'].append("no disponible")

    except Exception as e:
        pass

    print(informacion)
    return informacion

def alcaldias(direccion):
    palabras = direccion.split()
    palabras = [palabra.strip(",.") for palabra in palabras]
    alcaldias_cdmx = [
        "Álvaro Obregón",
        "Azcapotzalco",
        "Benito Juárez",
        "Coyoacán",
        "Cuajimalpa de Morelos",
        "Cuauhtémoc",
        "Gustavo A. Madero",
        "Iztacalco",
        "Iztapalapa",
        "Magdalena Contreras",
        "Miguel Hidalgo",
        "Milpa Alta",
        "Tláhuac",
        "Tlalpan",
        "Venustiano Carranza",
        "Xochimilco"
    ]
    for alcaldia in alcaldias_cdmx:
        if alcaldia in direccion:
            alcaldia = alcaldia.lower()
            alcaldia = unicodedata.normalize("NFD", alcaldia)
            alcaldia = alcaldia.encode("ascii","ignore").decode("utf-8")
            return alcaldia

def normalizar(string):
    string = string.lower()
    string = unicodedata.normalize("NFD", string)
    string = string.encode("ascii","ignore").decode()
    return string

def extraer_entero(cadena):
    # Convertir el valor a cadena si no es None
    cadena = str(cadena) if cadena is not None else ""
    
    # Buscar el número en la cadena
    match = re.search(r'\d+', cadena)
    if match:
        return float(match.group())  # Convertir a entero
    else:
        return 0  # Si no encuentra un número, devuelve 0

def convertir_precio(precio_str):

    tipo_cambio = 20.38

    if not precio_str or not isinstance(precio_str, str):
        return 0.0  # Devuelve 0.0 si el precio es inválido

    # Limpiar el formato y extraer número y moneda
    precio_str = precio_str.replace("$", "").replace(",", "").strip()  # Remover "$" y comas
    partes = precio_str.split()  # Dividir en partes para separar monto y moneda

    try:
        monto = float(partes[0])  # Convertir la parte numérica a float
        moneda = partes[1].upper() if len(partes) > 1 else "MXN"  # Obtener la moneda, MXN por defecto
        
        if moneda == "USD":
            monto *= tipo_cambio  # Convertir a pesos si es USD
        
        return monto
    except (ValueError, IndexError):
        return 0.0  # Devolver 0.0 si ocurre algún error

def transformar_claves(datos, claves_a_transformar):
    """
    Convierte listas de listas en listas simples para las claves indicadas en un diccionario.
    
    :param datos: Diccionario con la estructura de datos.
    :param claves_a_transformar: Lista de claves a transformar.
    :return: Diccionario con las claves transformadas.
    """
    for clave in claves_a_transformar:
        if clave in datos:
            datos[clave] = [item[0] if isinstance(item, list) and len(item) > 0 else item for item in datos[clave]]
    return datos

def main():
    service = Service(ChromeDriverManager().install())
    option = webdriver.ChromeOptions()
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-popup-blocking")
    option.add_argument("--disable-notifications")
    option.add_argument("--start-maximized")
    option.add_experimental_option("excludeSwitches", ["enable-automation"])
    option.add_experimental_option("useAutomationExtension", False)
    option.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")


    driver = webdriver.Chrome(service=service, options=option)
    driver.get("https://www.lamudi.com.mx/distrito-federal/for-sale/")

    #time.sleep(5)

    informacion_completa = {
        "id":[],
        "precios": [],
        "delegacion": [],
        "num_habitaciones": [],
        "num_duchas": [],
        "estacionamiento": [] ,
        "tipo": [],
        "area_terreno": [],
        "area_construida": []
    }

    informacion_almacen = {}
    prefijo = "LAM"
    index = 1
    for i in range(50):
        print(f"Scraping página {i + 1}...")

        # Obtener los enlaces únicos de los inmuebles en la página actual
        try:
            inmuebles = driver.find_elements(By.XPATH, "//a[contains(@href, '/detalle/')]")
            enlaces_unicos = {inmueble.get_attribute("href") for inmueble in inmuebles}  # Usar un conjunto para eliminar duplicados
            
            for href in enlaces_unicos:
                print(f"Ingresando al inmueble: {href}")
                informacion_almacen['estacionamiento'] = []
                # Abrir el enlace del inmueble
                driver.execute_script("window.open(arguments[0]);", href)
                driver.switch_to.window(driver.window_handles[1])
                #time.sleep(3)

                # Extraer detalles del inmueble e imprimirlos en cada inmueble
                informacion_almacen = obtener_informacion(driver)

                id_inmueble = generar_id(prefijo, index)
                index = index + 1
                
                informacion_almacen['delegacion'][0] = alcaldias(informacion_almacen['delegacion'][0])#Obtenemos unicamente las alcaldias
                informacion_almacen['tipo'][0] = normalizar(informacion_almacen['tipo'][0])#minusculas y sin acentos         

                #Guardamos los datos de la página actual en nuestro diccionario de los datos completos
                informacion_completa['precios'].append(informacion_almacen['precios'])
                informacion_completa['delegacion'].append(informacion_almacen['delegacion'])
                informacion_completa['num_habitaciones'].append(informacion_almacen['num_habitaciones'])
                informacion_completa['num_duchas'].append(informacion_almacen['num_duchas'])
                informacion_completa['estacionamiento'].append(informacion_almacen['estacionamiento'])
                informacion_completa['tipo'].append(informacion_almacen['tipo'])
                informacion_completa['area_terreno'].append(informacion_almacen['area_terreno'])
                informacion_completa['area_construida'].append(informacion_almacen['area_construida'])
                informacion_completa['id'].append(id_inmueble)  

                #Imprimimos la info de la página actual, nomás pa ver
                print(f"\nID del inmueble: {id_inmueble}")
                print(f"Precios: {informacion_almacen['precios']}")
                print(f"Delegación: {informacion_almacen['delegacion']}")
                print(f"Número de habitaciones: {informacion_almacen['num_habitaciones']}")
                print(f"Número de duchas: {informacion_almacen['num_duchas']}")
                print(f"Estacionamiento: {informacion_almacen['estacionamiento']}")
                print(f"Tipo: {informacion_almacen['tipo']}")
                print(f"Área del terrreno: {informacion_almacen['area_terreno']}")
                print(f"Área construida: {informacion_almacen['area_construida']}\n")
 
                # Cerrar la pestaña actual y volver a la página principal
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                #time.sleep(2)

        except Exception as e:
            break

        # Ir a la siguiente página
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "pagination-next"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            #time.sleep(2)
            driver.execute_script("arguments[0].click();", next_button)
            #time.sleep(5)  # Esperar para que la página cargue
        except Exception as e:
            break

        time.sleep(30)

    print(f"Datos originales de precios: {informacion_completa['precios']}")


    #Aquí vamos a convertir los datos que nos interesan que sean númericos a númericos. 
    informacion_completa['precios'] = [
        convertir_precio(precio[0]) if isinstance(precio, list) and len(precio) > 0 else 0.0
        for precio in informacion_completa['precios']
    ]
    informacion_completa['num_habitaciones'] = [
        extraer_entero(habitaciones) for habitaciones in informacion_completa['num_habitaciones']]        
    informacion_completa['num_duchas'] = [
        extraer_entero(duchas) for duchas in informacion_completa['num_duchas']]        
    informacion_completa['area_terreno'] = [
        extraer_entero(area) for area in informacion_completa['area_terreno']]
    informacion_completa['area_construida'] = [
        extraer_entero(area) for area in informacion_completa['area_construida']]

    print(f"lista de datos de precios: {informacion_completa['precios']}")
    print(f"lista de datos de habitaciones: {informacion_completa['num_habitaciones']}")
    print(f"lista de datos de duchas: {informacion_completa['num_duchas']}")
    print(f"lista de datos de area del terreno: {informacion_completa['area_terreno']}")
    print(f"lista de datos de area construida: {informacion_completa['area_construida']}")

    claves_transformar = ["tipo","estacionamiento","delegacion"]
    informacion_completa=transformar_claves(informacion_completa,claves_transformar)
    informacion_transformada = {}

    for clave, valores in informacion_completa.items():
        # Convertir cada lista en un diccionario indexado
        informacion_transformada[clave] = {str(index): valor for index, valor in enumerate(valores)}





    # creamos el archivo .json para guardar los datos:
    with open("DatosLamudi.json","w", encoding="utf-8") as archivo_json:
        json.dump(informacion_transformada,archivo_json,ensure_ascii=False, indent = 4)
    
    

    driver.quit()




if __name__ == "__main__":
    main()