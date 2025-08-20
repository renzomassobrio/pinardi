import yaml

def load_parts(filepath: str):
    """Load parts.yaml into a dict with int codes as keys."""
    with open(filepath, "r", encoding="utf-8") as f:
        parts = yaml.safe_load(f)
    # Ensure integer keys
    return {int(k): v for k, v in parts.items()}

def load_product(filepath: str):
    """Load a product YAML (keeps codes as ints in opciones/items_fijos)."""
    with open(filepath, "r", encoding="utf-8") as f:
        product = yaml.safe_load(f)

    # Normalize opciones to integers
    for sel in product.get("selecciones", []):
        sel["opciones"] = [int(c) for c in sel["opciones"]]

    # Normalize items_fijos codes
    for item in product.get("items_fijos", []):
        item["codigo"] = int(item["codigo"])

    return product

# --- Your existing functions from before ---
def apply_rules(selection, measures, rules, selections):
    for rule in rules:
        try:
            if eval(rule["condicion"], {}, {"selection": selection, "measures": measures}):
                exec(rule["accion"], {}, {"selection": selection, "measures": measures})
        except Exception as e:
            print("Rule error:", e, rule)

def get_available_decisions(product, user_selection):
    decisions = {sel["nombre"]: sel["opciones"][:] for sel in product["selecciones"]}
    measures = {sel["nombre"]: sel.get("medida") for sel in product["selecciones"]}
    apply_rules(user_selection, measures, product.get("reglas", []), product["selecciones"])
    for nombre, codigo in user_selection.items():
        if nombre in decisions and int(codigo) in decisions[nombre]:
            decisions[nombre] = [int(codigo)]
    return decisions

def calcular_medida(medida: str, A: int, H: int) -> float:
    try:
        # Replace A and H with their values
        expr = medida.replace("A", str(A)).replace("H", str(H))
        # Evaluate the resulting math expression
        return eval(expr)
    except:
        return None


def build_bom(user_selection, product, parts, ancho, alto):
    measures = {sel["nombre"]: sel.get("medida") for sel in product["selecciones"]}
    apply_rules(user_selection, measures, product.get("reglas", []), product["selecciones"])

    bom = []

    # Fixed items
    for item in product.get("items_fijos", []):
        bom.append({
            "codigo": item["codigo"],
            "descripcion": parts[item["codigo"]]["descripcion"],
            "especificacion_medida": item["medida"],
            "medida_calculada":calcular_medida(item["medida"], ancho, alto), 
            #"precio": parts[item["codigo"]]["precio"],
            "cantidad": item["cantidad"],
        })

    # User selections
    for sel in product.get("selecciones", []):
        if sel["nombre"] in user_selection:
            codigo = int(user_selection[sel["nombre"]])
            bom.append({
                "codigo": codigo,
                "descripcion": parts[codigo]["descripcion"],
                "especificacion_medida": measures.get(sel["nombre"], sel.get("medida")),
                "medida_calculada":calcular_medida(item["medida"], ancho, alto),
                #"precio": parts[codigo]["precio"],
                "cantidad": sel["cantidad"],
            })

    #total = sum(item["precio"] * item["cantidad"] for item in bom)
    return bom

