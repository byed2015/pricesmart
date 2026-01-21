"""
Catalog Service - Load and manage product catalog
"""
import csv
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CatalogProduct:
    """Representa un producto del catálogo."""
    id_articulo: str
    marca: str
    linea: str
    titulo: str
    ubicacion: str
    enlace: str
    costo: float
    
    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar en el selector."""
        return f"{self.marca} - {self.titulo} (${self.costo:.2f})"


class CatalogService:
    """Servicio para cargar y gestionar el catálogo de productos."""
    
    _instance = None
    _products = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializar el servicio de catálogo."""
        if self._products is None:
            self.load_catalog()
    
    @staticmethod
    def get_catalog_path() -> Path:
        """Obtener la ruta del archivo de catálogo."""
        # backend/data/productos_catalogo.csv
        backend_dir = Path(__file__).parent.parent.parent
        return backend_dir / "data" / "productos_catalogo.csv"
    
    def load_catalog(self) -> None:
        """Cargar el catálogo desde el archivo CSV."""
        catalog_path = self.get_catalog_path()
        
        if not catalog_path.exists():
            raise FileNotFoundError(f"Catálogo no encontrado en: {catalog_path}")
        
        self._products = []
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Limpiar el precio (remover $ y espacios)
                    costo_str = row.get('costo', '0').strip().replace('$', '').replace(',', '')
                    costo = float(costo_str)
                    
                    product = CatalogProduct(
                        id_articulo=row.get('Id_Articulo', '').strip(),
                        marca=row.get('Marca', '').strip(),
                        linea=row.get('Linea', '').strip(),
                        titulo=row.get('Titulo', '').strip(),
                        ubicacion=row.get('Ubicacion', '').strip(),
                        enlace=row.get('enlace', '').strip(),
                        costo=costo
                    )
                    
                    # Solo agregar si tiene URL y título
                    if product.enlace and product.titulo:
                        self._products.append(product)
                except (ValueError, KeyError) as e:
                    print(f"Error procesando fila: {e}")
                    continue
    
    def get_all_products(self) -> List[CatalogProduct]:
        """Obtener todos los productos del catálogo."""
        return self._products or []
    
    def get_products_by_marca(self, marca: str) -> List[CatalogProduct]:
        """Filtrar productos por marca."""
        return [p for p in (self._products or []) if p.marca.lower() == marca.lower()]
    
    def get_products_by_linea(self, linea: str) -> List[CatalogProduct]:
        """Filtrar productos por línea."""
        return [p for p in (self._products or []) if p.linea.lower() == linea.lower()]
    
    def get_product_by_id(self, id_articulo: str) -> Optional[CatalogProduct]:
        """Obtener producto por ID."""
        for p in (self._products or []):
            if p.id_articulo == id_articulo:
                return p
        return None
    
    def search_products(self, query: str) -> List[CatalogProduct]:
        """Buscar productos por título o ID."""
        query_lower = query.lower()
        return [
            p for p in (self._products or [])
            if query_lower in p.titulo.lower() or query_lower in p.id_articulo.lower()
        ]
    
    def get_marcas(self) -> List[str]:
        """Obtener lista de marcas disponibles."""
        marcas = set()
        for p in (self._products or []):
            marcas.add(p.marca)
        return sorted(list(marcas))
    
    def get_lineas(self) -> List[str]:
        """Obtener lista de líneas disponibles."""
        lineas = set()
        for p in (self._products or []):
            lineas.add(p.linea)
        return sorted(list(lineas))
    
    def get_product_dict(self, product: CatalogProduct) -> Dict[str, Any]:
        """Convertir producto a diccionario."""
        return {
            "id_articulo": product.id_articulo,
            "marca": product.marca,
            "linea": product.linea,
            "titulo": product.titulo,
            "ubicacion": product.ubicacion,
            "enlace": product.enlace,
            "costo": product.costo
        }
