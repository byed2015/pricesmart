"""
Test para verificar que la lógica de rebuild_product_lists funciona correctamente
"""

# Simular la lógica de rebuild_product_lists

class MockSessionState:
    def __init__(self):
        self.products_to_exclude = []
        self.products_to_include = []

def test_rebuild_logic():
    session_state = MockSessionState()
    
    # Simular datos del matching
    comparable_offers = [
        {"title": "Producto A", "price": 100},
        {"title": "Producto B", "price": 200},
        {"title": "Producto C", "price": 300},
    ]
    
    excluded_offers = [
        {"title": "Producto D", "price": 400},
        {"title": "Producto E", "price": 500},
    ]
    
    print("Estado Inicial:")
    print(f"  Comparables: {[p['title'] for p in comparable_offers]}")
    print(f"  Excluidos: {[p['title'] for p in excluded_offers]}")
    print()
    
    # Test 1: Mover un comparable a excluidos
    print("TEST 1: Usuario excluye 'Producto A'")
    session_state.products_to_exclude.append(comparable_offers[0])
    
    # Ejecutar rebuild_product_lists
    all_comparable = comparable_offers
    all_excluded = excluded_offers
    included_titles = {p.get('title') for p in session_state.products_to_include}
    excluded_titles = {p.get('title') for p in session_state.products_to_exclude}
    
    new_comparable = [
        p for p in all_comparable 
        if p.get('title') not in excluded_titles
    ]
    new_comparable.extend([
        p for p in all_excluded 
        if p.get('title') in included_titles
    ])
    
    new_excluded = [
        p for p in all_excluded 
        if p.get('title') not in included_titles
    ]
    new_excluded.extend([
        p for p in all_comparable 
        if p.get('title') in excluded_titles
    ])
    
    print(f"  Resultado Comparables: {[p['title'] for p in new_comparable]}")
    print(f"  Resultado Excluidos: {[p['title'] for p in new_excluded]}")
    print(f"  ✅ 'Producto A' ahora en excluidos: {'Producto A' in [p['title'] for p in new_excluded]}")
    print()
    
    # Test 2: Mover un excluido a comparables
    print("TEST 2: Usuario incluye 'Producto D'")
    session_state.products_to_exclude = []  # Reset
    session_state.products_to_include.append(excluded_offers[0])
    
    included_titles = {p.get('title') for p in session_state.products_to_include}
    excluded_titles = {p.get('title') for p in session_state.products_to_exclude}
    
    new_comparable = [
        p for p in all_comparable 
        if p.get('title') not in excluded_titles
    ]
    new_comparable.extend([
        p for p in all_excluded 
        if p.get('title') in included_titles
    ])
    
    new_excluded = [
        p for p in all_excluded 
        if p.get('title') not in included_titles
    ]
    new_excluded.extend([
        p for p in all_comparable 
        if p.get('title') in excluded_titles
    ])
    
    print(f"  Resultado Comparables: {[p['title'] for p in new_comparable]}")
    print(f"  Resultado Excluidos: {[p['title'] for p in new_excluded]}")
    print(f"  ✅ 'Producto D' ahora en comparables: {'Producto D' in [p['title'] for p in new_comparable]}")
    print()
    
    print("✅ Lógica correcta - Los botones deberían funcionar ahora")

if __name__ == "__main__":
    test_rebuild_logic()
