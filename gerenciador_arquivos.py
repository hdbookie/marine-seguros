import os
import json
import shutil
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st
from pathlib import Path

class GerenciadorArquivos:
    """Gerenciador de arquivos Excel com persistência local"""
    
    def __init__(self):
        # Use environment variable if available (for Railway volumes)
        data_dir = os.environ.get('DATA_PATH', 'data')
        self.caminho_armazenamento = Path(data_dir) / "arquivos_enviados"
        self.caminho_registro = Path(data_dir) / "registro_arquivos.json"
        
        # Initialize production flag and db_manager
        self.is_production = os.environ.get('RAILWAY_ENVIRONMENT') == 'production'
        self.db_manager = None
        
        # Criar diretórios se não existirem
        self.caminho_armazenamento.mkdir(parents=True, exist_ok=True)
        self.caminho_registro.parent.mkdir(parents=True, exist_ok=True)
        
        # Carregar ou criar registro
        self.registro = self._carregar_registro()
        
    def _carregar_registro(self) -> Dict:
        """Carregar registro de arquivos ou criar novo"""
        if self.caminho_registro.exists():
            try:
                with open(self.caminho_registro, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"arquivos": []}
        return {"arquivos": []}
    
    def _salvar_registro(self):
        """Salvar registro de arquivos"""
        with open(self.caminho_registro, 'w', encoding='utf-8') as f:
            json.dump(self.registro, f, ensure_ascii=False, indent=2)
    
    def _extrair_anos_do_arquivo(self, caminho_arquivo: str) -> List[int]:
        """Extrair anos disponíveis em um arquivo Excel"""
        anos = []
        try:
            excel_file = pd.ExcelFile(caminho_arquivo)
            
            # Verificar cada aba
            for sheet_name in excel_file.sheet_names:
                # Tentar identificar ano no nome da aba
                if sheet_name.isdigit() and 2000 <= int(sheet_name) <= 2030:
                    anos.append(int(sheet_name))
                # Procurar ano no formato 20XX
                elif any(str(year) in sheet_name for year in range(2018, 2030)):
                    for year in range(2018, 2030):
                        if str(year) in sheet_name:
                            anos.append(year)
                            break
            
            # Se não encontrou anos nas abas, tentar no nome do arquivo
            if not anos:
                nome_arquivo = os.path.basename(caminho_arquivo)
                # Procurar padrões como "2018_2023" ou "2024"
                import re
                anos_match = re.findall(r'20\d{2}', nome_arquivo)
                anos = [int(ano) for ano in anos_match]
                
        except Exception as e:
            st.error(f"Erro ao extrair anos: {str(e)}")
            
        return sorted(list(set(anos)))
    
    def enviar_arquivo(self, arquivo_enviado) -> bool:
        """Enviar e registrar novo arquivo Excel"""
        try:
            # Gerar ID único
            arquivo_id = f"arquivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Salvar arquivo
            caminho_destino = self.caminho_armazenamento / arquivo_enviado.name
            with open(caminho_destino, 'wb') as f:
                f.write(arquivo_enviado.getbuffer())
            
            # Extrair informações
            anos = self._extrair_anos_do_arquivo(str(caminho_destino))
            tamanho = os.path.getsize(caminho_destino)
            
            # Verificar se arquivo já existe no registro
            for arquivo in self.registro["arquivos"]:
                if arquivo["nome"] == arquivo_enviado.name:
                    # Atualizar arquivo existente
                    arquivo["data_envio"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    arquivo["tamanho"] = f"{tamanho // 1024}KB"
                    arquivo["anos_incluidos"] = anos
                    self._salvar_registro()
                    return True
            
            # Adicionar ao registro
            metadata = {
                "id": arquivo_id,
                "nome": arquivo_enviado.name,
                "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tamanho": f"{tamanho // 1024}KB",
                "anos_incluidos": anos,
                "caminho": str(caminho_destino)
            }
            
            self.registro["arquivos"].append(metadata)
            self._salvar_registro()
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao enviar arquivo: {str(e)}")
            return False
    
    def obter_anos_disponiveis(self) -> List[int]:
        """Obter todos os anos disponíveis em todos os arquivos"""
        anos = set()
        for arquivo in self.registro["arquivos"]:
            anos.update(arquivo.get("anos_incluidos", []))
        return sorted(list(anos))
    
    def obter_arquivos_por_anos(self, anos_selecionados: List[int]) -> List[Dict]:
        """Obter arquivos que contêm dados dos anos selecionados"""
        if not anos_selecionados:
            return self.registro["arquivos"]
            
        arquivos_filtrados = []
        for arquivo in self.registro["arquivos"]:
            anos_arquivo = set(arquivo.get("anos_incluidos", []))
            if anos_arquivo.intersection(anos_selecionados):
                arquivos_filtrados.append(arquivo)
                
        return arquivos_filtrados
    
    def obter_todos_arquivos(self) -> List[Dict]:
        """Obter todos os arquivos registrados"""
        return self.registro["arquivos"]
    
    def excluir_arquivo(self, arquivo_id: str) -> bool:
        """Excluir arquivo do sistema"""
        try:
            # Encontrar arquivo
            arquivo_para_excluir = None
            for arquivo in self.registro["arquivos"]:
                if arquivo["id"] == arquivo_id:
                    arquivo_para_excluir = arquivo
                    break
            
            if not arquivo_para_excluir:
                return False
            
            # Excluir arquivo físico
            caminho = Path(arquivo_para_excluir["caminho"])
            if caminho.exists():
                os.remove(caminho)
            
            # Remover do registro
            self.registro["arquivos"] = [
                arq for arq in self.registro["arquivos"] 
                if arq["id"] != arquivo_id
            ]
            self._salvar_registro()
            
            return True
            
        except Exception as e:
            st.error(f"Erro ao excluir arquivo: {str(e)}")
            return False
    
    def obter_caminhos_arquivos(self) -> List[str]:
        """Obter caminhos de todos os arquivos para processamento"""
        caminhos = []
        temp_files = []  # Track temp files for cleanup
        
        for arquivo in self.registro["arquivos"]:
            if arquivo.get("is_db_stored") and self.db_manager:
                # For DB-stored files, we need to extract them temporarily
                file_info = self.db_manager.get_file_from_db(arquivo["id"])
                if file_info:
                    # Save temporarily for processing
                    temp_path = self.caminho_armazenamento / f"temp_{arquivo['id']}_{arquivo['nome']}"
                    with open(temp_path, 'wb') as f:
                        f.write(file_info['file_data'])
                    caminhos.append(str(temp_path))
                    temp_files.append(temp_path)
            else:
                # For filesystem files
                if "caminho" in arquivo:
                    caminho = Path(arquivo["caminho"])
                    if caminho.exists():
                        caminhos.append(str(caminho))
        
        # Store temp files for later cleanup
        self._temp_files = temp_files
        return caminhos
    
    def cleanup_temp_files(self):
        """Clean up temporary files created for processing"""
        if hasattr(self, '_temp_files'):
            for temp_file in self._temp_files:
                try:
                    if temp_file.exists():
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file {temp_file}: {e}")
            self._temp_files = []
    
    def sincronizar_arquivos_existentes(self):
        """Sincronizar arquivos já existentes no diretório com o registro"""
        arquivos_no_disco = list(self.caminho_armazenamento.glob("*.xlsx"))
        arquivos_registrados = {arq["nome"] for arq in self.registro["arquivos"]}
        
        for arquivo_path in arquivos_no_disco:
            if arquivo_path.name not in arquivos_registrados:
                # Adicionar arquivo não registrado
                anos = self._extrair_anos_do_arquivo(str(arquivo_path))
                tamanho = os.path.getsize(arquivo_path)
                
                metadata = {
                    "id": f"arquivo_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{arquivo_path.stem}",
                    "nome": arquivo_path.name,
                    "data_envio": datetime.fromtimestamp(
                        arquivo_path.stat().st_mtime
                    ).strftime("%d/%m/%Y %H:%M"),
                    "tamanho": f"{tamanho // 1024}KB",
                    "anos_incluidos": anos,
                    "caminho": str(arquivo_path)
                }
                
                self.registro["arquivos"].append(metadata)
        
        self._salvar_registro()
    
    def set_database_manager(self, db_manager):
        """Set the database manager for production environment"""
        self.db_manager = db_manager
    
    def sync_from_database(self):
        """Sync files from database if in production mode"""
        if self.is_production and self.db_manager:
            # Get all files from database
            db_files = self.db_manager.list_files_in_db()
            
            # Update registry with database files
            db_file_ids = {f['id'] for f in db_files}
            registry_ids = {f['id'] for f in self.registro['arquivos']}
            
            # Add files that are in database but not in registry
            for db_file in db_files:
                if db_file['id'] not in registry_ids:
                    # Retrieve file to extract years
                    file_info = self.db_manager.get_file_from_db(db_file['id'])
                    if file_info:
                        anos = self._extrair_anos_do_arquivo_from_bytes(
                            file_info['file_data'], 
                            db_file['filename']
                        )
                        
                        metadata = {
                            "id": db_file['id'],
                            "nome": db_file['filename'],
                            "data_envio": db_file['created_at'],
                            "tamanho": f"{db_file['file_size'] // 1024}KB",
                            "anos_incluidos": anos,
                            "is_db_stored": True
                        }
                        
                        self.registro["arquivos"].append(metadata)
            
            self._salvar_registro()