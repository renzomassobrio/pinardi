import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import pdf
import cutting_stock as cs
import utils


###### Info estatica ######
df_productos = pd.DataFrame({
    'Producto': ['Perfil tipo 1', 'Perfil tipo 2', 'Esquina', 'Tornillo', 'Soporte'],
    'Peso_kg': [1.2, 2.5, 0.3, 0.05, 0.4],
    'Precio_USD': [10, 18, 1, 0.1, 2]
})

# DataFrame 2: Tipologías
df_tipologias = pd.DataFrame({
    'Tipologia': ['Ventana Pequeña', 'Ventana Mediana', 'Puerta'],
    'Productos_Requeridos': [
        ['Perfil tipo 1', 'Esquina', 'Tornillo'],
        ['Perfil tipo 2', 'Esquina', 'Tornillo', 'Soporte'],
        ['Perfil tipo 2', 'Esquina', 'Tornillo', 'Soporte', 'Soporte']
    ]
})
#############################

st.title("PROYECTO PINARDI - Cotizaciones")

tab1, tab2, tab3 = st.tabs(["⚙️ Items a cotizar", "📋 Presupuesto individual", "📋 Presupuesto total"])

# Initialize session state for the data
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Item", "Tipologia", "Ancho", "Largo"])

#Define topologias
tipologia_options=df_tipologias["Tipologia"]

with tab1:
    st.write("Agregar los items a cotizar")

    # Display editable table
    edited_data = utils.dynamic_input_data_editor(
        st.session_state.data,
        key="tab1",
        num_rows="dynamic",  # allows adding/removing rows
        column_config={
        "Tipologia": st.column_config.SelectboxColumn(
            "Tipologia", options=tipologia_options, help="Seleccione una tipología"
        )
    }
    )
        
    # Reset index to avoid None indices for new rows
    edited_data = edited_data.reset_index(drop=True)

    # Validate the edited data
    errors = utils.validate_items_table(edited_data,tipologia_options)

    # Show error status
    if errors:
        st.error("Errores encontrados:")
        for err in errors:
            st.write(f"- {err}")
    else:
        st.success("No se encontraron errores ✅")
        # Save the edited table back to session state
        st.session_state.data = edited_data
        
    # --- Upload section ---
    # --- Initialize flag for file upload ---
    if "uploaded" not in st.session_state:
        st.session_state.uploaded = False    
        
    st.subheader("Cargar lista de items")

    uploaded_file = st.file_uploader("Cargar archivo CSV", type=["csv"])

    if uploaded_file is not None and not st.session_state.uploaded:
        try:
            new_df = pd.read_csv(uploaded_file)
            st.session_state.data = new_df  # overwrite
            st.session_state.uploaded = True  # prevent re-trigger loop
            st.success("✅ Archivo cargado!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")    
            
    # reset the flag once file_uploader is cleared
    if uploaded_file is None and st.session_state.uploaded:
        st.session_state.uploaded = False
    ############
        

with tab2:
    if errors:
        st.error("Errores encontrados en los items a cotizar.")
    else:   
        # Dropdown menu with values from 'Item' column
        selected_name = st.selectbox("Seleccione un item:", st.session_state.data['Item'])
        
        # Filter the dataframe for the selected row
        selected_row = st.session_state.data[st.session_state.data['Item'] == selected_name]

        # Display the info of the selected row
        st.dataframe(selected_row.reset_index(drop=True), hide_index=True)

        row = df_tipologias[df_tipologias['Tipologia'] == selected_row["Tipologia"].iloc[0]]
               
        st.write("Productos requeridos")
        
        productos_requeridos = row.iloc[0]['Productos_Requeridos']
    
        # Crear dataframe con las propiedades de cada producto
        df_resultado = df_productos[df_productos['Producto'].isin(productos_requeridos)].copy()
        
        # Contar cuántas veces aparece cada producto en la lista
        df_resultado['Cantidad'] = df_resultado['Producto'].apply(lambda x: productos_requeridos.count(x))
        
        # Ajustar peso y precio por cantidad
        df_resultado['Peso_Total_kg'] = df_resultado['Peso_kg'] * df_resultado['Cantidad']
        df_resultado['Precio_Total_USD'] = df_resultado['Precio_USD'] * df_resultado['Cantidad']
        
        st.dataframe(df_resultado.reset_index(drop=True), hide_index=True)
        
        pdf_buffer = pdf.create_pdf(df_resultado, title="Customer Selection Report")
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_buffer,
            file_name="report.pdf",
            mime="application/pdf",
            key="individual_report"
        )


with tab3:
    if errors:
        st.error("Errores encontrados en los items a cotizar.")
    else:
        df_tab3=pd.DataFrame(st.session_state.data)
        # Add a 'Select' column for checkboxes
        df_tab3["Agregar al presupuesto?"] = False
        
        # Configure data_editor to allow editing only the 'Select' column
        edited_df_tab3 = st.data_editor(
            df_tab3,
            column_config={
                "Agregar al presupuesto?": st.column_config.CheckboxColumn("Agregar al presupuesto?")
            },
            hide_index=True,
            disabled=list(set(df_tab3.columns) - set(["Agregar al presupuesto?"])),  # block editing these columns
            key="data_editor_tab_3"
        )
        
        # Filter selected rows
        selected_rows = edited_df_tab3[edited_df_tab3["Agregar al presupuesto?"]]

        st.subheader("Selected Rows")
        st.dataframe(selected_rows.drop(columns="Agregar al presupuesto?"), hide_index=True)
        
        # Generate PDF only if data exists
        if not st.session_state.data.empty:
            pdf_buffer = pdf.create_pdf(selected_rows, title="Customer Selection Report")
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name="report.pdf",
                mime="application/pdf"
            )

