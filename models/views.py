from controllers.usuario_controller import *
from controllers.catalogo_productos_controller import catalogo_productos
from controllers.carrito_controller import carrito_controller


class Views:

    def display_login_screen(self):
        print("=== Login ===")
        username = input("Username: ")
        password = input("Password: ")
        login_hlp = usuario_controller()
        return login_hlp.login(username, password)

    def display_registration_screen(self):
        print("=== Registro ===")
        username = input("Username: ")
        password = input("Password: ")
        dni = input("DNI: ")
        address = input("Address: ")
        # self.controller.register(username, password, dni, address)

    def display_main_view(self):
        print("\n1. Buscar Producto"
              "\n2. Gestionar Carrito"
              "\n3. Cerrar Sesión")
        try:
            opcion = int(input("opcion: "))
        except ValueError:
            return
        return opcion

    def display_catalogo_productos_view(self):
        print("-- Buscar producto --")
        producto = input("Ingrese el producto que desea buscar: ")
        catalogo = catalogo_productos()
        resultados = catalogo.buscar(producto) # resultados tiene la lista de productos
        if resultados is not None:
            catalogo.mostrar_catalogo(resultados) # se muestran los resultados
            seleccion = int(input("Seleccione el número de producto para ver los detalles: "))
            try:
                producto_seleccionado = catalogo.seleccionar_producto(seleccion, catalogo.buscar(
                    producto))  # devuelve el producto (obj) si no existe, None
                if producto_seleccionado is not None:
                    print(producto_seleccionado)
                    print("\n1. Agregar al carrito")
                    print("2. Volver al menú principal")
                    seleccion = int(input("Seleccionar: "))
                    if seleccion == 1:
                        carrito = self.modificar_cantidad_carrito_view(producto_seleccionado)
                    elif seleccion == 2:
                        return
                    else:
                        print("Opción inválida.")
                else:
                    print("Selección inválida")
            except ValueError:
                print("Selección no válida")
            except IndexError:
                print("Opcion inválida")
            return carrito
        else:
            print("No se encontraron resultados.")

    def modificar_cantidad_carrito_view(self,producto):
        cantidad = int(input("\nSeleccione la cantidad: "))
        producto.cantidad = cantidad
        carrito = carrito_controller()
        carrito.agregarProducto(producto)  # se agrega el producto
        return carrito

    def display_gestionar_carrito_view(self,carrito):
        if carrito is not None:
            print("\n1. Listar carrito"
                  "\n2. Agregar Producto al carrito"
                  "\n3. Eliminar Producto del carrito"
                  "\n4. Modificar cantidad de un producto"
                  "\n5. Confirmar carrito"
                  "\n6. Revertir estado del carrito"
                  "\n7. Salir")
            opcion = int(input("opcion: "))
            if opcion == 1:
                carrito.mostrarCarrito()
            elif opcion == 2:
                self.display_catalogo_productos_view()
            elif opcion == 3:
                carrito.mostrarCarrito()
                eleccion = int(input("Elija el elemento que desea eliminar:"))
                carrito.eliminar_producto_por_posicion(eleccion)
            elif opcion == 4:
                carrito.mostrarCarrito()
                id = int(input("Elija el ID del elemento que desea modificar su cantidad:"))
                producto = carrito.getProductofromDoc(id)
                if producto is not None:
                    self.modificar_cantidad_carrito_view(producto)
            elif opcion == 5:
                usuario = usuario_controller().getUser()
                self.display_confirmar_carrito_view(carrito, usuario)
            elif opcion == 6:
                eleccion = input("Esta seguro que desea volver el carrito al estado anterior? s/n: ")
                if eleccion == 's':
                    carrito.obtener_estado_anterior_carrito()
                elif eleccion == 'n':
                    pass
                else:
                    print("Opcion invalida")
            elif opcion == 7:
                return
        else:
            print("No existe un carrito activo")

    def display_confirmar_carrito_view(self, carrito, cliente):
        print("-- Confirmación de Carrito --")
        carrito.mostrarCarrito()  # se muestran los productos del carrito
        items_carrito = carrito.getItems()  # se obtienen los items del carrito
        total_precio_items = carrito.total_items(items_carrito)
        impuestos = carrito.calcular_impuestos(total_precio_items)
        print("| " + f"Impuestos IVA 21% ".rjust(46) + "|" + f"  {impuestos}".rjust(16) + " |")
        tipo_descuento, descuento_porcentaje, importe_descuento = carrito.calcular_descuento(cliente, total_precio_items)
        print("| " + f"Descuentos: {tipo_descuento} ({descuento_porcentaje}%) ".rjust(46) + "|" + f"  -{importe_descuento}".rjust(16) + " |")

        pago_total = str(total_precio_items + impuestos - importe_descuento)
        print("| " + f"IMPORTE TOTAL ".rjust(46) + "|" + f"  ${total_precio_items + impuestos - importe_descuento}".rjust(16) + " |")

        print("+" + "--- Datos del Cliente ".ljust(65, "-") + "+")
        print("| " + f"Nombre y Apellido: {cliente['name']}".ljust(64) + "|")
        print("| " + f"Dirección: {cliente['address']}".ljust(64) + "|")
        print("| " + f"DNI: {cliente['dni']}".ljust(64) + "|")
        print("+" + "-" * 65 + "+")

        print("\n1. Confirmar")
        print("2. Volver")

        opcion = int(input("Seleccionar: "))
        if opcion == 1:
            self.procesar_confirmacion_carrito(carrito, items_carrito, cliente, pago_total)
        elif opcion == 2:
            return
        else:
            print("Opción inválida.")

    def procesar_confirmacion_carrito(self, carrito, items_carrito, cliente, pago_total):
        print("\nElija un Tipo de Pago para Finalizar la compra:\n"
              "1. Efectivo.\n"
              "2. Tarjeta de Crédito.\n"
              "3. Cuenta Corriente.\n"
              "0. Volver.\n")
        opcion = int(input("Seleccionar tipo de pago: "))
        if opcion == 1 or opcion == 2 or opcion == 3:
            carrito.insertar_datos_cassandra(items_carrito, cliente, opcion, pago_total)
        elif opcion == 0:
            return
        else:
            print("Opción inválida.")
