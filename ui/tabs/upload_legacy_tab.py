"""
Upload Tab - Legacy version extracted from app.py
Preserves all original functionality while organizing code
"""

import streamlit as st
from core.financial_processor import FinancialProcessor
from utils.legacy_helpers import (
    sync_processed_to_extracted,
    get_category_icon,
    get_category_name
)


def render_upload_tab(db, use_unified_extractor=True, show_anomalies=True):
    """Render the upload tab with file management and processing"""
    
    st.header("📊 Gerenciamento de Dados Financeiros")
    
    # Show last upload info
    last_upload = db.get_last_upload_info()
    if last_upload:
        upload_time = last_upload['created_at']
        username = last_upload['username']
        files = last_upload['files']
        
        st.info(f"""
        📊 **Dados Compartilhados**  
        Última atualização: {upload_time}  
        Por: {username}  
        Arquivos: {len(files)} arquivo(s)
        """)
    else:
        st.info("📊 **Dados Compartilhados** - Nenhum dado carregado ainda")
    
    # Show upload history
    with st.expander("📜 Histórico de Uploads", expanded=False):
        upload_history = db.get_upload_history(limit=10)
        if upload_history:
            for upload in upload_history:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{upload['username']}**")
                    st.caption(upload['email'])
                with col2:
                    st.write(f"📅 {upload['created_at']}")
                    files_str = ", ".join(upload['files']) if isinstance(upload['files'], list) else str(upload['files'])
                    st.caption(f"Arquivos: {files_str}")
                with col3:
                    st.write(f"Tipo: {upload['upload_type']}")
                st.markdown("---")
        else:
            st.info("Nenhum histórico de upload disponível")

    # File management bar
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        # Year filter
        anos_disponiveis = st.session_state.file_manager.obter_anos_disponiveis() if hasattr(st.session_state, 'file_manager') else []
        if anos_disponiveis:
            anos_selecionados = st.multiselect(
                "Filtrar por Anos:",
                options=sorted(anos_disponiveis),
                default=sorted(anos_disponiveis),
                key="file_year_filter"
            )
        else:
            anos_selecionados = []

    with col2:
        if st.button("🔄 Atualizar", help="Atualizar lista de arquivos"):
            if hasattr(st.session_state, 'file_manager'):
                st.session_state.file_manager.sincronizar_arquivos_existentes()
            st.rerun()

    with col3:
        gerenciar_mode = st.checkbox("📁 Gerenciar", help="Ativar modo de gerenciamento")

    st.markdown("---")

    # Upload section - Admin only
    if st.session_state.user and st.session_state.user.get('role') == 'admin':
        with st.expander("➕ Enviar Novos Arquivos", expanded=False):
            uploaded_files = st.file_uploader(
            "Selecione arquivos Excel",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="Formatos suportados: .xlsx, .xls | Você pode selecionar múltiplos arquivos"
        )

        if uploaded_files:
            if st.button(f"📤 Enviar {len(uploaded_files)} arquivo(s)"):
                success_count = 0
                error_count = 0
        
                for uploaded_file in uploaded_files:
                    if hasattr(st.session_state, 'file_manager') and st.session_state.file_manager.enviar_arquivo(uploaded_file):
                        success_count += 1
                    else:
                        error_count += 1
        
                if success_count > 0:
                    st.success(f"✅ {success_count} arquivo(s) enviado(s) com sucesso!")
                if error_count > 0:
                    st.error(f"❌ {error_count} arquivo(s) com erro")
        
                st.rerun()
    else:
        st.info("🔒 Apenas administradores podem fazer upload de arquivos.")

    # Display available files
    st.subheader("📁 Fontes de Dados Disponíveis")

    # Get files filtered by years
    if anos_selecionados and hasattr(st.session_state, 'file_manager'):
        arquivos = st.session_state.file_manager.obter_arquivos_por_anos(anos_selecionados)
    elif hasattr(st.session_state, 'file_manager'):
        arquivos = st.session_state.file_manager.obter_todos_arquivos()
    else:
        arquivos = []

    # Clear all button when in manage mode - Admin only
    if gerenciar_mode and arquivos and st.session_state.user and st.session_state.user.get('role') == 'admin':
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Limpar Todos", type="secondary", help="Remover todos os arquivos", use_container_width=True):
                if hasattr(st.session_state, 'file_manager'):
                    for arquivo in arquivos:
                        st.session_state.file_manager.excluir_arquivo(arquivo['id'])
                st.success("Todos os arquivos foram removidos!")
                st.rerun()
    
    # Add database clear button for admin
    if st.session_state.user and st.session_state.user.get('role') == 'admin':
        if st.button("🔄 Limpar Banco de Dados Completo", type="secondary", help="Remove todos os dados históricos do banco"):
            with st.spinner("Limpando banco de dados..."):
                if db.clear_all_data():
                    st.success("✅ Banco de dados completamente limpo!")
                    # Clear session state too
                    for key in list(st.session_state.keys()):
                        if key not in ['user', 'users', 'file_manager']:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error("❌ Erro ao limpar banco de dados")

    if arquivos:
        for arquivo in arquivos:
            with st.container():
                col1, col2 = st.columns([4, 1])
        
                with col1:
                    st.markdown(f"### ✅ {arquivo['nome']}")
            
                    # File info
                    anos_str = ", ".join(map(str, sorted(arquivo['anos_incluidos'])))
                    st.markdown(f"""
                    **Anos:** {anos_str}  
                    **Enviado:** {arquivo['data_envio']} | **Tamanho:** {arquivo['tamanho']}
                    """)
        
                with col2:
                    if gerenciar_mode and st.session_state.user and st.session_state.user.get('role') == 'admin':
                        # Create unique key using file ID and a counter to handle duplicates
                        button_key = f"del_{arquivo['id']}_{id(arquivo)}"
                        if st.button("🗑️ Excluir", key=button_key):
                            if hasattr(st.session_state, 'file_manager') and st.session_state.file_manager.excluir_arquivo(arquivo['id']):
                                st.success("Arquivo excluído!")
                                st.rerun()
        
                st.markdown("---")
    else:
        st.info("📭 Nenhum arquivo encontrado. Envie arquivos Excel para começar.")

    # Process data button
    if arquivos:
        st.markdown("### 🚀 Processar Dados")
        
        # Show warning about shared data update
        st.warning("⚠️ **Atenção**: Processar novos dados atualizará os dados para todos os usuários do sistema.")

        if st.button("Analisar Dados Financeiros", type="primary", use_container_width=True):
            # Clear old data before processing
            keys_to_clear = ['processed_data', 'extracted_data', 'monthly_data', 'financial_data', 'gemini_insights', 'unified_data']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            # Also clear database cache
            db.clear_session_data()
            
            # Track uploaded files for history - extract file names from arquivos
            uploaded_file_names = []
            for arquivo in arquivos:
                if isinstance(arquivo, dict) and 'nome' in arquivo:
                    uploaded_file_names.append(arquivo['nome'])
                elif hasattr(arquivo, 'name'):
                    uploaded_file_names.append(arquivo.name)
            st.session_state.uploaded_files = uploaded_file_names
            
            with st.spinner("Processando arquivos para todos os usuários..."):
                processor = FinancialProcessor()
        
                # Get file paths
                file_paths = st.session_state.file_manager.obter_caminhos_arquivos() if hasattr(st.session_state, 'file_manager') else []
        
                # Load Excel files
                excel_data = processor.load_excel_files(file_paths)
        
                # Use unified extractor for all data
                consolidated_df, unified_data = processor.consolidate_all_years(excel_data)
                
                # Store unified data for both dashboard and micro analysis
                st.session_state.unified_data = unified_data
        
                # Check if data extraction was successful
                if consolidated_df.empty:
                    st.error("❌ Não foi possível extrair dados dos arquivos Excel.")
                    st.info("Verifique se os arquivos contêm as seguintes informações:")
                    st.markdown("""
                    - Sheets com anos (ex: 2018, 2019, 2020, etc.)
                    - Linha com 'FATURAMENTO' para receitas
                    - Linha com 'CUSTOS VARIÁVEIS' para custos
                    - Colunas com meses (JAN, FEV, MAR, etc.)
                    - Coluna 'ANUAL' para totais anuais
                    """)
                else:
                    consolidated_df = processor.calculate_growth_metrics(consolidated_df)
            
                    # Get monthly data
                    monthly_df = processor.get_monthly_data(excel_data)
            
                    # Store in session state - use unified data
                    st.session_state.processed_data = {
                        'raw_data': unified_data,  # Unified data has both core metrics and line items
                        'consolidated': consolidated_df,
                        'summary': processor.get_financial_summary(consolidated_df),
                        'anomalies': processor.detect_anomalies(consolidated_df) if show_anomalies else []
                    }
                    st.session_state.monthly_data = monthly_df
                    
                    # Store extracted_data for compatibility
                    st.session_state.extracted_data = unified_data
            
                    # Sync to extracted_data format and save to database
                    sync_processed_to_extracted()
            
                    # Save to database
                    try:
                        print("DEBUG: Attempting to save to database...")
                        print(f"DEBUG: processed_data exists: {hasattr(st.session_state, 'processed_data')}")
                        print(f"DEBUG: monthly_data exists: {hasattr(st.session_state, 'monthly_data')}")
                        if hasattr(st.session_state, 'processed_data') and st.session_state.processed_data:
                            print(f"DEBUG: processed_data keys: {list(st.session_state.processed_data.keys())}")
                        db.auto_save_state(st.session_state)
                        save_success = True
                        print("DEBUG: Save completed successfully")
                    except Exception as e:
                        st.error(f"⚠️ Erro ao salvar no banco de dados: {str(e)}")
                        save_success = False
                        print(f"DEBUG: Save failed with error: {str(e)}")
                        import traceback
                        traceback.print_exc()
            
                    # Show unified data results
                    if unified_data:
                        # Show summary of detected categories
                        all_categories = set()
                        for year_data in unified_data.values():
                            if 'categories' in year_data:
                                all_categories.update(year_data['categories'].keys())
                
                        st.success(f"✅ Dados processados e compartilhados com sucesso!")
                        if save_success:
                            st.success("💾 Dados salvos e disponíveis para todos os usuários!")
                        st.info(f"📊 {len(consolidated_df)} anos encontrados | "
                               f"📁 {len(all_categories)} categorias detectadas | "
                               f"👥 Disponível para todos os usuários")
                
                        # Show detected categories
                        with st.expander("Categorias Detectadas"):
                            cols = st.columns(3)
                            for idx, category in enumerate(sorted(all_categories)):
                                col_idx = idx % 3
                                cols[col_idx].write(f"{get_category_icon(category)} {get_category_name(category)}")