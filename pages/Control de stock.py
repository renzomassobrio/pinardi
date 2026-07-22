import streamlit as st
import pandas as pd

from functions import load_stock, save_stock


st.set_page_config(
    page_title="Stock aluminio",
    page_icon="📦"
)


st.title("📦 Stock aluminio")


# -------------------------------------------------
# Load stock
# -------------------------------------------------

stock = load_stock()


df_stock = pd.DataFrame(stock)


if df_stock.empty:
    df_stock = pd.DataFrame(
        columns=[
            "posicion",
            "codigo",
            "largo"
        ]
    )


# -------------------------------------------------
# Editable table
# -------------------------------------------------

st.subheader("Barras disponibles")


edited_df = st.data_editor(
    df_stock,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "posicion": st.column_config.TextColumn(
            "Posición"
        ),
        "codigo": st.column_config.NumberColumn(
            "Código"
        ),
        "largo": st.column_config.NumberColumn(
            "Largo (mm)"
        )
    }
)


# -------------------------------------------------
# Save
# -------------------------------------------------

if st.button("💾 Guardar cambios"):

    errors = []

    # Validate empty positions
    if edited_df["posicion"].isna().any() or (edited_df["posicion"].astype(str).str.strip() == "").any():
        errors.append("❌ Hay barras sin posición.")

    # Validate codigo integer
    try:
        edited_df["codigo"] = edited_df["codigo"].astype(int)
    except Exception:
        errors.append("❌ El código debe ser un número entero.")

    # Validate largo integer
    try:
        edited_df["largo"] = edited_df["largo"].astype(int)
    except Exception:
        errors.append("❌ El largo debe ser un número entero.")

    # Validate positive lengths
    if (edited_df["largo"] <= 0).any():
        errors.append("❌ El largo debe ser mayor que cero.")

    if errors:
        for error in errors:
            st.error(error)

    else:
        new_stock = edited_df.to_dict(
            orient="records"
        )

        save_stock(new_stock)

        st.success("✅ Stock actualizado correctamente.")

        st.rerun()