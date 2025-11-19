import streamlit as st
import pandas as pd
from pathlib import Path
from functions import load_parts, load_product, get_available_decisions, build_bom_perfiles, build_bom_accesorios, get_product_by_name, render_product_card
from cutting_stock import cutting_stock_with_kerf
from pdf import generate_pdf
import json
from io import StringIO

# --- Load parts ---
parts = load_parts("parts.yaml")

# --- Load all product YAMLs ---
product_files = list(Path(".").glob("product_*.yaml"))
if not product_files:
    st.error("No se encontró ningún archivo YAML que defina un producto!")
    st.stop()

products = [load_product(pf) for pf in product_files]
product_names = [p["tipologia"] for p in products]

# --- Initialize session state ---
if "basket" not in st.session_state:
    st.session_state.basket = []

if "selection" not in st.session_state:
    st.session_state.selection = {}

st.title("PROYECTO PINARDI - Cotizaciones")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🛒 Ingresar productos", "📋 Combinar productos", "📏 Perfiles", "🔩 Accesorios", "🪟 Vidrios", "💰 Presupuestar"])

# ======================================================================
# TAB 1 — CARRITO
# ======================================================================
with tab1:

    #### SIDEBAR
    st.sidebar.write("## Importar/Exportar")

    # Download button
    cart_json = json.dumps(st.session_state.basket, ensure_ascii=False, indent=4)
    st.sidebar.download_button(
    label="💾 Descargar productos",
    data=cart_json,
    file_name="basket.json",
    mime="application/json"
    )
    
    #Upload button
    uploaded_cart = st.sidebar.file_uploader("📂 Cargar productos", type=["json"], key="cart_upload")
    
    if uploaded_cart is not None and not st.session_state.get("cart_processed"):
        data = json.load(uploaded_cart)
        st.session_state.basket = data
        st.session_state.cart_processed = True
        st.sidebar.success("Productos cargados desde archivo")
        st.rerun()

    if uploaded_cart is None and st.session_state.get("cart_processed"):
        st.session_state.cart_processed = False

    st.sidebar.divider()
    
    st.sidebar.write("## Opciones generales")
    kerf = st.sidebar.number_input("🪚 Ancho de la hoja de corte (mm)", value=5, step=1, min_value=0, format="%d")
    descarte_punta=st.sidebar.number_input("🪚 Descarte de punta (mm, por lado)", value=50, step=1, min_value=0, format="%d")

    st.subheader("Agregar producto")
    
    description = st.text_input("Ingresar un nombre para el producto", placeholder="p.ej. ventana dormitorio")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ancho = st.number_input(
            "Ancho (mm)",
            value=0,
            step=1,
            min_value=0,
            format="%d"
        )
    with col2:
        alto = st.number_input(
            "Alto (mm)",
            value=0,
            step=1,
            min_value=0,
            format="%d"
        )
    with col3:
        cantidad = st.number_input(
            "Cantidad",
            value=1,
            step=1,
            min_value=1,
            format="%d"
        )

    
    # Product selection
    selected_index = st.selectbox("Seleccionar tipologia", range(len(products)),
                                  format_func=lambda i: product_names[i])
    product = products[selected_index]

    st.text("⚙️ Configuración de opciones")
    available = get_available_decisions(product, st.session_state.selection)

    # Dynamic dropdowns
    for nombre, opciones in available.items():
        options_labels = {
            str(opt): f"{opt} - {parts[opt]['descripcion']}" 
            for opt in opciones
        }

        chosen = st.selectbox(
            f"{nombre}",
            options=[""] + list(options_labels.keys()),
            format_func=lambda x: options_labels.get(x, "") if x else "Seleccionar...",
            key=f"select_{nombre}",
            index=0
        )

        if chosen != "":
            st.session_state.selection[nombre] = int(chosen)
        else:
            st.session_state.selection.pop(nombre, None)

    # Add to basket
    if st.button("🛒➕ Agregar al pedido"):
        if not description:
            st.warning("⚠️ Debe ingresar un nombre para el producto.")
        elif any(d["description"] == description for d in st.session_state.basket):
            st.warning("⚠️ El nombre del producto ya está en uso.")
        else:
            st.session_state.basket.append({
                "description": description,
                "ancho": ancho,
                "alto": alto,
                "cantidad": cantidad,
                "product_name": product["tipologia"],
                "selection": st.session_state.selection.copy()
            })
            st.session_state.selection = {}
            st.success("✅ Producto agregado al pedido!")

    st.divider()
    # Show basket
    if st.session_state.basket:
        st.subheader("Productos agregados")
        for i, p in enumerate(st.session_state.basket):
            product = get_product_by_name(p["product_name"], products)
            render_product_card(i, p, product, parts)

  
# ======================================================================
# TAB 2 — SELECCION DE PRODUCTOS
# ======================================================================
with tab2:      

    if not st.session_state.basket:
        st.info("No hay productos en el pedido aún.")
        st.stop()

    st.text("Seleccione uno o más productos del pedido")
    
    selected_indices = []
    for i, item in enumerate(st.session_state.basket):
        if st.checkbox(item["description"] + f" (x{item['cantidad']})", key=f"basket_item_{i}"):
            selected_indices.append(i)
    st.divider()
    
    if not selected_indices:
        st.info("Seleccione al menos un producto para continuar.")
        st.stop()


with tab3:
    # -------------------------------------------------------------
    # PERFILES
    # -------------------------------------------------------------
    with st.expander("Lista de perfiles"):

        all_boms_perfiles = []
        for idx in selected_indices:
            selected_item = st.session_state.basket[idx]

            # Recover product
            product = get_product_by_name(selected_item["product_name"], products)

            bom = build_bom_perfiles(
                selected_item["selection"], 
                product, 
                parts, 
                selected_item["ancho"], 
                selected_item["alto"]
            )
            
            for row in bom:
                row["producto"] = selected_item["description"]
                row["cantidad"] = row["cantidad"] * selected_item["cantidad"]
            
            all_boms_perfiles.extend(bom)

        df_perfiles = pd.DataFrame(all_boms_perfiles)
        df_perfiles = df_perfiles[["producto", "codigo", "descripcion", "especificacion_medida", "medida_calculada", "cantidad"]]
        st.dataframe(df_perfiles, use_container_width=True)

    # -------------------------------------------------------------
    # CALCULO DE CORTES
    # -------------------------------------------------------------
    with st.expander("Cálculo de cortes"):

        to_cut = {}
        for _, row in df_perfiles.iterrows():
            to_cut.setdefault(row["codigo"], {"pieces": []})
            to_cut[row["codigo"]]["pieces"].extend([row["medida_calculada"]] * row["cantidad"])

        for k, v in to_cut.items():
            v["stock_length"] = parts[k]["largo"]

        piezas_invalidas = any(
            any(p > v["stock_length"] for p in v["pieces"])
            for v in to_cut.values()
        )

        if piezas_invalidas:
            st.warning("⚠️ Hay piezas a cortar mayores al largo de la barra.")
            st.stop()

        res_cuts = []
        for k, v in to_cut.items():
            bars, leftovers = cutting_stock_with_kerf(v["stock_length"], v["pieces"], kerf=kerf, edge_trim=descarte_punta)
            res_cuts.append({
                "codigo": k,
                "total_barras": len(bars),
                "detalle": [
                    {"Barra #": i+1, "Cortes": bars[i], "Sobrante": leftovers[i]}
                    for i in range(len(bars))
                ]
            })

        rows = []
        for res in res_cuts:
            for d in res["detalle"]:
                rows.append({
                    "Código": res["codigo"],
                    "Barra #": d["Barra #"],
                    "kg/m": parts[res["codigo"]]["kg/m"],
                    "Cortes": ", ".join(str(c) for c in d["Cortes"]),
                    "mm. usados": sum(d["Cortes"]),
                    "kg. usados": (sum(d["Cortes"])/1000) * parts[res["codigo"]]["kg/m"],
                    "mm. sobrantes": d["Sobrante"],
                    "kg. sobrantes": (d["Sobrante"]/1000) * parts[res["codigo"]]["kg/m"]
                })

        df_cuts_flat = pd.DataFrame(rows).sort_values(["Código", "Barra #"])

        kg_comprados = 0
        for codigo, group in df_cuts_flat.groupby("Código"):
            st.write(
                f"**{codigo} - {parts[codigo]['descripcion']}**  \n"
                f"total barras: {len(group)} | usados: {group['mm. usados'].sum():.0f} (mm) - "
                f"{group['kg. usados'].sum():.2f} (kg) | sobrantes: {group['mm. sobrantes'].sum():.0f} (mm) - "
                f"{group['kg. sobrantes'].sum():.2f} (kg)"
            )
            st.dataframe(group.drop(columns="Código").round(2), use_container_width=True, hide_index=True)
            kg_comprados += len(group) * parts[codigo]["kg/m"] * (parts[codigo]["largo"]/1000)

        ### PDF DE LISTA DE CORTES ###
        pdf_buffer = generate_pdf(
            df_cuts_flat=df_cuts_flat[["Código", "Barra #", "Cortes"]],
            parts=parts,
        )
        st.download_button(
            label="📥 Descargar lista de cortes",
            data=pdf_buffer,
            file_name="calculo_de_cortes.pdf",
            mime="application/pdf"
        )
        
    # -------------------------------------------------------------
    # LISTA DE PERFILES A PEDIR
    # -------------------------------------------------------------
    with st.expander("Lista de perfiles a comprar"):
        df_perf_a_comprar=(df_cuts_flat.groupby(["Código"]).agg("count")["Barra #"]).rename("Cantidad de barras")
        st.dataframe(df_perf_a_comprar)
        
    
    ### RESUMEN LISTA DE CORTES ### 
    kg_usados = df_cuts_flat["kg. usados"].sum()


    col1, col2 = st.columns(2)

    with col1:
        st.metric("⚖️ Kg comprados", f"{kg_comprados:,.2f}")
        kilos_a_cobrar = st.number_input(
            "📥 Kg a cobrar",
            min_value=0.0,
            value=0.0,
            step=0.10,
            format="%.2f",
            help="Cantidad de kilos que se van a cobrar."
        )

    with col2:
        st.metric("⚖️ Kg usados", f"{kg_usados:,.2f}")
        precio_kilo = st.number_input(
            "💲 Precio por kg",
            min_value=0.0,
            value=0.0,
            step=0.10,
            format="%.2f",
            help="Costo por cada kilo."
        )

    subtotal_perfiles = kilos_a_cobrar * precio_kilo

    st.markdown("---")
    st.markdown(f"### 🧾 Subtotal perfiles: **${subtotal_perfiles:,.2f}**")


with tab4:
    # -------------------------------------------------------------
    # ACCESORIOS
    # -------------------------------------------------------------

    all_boms_accesorios = []
    for idx in selected_indices:
        selected_item = st.session_state.basket[idx]
        product = get_product_by_name(selected_item["product_name"], products)

        bom = build_bom_accesorios(
            selected_item["selection"],
            product,
            parts
        )
        for row in bom:
            row["producto"] = selected_item["description"]
            row["cantidad"] = row["cantidad"] * selected_item["cantidad"]
        all_boms_accesorios.extend(bom)

    df_accesorios = pd.DataFrame(all_boms_accesorios)
    df_accesorios = df_accesorios[
        ["producto", "codigo", "descripcion", "cantidad", "precio unidad", "precio total"]
    ]
    
    with st.expander("Lista de accesorios individualizada"):
        st.dataframe(df_accesorios.round(2), use_container_width=True)
    
    with st.expander("Lista de accesorios por código"):
        st.dataframe(df_accesorios.groupby(["codigo","descripcion"]).agg({
                                                                            "cantidad": "sum",
                                                                            "precio unidad": "first",
                                                                            "precio total": "sum"
                                                                        }).round(2), use_container_width=True)

    # Cálculo inicial
    subtotal_accesorios_bruto = float(df_accesorios["precio total"].sum())

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            f"💵 **Suma accesorios:** ${subtotal_accesorios_bruto:,.2f}"
        )

    with col2:
        desc_accesorios = st.number_input(
            "🎯 Descuento (%)",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=1.0,
            help="Porcentaje de descuento aplicado a los accesorios."
        )

    # Calcular subtotal con descuento
    subtotal_accesorios = subtotal_accesorios_bruto * (1 - desc_accesorios / 100)

    st.markdown("---")
    st.markdown(f"### 🧾 Subtotal accesorios: **${subtotal_accesorios:,.2f}**")


    # -------------------------------------------------------------
    # VIDRIOS
    # -------------------------------------------------------------

with tab5:
    subtotal_vidrios=st.number_input("Costo vidrios", value=0.0, format="%.2f")


with tab6:
    # -------------------------------------------------------------
    # PRESUPUESTO FINAL
    # -------------------------------------------------------------

    st.subheader("Márgenes (%)")

    col1, col2, col3 = st.columns(3)

    with col1:
        perc_perfiles = st.number_input("Perfiles (%)", min_value=0.0, max_value=100.0, step=1.0)
        margen_perfiles = subtotal_perfiles * perc_perfiles / 100

    with col2:
        perc_accesorios = st.number_input("Accesorios (%)", min_value=0.0, max_value=100.0, step=1.0)
        margen_accesorios = subtotal_accesorios * perc_accesorios / 100

    with col3:
        perc_vidrios = st.number_input("Vidrios (%)", min_value=0.0, max_value=100.0, step=1.0)
        margen_vidrios = subtotal_vidrios * perc_vidrios / 100


    st.subheader("Costos adicionales")

    colA, colB, colC = st.columns(3)

    with colA:
        mano_obra = st.number_input("Mano de obra", value=0.0, format="%.2f")

    with colB:
        insumos = st.number_input("Insumos", value=0.0, format="%.2f")

    with colC:
        margen_adicional = st.number_input("Margen adicional", value=0.0, format="%.2f")

    data = {
        "Concepto": [
            "Subtotal perfiles", "Margen perfiles",
            "Subtotal accesorios", "Margen accesorios",
            "Subtotal vidrios", "Margen vidrios",
            "Mano de obra", "Insumos", "Margen adicional"
        ],
        "Valor": [
            subtotal_perfiles, margen_perfiles,
            subtotal_accesorios, margen_accesorios,
            subtotal_vidrios, margen_vidrios,
            mano_obra, insumos, margen_adicional
        ]
    }
    df = pd.DataFrame(data)

    st.subheader("IVA")
    iva_option = st.radio(
        "",
        ("a todo", "solo a compras"),
        label_visibility="collapsed"
    )

    if iva_option == "a todo":
        df["Multiplicador"] = 1.22
    else:
        df["Multiplicador"] = df["Concepto"].apply(
            lambda c: 1.22 if c in ["Subtotal perfiles", "Subtotal accesorios", "Subtotal vidrios"] else 1.00
        )

    df["Total"] = df["Valor"] * df["Multiplicador"]

    total_sin_iva = df["Valor"].sum()
    total_iva_incluido = df["Total"].sum()

    df["Valor"] = df["Valor"].map(lambda x: f"{x:.2f}")
    df["Multiplicador"] = df["Multiplicador"].map(lambda x: f"{x:.2f}")
    df["Total"] = df["Total"].map(lambda x: f"{x:.2f}")

    st.divider()
    st.dataframe(df, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("💰 Total sin IVA", f"{total_sin_iva:,.2f}")

    with col2:
        st.metric("💰 Total IVA incluido", f"{total_iva_incluido:,.2f}")


