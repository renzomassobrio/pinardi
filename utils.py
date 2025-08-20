import streamlit as st
import pandas as pd

def dynamic_input_data_editor(data, key, **_kwargs):
    """
    Like streamlit's data_editor but which allows you to initialize the data editor with input arguments that can
    change between consecutive runs. Fixes the problem described here: https://discuss.streamlit.io/t/data-editor-not-changing-cell-the-1st-time-but-only-after-the-second-time/64894/13?u=ranyahalom
    :param data: The `data` argument you normally pass to `st.data_editor()`.
    :param key: The `key` argument you normally pass to `st.data_editor()`.
    :param _kwargs: All other named arguments you normally pass to `st.data_editor()`.
    :return: Same result returned by calling `st.data_editor()`
    """
    changed_key = f'{key}_khkhkkhkkhkhkihsdhsaskskhhfgiolwmxkahs'
    initial_data_key = f'{key}_khkhkkhkkhkhkihsdhsaskskhhfgiolwmxkahs__initial_data'

    def on_data_editor_changed():
        if 'on_change' in _kwargs:
            args = _kwargs['args'] if 'args' in _kwargs else ()
            kwargs = _kwargs['kwargs'] if 'kwargs' in _kwargs else  {}
            _kwargs['on_change'](*args, **kwargs)
        st.session_state[changed_key] = True

    if changed_key in st.session_state and st.session_state[changed_key]:
        data = st.session_state[initial_data_key]
        st.session_state[changed_key] = False
    else:
        st.session_state[initial_data_key] = data
    __kwargs = _kwargs.copy()
    __kwargs.update({'data': data, 'key': key, 'on_change': on_data_editor_changed})
    return st.data_editor(**__kwargs)
    
    
# Function to validate data
def validate_items_table(df, tipologias_posibles):
    errors = []
    if isinstance(df, pd.DataFrame):
        if df.empty:
            errors.append(f"❌ Agregar al menos un item.")
        for i, row in df.iterrows():
            # Largo existe y mayor a cero
            largo = row["Largo"]
            try:
                largo_val = float(largo)
                if largo_val <= 0:
                    errors.append(f"❌ Fila {i}. El largo debe ser mayor a cero.")
            except:
                errors.append(f"❌ Fila {i}. Largo debe ser un número válido y no estar vacío.")
            
            # Ancho existe y mayor a cero
            ancho = row["Ancho"]
            try:
                ancho_val = float(ancho)
                if ancho_val <= 0:
                    errors.append(f"❌ Fila {i}. El ancho debe ser mayor a cero.")
            except (ValueError, TypeError):
                errors.append(f"❌ Fila {i}. Ancho debe ser un número válido y no estar vacío.")
                
            #Tipologia dentro de las disponibles
            if row["Tipologia"] == None:
                errors.append(f"❌ Fila {i}. Debe elegir una tipologia.")

        # Check for duplicate items
        if df["Item"].duplicated().any():
            duplicated_rows = df[df["Item"].duplicated()].index.tolist()
            for i in duplicated_rows:
                errors.append(f"❌ Fila {i}. Los nombres de los items deben ser únicos")
    return errors
