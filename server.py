from http.server import HTTPServer, BaseHTTPRequestHandler
from io import StringIO
import pandas as pd
import json

#   Este script implementa un servidor HTTP que recibe datos JSON a través de una solicitud POST,
#   procesa los datos utilizando pandas y guarda el resultado en un archivo CSV.

class JSONRequestHandler(BaseHTTPRequestHandler):
    #   Maneja las solicitudes OPTIONS para permitir CORS
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')  # Permitir cualquier origen
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    #   Maneja las solicitudes POST con datos JSON, los procesa con pandace y los guarda en un CSV
    def do_POST(self):
        try:
            # Lee y procesa los datos de la solicitud POST
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            # Procesa los datos con pandace
            df = pd.DataFrame(data)
             # Asegura que todas las columnas del libro estén presentes
            columnas_necesarias = [
                'id', 'title', 'author', 'isbn', 'genre', 'summary', 
                'authorId', 'picture'
            ]
            # Verifica si las columnas necesarias están presentes en el DataFrame
            # En caso de que falte alguna columna, la sustituye por "N/A"
            for columna in columnas_necesarias:
                if columna not in df.columns:
                    df[columna] = "N/A" 
            # Llama a la función limpiar_datos
            df = limpiar_datos(df)
           
            # Llama a la función crear_columnas_adicionales
            df = crear_columnas_adicionales(df)

            # Guarda el DataFrame en un archivo CSV
            csv_content = guardar_csv(df, "Books.csv")

            # Responde al cliente con un mensaje de exito y el CSV generado
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="books.csv"')
            self.send_header('Content-Length', str(len(csv_content)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(csv_content)

            # Lanza una excepcion en caso de que surga un error al procesar el JSON
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Error procesando JSON: {str(e)}".encode())

#   Limpia los datos del dataframe eliminando espacios en blanco y caracteres especiales
#   y convierte los valores nulos a "N/A", tambien selecciona small como la opción preferida del objeto picture
def limpiar_datos(df: pd.DataFrame):
    df = df.applymap(lambda x: x.strip().replace('\n', ' ').replace('\t', ' ') if isinstance(x, str) else x)
    df.fillna("N/A", inplace=True)
    df['picture'] = df['picture'].apply(
        lambda x: x.get('small') if isinstance(x, dict) and 'small' in x else str(x)
    )
    return df
#   Crea columnas adicionales en el dataframe, como longitud del título, autor en mayúsculas...
def crear_columnas_adicionales(df: pd.DataFrame):
    df['longitud_titulo'] = df['title'].apply(lambda x: len(x) if isinstance(x, str) else 0)
    df['autor_mayus'] = df['author'].apply(lambda x: x.upper() if isinstance(x, str) else "N/A")
    df['ISBN'] = df['isbn'].apply(lambda x: str(x).replace('-', '').replace(' ', '') if isinstance(x, str) else str(x))

    return df

#   Guarda el dataframe en un archivo CSV, codificado en utf-8-sig y separado por punto y coma
#   El contenido del CSV se devuelve como una cadena de bytes
#   para que pueda ser enviado como respuesta al cliente
def guardar_csv(df: pd.DataFrame, salida: str):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig',sep=';')
    return csv_buffer.getvalue().encode('utf-8-sig')

#   Inicia el servidor en el puerto 5000
#   Donde escucha las peticiones POST y OPTIONS 
if __name__ == "__main__":
    server = HTTPServer(('PORT', 5000), JSONRequestHandler)
    print("Servidor HTTP iniciado en http://localhost:5000")
    server.serve_forever()
