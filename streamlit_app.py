
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="HP2C | Dashboard financiero",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# Data model
# -----------------------------
YEARS = [1, 2, 3, 4, 5]

SCENARIOS = {
    "Pesimista": {
        "units": [18000, 45000, 90000, 150000, 240000],
        "net_price": [5.10, 5.10, 5.15, 5.20, 5.25],
        "unit_cost": [3.65, 3.55, 3.45, 3.35, 3.25],
        "fixed_costs": [52000, 100000, 155000, 235000, 340000],
        "discount_rate": 0.45,
        "sales_multiple": 1.10,
        "ebitda_multiple": 4.5,
    },
    "Base": {
        "units": [30000, 90000, 180000, 300000, 450000],
        "net_price": [5.40, 5.40, 5.35, 5.30, 5.25],
        "unit_cost": [3.45, 3.35, 3.25, 3.15, 3.05],
        "fixed_costs": [50000, 115000, 180000, 270000, 385000],
        "discount_rate": 0.35,
        "sales_multiple": 1.50,
        "ebitda_multiple": 6.0,
    },
    "Optimista": {
        "units": [45000, 150000, 300000, 520000, 800000],
        "net_price": [5.60, 5.55, 5.50, 5.45, 5.40],
        "unit_cost": [3.35, 3.20, 3.05, 2.95, 2.85],
        "fixed_costs": [60000, 145000, 245000, 390000, 560000],
        "discount_rate": 0.30,
        "sales_multiple": 2.00,
        "ebitda_multiple": 7.5,
    },
}

def build_forecast(scenario_name: str) -> pd.DataFrame:
    s = SCENARIOS[scenario_name]
    df = pd.DataFrame({
        "Año": YEARS,
        "Paquetes vendidos": s["units"],
        "Precio neto HP2C (USD)": s["net_price"],
        "Costo variable unitario (USD)": s["unit_cost"],
        "Costos fijos (USD)": s["fixed_costs"],
    })
    df["Arepas vendidas"] = df["Paquetes vendidos"] * 4
    df["Producción requerida con 5% merma"] = (df["Paquetes vendidos"] / 0.95).round(0).astype(int)
    df["Producción mensual requerida"] = (df["Producción requerida con 5% merma"] / 12).round(0).astype(int)
    df["Ingresos (USD)"] = df["Paquetes vendidos"] * df["Precio neto HP2C (USD)"]
    df["Costos variables (USD)"] = df["Paquetes vendidos"] * df["Costo variable unitario (USD)"]
    df["Margen bruto (USD)"] = df["Ingresos (USD)"] - df["Costos variables (USD)"]
    df["Margen bruto (%)"] = df["Margen bruto (USD)"] / df["Ingresos (USD)"]
    df["EBITDA (USD)"] = df["Margen bruto (USD)"] - df["Costos fijos (USD)"]
    df["Margen EBITDA (%)"] = df["EBITDA (USD)"] / df["Ingresos (USD)"]
    df["Margen contribución unitario (USD)"] = df["Precio neto HP2C (USD)"] - df["Costo variable unitario (USD)"]
    df["Punto de equilibrio (paquetes)"] = (df["Costos fijos (USD)"] / df["Margen contribución unitario (USD)"]).round(0).astype(int)
    return df

def valuation(scenario_name: str, df: pd.DataFrame) -> dict:
    s = SCENARIOS[scenario_name]
    year_3 = df[df["Año"] == 3].iloc[0]
    revenue_y3 = year_3["Ingresos (USD)"]
    ebitda_y3 = year_3["EBITDA (USD)"]

    sales_value_y3 = revenue_y3 * s["sales_multiple"]
    ebitda_value_y3 = max(ebitda_y3, 0) * s["ebitda_multiple"]

    sales_pv = sales_value_y3 / ((1 + s["discount_rate"]) ** 3)
    ebitda_pv = ebitda_value_y3 / ((1 + s["discount_rate"]) ** 3)

    current_value = (sales_pv + ebitda_pv) / 2
    investment = 90000
    equity_offer = investment / (current_value + investment) if current_value > 0 else None

    return {
        "Valor por ventas año 3 descontado": sales_pv,
        "Valor por EBITDA año 3 descontado": ebitda_pv,
        "Valor pre-money sugerido": current_value,
        "Inversión solicitada": investment,
        "Valor post-money": current_value + investment,
        "Participación sugerida": equity_offer,
    }

def money(x):
    return f"US${x:,.0f}"

def pct(x):
    return f"{x*100:,.1f}%"

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("HP2C")
st.sidebar.caption("Dashboard financiero de escenarios")
scenario = st.sidebar.radio(
    "Escenario",
    ["Base", "Optimista", "Pesimista"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Producto:** paquete de 4 arepas congeladas high-protein.  
    **Mercado destino:** Estados Unidos.  
    **Modelo:** entrada gradual por tiendas latinas, fitness, healthy stores y canales digitales.
    """
)

df = build_forecast(scenario)
val = valuation(scenario, df)

# -----------------------------
# Header
# -----------------------------
st.title("HP2C | Dashboard financiero")
st.subheader("Arepas congeladas high-protein para el mercado estadounidense")

st.info(
    "Este tablero muestra la proyección financiera en tres escenarios. "
    "El precio neto es lo que recibe HP2C después del margen del canal; "
    "no es el precio final pagado por el consumidor."
)

# -----------------------------
# KPIs
# -----------------------------
y1 = df.iloc[0]
y3 = df.iloc[2]
y5 = df.iloc[4]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Paquetes año 1", f"{int(y1['Paquetes vendidos']):,}")
col2.metric("Ingresos año 1", money(y1["Ingresos (USD)"]))
col3.metric("EBITDA año 1", money(y1["EBITDA (USD)"]))
col4.metric("Punto equilibrio año 1", f"{int(y1['Punto de equilibrio (paquetes)']):,}")
col5.metric("Valor pre-money", money(val["Valor pre-money sugerido"]))

col6, col7, col8, col9, col10 = st.columns(5)
col6.metric("Paquetes año 3", f"{int(y3['Paquetes vendidos']):,}")
col7.metric("Ingresos año 3", money(y3["Ingresos (USD)"]))
col8.metric("EBITDA año 3", money(y3["EBITDA (USD)"]))
col9.metric("Margen EBITDA año 3", pct(y3["Margen EBITDA (%)"]))
col10.metric("Participación por US$90k", pct(val["Participación sugerida"]))

# -----------------------------
# Charts
# -----------------------------
st.markdown("## Proyecciones principales")

chart_df = df.melt(
    id_vars="Año",
    value_vars=["Ingresos (USD)", "Costos variables (USD)", "Costos fijos (USD)", "EBITDA (USD)"],
    var_name="Métrica",
    value_name="Valor"
)

fig1 = px.line(
    chart_df,
    x="Año",
    y="Valor",
    color="Métrica",
    markers=True,
    title=f"Flujo operativo proyectado — Escenario {scenario}"
)
fig1.update_layout(yaxis_tickprefix="US$", hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    fig2 = px.bar(
        df,
        x="Año",
        y="Paquetes vendidos",
        title="Paquetes vendidos por año",
        text_auto=True
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    margin_df = df.melt(
        id_vars="Año",
        value_vars=["Margen bruto (%)", "Margen EBITDA (%)"],
        var_name="Margen",
        value_name="Porcentaje"
    )
    fig3 = px.line(
        margin_df,
        x="Año",
        y="Porcentaje",
        color="Margen",
        markers=True,
        title="Evolución de márgenes"
    )
    fig3.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# Scenario comparison
# -----------------------------
st.markdown("## Comparación de escenarios")

comparison_rows = []
for sc in ["Pesimista", "Base", "Optimista"]:
    sc_df = build_forecast(sc)
    sc_val = valuation(sc, sc_df)
    comparison_rows.append({
        "Escenario": sc,
        "Paquetes año 1": sc_df.iloc[0]["Paquetes vendidos"],
        "Ingresos año 1": sc_df.iloc[0]["Ingresos (USD)"],
        "EBITDA año 1": sc_df.iloc[0]["EBITDA (USD)"],
        "Ingresos año 3": sc_df.iloc[2]["Ingresos (USD)"],
        "EBITDA año 3": sc_df.iloc[2]["EBITDA (USD)"],
        "Valor pre-money": sc_val["Valor pre-money sugerido"],
        "Participación por US$90k": sc_val["Participación sugerida"],
    })

comparison = pd.DataFrame(comparison_rows)

fig4 = px.bar(
    comparison,
    x="Escenario",
    y=["Ingresos año 3", "EBITDA año 3", "Valor pre-money"],
    barmode="group",
    title="Escenarios: ingresos, EBITDA y valoración"
)
fig4.update_layout(yaxis_tickprefix="US$")
st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# Tables
# -----------------------------
st.markdown("## Tabla financiera del escenario seleccionado")

display_df = df.copy()
currency_cols = [
    "Precio neto HP2C (USD)", "Costo variable unitario (USD)", "Costos fijos (USD)",
    "Ingresos (USD)", "Costos variables (USD)", "Margen bruto (USD)",
    "EBITDA (USD)", "Margen contribución unitario (USD)"
]
percent_cols = ["Margen bruto (%)", "Margen EBITDA (%)"]

st.dataframe(
    display_df.style.format({
        **{col: "US${:,.2f}" for col in currency_cols},
        **{col: "{:.1%}" for col in percent_cols},
        "Paquetes vendidos": "{:,.0f}",
        "Arepas vendidas": "{:,.0f}",
        "Producción requerida con 5% merma": "{:,.0f}",
        "Producción mensual requerida": "{:,.0f}",
        "Punto de equilibrio (paquetes)": "{:,.0f}",
    }),
    use_container_width=True
)

st.markdown("## Valoración")

valuation_df = pd.DataFrame([
    {"Métrica": k, "Valor": v} for k, v in val.items()
])
st.dataframe(
    valuation_df.style.format({
        "Valor": lambda x: pct(x) if 0 <= x <= 1 and "Participación" in str(x) else f"US${x:,.0f}" if x > 1 else f"{x:.2%}"
    }),
    use_container_width=True,
    hide_index=True
)


st.markdown("## Supuestos de respaldo")
st.markdown(
    """
    - Los consumidores pueden pagar más por alimentos con atributos saludables claros.
    - El nicho fitness y high-protein permite una estrategia premium moderada.
    - La categoría de alimentos congelados en EE. UU. crece por conveniencia, hogares ocupados y búsqueda de soluciones rápidas.
    - El consumidor latino en EE. UU. permite defender identidad cultural, autenticidad y canales iniciales especializados.
    """
)
