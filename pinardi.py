import streamlit as st
import pandas as pd
from pathlib import Path
from bom_engine import load_parts, load_product, get_available_decisions, build_bom
from cutting_stock import cutting_stock_with_kerf
from pdf import create_pdf

#st.set_page_config(layout="wide")
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

tab1, tab2, tab3 = st.tabs(["🛒 Armar pedido", "📋 Presupuesto individual", "📋 Presupuesto total"])

# --- TAB 1: Configurator ---
with tab1:

    st.subheader("Configuración del producto")
    
    # Description input
    description = st.text_input("Ingresar un nombre para el producto", placeholder="p.ej. ventana dormitorio")
    
    # Input two integers directly
    ancho = st.number_input("Ingrese el ancho A (en mm)", value=0, step=1, format="%d")
    alto = st.number_input("Ingrese el alto H (en mm)", value=0, step=1, format="%d")
    
    # Product selection
    selected_index = st.selectbox("Seleccionar tipologia", range(len(products)),
                                  format_func=lambda i: product_names[i])

    product = products[selected_index]

    # Reset selection when changing product
    #if st.session_state.get("last_product_index") != selected_index:
    #    st.session_state.selection = {}
    #    st.session_state.last_product_index = selected_index
        
    st.text("⚙️ Configuración de opciones")

   # Dynamic dropdowns
    available = get_available_decisions(product, st.session_state.selection)

    for nombre, opciones in available.items():
        current_value = st.session_state.selection.get(nombre)
        options_labels = {
            str(opt): f"{opt} - {parts[opt]['descripcion']}" 
            for opt in opciones
        }

        chosen = st.selectbox(
            f"{nombre}",
            options=[""] + list(options_labels.keys()),
            format_func=lambda x: options_labels.get(x, "") if x else "Seleccionar...",
            key=f"select_{nombre}",
            index=0  # default to "Seleccionar..." if no prior choice
        )

        if chosen:
            st.session_state.selection[nombre] = int(chosen)
            
    # ✅ Validation check: make sure ALL dropdowns have a selection
    all_selected = all(st.session_state.selection.get(nombre) for nombre in available.keys())

    # Add to basket
    if st.button("🛒➕ Agregar al pedido"):
        if (not description):
            st.warning("⚠️ Debe ingresar un nombre para el producto.")
        elif any(d["description"] == description for d in st.session_state.basket):
            st.warning("⚠️ El nombre del producto ya está en uso.")
        elif ancho==0:
            st.warning("⚠️ El ancho debe ser mayor a cero.")
        elif alto==0:
            st.warning("⚠️ El alto debe ser mayor a cero.")
        elif not st.session_state.selection:
            st.warning("⚠️ Debe configurar el producto primero.")
        elif not all_selected:
            st.warning("⚠️ Selecciona una opción en todos los menús desplegables antes de continuar.")
        else:
            st.session_state.basket.append({
                "description": description,
                "ancho":ancho,
                "alto":alto,
                "product": product,
                "selection": st.session_state.selection.copy()
            })
            st.session_state.selection = {}  # reset after adding
            st.success("✅ Producto agregado al pedido!")

    # Show basket
    if st.session_state.basket:
        st.subheader("🛒 Pedido")

        for i, p in enumerate(st.session_state.basket):
            # Build product info with line breaks
            product_info_lines = [p["product"]["tipologia"]]
            for option_name, choice in p["selection"].items():
                product_info_lines.append(f"{option_name}: {choice} - {parts[choice]['descripcion']}")
            product_info = "<br>".join(product_info_lines)

            # Display description and product info
            st.markdown(f"**{p['description']}**<br>Ancho: {p['ancho']}<br>Alto: {p['alto']}<br>{product_info}", unsafe_allow_html=True)

            # Remove button
            remove_key = f"remove_{i}"
            if st.button("❌ Eliminar del pedido", key=remove_key):
                st.session_state.basket.pop(i)
                st.rerun()  

            st.markdown("---")

# --- TAB 2: BOM Viewer ---
with tab2:
    if not st.session_state.basket:
        st.info("No hay productos en el pedido aún.")
    else:
        # Select product from basket by description
        selected_basket_index = st.selectbox(
            "Seleccione un producto del pedido",
            range(len(st.session_state.basket)),
            format_func=lambda i: st.session_state.basket[i]["description"]
        )

        selected_item = st.session_state.basket[selected_basket_index]
        bom = build_bom(selected_item["selection"], selected_item["product"], parts, selected_item["ancho"], selected_item["alto"])
        df = pd.DataFrame(bom)
        
        st.header("🛠️ Lista de partes")
        df_partes=df[["codigo","descripcion","especificacion_medida","medida_calculada","cantidad"]]
        st.dataframe(df_partes, use_container_width=True)
        
        st.header("📏 Cálculo de cortes")
        
        # Crear diccionario de piezas a cortar
        to_cut = {}
        for _, row in df_partes.iterrows():
            to_cut.setdefault(row['codigo'], {'pieces': []})
            to_cut[row['codigo']]['pieces'].extend([row['medida_calculada']] * row['cantidad'])
        
        # Agregar el largo de cada barra
        for k,v in to_cut.items():
            v["stock_length"]=parts[k]["largo"]
    
        piezas_invalidas=False
        for k, v in to_cut.items():
            if any(p > v["stock_length"] for p in v["pieces"]):
                piezas_invalidas=True
                
        if piezas_invalidas:
            st.warning("⚠️ Hay piezas a cortar mayores al largo de la barra.")
        else:
            # Llamar al optimizador de cortes
            res_cuts=[]
            for k,v in to_cut.items():
                res=cutting_stock_with_kerf(v["stock_length"],v["pieces"],kerf=16) # Ajustar el valor de ancho de la hoja de corte
                res_cuts.append({"codigo":k,
                                "total_barras":len(res),
                                "cortes":res})
                
            df_cuts=pd.DataFrame(res_cuts)
            st.dataframe(df_cuts, use_container_width=True)

            st.header("💰 Presupuesto")

            df_presupuesto=df_cuts.copy()
            df_presupuesto.drop(columns="cortes",inplace=True)  
            df_presupuesto["precio_por_barra"]=df_presupuesto.apply(lambda row: parts[row["codigo"]]["precio"], axis=1)
            df_presupuesto["subtotal"]=df_presupuesto["total_barras"]*df_presupuesto["precio_por_barra"]   
            total=df_presupuesto["subtotal"].sum()      
            st.dataframe(df_presupuesto, use_container_width=True)
            st.write(f"**💰 Total: {total:.2f}**")
            
            pdf_presupuesto = create_pdf(df_presupuesto, title="Presupuesto individual", total_cost=total)
            st.download_button(
                label="📄 Descargar PDF",
                data=pdf_presupuesto,
                file_name="report.pdf",
                mime="application/pdf"
            )

#####
with tab3:
    st.title("🛠️ En construcción")
