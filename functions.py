import yaml
import streamlit as st

def render_product_card(index, item, product, parts):

    col_card, col_delete = st.columns([10, 1])

    with col_card:
        options_html = ""
        for option_name, choice in item["selection"].items():
            opt_desc = parts[choice]["descripcion"]
            options_html += f"""
                <div style='margin-bottom:4px;'>
                    <span style='font-weight:500;'>{option_name}:</span>
                    <span>{choice} – {opt_desc}</span>
                </div>
            """

        card_html = f"""
        <div style="
            border: 1px solid #DDD;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
            background: #FAFAFA;
            font-family: sans-serif;
            color: #333;  /* FIXES COLOR INCONSISTENCIES */
        ">
            <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 6px;">
                {item['description']}
            </div>

            <div style="margin-bottom: 8px;">
                <strong>Tipología:</strong> {product['tipologia']}
            </div>

            <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                <div><strong>Ancho:</strong> {item['ancho']} mm</div>
                <div><strong>Alto:</strong> {item['alto']} mm</div>
                <div><strong>Cantidad:</strong> {item['cantidad']}</div>
            </div>

            <div style="margin-top: 10px;">
                <strong>Opciones seleccionadas:</strong>
                <div>{options_html}</div>
            </div>
        </div>
        """

        st.html(card_html)

    with col_delete:
        if st.button("❌", key=f"remove_{index}"):
            st.session_state.basket.pop(index)
            st.rerun()


def get_product_by_name(name: str, products: list):
    for p in products:
        if p["tipologia"] == name:
            return p
    return None

def load_parts(filepath: str):
    """Load parts.yaml into a dict with int codes as keys."""
    with open(filepath, "r", encoding="utf-8") as f:
        parts = yaml.safe_load(f)
    return {k: v for k, v in parts.items()}

def load_product(filepath: str):
    """Load a product YAML (keeps codes as ints)."""
    with open(filepath, "r", encoding="utf-8") as f:
        product = yaml.safe_load(f)

    for sel in product.get("selecciones", []):
        sel["opciones"] = [c for c in sel["opciones"]]

    for item in product.get("items_fijos", []):
        item["codigo"] = item["codigo"]

    return product

def get_available_decisions(product, user_selection):
    return {sel["nombre"]: sel["opciones"][:] for sel in product["selecciones"]}

def calcular_medida(medida, A: int, H: int) -> float:
    if isinstance(medida, int):
        return medida
    try:
        expr = medida.replace("A", str(A)).replace("H", str(H))
        return eval(expr)
    except:
        return None

def apply_rules(product, user_selection) -> dict:
    rules = product.get("rules", [])
    result = {}

    for rule in rules:
        condition = rule.get("condition", {}).get("selection", {})
        if all(str(user_selection.get(k)) == str(v) for k, v in condition.items()):
            for action in rule.get("actions", []):
                if action.get("type") == "update_measure":
                    result[action["target"]] = action["value"]

    return result


def build_bom_perfiles(user_selection, product, parts, ancho, alto):
    measures = {sel["nombre"]: sel.get("medida") for sel in product["selecciones"]}
    medidas_por_reglas = apply_rules(product, user_selection)
    bom = []

    # Fixed items
    for item in product.get("items_fijos", []):
        if parts[item["codigo"]]["tipo"] == "perfil":
            bom.append({
                "codigo": item["codigo"],
                "descripcion": parts[item["codigo"]]["descripcion"],
                "especificacion_medida": item["medida"],
                "medida_calculada": calcular_medida(item["medida"], ancho, alto),
                "cantidad": item["cantidad"],
            })

    # User selections
    for sel in product.get("selecciones", []):
        if sel["nombre"] in user_selection:
            codigo = int(user_selection[sel["nombre"]])
            if parts[codigo]["tipo"] == "perfil":
                especificacion_medida = measures.get(sel["nombre"], sel.get("medida"))
                if especificacion_medida is None:
                    especificacion_medida = medidas_por_reglas[sel["nombre"]]
                bom.append({
                    "codigo": codigo,
                    "descripcion": parts[codigo]["descripcion"],
                    "especificacion_medida": especificacion_medida,
                    "medida_calculada": calcular_medida(especificacion_medida, ancho, alto),
                    "cantidad": sel["cantidad"],
                })

    return bom


def build_bom_accesorios(user_selection, product, parts):
    bom = []

    # Fixed items
    for item in product.get("items_fijos", []):
        if parts[item["codigo"]]["tipo"] == "accesorio":
            bom.append({
                "codigo": item["codigo"],
                "descripcion": parts[item["codigo"]]["descripcion"],
                "precio unidad": parts[item["codigo"]]["precio"],
                "cantidad": item["cantidad"],
                "precio total": parts[item["codigo"]]["precio"] * item["cantidad"]
            })
            
    # User selections
    for sel in product.get("selecciones", []):
        if sel["nombre"] in user_selection:
            codigo = int(user_selection[sel["nombre"]])
            if parts[codigo]["tipo"] == "accesorio":
                bom.append({
                    "codigo": codigo,
                    "descripcion": parts[codigo]["descripcion"],
                    "precio unidad": parts[codigo]["precio"],
                    "cantidad": sel["cantidad"],
                    "precio total": parts[codigo]["precio"]*sel["cantidad"]
                })
    return bom

