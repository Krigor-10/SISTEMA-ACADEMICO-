import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import pandas as pd
import os
import io

# --- CONFIGURAÇÕES GLOBAIS ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Caminho do arquivo CSV
# CORREÇÃO: Usamos r"..." para que as barras invertidas do caminho do Windows sejam interpretadas corretamente.
CAMINHO_ARQUIVO = r"C:\\Users\\Krigor\\OneDrive - UNIP\\Área de Trabalho\\HEITOR PIM ATUALIZADO\\output\\sistemaAcademico.csv" 

# Dicionário de perguntas e respostas para o Chatbot (Inalterado)
respostas = {
    "Quais cursos posso me matrícular?": "As aulas disponibilizadas para esse semestre são Educação Ambiental, Redes de Computadores, Banco de Dados, Inteligência Artificial, Ciberssegurança, Programação Orientada a Objetos, Python, Java, C / C++ e Análise e Projeto de Sistemas.",
    "Como calcular a média final?": "A média é calculada com média ponderada, onde cada prova tem peso 4 e o trabalho final tem peso 2. A fórmula é: (NP1 * 4 + NP2 * 4 + PIM * 2) / 10.",
    "Quais os horários que posso fazer as aulas?": "A partir do momento em que você se matricula em uma disciplina, tem um período de 6 meses para completar o curso.",
    "Quem é o coordenador geral?": "O coordenador geral é o Prof. Cordeiro, escolhido dentro da sua instituição.",
    "Qual é o prazo para entrega dos trabalhos?": "A data de entrega dos trabalhos é até o final do semestre.",
    "Qual é o conteúdo da aula de segunda-feira?": "Na segunda-feira, estudamos Programação Orientada a Objetos e Java.",
    "Qual é o conteúdo da aula de terça-feira?": "Na terça-feira, estudamos Educação Ambiental e C / C++.",
    "Qual é o conteúdo da aula de quarta-feira?": "Na quarta-feira, estudamos Redes de Computadores e Análise e Projeto de Sistemas.",
    "Qual é o conteúdo da aula de quinta-feira?": "Na quarta-feira, estudamos Banco de Dados e Ciberssegurança.",
    "Qual é o conteúdo da aula de sexta-feira?": "Na sexta-feira, estudamos Inteligência Artificial e Python.",
    "Como funciona a avaliação do curso?": "A avaliação são duas provas de 12 questões, sendo 10 alternativas e 2 dissertativas e um trabalho final.",
    "Quais são os horários de atendimento do coordenador?": "O Prof. Cordeiro atende às quartas, das 14h às 16h."
}

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---
def carregar_tabela(caminho_arquivo):
    """
    Carrega o arquivo CSV do projeto C (sistemaAcademico.csv),
    extrai APENAS a seção [USUARIOS], limpa e calcula a média final.
    Retorna o DataFrame ou um DataFrame vazio em caso de erro.
    """
    if not os.path.exists(caminho_arquivo):
        messagebox.showerror("Erro de Leitura", f"Arquivo CSV não encontrado no caminho: {caminho_arquivo}")
        return pd.DataFrame()

    try:
        # 1. LER O ARQUIVO MANUALMENTE PARA ENCONTRAR A SEÇÃO [USUARIOS]
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        start_index = -1
        end_index = -1

        # Encontra o início da seção [USUARIOS]
        for i, line in enumerate(lines):
            if line.strip().upper() == "[USUARIOS]":
                start_index = i + 1 # Começa a ler da linha *depois* do cabeçalho [USUARIOS]
                break
        
        if start_index == -1:
            messagebox.showerror("Erro de Formato", f"Não foi possível encontrar a seção [USUARIOS] no arquivo {caminho_arquivo}.")
            return pd.DataFrame()

        # Encontra o fim da seção
        for i in range(start_index, len(lines)):
            if lines[i].strip().startswith("["):
                end_index = i
                break
        
        if end_index == -1:
            end_index = len(lines)

        usuarios_lines = lines[start_index:end_index]
        usuarios_lines_clean = [line for line in usuarios_lines if line.strip()]

        if len(usuarios_lines_clean) <= 1:
            return pd.DataFrame() 

        # 3. CONVERTE A LISTA DE LINHAS EM UMA STRING E USA O PANDAS
        usuarios_csv_string = "".join(usuarios_lines_clean)
        csv_file_like = io.StringIO(usuarios_csv_string)
        
        df = pd.read_csv(csv_file_like, sep=';')

        # --- SINCRONIZAÇÃO DE COLUNAS COM O NOVO FORMATO C (14 COLUNAS) ---
        df.columns = df.columns.str.strip().str.upper()
        
        column_map = {
            # O nome da coluna no CSV C é "MATERIA" (que no C é 'listaMaterias')
            "MATERIA": "LISTA_MATERIAS", 
            "IDSTURMAS": "ID_TURMAS", # Nova coluna
            "ATIVIDADE": "STATUS DO ALUNO"
        }
        df.rename(columns=column_map, inplace=True)
        
        # Tipagem e limpeza de dados
        for col in ['ID', 'IDADE', 'NP1', 'NP2', 'PIM']:
             if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        if 'NOME' in df.columns: df["NOME"] = df["NOME"].astype(str).str.upper()
        if 'EMAIL' in df.columns: df["EMAIL"] = df["EMAIL"].astype(str).str.lower()
        if 'SENHA' in df.columns: df["SENHA"] = df["SENHA"].astype(str)
        if 'NIVEL' in df.columns: df["NIVEL"] = df["NIVEL"].astype(str).str.upper()
        if 'CURSO' in df.columns: df["CURSO"] = df["CURSO"].astype(str).str.upper()
        if 'MATERIA' in df.columns: df["MATERIA"] = df["MATERIA"].astype(str)
        if 'TURMAS' in df.columns: df["TURMAS"] = df["TURMAS"].astype(str)
        
        # 1. CÁLCULO DA MÉDIA FINAL
        if all(col in df.columns for col in ['NP1', 'NP2', 'PIM']):
            df["MEDIA"] = (df["NP1"] * 4 + df["NP2"] * 4 + df["PIM"] * 2) / 10
        elif 'MEDIA' not in df.columns:
            df["MEDIA"] = 0.0

        # 2. INICIALIZAÇÃO DO STATUS DO ALUNO
        if "STATUS DO ALUNO" not in df.columns:
            df["STATUS DO ALUNO"] = "PENDENTE"
        else:
            df["STATUS DO ALUNO"] = df["STATUS DO ALUNO"].astype(str).str.upper().replace('NAN', 'PENDENTE')
            
        # A lista de colunas a manter deve incluir os 14 campos principais
        cols_to_keep = [
            'ID', 'NOME', 'EMAIL', 'SENHA', 'IDADE', 'NIVEL', 'CURSO', 
            'MATERIAS', 'TURMAS', 
            'NP1', 'NP2', 'PIM', 'MEDIA', 'STATUS DO ALUNO'
        ]
        
        cols_existentes = [col for col in cols_to_keep if col in df.columns]
        df = df[cols_existentes]

        return df

    except pd.errors.EmptyDataError:
        messagebox.showerror("Erro de Leitura", "O arquivo CSV parece estar vazio ou a seção [USUARIOS] não pôde ser lida.")
        return pd.DataFrame()
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo CSV.\nErro: {e}")
        return pd.DataFrame()

# --- CLASSE CHATBOT (Inalterado) ---

class Chatbot(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill='both', expand=True, padx=10, pady=10)

        ctk.CTkLabel(self, text="Assistente Acadêmico", font=('Arial', 18, 'bold')).pack(pady=10)
        
        self.area_chat = tk.Text(self, height=12, state=tk.DISABLED, wrap=tk.WORD, font=('Arial', 10))
        self.area_chat.pack(padx=10, pady=5, fill='both', expand=True)

        frame_botoes = ctk.CTkFrame(self)
        frame_botoes.pack(padx=10, pady=10, fill='x')
        ctk.CTkLabel(frame_botoes, text="Perguntas Frequentes:", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        canvas = tk.Canvas(frame_botoes, height=200, bg=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"]), highlightthickness=0)
        v_scrollbar = ctk.CTkScrollbar(frame_botoes, orientation="vertical", command=canvas.yview)
        
        scrollable_frame = ctk.CTkFrame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        v_scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_rowconfigure(1, weight=1)

        for i, pergunta in enumerate(respostas.keys()):
            btn = ctk.CTkButton(scrollable_frame, text=pergunta, command=lambda p=pergunta: self.fazer_pergunta(p),
                                 corner_radius=5)
            btn.grid(row=i, column=0, padx=5, pady=2, sticky="ew")

        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.mostrar_mensagem_boas_vindas()

    def mostrar_mensagem_boas_vindas(self):
        self.adicionar_mensagem("Assistente", "Olá! Sou seu assistente acadêmico. Clique em uma pergunta para começar.")

    def adicionar_mensagem(self, remetente, mensagem):
        self.area_chat.config(state=tk.NORMAL)
        
        tag_color = "blue" if remetente == "Assistente" else "green"
        self.area_chat.tag_config(remetente, foreground=tag_color, font=('Arial', 10, 'bold'))
        
        self.area_chat.insert(tk.END, f"{remetente}: ", remetente)
        self.area_chat.insert(tk.END, f"{mensagem}\n\n")
        
        self.area_chat.config(state=tk.DISABLED)
        self.area_chat.see(tk.END)

    def fazer_pergunta(self, pergunta):
        self.adicionar_mensagem("Você", pergunta)
        self.adicionar_mensagem("Assistente", respostas[pergunta])

# --- CLASSE PRINCIPAL DA APLICAÇÃO (MainApp) ---

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Acadêmico Integrado")
        self.geometry("1100x700")

        # Variáveis de Estado
        self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
        self.data_frame = pd.DataFrame()
        self.tabela_widget = None
        self.frame_tabela_dados = None
        self.current_user = None

        # Container para alternar entre Login e Conteúdo Principal
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    # --- Métodos de Transição de Tela (Inalterado) ---

    def show_login(self):
        """Mostra a tela de Login."""
        for widget in self.container.winfo_children():
            widget.destroy()
            
        login_frame = LoginFrame(self.container, self.authenticate_user)
        login_frame.pack(fill="both", expand=True)
        self.geometry("400x300")
        self.title("Login - Sistema Acadêmico")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def show_main_content(self):
        """Mostra a tela principal após o login."""
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.geometry("1100x700")
        self.title(f"Sistema Acadêmico Integrado - Logado como {self.current_user['NOME']} ({self.current_user['NIVEL']})")
        
        self.create_user_info_banner(self.container)
        self.create_main_tabs(self.container)
        
        self.atualizar_tabela(reload_csv=False)

    def create_user_info_banner(self, master):
        """Cria e exibe o banner com o ID, Nome e Nível do usuário logado."""
        user_name = self.current_user.get('NOME', 'N/A')
        user_id = self.current_user.get('ID', 'N/A')
        user_level = self.current_user.get('NIVEL', 'N/A')

        banner_frame = ctk.CTkFrame(master, height=40)
        banner_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        banner_frame.grid_columnconfigure(0, weight=1)
        banner_frame.grid_columnconfigure(1, weight=0)
        
        info_text = f"👤 Logado como: {user_name} (ID: {user_id}) | Nível: {user_level}"
        info_label = ctk.CTkLabel(
            banner_frame, 
            text=info_text,
            font=("Arial", 14, "bold"),
            text_color="#1E90FF"
        )
        info_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")

        logout_button = ctk.CTkButton(
            banner_frame,
            text="Sair",
            command=self.show_login,
            width=80,
            fg_color="red"
        )
        logout_button.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="e")

    def authenticate_user(self, username_or_email, password):
        """Tenta autenticar o usuário."""
        df_auth = self.data_frame_full
        
        if df_auth.empty:
            messagebox.showerror("Erro de Login", "Não foi possível carregar os dados de usuários. Verifique o arquivo CSV.")
            return False

        # Verifica se as colunas essenciais para login existem
        if not all(col in df_auth.columns for col in ['NOME', 'EMAIL', 'SENHA', 'NIVEL']):
            messagebox.showerror("Erro de Configuração", "O arquivo CSV deve conter as colunas 'NOME', 'EMAIL', 'SENHA' e 'NIVEL'.")
            return False

        input_lower = username_or_email.strip().lower()

        user_row = df_auth[
            (df_auth['EMAIL'] == input_lower) | 
            (df_auth['NOME'] == input_lower.upper())
        ]
        
        if user_row.empty:
            messagebox.showerror("Login Falhou", "Usuário não encontrado.")
            return False

        user = user_row.iloc[0]
        
        if str(user['SENHA']) == str(password):
            self.current_user = user
            messagebox.showinfo("Sucesso", f"Bem-vindo(a), {user['NOME']}!")
            self.show_main_content()
            return True
        else:
            messagebox.showerror("Login Falhou", "Senha incorreta.")
            return False

    # --- Criação da Interface Principal ---

    def create_main_tabs(self, master):
        """
        Cria e configura o Notebook (abas Chatbot e Tabela).
        """
        # Estilo da tabela (necessário para Treeview)
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.map('Treeview', background=[('selected', 'blue')])
        
        # Abas (Notebook)
        self.abas = ttk.Notebook(master)
        frame_tabela = ctk.CTkFrame(self.abas)
        
        user_level = self.current_user.get('NIVEL', 'ALUNO')
        is_student = (user_level == "ALUNO")

        # CRIA A ABA DO CHATBOT SE O USUÁRIO FOR ALUNO
        if is_student:
            frame_chatbot = ctk.CTkFrame(self.abas)
            self.abas.add(frame_chatbot, text="Assistente Acadêmico")
            Chatbot(frame_chatbot)

        # ADICIONA SEMPRE A ABA DA TABELA
        self.abas.add(frame_tabela, text="Tabela de Usuários")
        self.abas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configura o Frame da Tabela
        self.create_tabela_frame(frame_tabela)


    def create_tabela_frame(self, frame_tabela):
        """Cria o frame de controles e o container para a Treeview."""
        
        # Frame de controle (botões e filtros)
        frame_controles = ctk.CTkFrame(frame_tabela)
        frame_controles.pack(fill="x", padx=10, pady=10)

        user_level = self.current_user['NIVEL'] if self.current_user is not None else "NÃO AUTORIZADO"
        user_is_admin = (user_level == "ADMINISTRADOR") 
        
        titulo = ctk.CTkLabel(frame_controles, text=f"Gerenciamento de Usuários (Nível: {user_level})", font=("Arial", 16, "bold"))
        titulo.pack(pady=5)

        # Configuração de botões e filtros (visíveis apenas para ADMIN)
        if user_is_admin:
            frame_botoes = ctk.CTkFrame(frame_controles)
            frame_botoes.pack(fill="x", padx=10, pady=10)

            # Botões de Ação (Apenas ADMIN)
            botao_ativar = ctk.CTkButton(frame_botoes, text="🟢 Ativar Aluno", command=self.ativar_aluno, fg_color="#3A8A3A")
            botao_ativar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            botao_desativar = ctk.CTkButton(frame_botoes, text="🔴 Desativar Aluno", command=self.desativar_aluno, fg_color="#E03C31")
            botao_desativar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            botao_editar = ctk.CTkButton(frame_botoes, text="✏️ Editar Usuário", command=self.abrir_janela_edicao)
            botao_editar.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

            # Botão de Excluir Usuário
            botao_excluir = ctk.CTkButton(frame_botoes, text="❌ Excluir Usuário", command=self.excluir_usuario, fg_color="#CC0000")
            botao_excluir.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

            botao_salvar = ctk.CTkButton(frame_botoes, text="💾 Salvar Alterações", command=self.salvar_dados, fg_color="#3C66E0")
            botao_salvar.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(frame_botoes, text="| Filtros Rápidos:", font=("Arial", 12, "bold")).grid(row=0, column=5, padx=10)

            # Botões de Filtro Rápido (Apenas ADMIN)
            botao_filtrar_ativos = ctk.CTkButton(frame_botoes, text="Mostrar Ativos", command=lambda: self.filtrar_por_status("ATIVO"), fg_color="#4CAF50")
            botao_filtrar_ativos.grid(row=0, column=6, padx=5, pady=5, sticky="ew")

            botao_filtrar_inativos = ctk.CTkButton(frame_botoes, text="Mostrar Inativos", command=lambda: self.filtrar_por_status("INATIVO"), fg_color="#FF9800")
            botao_filtrar_inativos.grid(row=0, column=7, padx=5, pady=5, sticky="ew")

            botao_atualizar = ctk.CTkButton(frame_botoes, text="🔄 Recarregar CSV", command=lambda: self.atualizar_tabela(reload_csv=True))
            botao_atualizar.grid(row=0, column=8, padx=5, pady=5, sticky="ew")
            
            # Garante que as 9 colunas tenham peso igual
            for i in range(9): frame_botoes.grid_columnconfigure(i, weight=1)

            # Container para todos os filtros
            filtros_container = ctk.CTkFrame(frame_controles)
            filtros_container.pack(fill="x", padx=10, pady=5)

            # --- Filtro Geral com Combobox ---
            ctk.CTkLabel(filtros_container, text="Filtrar por:").grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")
            
            # Pega as colunas para o combobox, tratando o caso de DF vazio
            colunas_filtro = ["Filtrar por Coluna..."]
            if not self.data_frame_full.empty:
                colunas_filtro.extend(self.data_frame_full.columns.tolist())

            self.combo_filtro_coluna = ctk.CTkComboBox(filtros_container, values=colunas_filtro, width=180)
            self.combo_filtro_coluna.grid(row=0, column=1, padx=5, pady=10, sticky="w")

            self.entrada_filtro_geral = ctk.CTkEntry(filtros_container, placeholder_text="Digite o valor...", width=180)
            self.entrada_filtro_geral.grid(row=0, column=2, padx=5, pady=10, sticky="w")
            botao_filtrar_geral = ctk.CTkButton(filtros_container, text="Buscar", command=self.filtrar_geral, width=80)
            botao_filtrar_geral.grid(row=0, column=3, padx=5, pady=10, sticky="w")
            
            # --- Botão Limpar (Agora na coluna 4, onde estava o filtro de idade) ---
            botao_limpar_filtros = ctk.CTkButton(filtros_container, text="Limpar Filtros", command=self.limpar_filtros)
            botao_limpar_filtros.grid(row=0, column=4, padx=(20, 10), pady=10, sticky="w")

        else:
            # Botão de atualização para o aluno/professor/coordenador
            botao_atualizar = ctk.CTkButton(frame_controles, text="🔄 Recarregar Dados", command=lambda: self.atualizar_tabela(reload_csv=True))
            botao_atualizar.pack(pady=10)


        # Frame da tabela de dados (onde o Treeview será inserido)
        self.frame_tabela_dados = ctk.CTkFrame(frame_tabela)
        self.frame_tabela_dados.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Métodos de Interação da Tabela (Lógica inalterada) ---

    def excluir_usuario(self):
        """Exclui o usuário selecionado (Apenas ADMIN)."""
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Somente usuários ADMIN podem excluir usuários.")
            return

        if self.tabela_widget is None: return
        selecionado = self.tabela_widget.focus()

        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione uma linha para excluir.")
            return
            
        try:
            # 1. Obter o ID da linha selecionada no DataFrame VISÍVEL
            idx_visible = int(selecionado)
            user_id = self.data_frame.loc[idx_visible, 'ID']
        
            # 2. Confirmação
            if not messagebox.askyesno("Confirmação de Exclusão", 
                                        f"Tem certeza que deseja EXCLUIR o usuário ID {user_id}? Esta ação é permanente e não pode ser desfeita."):
                return

            # 3. Encontrar e remover o usuário do DataFrame COMPLETO (fonte da verdade)
            idx_full_list = self.data_frame_full[self.data_frame_full['ID'] == user_id].index
            
            if not idx_full_list.empty:
                idx_full = idx_full_list[0]
                self.data_frame_full.drop(idx_full, inplace=True)
                
                # 4. Salvar as alterações no CSV (CHAMADA ÚNICA PARA A FUNÇÃO CORRIGIDA)
                self.salvar_dados() 
                
            else:
                messagebox.showwarning("Erro", f"Usuário ID {user_id} não encontrado no banco de dados completo.")

        except Exception as e:
            messagebox.showerror("Erro de Exclusão", f"Ocorreu um erro ao excluir o usuário: {e}")

    def filtrar_por_status(self, status):
        """Filtra a tabela por status (Apenas ADMIN)."""
        if self.current_user['NIVEL'] == "ADMINISTRADOR":
             self.atualizar_tabela(reload_csv=False, filter_status=status)
        else:
             messagebox.showwarning("Permissão Negada", "Filtros rápidos são exclusivos para ADMIN.")

    def filtrar_geral(self):
        """Filtra a tabela pelo valor e coluna selecionados (Apenas ADMIN)."""
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
             messagebox.showwarning("Permissão Negada", "Filtros são exclusivos para ADMIN.")
             return
             
        coluna = self.combo_filtro_coluna.get()
        texto = self.entrada_filtro_geral.get().strip()

        if coluna == "Filtrar por Coluna..." or not texto:
            messagebox.showwarning("Filtro", "Selecione uma coluna e digite um valor de busca.")
            return

        self.atualizar_tabela(reload_csv=False, general_filter_text=texto, filter_column=coluna)

    def limpar_filtros(self):
        """Limpa todos os filtros e recarrega a tabela completa (Apenas ADMIN)."""
        if self.current_user['NIVEL'] == "ADMINISTRADOR":
            self.combo_filtro_coluna.set("Filtrar por Coluna...")
            self.entrada_filtro_geral.delete(0, tk.END)
            self.atualizar_tabela(reload_csv=False)
        else:
            messagebox.showwarning("Permissão Negada", "Limpar filtros é exclusivo para ADMIN.")

    def atualizar_tabela(self, reload_csv=True, filter_status=None, general_filter_text=None, filter_column=None):
        """
        Carrega, filtra e exibe os dados com base no nível do usuário e filtros rápidos.
        """
        if reload_csv:
            # 1. Recarrega o conjunto de dados completo
            self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
            if self.data_frame_full.empty:
                self.data_frame = pd.DataFrame()
                self.mostrar_tabela(self.data_frame)
                return
            
        if self.data_frame_full is None:
            self.data_frame_full = pd.DataFrame()
        
        df_display = self.data_frame_full.copy()
        
        if self.current_user is None:
            self.mostrar_tabela(pd.DataFrame())
            return
        
        user_level = self.current_user['NIVEL']

        # 2. FILTRAGEM DE ACESSO BASEADA NO NÍVEL DO USUÁRIO
        columns_to_drop = []
        rows_filter = None
        
        if user_level == "ALUNO":
            user_id = self.current_user['ID']
            rows_filter = df_display['ID'] == user_id
            # 🚨 ATUALIZAÇÃO: Esconder as listas de matérias e turmas do aluno
            columns_to_drop.extend(['STATUS DO ALUNO', 'SENHA', 'LISTA_MATERIAS', 'ID_TURMAS']) 
            
        elif user_level == "PROFESSOR":
            rows_filter = df_display['NIVEL'] == 'ALUNO'
            columns_to_drop.append('SENHA')
            columns_to_drop.append('ID_TURMAS') 
            
        elif user_level == "COORDENADOR":
            rows_filter = df_display['NIVEL'].isin(['ALUNO', 'PROFESSOR', 'COORDENADOR'])
            columns_to_drop.append('SENHA')
            columns_to_drop.extend(['NP1', 'NP2', 'PIM'])
            columns_to_drop.append('ID_TURMAS') 
            
        elif user_level == "ADMINISTRADOR":
            columns_to_drop.append('SENHA') # ADMIN vê tudo, exceto SENHA
            
        # Aplica o filtro de linhas
        if rows_filter is not None:
            df_display = df_display[rows_filter].copy()

        # Remove colunas confidenciais
        cols_to_drop_final = [col for col in columns_to_drop if col in df_display.columns]
        if cols_to_drop_final:
            df_display = df_display.drop(columns=cols_to_drop_final)

        # 3. FILTROS RÁPIDOS (APLICADOS SOMENTE SE O USUÁRIO FOR ADMIN)
        if user_level == "ADMINISTRADOR":
            if filter_status:
                df_display = df_display[df_display["STATUS DO ALUNO"] == filter_status.upper()]
            
            # Lógica do filtro geral 
            if general_filter_text and filter_column and filter_column in df_display.columns:
                search_term = general_filter_text.lower()
                df_display = df_display[df_display[filter_column].astype(str).str.lower().str.contains(search_term, na=False)]

        # Fim da filtragem. O DF de exibição (self.data_frame) é definido.
        self.data_frame = df_display.reset_index(drop=True)
        self.mostrar_tabela(self.data_frame)
        
        if reload_csv and user_level == "ADMINISTRADOR":
            messagebox.showinfo("Atualização", "Tabela recarregada a partir do arquivo CSV.")
        
    def mostrar_tabela(self, df):
        """
        Exibe o DataFrame na Treeview. 
        """
        
        # Destrói widgets antigos
        for widget in self.frame_tabela_dados.winfo_children():
            widget.destroy()
            
        # Se o DataFrame estiver vazio
        if df.empty:
            ctk.CTkLabel(self.frame_tabela_dados, text="Nenhum dado encontrado para o filtro aplicado ou seu nível de acesso.", 
                         text_color="red").pack(pady=20)
            self.tabela_widget = None
            return

        # Configura Treeview
        colunas = list(df.columns)
        self.tabela_widget = ttk.Treeview(self.frame_tabela_dados, columns=colunas, show="headings")

        # Scrollbars
        vsb = ttk.Scrollbar(self.frame_tabela_dados, orient="vertical", command=self.tabela_widget.yview)
        hsb = ttk.Scrollbar(self.frame_tabela_dados, orient="horizontal", command=self.tabela_widget.xview)
        self.tabela_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Configura cabeçalhos e colunas
        for col in colunas:
            self.tabela_widget.heading(col, text=col.replace('_', ' '))
            # Ajuste a largura para os novos campos
            self.tabela_widget.column(col, anchor="center", width=100 if col not in ['NOME', 'EMAIL', 'CURSO', 'LISTA_MATERIAS'] else 150)

        # Insere os dados
        for i, row in df.iterrows():
            row_list = list(row)
            if 'MEDIA' in colunas:
                media_index = colunas.index('MEDIA')
                try:
                    # Tenta formatar como float, se falhar, usa como string
                    row_list[media_index] = f"{float(row_list[media_index]):.2f}"
                except ValueError:
                    pass
                    
            self.tabela_widget.insert("", "end", iid=i, values=row_list)

        self.tabela_widget.pack(fill="both", expand=True)

    def ativar_aluno(self):
        """Define o STATUS DO ALUNO como ATIVO (Apenas ADMIN)."""
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Somente usuários ADMIN podem alterar o status do aluno.")
            return

        if self.tabela_widget is None: return
        selecionado = self.tabela_widget.focus()

        if selecionado:
            idx = int(selecionado)
            # Atualiza o DataFrame visível
            self.data_frame.loc[idx, "STATUS DO ALUNO"] = "ATIVO"
            
            # Atualiza a linha na Treeview
            current_values = list(self.data_frame.loc[idx].values)
            if 'MEDIA' in self.data_frame.columns:
                media_index = self.data_frame.columns.tolist().index('MEDIA')
                current_values[media_index] = f"{float(current_values[media_index]):.2f}"
                
            self.tabela_widget.item(selecionado, values=current_values)
            messagebox.showinfo("Status", f"Aluno ID {self.data_frame.loc[idx, 'ID']} ativado. Lembre-se de SALVAR as alterações no CSV.")
        else:
            messagebox.showwarning("Seleção", "Selecione uma linha para ativar.")

    def desativar_aluno(self):
        """Define o STATUS DO ALUNO como INATIVO (Apenas ADMIN)."""
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Somente usuários ADMIN podem alterar o status do aluno.")
            return

        if self.tabela_widget is None: return
        selecionado = self.tabela_widget.focus()

        if selecionado:
            idx = int(selecionado)
            # Atualiza o DataFrame visível
            self.data_frame.loc[idx, "STATUS DO ALUNO"] = "INATIVO"

            # Atualiza a linha na Treeview
            current_values = list(self.data_frame.loc[idx].values)
            if 'MEDIA' in self.data_frame.columns:
                media_index = self.data_frame.columns.tolist().index('MEDIA')
                current_values[media_index] = f"{float(current_values[media_index]):.2f}"
                
            self.tabela_widget.item(selecionado, values=current_values)
            messagebox.showinfo("Status", f"Aluno ID {self.data_frame.loc[idx, 'ID']} desativado. Lembre-se de SALVAR as alterações no CSV.")
        else:
            messagebox.showwarning("Seleção", "Selecione uma linha para desativar.")
            
    def abrir_janela_edicao(self):
        """Abre uma janela para editar os dados do usuário selecionado."""
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Somente usuários ADMIN podem editar usuários.")
            return

        if not isinstance(self.tabela_widget, ttk.Treeview):
            messagebox.showwarning("Aviso", "A tabela não está carregada.")
            return

        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Por favor, selecione um usuário na tabela para editar.")
            return

        # Obter os dados da linha selecionada do DataFrame VISÍVEL
        idx = int(selecionado)
        user_data_series = self.data_frame.loc[idx]
        
        # Busca a linha completa no DF full
        user_id = user_data_series['ID']
        full_user_data_row = self.data_frame_full[self.data_frame_full['ID'] == user_id]
        if full_user_data_row.empty:
            messagebox.showerror("Erro", "Dados completos do usuário não encontrados.")
            return

        full_user_data = full_user_data_row.iloc[0]

        # --- Cria a janela de edição ---
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Editar Usuário ID: {user_id}")
        edit_window.geometry("400x650")
        edit_window.transient(self)
        edit_window.grab_set()

        # --- Cria o formulário ---
        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        entries = {}
        # 🚨 ATUALIZAÇÃO: Lista de colunas a serem exibidas no formulário de edição (incluindo LISTA_MATERIAS e ID_TURMAS)
        editaveis = ['NOME', 'EMAIL', 'IDADE', 'CURSO', 'LISTA_MATERIAS', 'ID_TURMAS', 'NIVEL', 'SENHA', 'NP1', 'NP2', 'PIM']
        
        for i, col in enumerate(editaveis):
            if col in full_user_data.index:
                # Ajusta o label para ser mais amigável
                label_text = col.replace('_', ' ')
                ctk.CTkLabel(form_frame, text=f"{label_text}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
                entry = ctk.CTkEntry(form_frame, width=250)
                entry.insert(0, str(full_user_data[col]))
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entries[col] = entry

        # Botão de salvar
        save_button = ctk.CTkButton(
            form_frame,
            text="Salvar Alterações",
            command=lambda: self.salvar_edicao_usuario(user_id, entries, edit_window)
        )
        save_button.grid(row=len(editaveis), column=0, columnspan=2, padx=10, pady=20, sticky="ew")

    def salvar_edicao_usuario(self, user_id, entries, window):
        """Salva os dados editados do usuário no DataFrame e no CSV."""
        try:
            # Encontra o índice do usuário no DataFrame completo
            user_index = self.data_frame_full[self.data_frame_full['ID'] == user_id].index[0]

            # Atualiza cada valor no DataFrame completo
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                
                # Validação e conversão de tipo para colunas numéricas
                if col in ['IDADE', 'NP1', 'NP2', 'PIM']:
                    try:
                        new_value_converted = 0 if not new_value else int(new_value)
                        
                        if col in ['NP1', 'NP2', 'PIM'] and not (0 <= new_value_converted <= 10):
                            messagebox.showerror("Erro de Validação", f"As notas NP1, NP2 e PIM devem estar entre 0 e 10. Valor inválido em '{col}'.")
                            return
                            
                        self.data_frame_full.loc[user_index, col] = new_value_converted

                    except ValueError:
                        messagebox.showerror("Erro de Validação", f"O campo '{col}' deve ser um número inteiro válido.")
                        return
                
                # Campos de texto (Nome, Email, Nível, Curso, LISTA_MATERIAS, ID_TURMAS, Senha)
                elif col in ['NOME', 'EMAIL', 'NIVEL', 'CURSO']:
                    if col == 'NOME' or col == 'NIVEL' or col == 'CURSO':
                        new_value = new_value.upper()
                    elif col == 'EMAIL':
                        new_value = new_value.lower()
                    
                    self.data_frame_full.loc[user_index, col] = new_value
                
                elif col in ['LISTA_MATERIAS', 'ID_TURMAS']:
                    # Salva como string sem conversão de case
                    self.data_frame_full.loc[user_index, col] = new_value
                
                elif col == 'SENHA':
                    self.data_frame_full.loc[user_index, col] = new_value

            # Recalcular a média após a edição das notas
            if all(col in self.data_frame_full.columns for col in ['NP1', 'NP2', 'PIM']):
                row = self.data_frame_full.loc[user_index]
                media = (row['NP1'] * 4 + row['NP2'] * 4 + row['PIM'] * 2) / 10
                self.data_frame_full.loc[user_index, 'MEDIA'] = media

            # Salva o DataFrame completo no arquivo CSV
            self.salvar_dados()
            
            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            window.destroy()
            
            # Recarrega a tabela na interface principal para mostrar as alterações
            self.atualizar_tabela(reload_csv=False)

        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar as alterações: {e}")

    # --- FUNÇÃO 'salvar_dados' (CRUCIALMENTE CORRIGIDA PARA 14 CAMPOS) ---
    # Dentro da classe MainApp...

    def salvar_dados(self):
        """
        Salva o DataFrame completo no arquivo CSV, preservando as demais seções 
        ([TURMAS], [NOTAS], etc.), usando o formato de 14 colunas do programa C.
        (Apenas ADMIN)
        """
        if self.current_user['NIVEL'] != "ADMINISTRADOR":
            messagebox.showwarning("Permissão Negada", "Somente usuários ADMIN podem salvar alterações no banco de dados.")
            return
            
        if self.data_frame_full is None or self.data_frame_full.empty:
            messagebox.showwarning("Salvar", "Não foi possível salvar, o banco de dados está vazio ou não foi carregado.")
            return

        try:
            # 1. SINCRONIZA AS MUDANÇAS DE STATUS (Lógica inalterada)
            for index_visible, row_visible in self.data_frame.iterrows():
                user_id = row_visible['ID']
                idx_full_list = self.data_frame_full[self.data_frame_full['ID'] == user_id].index
                
                if not idx_full_list.empty:
                    idx_full = idx_full_list[0]
                    if 'STATUS DO ALUNO' in row_visible and 'STATUS DO ALUNO' in self.data_frame_full.columns:
                        self.data_frame_full.loc[idx_full, 'STATUS DO ALUNO'] = row_visible['STATUS DO ALUNO']
            
            # 2. PREPARA O DATAFRAME [USUARIOS] PARA SALVAR (Lógica de renomeação de 14 colunas inalterada)
            df_to_save = self.data_frame_full.copy()
            
            # ... (Lógica de renomeação de colunas do DF para o padrão C inalterada) ...
            column_map_save = {
                "LISTA_MATERIAS": "Materia", 
                "ID_TURMAS": "IDsTurmas",
                "STATUS DO ALUNO": "Atividade"
            }
            df_to_save.rename(columns=column_map_save, inplace=True)
            
            final_c_cols = [
                'ID', 'Nome', 'Email', 'Senha', 'Idade', 'Nivel', 'Curso', 
                'Materia', 'IDsTurmas', 'NP1', 'NP2', 'PIM', 'Media', 'Atividade'
            ]
            
            df_to_save.columns = [col.capitalize() if col.lower() not in ['id'] else col.upper() for col in df_to_save.columns]
            df_to_save = df_to_save[[col for col in final_c_cols if col in df_to_save.columns]]

            # 4. LÊ O ARQUIVO CSV ORIGINAL PARA PRESERVAR OUTRAS SEÇÕES (Lógica inalterada)
            preserved_lines = []
            in_usuarios_section = False

            if os.path.exists(CAMINHO_ARQUIVO):
                with open(CAMINHO_ARQUIVO, 'r', encoding='utf-8', errors='ignore') as f:
                    # ... (Lógica de preservação de seções inalterada) ...
                    for line in f:
                        stripped_line = line.strip().upper()
                        
                        if stripped_line.startswith("[") and stripped_line.endswith("]"):
                            if stripped_line == "[USUARIOS]":
                                in_usuarios_section = True
                                continue 
                            
                            in_usuarios_section = False
                            preserved_lines.append(line)
                            continue 
                        
                        if in_usuarios_section:
                            continue
                        
                        preserved_lines.append(line)
            
            # 5. RECONSTROI O ARQUIVO NO FORMATO C (Sobrescreve o arquivo)
            # 🚨 CORREÇÃO ESSENCIAL: Abrir o arquivo com newline=''
            with open(CAMINHO_ARQUIVO, 'w', encoding='utf-8', newline='') as f:
                f.write("[USUARIOS]\n")
                
                # CORREÇÃO: 'line_terminator' -> 'lineterminator'
                df_to_save.to_csv(f, sep=';', index=False, lineterminator='\r\n') 
                
                # Adiciona as outras seções de volta
                if preserved_lines:
                    f.write("\n")
                    f.writelines(preserved_lines)
            
            messagebox.showinfo("Salvo", "Todas as alterações (Status e Edições) foram salvas com sucesso no arquivo CSV, preservando as demais seções.")
            
            # 6. Recarrega a tabela para garantir que o estado visível reflita o estado completo
            self.atualizar_tabela(reload_csv=True)
            
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao salvar os dados: {e}")


# --- CLASSE LOGIN (Inalterado) ---

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, login_callback):
        super().__init__(master)
        self.login_callback = login_callback
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Acesso ao Sistema Acadêmico", font=('Arial', 18, 'bold')).grid(row=1, column=1, padx=20, pady=(20, 10))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Usuário (Nome/Email)", width=250)
        self.username_entry.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=250)
        self.password_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        
        self.login_button = ctk.CTkButton(self, text="Entrar", command=self.attempt_login, width=250)
        self.login_button.grid(row=4, column=1, padx=20, pady=(10, 20), sticky="ew")

        self.password_entry.bind('<Return>', lambda event: self.attempt_login())
        self.username_entry.bind('<Return>', lambda event: self.attempt_login())
        
    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.login_callback(username, password)
        else:
            messagebox.showwarning("Aviso", "Por favor, insira o usuário e a senha.")

# --- INICIALIZAÇÃO ---

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
