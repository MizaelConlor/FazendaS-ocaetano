import streamlit as st
import json
import os
import datetime
import pandas as pd
import plotly.express as px  # Para criar gráficos interativos


# --- Constantes ---
PAGINA_REGISTRO = "Registro de operações"
PAGINA_EDITOR = "Editor operacional"
PAGINA_EXPORTAR_EXCEL = "Exportar Excel"
PAGINA_FINANCEIRO = "Financeiro"
PAGINA_GRAFICOS = "Gráficos"  # Novo menu de gráficos
SUBMENU_REGISTRAR_GASTO = "Registrar Novo Gasto"
SUBMENU_EDITAR_REGISTRO = "Editar Registro"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
TIPO_OPERACAO = ["Operação Aérea", "Operação Terrestre"]

# --- Funções de utilidade ---

def carregar_registros():
    """Carrega os registros do arquivo JSON e adiciona o ano, se necessário."""
    try:
        with open("registros.json", "r") as arquivo:
            registros = json.load(arquivo)
            ano_atual = datetime.datetime.now().year
        for registro in registros:
            if "ano" not in registro:
                registro["ano"] = ano_atual
        return registros
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_registros(registros):
    """Salva os registros no arquivo JSON."""
    try:
        with open("registros.json", "w") as arquivo:
            json.dump(registros, arquivo, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar registros: {e}")

def carregar_gastos():
    """Carrega os gastos do arquivo JSON."""
    try:
        with open("gastos.json", "r") as arquivo:
            gastos = json.load(arquivo)
        return gastos
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_gastos(gastos):
    """Salva os gastos no arquivo JSON."""
    try:
        with open("gastos.json", "w") as arquivo:
            json.dump(gastos, arquivo, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar gastos: {e}")

def validar_campos(dados):
    """Valida os campos do formulário."""
    erros = {}
    if dados.get("hectares_totais") is not None and dados["hectares_totais"] <= 0:
        erros["hectares_totais"] = "Hectares totais deve ser maior que 0"
    if "produtos" in dados:
        for i, produto in enumerate(dados["produtos"]):
            if produto.get("dose_por_hectare") is not None and produto["dose_por_hectare"] <= 0:
                erros[f"produto_{i}_dose"] = "Dose deve ser maior que 0"
    return erros

def gerar_campos_formulario(dados, finalizando=False):
    """Gera os campos do formulário, adaptando-se ao tipo de operação."""
    mes = st.selectbox("Mês", MESES, index=MESES.index(dados.get("mes", "Janeiro")) if "mes" in dados else 0,
                     disabled=finalizando, key="mes")
    ano_atual = datetime.datetime.now().year
    ano = st.number_input("Ano", min_value=2000, max_value=2100, value=dados.get("ano", ano_atual),
                         disabled=finalizando, key="ano")

    # Usamos st.session_state para manter o tipo de operação selecionado
    if "tipo_operacao" not in st.session_state:
        st.session_state.tipo_operacao = ""

    tipo_operacao = st.selectbox("Operação", [""] + TIPO_OPERACAO,
                                 index=TIPO_OPERACAO.index(st.session_state.tipo_operacao) + 1 if st.session_state.tipo_operacao else 0,
                                 key="tipo_operacao_select")

    st.session_state.tipo_operacao = tipo_operacao

    if tipo_operacao == "Operação Terrestre":
        nome_fazenda = st.text_input("Nome da fazenda", value=dados.get("nome_fazenda", ""), disabled=finalizando,
                                   key="nome_fazenda")
        talhao_aplicado = st.text_input("Talhão aplicado", value=dados.get("talhao_aplicado", ""),
                                       disabled=finalizando, key="talhao_aplicado")
        hectares_totais = st.number_input("Hectares totais", min_value=0.0, value=dados.get("hectares_totais", 0.0),
                                         disabled=finalizando, key="hectares_totais")
        cultura = st.text_input("Cultura", value=dados.get("cultura", ""), disabled=finalizando, key="cultura")
        trator = st.text_input("Trator", value=dados.get("trator", ""), disabled=finalizando, key="trator")
        implemento = st.text_input("Implemento", value=dados.get("implemento", ""), disabled=finalizando,
                                   key="implemento")

        # --- Campos de produtos para Operação Terrestre ---
        num_produtos_terrestre = st.number_input("Número de Produtos", min_value=0, value=dados.get("num_produtos_terrestre", 1), step=1, disabled=finalizando, key="num_produtos_terrestre")
        produtos_terrestre = []
        for i in range(num_produtos_terrestre):
            produto_atual = dados.get("produtos", [{}])[i] if i < len(dados.get("produtos", [])) else {"nome_produto": "", "dose": 0.0}
            with st.container():
                st.markdown(f"**Produto {i + 1}**")
                nome_produto = st.text_input("Nome do Produto", value=produto_atual.get("nome_produto", ""), disabled=finalizando, key=f"nome_produto_terrestre_{i}")
                dose = st.number_input("Dose", min_value=0.0, value=produto_atual.get("dose", 0.0), disabled=finalizando, key=f"dose_terrestre_{i}")
                produtos_terrestre.append({"nome_produto": nome_produto, "dose": dose})
        # --- Fim dos campos de produtos ---

        observacao = st.text_area("Observação", value=dados.get("observacao", ""), disabled=finalizando, key="observacao")
        responsavel = st.text_input("Responsável pela Operação", value=dados.get("responsavel", ""),
                                   disabled=finalizando, key="responsavel")

        return {
            "mes": mes,
            "ano": ano,
            "tipo_operacao": tipo_operacao,
            "nome_fazenda": nome_fazenda,
            "talhao_aplicado": talhao_aplicado,
            "hectares_totais": hectares_totais,
            "cultura": cultura,
            "trator": trator,
            "implemento": implemento,
            "produtos": produtos_terrestre,  # Usamos a lista de produtos terrestres
            "observacao": observacao,
            "responsavel": responsavel,
            "status": "Em aberto",
            "num_produtos_terrestre": num_produtos_terrestre #Adicionado para persistir o numero
        }

    elif tipo_operacao == "Operação Aérea":
        nome_fazenda = st.text_input("Nome da fazenda", value=dados.get("nome_fazenda", ""), disabled=finalizando,
                                   key="nome_fazenda")
        talhao_aplicado = st.text_input("Talhão aplicado", value=dados.get("talhao_aplicado", ""),
                                       disabled=finalizando, key="talhao_aplicado")
        hectares_totais = st.number_input("Hectares totais", min_value=0.0, value=dados.get("hectares_totais", 0.0),
                                         disabled=finalizando, key="hectares_totais")
        cultura = st.text_input("Cultura", value=dados.get("cultura", ""), disabled=finalizando, key="cultura")
        velocidade = st.number_input("Velocidade", min_value=0.0, value=dados.get("velocidade", 0.0), key="velocidade")
        altura = st.number_input("Altura", min_value=0.0, value=dados.get("altura", 0.0), key="altura")
        status = st.selectbox("Status", ["Em aberto", "Finalizado"],
                             index=0 if dados.get("status", "Em aberto") == "Em aberto" else 1, disabled=finalizando,
                             key="status")
        num_produtos = st.number_input("Número de Produtos", min_value=0,  value= len(dados.get("produtos",[{}])), #Mudança aqui
                                      step=1, disabled=finalizando, key="num_produtos")

        produtos = []
        for i in range(num_produtos):
            produto_atual = dados.get("produtos", [{}])[i] if i < len(dados.get("produtos", [])) else {
                "nome": "", "dose_por_hectare": 0.0}
            with st.container():
                st.markdown(f"**Produto {i + 1}**")
                nome_produto = st.text_input("Nome do Produto", value=produto_atual.get("nome", ""),
                                            disabled=finalizando, key=f"produto_nome_{i}")
                dose_por_hectare = st.number_input("Dose por Hectare", min_value=0.0,
                                                 value=produto_atual.get("dose_por_hectare", 0.0),
                                                 disabled=finalizando, key=f"produto_dose_{i}")
                dose_total = hectares_totais * dose_por_hectare
                st.write(f"Dose Total: {dose_total:.2f}")
                produtos.append(
                    {"nome": nome_produto, "dose_por_hectare": dose_por_hectare, "dose_total": dose_total})

        aeronave = st.text_input("Aeronave", value=dados.get("aeronave", ""), disabled=finalizando, key="aeronave")
        responsavel = st.text_input("Responsável pela Aplicação", value=dados.get("responsavel", ""),
                                   disabled=finalizando, key="responsavel")

        return {
            "mes": mes,
            "ano": ano,
            "tipo_operacao": tipo_operacao,
            "nome_fazenda": nome_fazenda,
            "talhao_aplicado": talhao_aplicado,
            "hectares_totais": hectares_totais,
            "cultura": cultura,
            "velocidade": velocidade,
            "altura": altura,
            "status": status,
            "produtos": produtos,
            "aeronave": aeronave,
            "responsavel": responsavel,
        }
    else:
        return {
            "mes": mes,
            "ano": ano,
            "tipo_operacao": tipo_operacao,
            "produtos": []
        }

def exibir_barra_lateral():
    """Exibe a barra lateral."""
    with st.sidebar:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
                background-color:rgb(26, 28, 26);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
            }
            .stButton>button {
                width: 100%;
                margin: 5px 0;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                cursor: pointer;
            }
            .stButton>button:hover {
                background-color: #45a049;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<h2 style='color: white;'>FAZENDA SÃO CAETANO</h2>", unsafe_allow_html=True)

        if st.button("Registro de operações"):
            st.session_state.pagina_selecionada = PAGINA_REGISTRO
        if st.button("Editor operacional"):
            st.session_state.pagina_selecionada = PAGINA_EDITOR
        if st.button("Exportar Excel"):
            st.session_state.pagina_selecionada = PAGINA_EXPORTAR_EXCEL
        if st.button("Financeiro"):
            st.session_state.pagina_selecionada = PAGINA_FINANCEIRO
        if st.button("Gráficos"):  # Novo botão para a página de gráficos
            st.session_state.pagina_selecionada = PAGINA_GRAFICOS

def exibir_pagina_registro():
    """Exibe a página de registro."""
    st.header("Registro de operações")

    if "registro_editando" in st.session_state:
        dados_edicao = st.session_state.registro_editando
        st.subheader("Editando Registro")
        dados = gerar_campos_formulario(dados_edicao)
        if st.button("Salvar edição", type="secondary"):
            erros = validar_campos(dados)
            if not erros:
                registros = carregar_registros()
                index_edicao = registros.index(st.session_state.registro_editando)
                registros[index_edicao] = dados
                del st.session_state.registro_editando
                salvar_registros(registros)
                st.success("Registro editado com sucesso!")
                st.session_state.pagina_selecionada = PAGINA_EDITOR
    else:
        st.subheader("Novo Registro")
        dados = gerar_campos_formulario({})
        if st.button("Criar Registro"):
            erros = validar_campos(dados)
            if not erros:
                registros = carregar_registros()
                registros.append(dados)
                salvar_registros(registros)
                st.success("Registro criado com sucesso!")
                st.session_state.pagina_selecionada = PAGINA_EDITOR
            else:
                for erro in erros.values():
                    st.error(erro)

def exibir_pagina_editor():
    """Exibe a página do editor, separando por anos e meses."""
    st.header("Editor Operacional")
    registros = carregar_registros()

    registros_por_ano = {}
    for registro in registros:
        ano = registro['ano']
        mes = registro['mes']
        if ano not in registros_por_ano:
            registros_por_ano[ano] = {}
        if mes not in registros_por_ano[ano]:
            registros_por_ano[ano][mes] = []
        registros_por_ano[ano][mes].append(registro)

    anos = sorted(registros_por_ano.keys(), reverse=True)
    ano_selecionado = st.radio("Selecione o Ano", anos, horizontal=True)

    if ano_selecionado:
        st.subheader(f"Registros de {ano_selecionado}")
        for mes in MESES:
            if mes in registros_por_ano[ano_selecionado]:
                with st.expander(f"Mês: {mes}", expanded=False):
                    for i, registro in enumerate(registros_por_ano[ano_selecionado][mes]):
                        st.markdown(
                            f"""
                            <style>
                            .registro-container-{ano_selecionado}-{mes}-{registro.get('nome_fazenda', 'N/A')}-{registro.get('talhao_aplicado', 'N/A')} {{
                                border: 1px solid #4CAF50;
                                border-radius: 5px;
                                padding: 10px;
                                margin-bottom: 10px;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                text-align: center;
                                width: 95%;
                                margin-left: auto;
                                margin-right: auto;
                            }}
                            .registro-container-{ano_selecionado}-{mes}-{registro.get('nome_fazenda', 'N/A')}-{registro.get('talhao_aplicado', 'N/A')} .stButton>button {{
                                background-color: #4CAF50;
                                color: white;
                                border: none;
                                border-radius: 5px;
                                padding: 5px 10px;
                                cursor: pointer;
                            }}
                            .registro-container-{ano_selecionado}-{mes}-{registro.get('nome_fazenda', 'N/A')}-{registro.get('talhao_aplicado', 'N/A')} .stButton>button:hover {{
                                background-color: #45a049;
                            }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                        with st.container():
                            st.markdown(
                                f"<div class='registro-container-{ano_selecionado}-{mes}-{registro.get('nome_fazenda', 'N/A')}-{registro.get('talhao_aplicado', 'N/A')}'>",
                                unsafe_allow_html=True)
                            st.write(f"**Tipo de Operação:** {registro.get('tipo_operacao', 'N/A')}")
                            if registro.get('tipo_operacao') == 'Operação Terrestre':
                                st.write(
                                    f"**Fazenda:** {registro.get('nome_fazenda', 'N/A')}, **Talhão:** {registro.get('talhao_aplicado', 'N/A')}")
                                st.write(
                                    f"**Hectares:** {registro.get('hectares_totais', 'N/A')}, **Cultura:** {registro.get('cultura', 'N/A')}")
                                st.write(
                                    f"**Trator:** {registro.get('trator', 'N/A')}, **Implemento:** {registro.get('implemento', 'N/A')}")
                                st.write("**Produtos:**")
                                for produto in registro.get('produtos', []):
                                    st.write(
                                        f"- {produto.get('nome_produto', 'N/A')}: Dose: {produto.get('dose', 'N/A')}")
                                st.write(f"**Observação:** {registro.get('observacao', 'N/A')}")
                                st.write(f"**Responsável:** {registro.get('responsavel', 'N/A')}")

                            elif registro.get('tipo_operacao') == 'Operação Aérea':
                                st.write(
                                    f"**Fazenda:** {registro.get('nome_fazenda', 'N/A')}, **Talhão:** {registro.get('talhao_aplicado', 'N/A')}, **Status:** {registro.get('status', 'N/A')}")
                                st.write(
                                    f"**Hectares:** {registro.get('hectares_totais', 'N/A')}, **Cultura:** {registro.get('cultura', 'N/A')}")
                                st.write(
                                    f"**Velocidade:** {registro.get('velocidade', 'N/A')}, **Altura:** {registro.get('altura', 'N/A')}")
                                st.write("**Produtos:**")
                                for produto in registro.get('produtos', []):
                                    st.write(
                                        f"- {produto.get('nome', 'N/A')}: {produto.get('dose_por_hectare', 'N/A')} (Dose total: {produto.get('dose_total', 'N/A'):.2f}")
                                st.write(f"**Aeronave:** {registro.get('aeronave', 'N/A')}")
                                st.write(f"**Responsável:** {registro.get('responsavel', 'N/A')}")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("Editar",
                                             key=f"editar_{registro.get('nome_fazenda', 'N/A')}_{registro.get('talhao_aplicado', 'N/A')}_{registro.get('mes', 'N/A')}_{ano_selecionado}_{i}"):
                                    st.session_state.registro_editando = registro
                                    st.session_state.pagina_selecionada = PAGINA_REGISTRO
                                    st.rerun()
                            with col2:
                                if registro.get('tipo_operacao') == 'Operação Aérea' and registro.get('status') == "Em aberto":
                                    if st.button("Finalizar",
                                                 key=f"finalizar_{registro.get('nome_fazenda', 'N/A')}_{registro.get('talhao_aplicado', 'N/A')}_{registro.get('mes', 'N/A')}_{ano_selecionado}_{i}"):
                                        registro['status'] = "Finalizado"
                                        salvar_registros(registros)
                                        st.success("Registro finalizado com sucesso!")
                                        st.rerun()
                            with col3:
                                if st.button("Excluir",
                                             key=f"excluir_{registro.get('nome_fazenda', 'N/A')}_{registro.get('talhao_aplicado', 'N/A')}_{registro.get('mes', 'N/A')}_{ano_selecionado}_{i}"):
                                    registros.remove(registro)
                                    salvar_registros(registros)
                                    st.success("Registro excluído com sucesso!")
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info(f"Nenhum registro para {mes}/{ano_selecionado}.")

def exibir_pagina_exportar_excel():
    """Exibe a página de exportação para Excel."""
    st.header("Exportar Operações para Excel")
    registros = carregar_registros()

    if not registros:
        st.info("Nenhum registro para exportação")
        return

    # Converter registros para DataFrame
    dados_para_df = []
    for registro in registros:
        if registro.get('tipo_operacao') == "Operação Terrestre":
            dados_para_df.append({
                'Mês': registro.get('mes', 'N/A'),
                'Ano': registro.get('ano', 'N/A'),
                'Tipo de Operação': registro.get('tipo_operacao', 'N/A'),
                'Fazenda': registro.get('nome_fazenda', 'N/A'),
                'Talhão': registro.get('talhao_aplicado', 'N/A'),
                'Hectares': registro.get('hectares_totais', 'N/A'),
                'Cultura': registro.get('cultura', 'N/A'),
                'Trator': registro.get('trator', 'N/A'),
                'Implemento': registro.get('implemento', 'N/A'),
                'Produto': registro.get('nome_produto', 'N/A'),
                'Dose': registro.get('dose', 'N/A'),
                'Observação': registro.get('observacao', 'N/A'),
                'Responsável': registro.get('responsavel', 'N/A'),
                'Status': registro.get('status', 'N/A')
            })
        elif registro.get('tipo_operacao') == 'Operação Aérea':
            produtos_str = ""
            for produto in registro.get('produtos', []):
                produtos_str += f"{produto.get('nome', 'N/A')}: {produto.get('dose_por_hectare', 'N/A')} (Dose total: {produto.get('dose_total', 'N/A'):.2f}); "

            dados_para_df.append({
                'Mês': registro.get('mes', 'N/A'),
                'Ano': registro.get('ano', 'N/A'),
                'Tipo de Operação': registro.get('tipo_operacao', 'N/A'),
                'Fazenda': registro.get('nome_fazenda', 'N/A'),
                'Talhão': registro.get('talhao_aplicado', 'N/A'),
                'Hectares': registro.get('hectares_totais', 'N/A'),
                'Cultura': registro.get('cultura', 'N/A'),
                'Velocidade': registro.get('velocidade', 'N/A'),
                'Altura': registro.get('altura', 'N/A'),
                'Produtos': produtos_str,
                'Aeronave': registro.get('aeronave', 'N/A'),
                'Responsável': registro.get('responsavel', 'N/A'),
                'Status': registro.get('status', 'N/A')
            })

    df = pd.DataFrame(dados_para_df)

    # Exibir o DataFrame na interface
    st.dataframe(df)

    # Botão para exportar para Excel
    if st.button("Exportar para Excel"):
        excel_file = "operacoes_exportadas.xlsx"
        df.to_excel(excel_file, index=False)

        with open(excel_file, "rb") as arquivo:
            st.download_button(
                label="Baixar arquivo Excel",
                data=arquivo,
                file_name=excel_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        os.remove(excel_file)

def exibir_pagina_financeiro():
    """Exibe a página financeira."""
    st.header("Financeiro")
    st.write("Aqui você pode gerenciar as informações financeiras relacionadas às operações.")

    # Submenus para a página financeira (em colunas)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(SUBMENU_REGISTRAR_GASTO):
            st.session_state.submenu_financeiro = SUBMENU_REGISTRAR_GASTO
    with col2:
        if st.button(SUBMENU_EDITAR_REGISTRO):
            st.session_state.submenu_financeiro = SUBMENU_EDITAR_REGISTRO

    # Verifica qual submenu está ativo
    submenu_ativo = st.session_state.get("submenu_financeiro", SUBMENU_REGISTRAR_GASTO)

    if submenu_ativo == SUBMENU_REGISTRAR_GASTO:
        st.subheader("Registrar Novo Gasto")
        with st.form("form_registrar_gasto"):
            descricao = st.text_input("Descrição do Gasto")
            valor = st.number_input("Valor do Gasto", min_value=0.0, format="%.2f")
            categoria = st.selectbox("Categoria", ["Produtos", "Combustível", "Manutenção", "Outros"])
            data = st.date_input("Data do Gasto")
            if st.form_submit_button("Registrar Gasto"):
                gastos = carregar_gastos()
                novo_gasto = {
                    "descricao": descricao,
                    "valor": valor,
                    "categoria": categoria,
                    "data": data.strftime("%Y-%m-%d")
                }
                gastos.append(novo_gasto)
                salvar_gastos(gastos)
                st.success("Gasto registrado com sucesso!")

    elif submenu_ativo == SUBMENU_EDITAR_REGISTRO:
        st.subheader("Editar Registro de Gastos")
        gastos = carregar_gastos()
        if not gastos:
            st.info("Nenhum gasto registrado.")
        else:
            # Organizar gastos por ano e mês
            gastos_por_ano_mes = {}
            for gasto in gastos:
                data = datetime.datetime.strptime(gasto["data"], "%Y-%m-%d")
                ano = data.year
                mes = MESES[data.month - 1]  # Ajuste para índice base 0
                if ano not in gastos_por_ano_mes:
                    gastos_por_ano_mes[ano] = {}
                if mes not in gastos_por_ano_mes[ano]:
                    gastos_por_ano_mes[ano][mes] = []
                gastos_por_ano_mes[ano][mes].append(gasto)

            # Selecionar ano e mês
            anos = sorted(gastos_por_ano_mes.keys(), reverse=True)
            ano_selecionado = st.selectbox("Selecione o Ano", anos)
            if ano_selecionado:
                meses = sorted(gastos_por_ano_mes[ano_selecionado].keys(), key=lambda x: MESES.index(x))
                mes_selecionado = st.selectbox("Selecione o Mês", meses)
                if mes_selecionado:
                    gastos_mes = gastos_por_ano_mes[ano_selecionado][mes_selecionado]
                    for i, gasto in enumerate(gastos_mes):
                        with st.expander(f"Gasto {i + 1}: {gasto['descricao']}"):
                            with st.form(f"form_editar_gasto_{i}"):
                                descricao = st.text_input("Descrição do Gasto", value=gasto["descricao"])
                                valor = st.number_input("Valor do Gasto", min_value=0.0, value=gasto["valor"], format="%.2f")
                                categoria = st.selectbox("Categoria", ["Produtos", "Combustível", "Manutenção", "Outros"], index=["Produtos", "Combustível", "Manutenção", "Outros"].index(gasto["categoria"]))
                                data = st.date_input("Data do Gasto", value=datetime.datetime.strptime(gasto["data"], "%Y-%m-%d"))
                                if st.form_submit_button("Salvar Alterações"):
                                    gasto["descricao"] = descricao
                                    gasto["valor"] = valor
                                    gasto["categoria"] = categoria
                                    gasto["data"] = data.strftime("%Y-%m-%d")
                                    salvar_gastos(gastos)
                                    st.success("Gasto atualizado com sucesso!")
                                if st.form_submit_button("Excluir Gasto"):
                                    gastos.remove(gasto)
                                    salvar_gastos(gastos)
                                    st.success("Gasto excluído com sucesso!")
                                    st.rerun()

def exibir_pagina_graficos():
    """Exibe a página de gráficos."""
    st.header("Gráficos")

    # Carregar dados
    registros = carregar_registros()
    gastos = carregar_gastos()

    # Selecionar ano e mês
    anos_disponiveis = sorted(list(set([registro["ano"] for registro in registros] + [datetime.datetime.strptime(gasto["data"], "%Y-%m-%d").year for gasto in gastos])), reverse=True)
    ano_selecionado = st.selectbox("Selecione o Ano", anos_disponiveis)

    meses_disponiveis = MESES
    mes_selecionado = st.selectbox("Selecione o Mês", meses_disponiveis)

    # Filtrar dados pelo ano e mês selecionados
    registros_filtrados = [registro for registro in registros if registro["ano"] == ano_selecionado and registro["mes"] == mes_selecionado]
    gastos_filtrados = [gasto for gasto in gastos if datetime.datetime.strptime(gasto["data"], "%Y-%m-%d").year == ano_selecionado and MESES[datetime.datetime.strptime(gasto["data"], "%Y-%m-%d").month - 1] == mes_selecionado]

    # Gráfico 1: Gastos Mensais por Categoria
    if gastos_filtrados:
        df_gastos = pd.DataFrame(gastos_filtrados)
        df_gastos_agrupados = df_gastos.groupby("categoria")["valor"].sum().reset_index()
        total_gastos = df_gastos_agrupados["valor"].sum()
        fig_gastos = px.pie(df_gastos_agrupados, values="valor", names="categoria", title=f"Gastos Mensais em {mes_selecionado}/{ano_selecionado}",
                            color_discrete_sequence=px.colors.sequential.Oranges)  # Cor laranja
        fig_gastos.update_traces(hoverinfo='label+value', textinfo='none',  # Remove porcentagens e rótulos
                                textposition='inside', textfont_size=15,
                                insidetextorientation='radial')
        fig_gastos.update_layout(annotations=[dict(text=f"R$ {total_gastos:.2f}", x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig_gastos)
    else:
        st.info("Nenhum gasto registrado para o mês e ano selecionados.")

    # Gráfico 2: Hectares Realizados por Tipo de Operação
    if registros_filtrados:
        df_hectares = pd.DataFrame(registros_filtrados)
        df_hectares_agrupados = df_hectares.groupby("tipo_operacao")["hectares_totais"].sum().reset_index()
        total_hectares = df_hectares_agrupados["hectares_totais"].sum()
        fig_hectares = px.pie(df_hectares_agrupados, values="hectares_totais", names="tipo_operacao", title=f"Hectares Realizados em {mes_selecionado}/{ano_selecionado}",
                              color_discrete_sequence=px.colors.sequential.Greens)  # Cor verde
        fig_hectares.update_traces(hoverinfo='label+value', textinfo='none',  # Remove porcentagens e rótulos
                                  textposition='inside', textfont_size=15,
                                  insidetextorientation='radial')
        fig_hectares.update_layout(annotations=[dict(text=f"{total_hectares:.2f} ha", x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig_hectares)
    else:
        st.info("Nenhum registro de operação para o mês e ano selecionados.")

def main():
    """Função principal."""
    st.set_page_config(layout="wide")
    if "pagina_selecionada" not in st.session_state:
        st.session_state.pagina_selecionada = PAGINA_REGISTRO
    if "erros" not in st.session_state:
        st.session_state.erros = {}

    exibir_barra_lateral()

    if st.session_state.pagina_selecionada == PAGINA_REGISTRO:
        exibir_pagina_registro()
    elif st.session_state.pagina_selecionada == PAGINA_EDITOR:
        exibir_pagina_editor()
    elif st.session_state.pagina_selecionada == PAGINA_EXPORTAR_EXCEL:
        exibir_pagina_exportar_excel()
    elif st.session_state.pagina_selecionada == PAGINA_FINANCEIRO:
        exibir_pagina_financeiro()
    elif st.session_state.pagina_selecionada == PAGINA_GRAFICOS:  # Nova condição para a página de gráficos
        exibir_pagina_graficos()

if __name__ == "__main__":
    main()
