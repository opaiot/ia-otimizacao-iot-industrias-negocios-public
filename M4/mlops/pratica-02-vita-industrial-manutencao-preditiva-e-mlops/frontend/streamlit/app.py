"""Dashboard Streamlit do case industrial VITA."""

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from pathlib import Path

API_URL = os.getenv("VITA_API_URL", "http://127.0.0.1:8000")
TIMEOUT = 180
APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = APP_DIR / "vita.png"

st.set_page_config(
    page_title="VITA Industrial",
    page_icon="V",
    layout="wide",
)


def api_get(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=TIMEOUT)
    response.raise_for_status()
    return response


def api_post(path: str, payload: dict):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response


def service_status():
    try:
        health = api_get("/health").json()
        st.sidebar.success(f"API ativa - v{health['service_version']}")
        return True
    except requests.RequestException:
        st.sidebar.error("API indisponível")
        return False


st.sidebar.image(str(LOGO_PATH), width=120)
st.sidebar.title("VITA Industrial")
online = service_status()
page = st.sidebar.radio(
    "Navegação",
    [
        "Visão geral 6C",
        "Treinamento e tracking",
        "Inferência e decisão",
        "Monitoramento",
        "Governança",
        "Assistente de Consciência",
    ],
)
st.sidebar.caption(f"Backend: {API_URL}")


if page == "Visão geral 6C":
    st.title("Predição de falha em bombas e motores")
    st.write(
        "Case educacional de IA industrial organizado pela arquitetura VITA de seis camadas."
    )
    if online:
        architecture = api_get("/api/v1/architecture").json()
        columns = st.columns(3)
        colors = ["#334155", "#b91c1c", "#c2410c", "#ca8a04", "#65a30d", "#15803d"]
        for index, layer in enumerate(architecture["layers"]):
            with columns[index % 3]:
                st.markdown(
                    f"""
                    <div style="border-left: 6px solid {colors[index]}; padding: 12px;
                                margin-bottom: 14px; background: #f8fafc; min-height: 120px;
                                color: #0f172a;">
                      <h4 style="margin:0; color:#0f172a !important;">
                        {index + 1}. {layer['name']}
                      </h4>
                      <p style="color:#334155 !important; margin-top:10px;">
                        {layer['implementation']}
                      </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        registry = api_get("/api/v1/registry").json()
        if registry.get("production_version"):
            st.success(
                "Modelo disponível para demonstração: "
                f"PumpFailureRisk {registry['production_version']}."
            )
        else:
            st.warning(
                "A arquitetura pode ser explorada agora. Para liberar inferência, "
                "monitoramento e documentos gerados, abra 'Treinamento e tracking' "
                "e execute o primeiro treinamento."
            )
    st.subheader("Fluxo operacional")
    st.code(
        "sensores -> validação -> features -> estado digital -> modelo -> decisão -> monitoramento"
    )
    st.info(
        "Tracking, registry, versionamento e documentação conectam as camadas. "
        "A Consciência consolida essas evidências e retroalimenta todo o sistema."
    )


elif page == "Treinamento e tracking":
    st.title("Treinamento, tracking e registry")
    col1, col2 = st.columns(2)
    with col1:
        n_samples = st.number_input("Quantidade de leituras", 300, 20000, 1200, 100)
    with col2:
        seed = st.number_input("Semente", 0, 1_000_000, 42)

    if st.button("Treinar e registrar modelos", type="primary", disabled=not online):
        with st.spinner("Treinando três candidatos e registrando artefatos..."):
            try:
                result = api_post(
                    "/api/v1/train", {"n_samples": n_samples, "seed": seed}
                ).json()
                selected = result["selected_model"]
                st.success(
                    f"{selected['algorithm']} promovido como versão {selected['version']}"
                )
                st.json(selected)
            except requests.RequestException as error:
                st.error(f"Falha no treinamento: {error}")

    if online:
        runs = api_get("/api/v1/experiments").json()["runs"]
        if runs:
            frame = pd.DataFrame(runs)
            st.subheader("Histórico de runs")
            visible = [
                "run_id",
                "algorithm",
                "roc_auc",
                "f1",
                "recall_failure",
                "expected_cost",
                "data_sha256",
                "code_commit",
            ]
            st.dataframe(frame[[column for column in visible if column in frame]], use_container_width=True)
            chart = px.bar(
                frame,
                x="algorithm",
                y=["roc_auc", "recall_failure"],
                barmode="group",
                title="Comparação dos candidatos",
            )
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("Nenhuma execução registrada. Inicie o primeiro treinamento.")

        st.subheader("Registry")
        st.json(api_get("/api/v1/registry").json())


elif page == "Inferência e decisão":
    st.title("Estado do ativo, risco e recomendação")
    with st.form("prediction_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            machine_id = st.number_input("Máquina", 1, 100000, 42)
            plant = st.selectbox("Planta", ["SP", "MG", "PR"])
            motor_age_days = st.number_input("Idade do motor (dias)", 0, 5000, 1200)
        with col2:
            temperature = st.number_input("Temperatura média 24h", 0.0, 150.0, 82.5)
            vibration = st.number_input("Vibração RMS 24h", 0.0, 30.0, 4.2)
            current = st.number_input("Corrente média 24h", 0.0, 80.0, 19.5)
        with col3:
            load = st.number_input("Carga média 24h", 0.0, 1.5, 0.87)
            maintenance = st.selectbox("Manutenção nos últimos 30 dias", [0, 1])
        submit = st.form_submit_button("Calcular risco", type="primary", disabled=not online)

    if submit:
        payload = {
            "machine_id": machine_id,
            "plant": plant,
            "motor_age_days": motor_age_days,
            "temp_mean_24h": temperature,
            "vibration_rms_24h": vibration,
            "current_mean_24h": current,
            "load_mean_24h": load,
            "maintenance_last_30d": maintenance,
        }
        try:
            result = api_post("/api/v1/predict", payload).json()
            prediction = result["prediction"]
            decision = result["decision"]
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Risco de falha", f"{prediction['risk_probability']:.1%}")
            metric2.metric("Prioridade", decision["priority"].upper())
            metric3.metric("Modelo", prediction["model_version"])
            st.subheader("Recomendação")
            st.warning(decision["recommendation"])
            st.json(result)
        except requests.HTTPError as error:
            st.error(error.response.json().get("detail", str(error)))


elif page == "Monitoramento":
    st.title("Consciousness: drift e evolução")
    col1, col2, col3 = st.columns(3)
    with col1:
        n_samples = st.number_input("Leituras de produção", 100, 20000, 1000, 100)
    with col2:
        seed = st.number_input("Semente de produção", 0, 1_000_000, 99)
    with col3:
        drift = st.toggle("Simular drift", value=True)

    if st.button("Executar monitoramento", type="primary", disabled=not online):
        try:
            report = api_post(
                "/api/v1/monitor",
                {"n_samples": n_samples, "seed": seed, "drift": drift},
            ).json()
            if report["alerts_count"]:
                st.error(f"{report['alerts_count']} feature(s) em alerta")
            else:
                st.success("Nenhuma feature em alerta")
            frame = pd.DataFrame(
                [
                    {"feature": feature, **values}
                    for feature, values in report["features"].items()
                ]
            )
            figure = px.bar(
                frame,
                x="feature",
                y="psi",
                color="status",
                color_discrete_map={"ok": "#15803d", "alert": "#b91c1c"},
                title="Population Stability Index por feature",
            )
            figure.add_hline(y=0.2, line_dash="dash", line_color="orange")
            st.plotly_chart(figure, use_container_width=True)
            st.info(report["recommended_action"])
            st.dataframe(frame, use_container_width=True)
        except requests.HTTPError as error:
            st.error(error.response.json().get("detail", str(error)))


elif page == "Governança":
    st.title("Transparência, documentação e auditoria")
    st.caption(
        "Documentação viva: dados, modelo, aprovação, monitoramento e rastreabilidade "
        "devem mudar junto com o sistema."
    )
    model_tab, data_tab, trace_tab, registry_tab, audit_tab = st.tabs(
        ["Model Card", "Datasheet", "Rastreabilidade", "Registry", "Auditoria"]
    )
    if online:
        with model_tab:
            try:
                st.markdown(api_get("/api/v1/governance/model-card").text)
            except requests.HTTPError:
                st.warning("Execute o treinamento para gerar o model card.")
        with data_tab:
            try:
                st.markdown(api_get("/api/v1/governance/datasheet").text)
            except requests.HTTPError:
                st.warning("Execute o treinamento para gerar o datasheet.")
        with trace_tab:
            try:
                st.markdown(api_get("/api/v1/governance/traceability").text)
            except requests.HTTPError:
                st.warning("Execute o treinamento para gerar a rastreabilidade.")
        with registry_tab:
            st.json(api_get("/api/v1/registry").json())
        with audit_tab:
            events = api_get("/api/v1/governance/audit").json()["events"]
            if events:
                st.dataframe(pd.DataFrame(events), use_container_width=True)
            else:
                st.info("A trilha será preenchida conforme o sistema for utilizado.")


elif page == "Assistente de Consciência":
    st.title("Assistente da camada de Consciência")
    st.write(
        "Consulte versões, experimentos, dados, features, monitoramento e governança. "
        "O assistente responde a partir das evidências controladas da VITA."
    )
    st.warning(
        "O assistente explica e recomenda investigação. Ele não aprova modelos, "
        "não executa retreinamento e não controla equipamentos."
    )

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []

    suggestions = st.columns(3)
    suggestions[0].caption("Qual versão do modelo está em produção?")
    suggestions[1].caption("O último monitoramento detectou drift?")
    suggestions[2].caption("Quais são os limites de governança?")

    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Pergunte sobre as evidências da VITA", disabled=not online
    )
    if question:
        st.session_state.assistant_messages.append(
            {"role": "user", "content": question}
        )
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Consultando fontes controladas..."):
                try:
                    result = api_post(
                        "/api/v1/consciousness/assistant", {"question": question}
                    ).json()
                    answer = result["answer"]
                    st.markdown(answer)
                    st.caption(
                        f"Provedor: {result['provider']} | Fontes: "
                        f"{', '.join(result['sources'])}"
                    )
                    if result.get("provider_warning"):
                        st.info(result["provider_warning"])
                except requests.RequestException as error:
                    answer = f"Não foi possível consultar o assistente: {error}"
                    st.error(answer)
        st.session_state.assistant_messages.append(
            {"role": "assistant", "content": answer}
        )
