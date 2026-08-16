"""Pruebas unitarias de los Objetos de Valor del dominio."""

from decimal import Decimal

import pytest

from sgrf.dominio.excepciones import UnidadesIncompatibles, ValorInvalido
from sgrf.dominio.objetos_valor import Cantidad, Rendimiento, TipoEscalado, Unidad


class TestCantidad:
    """Cantidad: valor no negativo con Unidad, inmutable."""

    def test_acepta_enteros_flotantes_y_decimales(self):
        assert Cantidad(500, Unidad.GRAMO).valor == Decimal("500")
        assert Cantidad(1.5, Unidad.LITRO).valor == Decimal("1.5")
        assert Cantidad(Decimal("2.25"), Unidad.TAZA).valor == Decimal("2.25")

    def test_rechaza_valores_negativos(self):
        with pytest.raises(ValorInvalido):
            Cantidad(-1, Unidad.GRAMO)

    def test_es_inmutable(self):
        cantidad = Cantidad(100, Unidad.GRAMO)
        with pytest.raises(Exception):
            cantidad.valor = Decimal("200")

    def test_escalar_devuelve_nueva_instancia_sin_alterar_la_original(self):
        original = Cantidad(200, Unidad.GRAMO)
        escalada = original.escalar(Decimal("2"))
        assert escalada.valor == Decimal("400")
        assert original.valor == Decimal("200")
        assert escalada is not original

    def test_escalar_por_factor_fraccionario(self):
        assert Cantidad(300, Unidad.GRAMO).escalar(Decimal("0.5")).valor == Decimal("150")

    def test_sumar_cantidades_de_la_misma_unidad(self):
        total = Cantidad(100, Unidad.GRAMO).sumar(Cantidad(250, Unidad.GRAMO))
        assert total.valor == Decimal("350")

    def test_sumar_unidades_distintas_falla(self):
        with pytest.raises(UnidadesIncompatibles):
            Cantidad(100, Unidad.GRAMO).sumar(Cantidad(100, Unidad.MILILITRO))

    def test_igualdad_por_valor(self):
        assert Cantidad(100, Unidad.GRAMO) == Cantidad(100, Unidad.GRAMO)
        assert Cantidad(100, Unidad.GRAMO) != Cantidad(100, Unidad.MILILITRO)

    def test_evita_errores_de_coma_flotante(self):
        """0.1 + 0.2 debe dar exactamente 0.3, no 0.30000000000000004."""
        total = Cantidad(0.1, Unidad.LITRO).sumar(Cantidad(0.2, Unidad.LITRO))
        assert total.valor == Decimal("0.3")

    def test_nunca_usa_notacion_cientifica(self):
        """Quien cocina debe leer '1000 g', jamas '1E+3 g'."""
        assert str(Cantidad(500, Unidad.GRAMO).escalar(Decimal("2"))) == "1000 g"
        assert str(Cantidad(1000, Unidad.GRAMO).escalar(Decimal("10"))) == "10000 g"

    def test_conserva_los_decimales_significativos(self):
        assert str(Cantidad(2.5, Unidad.CUCHARADA)) == "2.5 cda"
        assert str(Cantidad("0.25", Unidad.TAZA)) == "0.25 taza"


class TestRendimiento:
    """Rendimiento: cantidad producida, base del escalado."""

    def test_rechaza_valores_no_positivos(self):
        with pytest.raises(ValorInvalido):
            Rendimiento(0)
        with pytest.raises(ValorInvalido):
            Rendimiento(-4)

    def test_rechaza_descripcion_vacia(self):
        with pytest.raises(ValorInvalido):
            Rendimiento(4, "   ")

    def test_factor_hacia_duplicar(self):
        base = Rendimiento(4, "porciones")
        assert base.factor_hacia(Rendimiento(8, "porciones")) == Decimal("2")

    def test_factor_hacia_reducir(self):
        base = Rendimiento(8, "porciones")
        assert base.factor_hacia(Rendimiento(2, "porciones")) == Decimal("0.25")

    def test_factor_hacia_mismo_rendimiento_es_uno(self):
        base = Rendimiento(6, "porciones")
        assert base.factor_hacia(Rendimiento(6, "porciones")) == Decimal("1")

    def test_no_compara_rendimientos_de_distinta_naturaleza(self):
        with pytest.raises(ValorInvalido):
            Rendimiento(4, "porciones").factor_hacia(Rendimiento(2, "tortas"))

    def test_no_muestra_ceros_sobrantes_al_volver_de_la_base(self):
        """PostgreSQL devuelve siempre la precision completa de la columna:
        un rendimiento guardado como 50 vuelve como Decimal('50.000'). En
        formato argentino el punto es separador de miles, asi que mostrar
        ese texto tal cual haria leer "50.000" como cincuenta mil.
        """
        recuperado = Rendimiento(Decimal("50.000"), "porciones")
        assert str(recuperado.valor) == "50"

    def test_nunca_usa_notacion_cientifica(self):
        grande = Rendimiento(Decimal("1000.000"), "porciones")
        assert str(grande.valor) == "1000"

    def test_conserva_decimales_reales(self):
        con_decimales = Rendimiento(Decimal("4.5"), "kg")
        assert str(con_decimales.valor) == "4.5"


class TestTipoEscalado:
    """TipoEscalado: comportamiento de cada ingrediente al escalar."""

    def test_lineal_y_fijo_requieren_cantidad(self):
        assert TipoEscalado.LINEAL.requiere_cantidad
        assert TipoEscalado.FIJO.requiere_cantidad

    def test_a_gusto_y_cantidad_necesaria_no_admiten_cantidad(self):
        assert not TipoEscalado.A_GUSTO.admite_cantidad
        assert not TipoEscalado.CANTIDAD_NECESARIA.admite_cantidad

    def test_solo_el_lineal_se_multiplica(self):
        assert TipoEscalado.LINEAL.se_multiplica
        assert not TipoEscalado.FIJO.se_multiplica
        assert not TipoEscalado.A_GUSTO.se_multiplica


class TestUnidad:
    """Unidad: simbolo y sistema de medida."""

    def test_recupera_unidad_desde_su_simbolo(self):
        assert Unidad.desde_simbolo("g") is Unidad.GRAMO

    def test_simbolo_desconocido_falla(self):
        with pytest.raises(ValueError):
            Unidad.desde_simbolo("galones")
