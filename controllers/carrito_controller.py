import random
from controllers.mongo_hlp import MongoHelper
from controllers.cassandra_hlp import CassandraHelper
from controllers.redis_hlp import RedisHelper
from all_classes.clases import Producto
from controllers.catalogo_productos_controller import catalogo_productos

class carrito_controller:
    def __init__(self):
        self.mongo_helper = MongoHelper()
        self.mongo_helper.conectar()
        self.mongo_helper.usar_db('bdd2')
        self.collection = "carrito"
        self.cassandra_helper = CassandraHelper()
        self.redis_helper = RedisHelper()
        # hace falta agregar un atributo "estado" para el carrito

    def inicializar_carrito(self):
        self.borrarCarrito()

    def existeCarrito(self):
        return self.mongo_helper.exists_documents(self.collection) is not None

    def existeProductoEnCarrito(self,prod):
        return self.mongo_helper.get_document_by_id(self.collection,prod.id)

    def getDocProducto(self,id):
        return self.mongo_helper.get_document_by_id(self.collection,id)

    def getProductofromDoc(self,id): # este controlador debería estar en productos controller
        documento = self.getDocProducto(id)
        producto = Producto(documento['id'], documento['nombre'], documento['precio'], 0, documento['categoria'],
        documento['descripcion'])
        return producto

    def agregarProducto(self,producto):
        try: # se agrega el producto al carrito
            if not self.existeCarrito():
                self.inicializar_carrito()
            if (not self.existeCarrito() or (self.existeCarrito() and self.existeProductoEnCarrito(producto) is None)):
                self.guardar_estado_carrito()
                # se agrega el producto
                query = {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'precio': producto.precio,
                    'cantidad': producto.cantidad,
                    'categoria': producto.categoria,
                    'descripcion': producto.descripcion
                }
                self.mongo_helper.insert_document('carrito',query)
                print("Agregado al carrito!")
            else: # se actualiza la cantidad del producto
                try:
                    self.guardar_estado_carrito()
                    print("ATENCION: El producto existe y se fijará una nueva Cantidad.")
                    print("Continuar? (s/n)")
                    optCantidad = input()
                    if optCantidad == 's':
                        # Realizar la actualización
                        # doc = self.mongo_helper.get_document_by_id(self.collection,producto.id)
                        # cantidadActual = doc['cantidad']
                        query = (
                            {'$set': {'cantidad':producto.cantidad}}
                        )
                        self.mongo_helper.update_document(self.collection,producto.id,query)
                        print('Actualización Exitosa.')
                    else:
                        pass
                except Exception as e:
                    print('Error al actualizar la cantidad:', e)
        except Exception as e:
            print("se ha producido un error a la hora de cargar el producto al carrito:", e)

    def agregarProductos(self,productos):
        for producto in productos:
            query = {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'cantidad': producto.cantidad,
                'categoria': producto.categoria,
                'descripcion': producto.descripcion
            }
            self.mongo_helper.insert_document('carrito', query)

    def eliminar_producto_por_posicion(self, posicion):
        self.guardar_estado_carrito()
        carrito = self.mongo_helper.get_collection(self.collection)
        productos = list(carrito.find())  # Convertir el cursor en una lista de productos

        if posicion >= 0 and posicion < len(productos)+1:
            producto_eliminar = productos[posicion - 1]
            id_producto = producto_eliminar['id']

            self.mongo_helper.delete_document(self.collection,id_producto)
            print("Producto eliminado del carrito.")
        else:
            print("Posición inválida.")

    def getItems(self):
        carrito = self.mongo_helper.get_documents(self.collection)
        return carrito

    def getCarrito(self):
        return self.mongo_helper.get_documents(self.collection)

    def borrarCarrito(self):
        self.mongo_helper.delete_collection_docs(self.collection)

    def mostrarCarrito(self):
        print("+" + " Carrito ".center(65, "-") + "+")
        print("| " + "ID PRODUCTO | DESCRIPCIÓN          | CANTIDAD | PRECIO UNITARIO" + " |")  # header
        i = 0
        carrito = self.getCarrito()
        for producto in carrito:
            i += 1
            id = producto['id']
            nombre = producto['nombre']
            cantidad = producto['cantidad']
            precio = producto['precio']
            print("| " + f"{i}.ID:{id: <6} | {nombre: <20} | " + f"(x{cantidad})".ljust(8) + " | " + f"${precio} c/u".rjust(15) + " |")
        print("+" + "-" * 65 + "+")

    def calcular_impuestos(self, total_items):
        impuestos = total_items * 0.21  # 21% de impuestos IVA
        return impuestos

    def calcular_descuento(self, cliente, total_items):
        tiempo_promedio = cliente['tiempo_promedio']
        if tiempo_promedio > 240:
            porcentaje_descuento = 40
            tipo_descuento = "Usuario TOP"
        elif tiempo_promedio > 120:
            porcentaje_descuento = 20
            tipo_descuento = "Usuario MEDIUM"
        else:
            porcentaje_descuento = 10
            tipo_descuento = "Usuario LOW"

        importe_descuento = porcentaje_descuento * 0.01 * total_items
        return tipo_descuento, porcentaje_descuento, importe_descuento

    def total_items(self,carrito):
        total_carrito= 0
        for i in carrito:
            total_carrito += (i['cantidad'] * i['precio'])
        return total_carrito

    def calcular_importe_total(self, carrito, impuestos, importe_descuento):
        total_carrito = 0
        for i in carrito:
            total_carrito += (i['cantidad'] * i['precio'])
        total_carrito = total_carrito + impuestos - importe_descuento
        return total_carrito

    def insertar_datos_cassandra(self, items_carrito, cliente, opcion, pago):
        self.cassandra_helper.conectar()  # Conexión a Cassandra
        self.cassandra_helper.usar_db('bdd')  # Utilizar el keyspace 'BDD'

        print("Procesando compra...")
        # Creo un índice por Nombre de Cliente
        self.cassandra_helper.execute_query("CREATE INDEX IF NOT EXISTS indice_nombre ON clientes (nombre);")

        # Busco el ID del cliente en la tabla Clientes
        id_cliente = self.cassandra_helper.execute_query(
            "SELECT id FROM clientes where nombre='" + cliente['name'] + "';")

        # Si el cliente no existe, se inserta en la tabla
        if id_cliente is None:
            # Insertar los datos del cliente en la tabla (id, nombre, direccion, documento)
            columns_usr = ["id", "nombre", "direccion", "documento"]
            values_usr = [f"now()", f"'{cliente['name']}'", f"'{cliente['address']}'", f"'{cliente['dni']}'"]
            self.cassandra_helper.insert_document("clientes", columns_usr, values_usr)

            # Una vez insertado, busco el id del cliente nuevamente
            # el string directo de id_cliente será: id_cliente.was_applied.urn[9:]
            id_cliente = self.cassandra_helper.execute_query("SELECT id FROM clientes where nombre='" + cliente['name'] + "';")
            print("Cliente Ok.")

        # Crear un número de factura aleatorio
        nro_factura_random = random.randint(1000000, 9999999)

        # Creo un índice para nro_factura en la tabla facturaciones
        self.cassandra_helper.execute_query("CREATE INDEX IF NOT EXISTS indice_nro_factura ON facturaciones (nro_factura);")

        # Busco el numero de factura en la tabla facturaciones
        valorBuscado = self.cassandra_helper.execute_query("SELECT nro_factura FROM facturaciones where nro_factura=" + str(nro_factura_random) + ";")
        if len(valorBuscado.current_rows) > 0:  # Si el número de factura ya existe, genero otro
            nro_factura_random = random.randint(1000000, 9999999)

        # Insertar los datos del producto en la tabla
        for producto in items_carrito:
            columns = ["id", "nro_factura", "cliente_id", "cliente_nombre", "cliente_direccion", "cliente_documento",
                       "producto_nombre", "cantidad", "precio_unitario", "tipo_pago", "importe_total",
                       "fecha_compra"]
            values = [f"now()", f"{nro_factura_random}", f"{id_cliente.was_applied.urn[9:]}", f"'{cliente['name']}'", f"'{cliente['address']}'", f"'{cliente['dni']}'",
                      f"'{producto['nombre']}'", str(producto['cantidad']), str(producto['precio']),
                      f"'{opcion}'", f"{pago}", f"toTimestamp(now())"]
            self.cassandra_helper.insert_document("facturaciones", columns, values)
        print("Compra registrada Ok.")

        # Vaciar carrito
        self.borrarCarrito()
        # Cerrar la conexión a Cassandra
        self.cassandra_helper.close_connection()  # Cerrar la conexión a Cassandra

    def guardar_estado_carrito(self):
        self.redis_helper.connect()
        self.mongo_helper.get_documents(self.collection)
        carrito = self.getCarrito()
        index = 0
        for item in carrito:
            id = item['id']
            cantidad = item['cantidad']
            self.redis_helper.set_value(f'carrito:{index}:id',id)
            self.redis_helper.set_value(f'carrito:{index}:cantidad',cantidad)
            index += 1
        self.redis_helper.set_value('index',index)
        self.redis_helper.set_value('estado_anterior',1) # esta variable se usa para saber si es posible revertir el estado del carrito al anterior o si ya se revirtió.
        self.redis_helper.close_connection()

    def obtener_estado_anterior_carrito(self):
        if self.redis_helper.get_value('estado_anterior') == '0': #se pregunta si se puede volver al estado anterior
            print("El carrito ya se encuentra en el estado anterior")
        else:
            index = int(self.redis_helper.get_value('index'))
            self.borrarCarrito()
            catalogo = catalogo_productos()
            productos = []
            for i in range(index):
                productoID = int(self.redis_helper.get_value(f'carrito:{i}:id'))
                cantidadProducto = int(self.redis_helper.get_value(f'carrito:{i}:cantidad'))
                producto = catalogo.get_producto_por_id(productoID)
                producto.cantidad = cantidadProducto
                productos.append(producto)
            self.agregarProductos(productos)
            self.redis_helper.set_value('estado_anterior', 0)
            print("Se ha vuelto al estado anterior del carrito")
