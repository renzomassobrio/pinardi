import streamlit as st
import pandas as pd

from functions import load_stock, save_stock


# -------------------------------------------------
# Constants
# -------------------------------------------------

COL_POS = "posicion"
COL_CODE = "codigo"
COL_LENGTH = "largo"


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def sort_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Sort stock by position and code."""
    return (
        df.sort_values(
            by=[COL_POS, COL_CODE],
            ascending=[True, True],
        )
        .reset_index(drop=True)
    )


def prepare_stock(stock: list[dict]) -> pd.DataFrame:
    """Create the stock DataFrame."""
    df = pd.DataFrame(stock)

    if df.empty:
        return pd.DataFrame(
            columns=[COL_POS, COL_CODE, COL_LENGTH]
        )

    return sort_stock(df)


def validate_stock(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Validate user edits."""
    df = df.copy()
    errors = []

    # Position
    missing_pos = (
        df[COL_POS].isna()
        | (df[COL_POS].astype(str).str.strip() == "")
    )

    if missing_pos.any():
        rows = ", ".join(str(i + 1) for i in df.index[missing_pos])
        errors.append(
            f"❌ Las filas {rows} no tienen posición."
        )

    # Code
    try:
        df[COL_CODE] = df[COL_CODE].astype(int)
    except (ValueError, TypeError):
        errors.append(
            "❌ El código debe ser un número entero."
        )

    # Length
    try:
        df[COL_LENGTH] = df[COL_LENGTH].astype(int)
    except (ValueError, TypeError):
        errors.append(
            "❌ El largo debe ser un número entero."
        )

    if not errors and (df[COL_LENGTH] <= 0).any():
        rows = ", ".join(
            str(i + 1)
            for i in df.index[df[COL_LENGTH] <= 0]
        )
        errors.append(
            f"❌ El largo debe ser mayor que cero (filas {rows})."
        )

    return df, errors


# -------------------------------------------------
# Page
# -------------------------------------------------

st.set_page_config(
    page_title="PROYECTO PINARDI",
    layout="wide",
)

st.title("PROYECTO PINARDI - Control de stock")


# -------------------------------------------------
# Load stock
# -------------------------------------------------

stock, sha = load_stock()
df_stock = prepare_stock(stock)


# -------------------------------------------------
# Stock table
# -------------------------------------------------

st.subheader(f"Total de items en stock: **{len(df_stock)}**")

with st.expander("📖 Instrucciones", expanded=False):
    st.markdown(
        """
- **Editar un item:** haga doble clic en una celda para cambiar posición, código o largo.
- **Agregar un item:** haga clic en '+' al final de la tabla para agregar una nueva fila.
- **Eliminar items:**
    1. Seleccione las filas mediante la casilla ✓ a la izquierda de cada fila.
    2. Pulse el icono 🗑 situado en la esquina superior derecha.
- Cuando termine, pulse **💾 Guardar cambios**.
"""
    )

# Reserve the space before the table
changes_placeholder = st.empty()

edited_df = st.data_editor(
    df_stock,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        COL_POS: st.column_config.TextColumn(
            "Posición",
            required=True,
        ),
        COL_CODE: st.column_config.NumberColumn(
            "Código",
            required=True,
            step=1,
        ),
        COL_LENGTH: st.column_config.NumberColumn(
            "Largo (mm)",
            required=True,
            step=1,
            min_value=1,
        ),
    },
)


# -------------------------------------------------
# Save
# -------------------------------------------------

has_changes = not sort_stock(edited_df).equals(sort_stock(df_stock))

if has_changes:
    changes_placeholder.warning("✏️ Hay cambios sin guardar.")

    
if st.button(
    "💾 Guardar cambios",
    use_container_width=True,
    disabled=not has_changes,
):

    validated_df, errors = validate_stock(edited_df)

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    validated_df = sort_stock(validated_df)

    # Nothing changed
    if validated_df.equals(sort_stock(df_stock)):
        st.info("ℹ️ No hay cambios para guardar.")
        st.stop()

    try:
        with st.spinner("Guardando cambios..."):

            save_stock(
                validated_df.to_dict("records"),
                sha,
            )

        st.success("✅ Stock actualizado correctamente.")
        st.rerun()

    except Exception as e:
        st.error(
            f"No se pudo guardar el archivo en GitHub.\n\n{e}"
        )