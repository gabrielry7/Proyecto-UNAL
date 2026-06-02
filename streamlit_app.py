
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

st.markdown("## Preguntas metodológicas y defensa del modelo")

st.caption(
    "Esta sección responde preguntas que podría hacer el jurado sobre supuestos, "
    "metodología de proyección, rentabilidad, escenarios y valoración."
)

preguntas_metodologicas = [
    (
        "1. ¿Qué metodología usaron para hacer la proyección financiera?",
        "Usamos una metodología bottom-up. Es decir, no partimos de una cifra general del mercado, sino de unidades concretas: paquetes vendidos por año, precio neto por paquete, costo variable unitario, costos fijos y margen. A partir de eso proyectamos ingresos, costos, EBITDA y punto de equilibrio."
    ),
    (
        "2. ¿Por qué bottom-up y no una proyección general del mercado?",
        "Porque HP2C es una empresa nueva. Aunque el mercado de alimentos funcionales en Estados Unidos sea grande, eso no significa que vayamos a capturar una gran participación desde el inicio. Por eso preferimos una proyección por unidades vendidas, que es más prudente y defendible."
    ),
    (
        "3. ¿De dónde sale la proyección de 30.000 paquetes en el año 1?",
        "Sale de una lógica de validación gradual. 30.000 paquetes al año equivalen a 2.500 paquetes mensuales. Para una entrada inicial en tiendas latinas, tiendas saludables, gimnasios aliados y canales digitales, es una meta exigente, pero razonable."
    ),
    (
        "4. ¿Cómo estimaron la producción requerida?",
        "Tomamos los paquetes vendidos esperados y agregamos una merma del 5%. La fórmula es: producción requerida = paquetes vendidos / 0,95. Por eso, para vender 30.000 paquetes necesitamos producir aproximadamente 31.579 paquetes."
    ),
    (
        "5. ¿Por qué usan una merma del 5%?",
        "Porque en alimentos congelados siempre hay pérdidas normales: pruebas de calidad, manipulación, errores de empaque, congelación, devoluciones o producto deteriorado. No sería realista asumir que el 100% de lo producido se vende perfectamente."
    ),
    (
        "6. ¿Cómo calcularon el volumen físico del producto?",
        "Cada arepa pesa 85 gramos y cada paquete trae 4 arepas. Entonces cada paquete pesa 340 gramos. En el año 1: 30.000 paquetes por 340 gramos son 10.200 kg, es decir, 10,2 toneladas vendidas."
    ),
    (
        "7. ¿Por qué usan precio neto y no precio final al consumidor?",
        "Porque HP2C no recibe todo lo que paga el consumidor final. Si una tienda vende el paquete a precio retail, una parte queda para distribuidores, tiendas, promociones o comisiones. Por eso usamos precio neto: lo que realmente entra a HP2C."
    ),
    (
        "8. ¿Por qué el precio neto es USD 5,40?",
        "Porque asumimos que HP2C vende a distribuidores o canales especializados con margen para el canal. El precio final puede estar cerca de USD 8,99, pero el ingreso real de HP2C sería menor. USD 5,40 permite modelar la empresa sin inflar artificialmente los ingresos."
    ),
    (
        "9. ¿Cómo calcularon el costo variable unitario de USD 3,45?",
        "Lo construimos por componentes: ingredientes, whey protein, clara de huevo, queso, maquila, empaque, cadena de frío, flete, seguro, control de calidad y promoción inicial. Es decir, no es solo el costo de la arepa; incluye llevarla al mercado internacional."
    ),
    (
        "10. ¿Qué método usaron para medir rentabilidad?",
        "Usamos unit economics. Eso significa analizar cuánto deja cada unidad vendida. Precio neto menos costo variable unitario nos da el margen de contribución. En el caso base: USD 5,40 - USD 3,45 = USD 1,95 por paquete."
    ),
    (
        "11. ¿Qué significa margen de contribución?",
        "Es lo que aporta cada paquete para cubrir costos fijos y generar utilidad. Si cada paquete deja USD 1,95, entonces mientras más paquetes vendamos por encima del punto de equilibrio, más utilidad operativa genera el negocio."
    ),
    (
        "12. ¿Cómo calcularon el margen bruto de 36%?",
        "Con la fórmula: margen bruto = margen de contribución / precio neto. En este caso: USD 1,95 / USD 5,40 = 36,1%. Eso muestra que el producto tiene espacio para cubrir costos fijos y crecer."
    ),
    (
        "13. ¿Cómo calcularon el punto de equilibrio?",
        "Usamos la fórmula: punto de equilibrio = costos fijos / margen de contribución unitario. En año 1: USD 50.000 / USD 1,95 = 25.641 paquetes. Ese es el volumen mínimo para no perder dinero operativamente."
    ),
    (
        "14. ¿Por qué usan EBITDA como indicador?",
        "Porque EBITDA muestra la rentabilidad operativa antes de intereses, impuestos, depreciaciones y amortizaciones. Para una empresa temprana, sirve para ver si el negocio funciona antes de decisiones financieras o contables."
    ),
    (
        "15. ¿Qué metodología usaron para los escenarios pesimista, base y optimista?",
        "Usamos análisis de sensibilidad. Cambiamos variables clave: unidades vendidas, precio neto, costo unitario, costos fijos, tasa de descuento y múltiplos de valoración. Así evaluamos qué pasa si el mercado responde peor o mejor de lo esperado."
    ),
    (
        "16. ¿Por qué presentar solo el caso base si hay tres escenarios?",
        "Porque el caso base es el punto medio y más defendible para exposición. Los escenarios pesimista y optimista sirven como respaldo técnico: muestran que no dependemos de una sola predicción rígida y que analizamos riesgo."
    ),
    (
        "17. ¿Qué método usaron para valorar la empresa?",
        "Usamos valoración por múltiplos, específicamente múltiplo sobre ventas y múltiplo sobre EBITDA del año 3. Luego descontamos esos valores al presente porque HP2C todavía sería una empresa temprana y riesgosa."
    ),
    (
        "18. ¿Por qué usaron el año 3 para valorar y no el año 1?",
        "Porque el año 1 es de validación y todavía no refleja el potencial del negocio. El año 3 muestra una operación más estabilizada, con mayor volumen, mejores márgenes y datos más útiles para estimar valor futuro."
    ),
    (
        "19. ¿Por qué descuentan la valoración al presente?",
        "Porque un dólar de valor futuro no vale lo mismo que un dólar hoy, especialmente en una empresa nueva con riesgo comercial, logístico y regulatorio. Descontar al presente ajusta la valoración por incertidumbre."
    ),
    (
        "20. ¿Por qué la tasa de descuento es alta?",
        "Porque HP2C está en etapa temprana. Hay riesgo de aceptación del producto, riesgo logístico, riesgo de cadena de frío, riesgo regulatorio y riesgo comercial. Una tasa alta castiga la valoración y evita sobrevalorar el negocio."
    ),
    (
        "21. ¿Por qué usar múltiplo de ventas y múltiplo de EBITDA al mismo tiempo?",
        "Porque cada método mira algo distinto. El múltiplo de ventas captura potencial comercial y crecimiento. El múltiplo de EBITDA captura rentabilidad operativa. Usar ambos nos da una valoración más equilibrada."
    ),
    (
        "22. ¿Por qué no usaron solo flujo de caja descontado?",
        "Porque para una empresa nueva, el flujo de caja libre puede ser muy incierto. Un DCF completo exigiría muchos supuestos sobre impuestos, depreciación, inversión en activos, capital de trabajo y valor terminal. Para Shark Tank, múltiplos descontados son más simples y defendibles."
    ),
    (
        "23. ¿Cómo llegaron a la valoración pre-money de USD 510.000?",
        "Calculamos un rango de valoración usando ventas y EBITDA proyectados del año 3, aplicamos múltiplos conservadores y descontamos al presente. El resultado cae alrededor de USD 500.000 a USD 600.000, por eso usamos USD 510.000 como pre-money."
    ),
    (
        "24. ¿Qué significa pre-money y post-money?",
        "Pre-money es lo que vale la empresa antes de recibir inversión. Post-money es lo que vale después. Si HP2C vale USD 510.000 antes y recibe USD 90.000, la valoración post-money es USD 600.000."
    ),
    (
        "25. ¿Por qué pedir USD 90.000 por el 15%?",
        "Porque USD 90.000 cubren producción inicial, empaque, cadena de frío, requisitos sanitarios, marketing y capital de trabajo. Si el inversionista recibe 15%, eso implica una valoración post-money de USD 600.000, coherente con nuestro rango de valoración."
    ),
    (
        "26. ¿Qué variable afecta más el modelo financiero?",
        "La variable más sensible es el volumen vendido. Si vendemos menos paquetes, el negocio tarda más en cubrir costos fijos. Después vienen el precio neto y el costo variable, porque afectan directamente el margen por paquete."
    ),
    (
        "27. ¿Qué pasa si sube el costo del whey protein o la logística?",
        "Baja el margen de contribución y sube el punto de equilibrio. Por eso el escenario pesimista incluye costos unitarios más altos. La mitigación sería negociar proveedores, ajustar formulación o subir precio si el mercado lo permite."
    ),
    (
        "28. ¿Cómo se conecta la logística CIF con el modelo financiero?",
        "Como HP2C asume flete y seguro internacional bajo CIF, esos costos deben estar dentro del costo variable. Por eso nuestro costo unitario incluye no solo producción, sino también transporte internacional y protección de la mercancía."
    ),
    (
        "29. ¿Qué supuesto financiero sería el primero que validarían en la vida real?",
        "El precio neto. Antes de escalar, deberíamos validar cuánto pagaría realmente un distribuidor o tienda por paquete. Ese dato confirmaría si el margen de USD 1,95 es realista."
    ),
    (
        "30. ¿Cuál es la conclusión metodológica del modelo?",
        "El modelo no intenta predecir el futuro con exactitud. Intenta probar si HP2C tiene lógica económica bajo supuestos razonables. En el caso base, el negocio supera punto de equilibrio en año 1 y escala con márgenes positivos, por eso es financieramente defendible."
    ),
]

for pregunta, respuesta in preguntas_metodologicas:
    with st.expander(pregunta):
        st.write(respuesta)
)
