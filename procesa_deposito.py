import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.title("Análisis de Depósitos por Usuario")

# Subir archivo
uploaded_file = st.file_uploader("Subí un archivo CSV con los depósitos", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer archivo CSV
        df = pd.read_csv(uploaded_file, sep=';')

        # Normalizar nombre de columna de usuario
        usuario_col = next((col for col in df.columns if col.strip().lower() == 'usuario'), None)
        fecha_col = next((col for col in df.columns if 'fecha' in col.lower()), None)
        monto_col = next((col for col in df.columns if 'monto' in col.lower() or 'deposito' in col.lower()), None)

        if not usuario_col or not fecha_col or not monto_col:
            st.error("No se encontraron columnas requeridas: usuario, fecha y monto.")
        else:
            # Convertir tipos
            df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')
            df[monto_col] = pd.to_numeric(df[monto_col], errors='coerce')

            # Eliminar nulos
            df = df.dropna(subset=[fecha_col, monto_col])

            # Extraer hora
            df["hora"] = df[fecha_col].dt.hour

            # Crear resumen
            resumen = df.groupby(usuario_col).agg(
                total_depositado=(monto_col, 'sum'),
                max_deposito=(monto_col, 'max'),
                min_deposito=(monto_col, 'min')
            ).reset_index()

            # Filtrar entre 17 y 23 hs
            df_17_23 = df[(df["hora"] >= 17) & (df["hora"] <= 23)]
            max_17_23 = df_17_23.groupby(usuario_col)[monto_col].max().reset_index().rename(columns={monto_col: "max_deposito_17_a_23"})

            # Unir todo
            resumen = pd.merge(resumen, max_17_23, on=usuario_col, how="left")

            st.subheader("Resumen de depósitos por usuario")
            st.dataframe(resumen)

            # Descargar Excel
            def to_excel_bytes(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Resumen')
                return output.getvalue()

            excel_bytes = to_excel_bytes(resumen)
            st.download_button(
                label="📥 Descargar resumen en Excel",
                data=excel_bytes,
                file_name="resumen_depositos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
