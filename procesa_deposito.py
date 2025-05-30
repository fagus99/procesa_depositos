import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import unicodedata

st.set_page_config(page_title="Resumen de Depósitos", layout="centered")

st.title("💸 Resumen de Depósitos por Beneficiario")

uploaded_file = st.file_uploader("Subí un archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        # Función para normalizar texto (minúsculas, sin tildes)
        def normalizar(texto):
            return unicodedata.normalize('NFKD', str(texto)).encode('ascii', errors='ignore').decode().lower().strip()

        columnas_norm = {col: normalizar(col) for col in df.columns}

        # Buscar columna de beneficiario
        beneficiario_col = next((col for col, norm in columnas_norm.items() if 'beneficiario' in norm), None)
        if not beneficiario_col:
            st.error("❌ No se encontró una columna con el nombre 'beneficiario'.")
        else:
            # Buscar columna de fecha
            fecha_col = next((col for col, norm in columnas_norm.items() if 'fecha' in norm or 'hora' in norm), None)
            if not fecha_col:
                st.error("❌ No se encontró una columna con la fecha u hora del depósito.")
            else:
                # Buscar columna de monto (incluye 'cantidad' ahora)
                monto_col = next((col for col, norm in columnas_norm.items() if any(x in norm for x in ['monto', 'importe', 'cantidad'])), None)
                if not monto_col:
                    st.error("❌ No se encontró una columna con el monto del depósito (monto, importe o cantidad).")
                else:
                    # Procesamiento
                    df[fecha_col] = pd.to_datetime(df[fecha_col], errors='coerce')
                    df[monto_col] = pd.to_numeric(df[monto_col], errors='coerce')
                    df = df.dropna(subset=[beneficiario_col, fecha_col, monto_col])

                    # Agrupar
                    resumen = df.groupby(beneficiario_col).agg(
                        suma_total_depositos=(monto_col, 'sum'),
                        deposito_maximo=(monto_col, 'max'),
                        deposito_minimo=(monto_col, 'min')
                    ).reset_index()

                    # Filtrar entre 17 y 23 hs
                    df['hora'] = df[fecha_col].dt.hour
                    en_franja = df[(df['hora'] >= 17) & (df['hora'] <= 23)]

                    max_17a23 = en_franja.groupby(beneficiario_col)[monto_col].max().reset_index()
                    max_17a23.rename(columns={monto_col: 'max_deposito_17_23hs'}, inplace=True)

                    resumen = resumen.merge(max_17a23, on=beneficiario_col, how='left')

                    # Mostrar y descargar
                    st.subheader("📊 Resumen generado")
                    st.dataframe(resumen)

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        resumen.to_excel(writer, sheet_name="Resumen", index=False)
                    output.seek(0)

                    st.download_button(
                        label="📥 Descargar resumen en Excel",
                        data=output,
                        file_name="resumen_depositos.xlsx",
                        mime="application/octet-stream"
                    )
    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo: {e}")
