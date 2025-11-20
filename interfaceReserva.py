# -*- coding: utf-8 -*-
"""
Sistema Acadêmico Integrado
Versão refatorada para organização (17/11/2025).
"""

# === 1. IMPORTAÇÕES ===
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import io
import pandas as pd
from pathlib import Path
from PIL import Image, ImageTk  # Adicionado ImageTk para melhor gestão de imagem
import shutil
from datetime import datetime

# === 2. CONSTANTES E DADOS GLOBAIS ===

CAMINHO_ARQUIVO = "Output/SistemaAcademico.csv"
SECAO_ALVO = "[USUARIOS]"
CONSENT_FILE = "lgpd_consent.txt"
DIR_ATIVIDADES = "atividades"

# Dicionário de respostas do Chatbot
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
    "Quais são os horários de atendimento do coordenador?": "O Prof. Cordeiro atende às quartas, das 14h às 16h.",
}


# === 3. FUNÇÕES UTILITÁRIAS ===


def check_lgpd_consentimento():
    """Verifica se o usuário já aceitou os termos da LGPD."""
    return os.path.exists(CONSENT_FILE)


def criar_lgpd_consentimento():
    """Registra o consentimento do usuário em um arquivo."""
    try:
        with open(CONSENT_FILE, "w") as f:
            f.write("accepted")
    except Exception as e:
        print(f"Erro ao salvar consentimento: {e}")


def carregar_tabela(caminho_arquivo):
    """Carrega e processa a seção [USUARIOS] do arquivo CSV."""
    if not os.path.exists(caminho_arquivo):
        messagebox.showerror(
            "Erro de Leitura",
            f"Arquivo CSV não encontrado no caminho: {caminho_arquivo}",
        )
        return pd.DataFrame()
    try:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        start_index = -1
        end_index = -1
        for i, line in enumerate(lines):
            if line.strip().upper() == SECAO_ALVO:
                start_index = i + 1
                break
        if start_index == -1:
            messagebox.showerror(
                "Erro de Formato",
                f"Não foi possível encontrar a seção {SECAO_ALVO} no arquivo {caminho_arquivo}.",
            )
            return pd.DataFrame()

        for i in range(start_index, len(lines)):
            if lines[i].strip().startswith("["):
                end_index = i
                break
        if end_index == -1:
            end_index = len(lines)

        usuarios_lines = lines[start_index:end_index]
        usuarios_lines_clean = [line for line in usuarios_lines if line.strip()]

        header_default = (
            "id;nome;email;senha;nivel;curso;turma;idade;np1;np2;pim;media;atividade"
        )
        if len(usuarios_lines_clean) <= 1:
            header_line = (
                usuarios_lines_clean[0] if usuarios_lines_clean else header_default
            )
            colunas = [col.strip() for col in header_line.split(";")]
            return pd.DataFrame(columns=colunas)

        header_line = usuarios_lines_clean[0]
        colunas = [col.strip() for col in header_line.split(";")]
        data_lines = "".join(usuarios_lines_clean[1:])
        csv_file_like = io.StringIO(data_lines)
        df = pd.read_csv(csv_file_like, sep=";", header=None, names=colunas)

        df.columns = df.columns.str.strip().str.upper()

        column_map = {"TURMA": "TURMAS", "ATIVIDADE": "STATUS DO ALUNO"}
        df.rename(columns=column_map, inplace=True)

        cols_numericas = ["NP1", "NP2", "PIM", "MEDIA"]
        for col in cols_numericas:
            if col in df.columns:
                # Trata a vírgula como separador decimal para leitura do CSV
                df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        cols_inteiras = ["ID", "IDADE"]
        for col in cols_inteiras:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        if "NOME" in df.columns:
            df["NOME"] = df["NOME"].astype(str).str.upper()
        if "EMAIL" in df.columns:
            df["EMAIL"] = df["EMAIL"].astype(str).str.lower()
        if "SENHA" in df.columns:
            df["SENHA"] = df["SENHA"].astype(str)
        if "NIVEL" in df.columns:
            df["NIVEL"] = df["NIVEL"].astype(str).str.upper()
        if "CURSO" in df.columns:
            # Remove espaços extras e converte para maiúsculo
            df["CURSO"] = df["CURSO"].astype(str).str.strip().str.upper()

        if all(col in df.columns for col in ["NP1", "NP2", "PIM"]):
            df["MEDIA"] = (df["NP1"] * 4 + df["NP2"] * 4 + df["PIM"] * 2) / 10
            df["MEDIA"] = df["MEDIA"].round(2)

        return df
    except Exception as e:
        messagebox.showerror(
            "Erro de Leitura", f"Não foi possível ler o arquivo CSV.\nErro: {e}"
        )
        return pd.DataFrame()


# === 4. CLASSES DE GUI AUXILIARES (Pop-up e Login) ===


class LGPDPopup(ctk.CTkToplevel):
    """Janela pop-up para consentimento LGPD."""

    def __init__(self, master, on_accept_callback):
        super().__init__(master)
        self.title("Aviso de Privacidade (LGPD)")
        self.on_accept_callback = on_accept_callback
        popup_width, popup_height = 500, 350
        screen_width, screen_height = (
            self.winfo_screenwidth(),
            self.winfo_screenheight(),
        )
        pos_x, pos_y = (screen_width // 2) - (popup_width // 2), (
            screen_height // 2
        ) - (popup_height // 2)
        self.geometry(f"{popup_width}x{popup_height}+{pos_x}+{pos_y}")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", master.quit)
        msg = "De acordo com a Lei Geral de Proteção de Dados (LGPD), precisamos do seu consentimento para processar seus dados. Ao clicar em 'Aceitar', você concorda com o uso de seus dados (como login, senha e notas) para o funcionamento deste aplicativo."
        ctk.CTkLabel(self, text=msg, wraplength=380, font=("Arial", 14)).pack(
            pady=30, padx=20, fill="x"
        )
        ctk.CTkButton(
            self,
            text="Aceitar e Continuar",
            command=self.accept,
            fg_color="green",
            font=("Arial", 12, "bold"),
        ).pack(pady=20, padx=20, ipady=5)

    def accept(self):
        criar_lgpd_consentimento()
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.grab_release()
        self.destroy()
        self.on_accept_callback()


class LoginFrame(ctk.CTkFrame):
    """Frame que gerencia a interface de Login."""

    def __init__(self, master, login_callback, forgot_password_callback):
        super().__init__(master)
        self.login_callback = login_callback
        self.forgot_password_callback = forgot_password_callback
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        logo_path = Path(__file__).parent / "logo.png"
        logo_image = None
        try:
            pil_image = Image.open(logo_path)
            logo_image = ctk.CTkImage(pil_image, size=(80, 80))
            self.logo_label = ctk.CTkLabel(self, image=logo_image, text="")
            # Mantém a referência para evitar que a imagem seja coletada pelo garbage collector
            self.logo_label.image = logo_image
        except FileNotFoundError:
            self.logo_label = ctk.CTkLabel(
                self, text="[Logo - logo.png não encontrado]", font=("Arial", 16)
            )
        except Exception:
            self.logo_label = ctk.CTkLabel(
                self, text="[Logo - Erro ao carregar]", font=("Arial", 16)
            )

        self.logo_label.grid(row=1, column=1, padx=20, pady=(10, 10))

        ctk.CTkLabel(
            self, text="Acesso ao Sistema Acadêmico", font=("Arial", 18, "bold")
        ).grid(row=2, column=1, padx=20, pady=(10, 10))
        self.username_entry = ctk.CTkEntry(
            self, placeholder_text="Usuário (Nome/Email)", width=250
        )
        self.username_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")
        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Senha", show="*", width=250
        )
        self.password_entry.grid(row=4, column=1, padx=20, pady=10, sticky="ew")

        self.show_password_var = ctk.StringVar(value="off")
        self.show_password_check = ctk.CTkCheckBox(
            self,
            text="Mostrar Senha",
            variable=self.show_password_var,
            onvalue="on",
            offvalue="off",
            command=self.toggle_password_visibility,
            font=("Arial", 12),
        )
        self.show_password_check.grid(
            row=5, column=1, padx=20, pady=(0, 10), sticky="w"
        )

        self.login_button = ctk.CTkButton(
            self,
            text="Entrar",
            command=self.attempt_login,
            width=250,
            fg_color="#3C66E0",
        )
        self.login_button.grid(row=6, column=1, padx=20, pady=(10, 20), sticky="ew")

        self.password_entry.bind("<Return>", lambda event: self.attempt_login())
        self.username_entry.bind("<Return>", lambda event: self.attempt_login())

    def toggle_password_visibility(self):
        """Alterna a visualização da senha entre texto puro e asteriscos."""
        if self.show_password_var.get() == "on":
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="*")

    def attempt_login(self):
        """Coleta dados, valida e tenta realizar o login."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Aviso", "Por favor, insira o usuário e a senha.")
            return

        self.login_button.configure(state="disabled", text="Verificando...")
        self.update_idletasks()

        login_successful = self.login_callback(username, password)
        if not login_successful:
            self.login_button.configure(state="normal", text="Entrar")


# === 5. CLASSE PRINCIPAL DA APLICAÇÃO ===


class MainApp(ctk.CTk):
    """Classe principal que gerencia o fluxo da aplicação e a UI."""

    def __init__(self):
        super().__init__()
        self.title("Sistema Acadêmico Integrado")
        self.geometry("1100x700")

        self.data_frame_full = None
        self.data_frame = pd.DataFrame()
        self.tabela_widget = None
        self.frame_tabela_dados = None
        self.current_user = None
        self.password_column_visible = False
        self.btn_toggle_senhas = None

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

    # --- 1. Gerenciamento de Janelas e Fluxo (Login/LGPD) ---

    def iniciar_lgpd_check(self):
        """Verifica o consentimento LGPD antes de iniciar o app principal."""
        self.center_window(400, 480)
        if not check_lgpd_consentimento():
            self.withdraw()
            LGPDPopup(self, self.on_lgpd_accepted)
        else:
            self.on_lgpd_accepted()

    def on_lgpd_accepted(self):
        """Chamado após o usuário aceitar a LGPD. Inicia a tela de login."""
        self.deiconify()
        self.after(50, self.show_login)

    def center_window(self, width=1100, height=700):
        """Função auxiliar para centralizar a janela principal."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        """Mostra a tela de Login."""
        for widget in self.container.winfo_children():
            widget.destroy()
        login_frame = LoginFrame(
            self.container, self.authenticate_user, self.handle_forgot_password
        )
        login_frame.pack(fill="both", expand=True)
        self.center_window(400, 480)
        self.title("Login - Sistema Acadêmico")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def show_main_content(self):
        """Mostra a tela principal após o login."""
        for widget in self.container.winfo_children():
            widget.destroy()
        self.center_window(1100, 700)
        self.title(
            f"Sistema Acadêmico Integrado - Logado como {self.current_user.get('NOME', 'N/A')} ({self.current_user.get('NIVEL', 'N/A')})"
        )
        self.criar_banner(self.container)
        self.criar_abas(self.container)
        self.atualizar_tabela(reload_csv=False)

    def handle_forgot_password(self):
        """Callback para a funcionalidade de 'Esqueci minha senha'."""
        messagebox.showinfo(
            "Recuperação de Senha",
            "A funcionalidade de recuperação de senha (ex: Toplevel) seria iniciada aqui.",
            parent=self.container,
        )

    # ===============================================================
    # 2. Autenticação e Dados do Usuário ----------------------------

    # 2. Autenticação e Dados do Usuário ----------------------------

    def authenticate_user(self, username_or_email, password):
        """Valida o usuário e senha contra o DataFrame carregado."""
        if self.data_frame_full is None:
            self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
        df_auth = self.data_frame_full

        if df_auth is None or df_auth.empty:
            messagebox.showerror(
                "Erro de Login",
                "Não foi possível carregar os dados de usuários. Verifique o arquivo CSV.",
            )
            return False
        if not all(
            col in df_auth.columns
            for col in ["NOME", "EMAIL", "SENHA", "NIVEL", "STATUS DO ALUNO"]
        ):
            messagebox.showerror(
                "Erro de Configuração",
                "O arquivo CSV deve conter as colunas 'nome', 'email', 'senha', 'nivel' e 'atividade' (Status do Aluno).",
            )
            return False

        input_lower = username_or_email.strip().lower()
        user_row = df_auth[
            (df_auth["EMAIL"] == input_lower)
            | (df_auth["NOME"] == username_or_email.strip().upper())
        ]

        if user_row.empty:
            messagebox.showerror("Login Falhou", "Usuário não encontrado.")
            return False

        user = user_row.iloc[0]

        if str(user["SENHA"]) == str(password):

            # === NOVO BLOQUEIO DE STATUS (Linhas 816-820) ===
            if (
                user.get("NIVEL") == "ALUNO"
                and user.get("STATUS DO ALUNO") == "INATIVO"
            ):
                messagebox.showerror(
                    "Acesso Bloqueado",
                    "Acesso bloqueado. Sua matrícula está INATIVA. Por favor, entre em contato com a secretaria acadêmica.",
                )
                return False
            # ===============================================

            self.current_user = user
            messagebox.showinfo("Sucesso", f"Bem-vindo(a), {user['NOME']}!")
            self.show_main_content()
            return True
        else:
            messagebox.showerror("Login Falhou", "Senha incorreta.")
            return False

    def _gerar_novo_id(self):
        """Gera um novo ID de usuário com base no ID máximo existente."""
        if self.data_frame_full is None or self.data_frame_full.empty:
            return 1
        if "ID" in self.data_frame_full.columns:
            max_id = self.data_frame_full["ID"].max()
            return int(max_id) + 1
        return 1

    def _get_all_turmas_list(self):
        """Busca todas as turmas únicas do DataFrame principal."""
        if self.data_frame_full is None or "TURMAS" not in self.data_frame_full.columns:
            return []

        turmas = (
            self.data_frame_full["TURMAS"]
            .astype(str)
            .str.strip()
            .str.upper()
            .unique()
            .tolist()
        )

        turmas_filtradas = [
            t for t in turmas if t and t not in ["GERAL", "DUMMY", "N/A", ""]
        ]
        turmas_filtradas.sort()
        return turmas_filtradas

    def _validar_turma_curso(self, turma_nome, curso_nome, user_id_to_ignore=None):
        """
        Verifica se um nome de turma já existe e, em caso afirmativo,
        se está associado a um curso diferente.
        """
        if self.data_frame_full is None or self.data_frame_full.empty:
            return True, ""  # Dataframe vazio, pode criar

        df_check = self.data_frame_full.copy()

        # Se estivermos editando, ignoramos o próprio usuário da verificação
        if user_id_to_ignore is not None:
            df_check = df_check[df_check["ID"] != user_id_to_ignore]

        # Procurar se a turma já existe em outro registro
        turma_existente_df = df_check[
            df_check["TURMAS"].astype(str).str.upper() == turma_nome.upper()
        ]

        if turma_existente_df.empty:
            return True, ""  # Turma é nova, pode criar

        # Turma existe, verificar se o curso bate
        curso_existente = turma_existente_df["CURSO"].iloc[0]
        if curso_existente.upper() != curso_nome.upper():
            msg_erro = (
                f"A turma '{turma_nome}' já existe e está "
                f"associada ao curso '{curso_existente}'.\n\n"
                f"Não é possível associá-la também ao curso '{curso_nome}'."
            )
            return False, msg_erro

        return True, ""  # Turma existe, mas o curso é o mesmo, OK

    # --- 3. Criação da UI Principal (Abas, Banners, Controles) ---

    # =================================================================================
    # Cria o banner superior com informações do usuário e botão de Sair

    def criar_banner(self, master):
        """Cria o banner superior com informações do usuário e botão de Sair."""
        user_name = self.current_user.get("NOME", "N/A")
        user_id = self.current_user.get("ID", "N/A")
        user_level = self.current_user.get("NIVEL", "N/A")
        banner_frame = ctk.CTkFrame(master, height=40)
        banner_frame.pack(fill="x", padx=10, pady=(10, 5))
        banner_frame.grid_columnconfigure(0, weight=1)
        banner_frame.grid_columnconfigure(1, weight=0)
        info_text = f"👤 Logado como: {user_name} (ID: {user_id}) | Nível: {user_level}"
        info_label = ctk.CTkLabel(
            banner_frame,
            text=info_text,
            font=("Arial", 14, "bold"),
            text_color="#B0B6BB",
        )
        info_label.grid(row=0, column=0, padx=20, pady=5, sticky="w")
        logout_button = ctk.CTkButton(
            banner_frame, text="Sair", command=self.show_login, width=80, fg_color="red"
        )
        logout_button.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="e")

    def criar_abas(self, master):
        """Cria o Notebook de abas (Tabela, Turmas, Chatbot)"""

        # -----------------------------------------------------------
        # 🟢 INÍCIO DA CUSTOMIZAÇÃO DO NOTEBOOK (TTK.STYLE)
        # -----------------------------------------------------------
        style = ttk.Style(self)
        style.theme_use("default")

        # 1. Configuração padrão para a tabela (mantida)
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "blue")])

        # 2. Configura o estilo da ÁREA do Notebook e do Frame interno
        style.configure(
            "Custom.TNotebook",
            background="#2A2D2E",  # Cor de fundo da área ao redor das abas e do conteúdo
            bordercolor="#1F1F1F",  # Cor da borda
        )

        # 3. Configura o estilo das ABAS (quando não selecionadas)
        style.configure(
            "Custom.TNotebook.Tab",
            background="#333333",  # Fundo da aba
            foreground="white",  # Cor do texto da aba
            font=("Arial", 11, "bold"),
            padding=[10, 5],  # Espaçamento (largura, altura)
        )

        # 4. Mapeia a cor de fundo e borda quando a aba está SELECIONADA
        style.map(
            "Custom.TNotebook.Tab",
            background=[
                ("selected", "#3C66E0")
            ],  # Cor de fundo da aba SELECIONADA (Azul)
            foreground=[("selected", "white")],
            expand=[("selected", [1, 1, 1, 0])],
        )

        # -----------------------------------------------------------
        # 🟢 FIM DA CUSTOMIZAÇÃO DO NOTEBOOK
        # -----------------------------------------------------------

        # 5. Cria o Notebook usando o novo estilo
        self.abas = ttk.Notebook(
            master, style="Custom.TNotebook"
        )  # 🟢 Aplica o novo estilo!

        user_level = self.current_user.get("NIVEL", "ALUNO")

        if user_level in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            frame_turmas = ctk.CTkFrame(self.abas)
            self.abas.add(frame_turmas, text="Gerenciar Turmas")
            GerenciarTurmasFrame(frame_turmas, self)

        if user_level == "ALUNO":
            frame_chatbot = ctk.CTkFrame(self.abas)
            self.abas.add(frame_chatbot, text="Assistente Acadêmico")
            Chatbot(frame_chatbot)

        frame_tabela = ctk.CTkFrame(self.abas)
        self.abas.add(frame_tabela, text="Tabela de Usuários")
        self.abas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.criar_tabela_frame(frame_tabela)

    def criar_tabela_frame(self, frame_tabela):
        """Cria o conteúdo da aba 'Tabela de Usuários', incluindo controles."""
        frame_controles = ctk.CTkFrame(frame_tabela)
        frame_controles.pack(fill="x", padx=10, pady=10)

        user_level = self.current_user.get("NIVEL", "NÃO AUTORIZADO")

        titulo = ctk.CTkLabel(
            frame_controles,
            text=f"Gerenciamento de Usuários (Nível: {user_level})",
            font=("Arial", 16, "bold"),
        )
        titulo.pack(pady=5)

        # --- Frame de Botões Padrão (Ver Dados) ---
        standard_buttons_frame = ctk.CTkFrame(frame_controles)
        standard_buttons_frame.pack(pady=(10, 15), fill="x", padx=20)

        # Este frame de controles específicos será usado pelo ALUNO
        frame_controles_especificos = ctk.CTkFrame(frame_controles)
        frame_controles_especificos.pack(fill="x", padx=10, pady=10)

        if user_level == "ALUNO":
            self._criar_controles_aluno(frame_controles_especificos)

        else:
            ctk.CTkButton(
                standard_buttons_frame,
                text="👤 Ver Meus Dados",
                command=self.abrir_janela_meus_dados,
                fg_color="#007BFF",
                font=("Arial", 12, "bold"),
            ).pack(side="left", padx=5, pady=5)

            if user_level == "ADMINISTRADOR":
                self._criar_controles_admin(frame_controles_especificos)
                filtros_container = ctk.CTkFrame(frame_controles)
                filtros_container.pack(fill="x", padx=10, pady=5)
                self.criar_widgets_filtro(filtros_container)

            elif user_level == "COORDENADOR":
                self._criar_controles_coordenador(frame_controles_especificos)
                filtros_container_coord = ctk.CTkFrame(frame_controles)
                filtros_container_coord.pack(fill="x", padx=10, pady=5)
                self.criar_widgets_filtro(filtros_container_coord)

            elif user_level == "PROFESSOR":
                self._criar_controles_professor(frame_controles_especificos)
                filtros_container_prof = ctk.CTkFrame(frame_controles)
                filtros_container_prof.pack(fill="x", padx=10, pady=5)
                self.criar_widgets_filtro(filtros_container_prof)

        # Frame da Tabela (comum a todos)
        self.frame_tabela_dados = ctk.CTkFrame(frame_tabela)
        self.frame_tabela_dados.pack(fill="both", expand=True, padx=10, pady=10)

    def _get_curso_da_turma(self, turma):
        """Helper para encontrar o curso associado a uma turma no CSV."""
        if self.data_frame_full is None:
            return "CURSO_DESCONHECIDO"

        # Busca linhas que tenham essa turma
        turma_upper = str(turma).strip().upper()
        rows = self.data_frame_full[self.data_frame_full["TURMAS"] == turma_upper]

        if not rows.empty:
            return rows.iloc[0]["CURSO"]
        return "CURSO_NAO_ENCONTRADO"

    def abrir_janela_realizar_atividades(self):
        """
        Abre uma janela listando todos os arquivos encontrados nas pastas
        'MATERIAL_PARA_ESTUDO' de todas as disciplinas da turma do aluno.
        """
        user_turma = self.current_user.get("TURMAS", "Turma_Desconhecida")
        user_curso = self.current_user.get("CURSO", "Curso_Desconhecido")

        # 1. Monta o caminho base da turma: Atividades > Curso > Turma
        pasta_base_turma = os.path.join(
            DIR_ATIVIDADES, str(user_curso), str(user_turma)
        )

        material_encontrado = []

        # 2. Varredura de arquivos
        if os.path.exists(pasta_base_turma):
            # Itera sobre cada disciplina (pastas dentro da turma)
            for nome_disciplina in os.listdir(pasta_base_turma):
                pasta_disciplina = os.path.join(pasta_base_turma, nome_disciplina)

                if os.path.isdir(pasta_disciplina):
                    # Verifica se existe a pasta MATERIAL_PARA_ESTUDO dentro da disciplina
                    pasta_material = os.path.join(
                        pasta_disciplina, "MATERIAL_PARA_ESTUDO"
                    )

                    if os.path.exists(pasta_material):
                        # Lista os arquivos dentro dessa pasta
                        for arquivo in os.listdir(pasta_material):
                            # Ignora arquivos ocultos
                            if not arquivo.startswith("."):
                                full_path = os.path.join(pasta_material, arquivo)
                                if os.path.isfile(full_path):
                                    material_encontrado.append(
                                        {
                                            "disciplina": nome_disciplina,
                                            "arquivo": arquivo,
                                            "caminho": full_path,
                                        }
                                    )

        # 3. Criação da Janela (UI)
        window = ctk.CTkToplevel(self)
        window.title("Mural de Atividades e Materiais")
        window.geometry("700x500")
        window.transient(self)
        window.grab_set()

        # Cabeçalho
        frame_top = ctk.CTkFrame(window)
        frame_top.pack(padx=20, pady=20, fill="x")

        ctk.CTkLabel(
            frame_top, text="Materiais Disponibilizados", font=("Arial", 18, "bold")
        ).pack()
        ctk.CTkLabel(
            frame_top,
            text=f"Curso: {user_curso} | Turma: {user_turma}",
            text_color="gray",
        ).pack()

        # Tabela
        frame_tabela = ctk.CTkFrame(window)
        frame_tabela.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        colunas = ("Disciplina", "Nome do Arquivo", "Tipo")
        tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        # Barras de rolagem
        vsb = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)

        tree.heading("Disciplina", text="Disciplina")
        tree.heading("Nome do Arquivo", text="Nome do Arquivo")
        tree.heading("Tipo", text="Extensão")

        tree.column("Disciplina", width=150, anchor="w")
        tree.column("Nome do Arquivo", width=300, anchor="w")
        tree.column("Tipo", width=80, anchor="center")

        tree.pack(fill="both", expand=True)

        # Preencher tabela
        if not material_encontrado:
            tree.insert("", "end", values=("---", "Nenhum material postado ainda.", ""))
        else:
            # Ordena por disciplina
            material_encontrado.sort(key=lambda x: x["disciplina"])

            for i, item in enumerate(material_encontrado):
                _, ext = os.path.splitext(item["arquivo"])
                tree.insert(
                    "",
                    "end",
                    iid=i,
                    values=(item["disciplina"], item["arquivo"], ext.upper()),
                )

        # 4. Botão de Download
        ctk.CTkButton(
            window,
            text="📥 Baixar Material Selecionado",
            command=lambda: self._baixar_material_estudo(tree, material_encontrado),
            fg_color="#007BFF",
            font=("Arial", 12, "bold"),
        ).pack(pady=15)

    def _baixar_material_estudo(self, tree, lista_materiais):
        """Função para baixar o arquivo selecionado na tabela de materiais."""
        selecionado = tree.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um arquivo para baixar.")
            return

        try:
            idx = int(selecionado)
            if idx >= len(lista_materiais):
                return  # Caso seja a linha de "nenhum material"

            dados = lista_materiais[idx]
            caminho_origem = dados["caminho"]
            nome_arquivo = dados["arquivo"]
            _, ext = os.path.splitext(nome_arquivo)

            # Abre diálogo para salvar
            caminho_destino = filedialog.asksaveasfilename(
                title="Salvar Material como...",
                initialfile=nome_arquivo,
                defaultextension=ext,
                filetypes=[(f"Arquivo {ext}", f"*{ext}"), ("Todos", "*.*")],
            )

            if caminho_destino:
                shutil.copy(caminho_origem, caminho_destino)
                messagebox.showinfo("Sucesso", "Material baixado com sucesso!")

        except ValueError:
            pass  # Clicou em linha vazia ou cabeçalho
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível baixar o arquivo.\n{e}")

    # =================================================================================
    # Criação de Controles (Por Nível) -------------------------------------------------
    # =================================================================================

    # ==========================
    # BOTÕES ALUNO MAIN APP

    def _criar_controles_aluno(self, master_frame):
        """Cria os botões específicos para o nível ALUNO."""
        # Ajuste de colunas para caber o novo botão (agora são 5 botões)
        master_frame.grid_columnconfigure(0, weight=1)
        master_frame.grid_columnconfigure(1, weight=1)
        master_frame.grid_columnconfigure(2, weight=1)
        master_frame.grid_columnconfigure(3, weight=1)
        master_frame.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(
            master_frame,
            text="Enviar Atividades",
            command=self.janela_envio_atividade_aluno,
            fg_color="#3A8A3A",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Ver Material de estudo",
            command=self.abrir_janela_realizar_atividades,
            fg_color="#FF9800",
            text_color="white",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Minhas Entregas",
            command=self.abrir_janela_atividades_enviadas,
            fg_color="#656563",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Meus Dados",
            command=self.abrir_janela_meus_dados,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Atualizar",
            command=lambda: self.atualizar_tabela(reload_csv=True),
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=4, padx=5, pady=5, sticky="ew")

    # =================================================================================
    # BOTÕES ADMIN MAIN APP

    def _criar_controles_admin(self, master_frame):
        """Cria os botões específicos para o nível ADMINISTRADOR."""
        # Aumentado para 11 colunas
        for i in range(11):
            master_frame.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(
            master_frame,
            text="Ativar Aluno",
            command=self.ativar_aluno,
            fg_color="#3A8A3A",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Desativar Aluno",
            command=self.desativar_aluno,
            fg_color="#E03C31",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Editar Usuário",
            command=self.abrir_janela_edicao_usuario,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="❌ Excluir Usuário",
            command=self.excluir_usuario,
            fg_color="#CC0000",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="➕ Adicionar Usuário",
            command=self.abrir_janela_novo_usuario,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Salvar Alterações",
            command=self.salvar_dados,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(
            master_frame, text="| Filtros Rápidos:", font=("Arial", 12, "bold")
        ).grid(row=0, column=6, padx=10)
        ctk.CTkButton(
            master_frame,
            text="Mostrar Ativos",
            command=lambda: self.filtrar_por_status("ATIVO"),
            fg_color="#3A8A3A",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=7, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Mostrar Inativos",
            command=lambda: self.filtrar_por_status("INATIVO"),
            fg_color="#FF9800",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=8, padx=5, pady=5, sticky="ew")
        self.btn_toggle_senhas = ctk.CTkButton(
            master_frame,
            text="Mostrar Senhas",
            command=self.abrir_janela_visualizacao_senhas,
            fg_color="#5A5E5B",
            font=("Arial", 12, "bold"),
        )
        self.btn_toggle_senhas.grid(row=0, column=9, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Atualizar",
            command=lambda: self.atualizar_tabela(reload_csv=True),
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=10, padx=5, pady=5, sticky="ew")

    # =================================================================================
    # BOTÕES COORDENADOR MAIN APP

    def _criar_controles_coordenador(self, master_frame):
        """Cria os botões específicos para o nível COORDENADOR."""
        # Ajustado para 6 colunas
        for i in range(6):
            master_frame.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(
            master_frame,
            text="🟢 Ativar Aluno",
            command=self.ativar_aluno,
            fg_color="#3A8A3A",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="🔴 Desativar Aluno",
            command=self.desativar_aluno,
            fg_color="#E03C31",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Editar Usuário",
            command=self.abrir_janela_edicao_usuario,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="➕ Adicionar Usuário",
            command=self.abrir_janela_novo_usuario,
            fg_color="#007BFF",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Salvar Alterações",
            command=self.salvar_dados,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            master_frame,
            text="Atualizar Arquivo",
            command=lambda: self.atualizar_tabela(reload_csv=True),
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=5, padx=5, pady=5, sticky="ew")

    # =================================================================================
    # BOTÕES PROFESSOR MAIN APP

    def _criar_controles_professor(self, master_frame):
        """Cria os botões específicos para o nível PROFESSOR."""
        for i in range(3):
            master_frame.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(
            master_frame,
            text="Lançar/Editar Notas",
            command=self.abrir_janela_edicao_notas,
            fg_color="#3A8A3A",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Salvar Alterações",
            command=self.salvar_dados,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            master_frame,
            text="Atualizar",
            command=lambda: self.atualizar_tabela(reload_csv=True),
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    # ==================================================================
    # Lógica da Tabela Principal (CRUD, Filtros, Salvar) ---------------

    def atualizar_tabela(
        self,
        reload_csv=True,
        filter_status=None,
        general_filter_text=None,
        filter_column=None,
    ):
        """Filtra e atualiza o DataFrame principal com base no nível de usuário e filtros."""
        if reload_csv:
            self.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
        if self.data_frame_full is None or self.data_frame_full.empty:
            self.data_frame = pd.DataFrame()
            self.mostrar_tabela(self.data_frame)
            return

        df_display = self.data_frame_full.copy()
        user_level = self.current_user["NIVEL"]
        columns_to_drop = []
        rows_filter = None

        if user_level == "ALUNO":
            user_id = self.current_user["ID"]
            rows_filter = df_display["ID"] == user_id
            columns_to_drop.extend(
                ["STATUS DO ALUNO", "SENHA", "TURMAS", "EMAIL", "IDADE", "NIVEL"]
            )
        elif user_level == "PROFESSOR":
            rows_filter = df_display["NIVEL"] == "ALUNO"
            columns_to_drop.append("SENHA")
            columns_to_drop.append("EMAIL")
            columns_to_drop.append("IDADE")

        elif user_level == "COORDENADOR":
            rows_filter = df_display["NIVEL"].isin(
                ["ALUNO", "PROFESSOR", "COORDENADOR"]
            )
            columns_to_drop.append("SENHA")
            columns_to_drop.extend(["NP1", "NP2", "PIM"])
            # columns_to_drop.append("TURMAS")

        elif user_level == "ADMINISTRADOR":
            if not self.password_column_visible:
                columns_to_drop.append("SENHA")

        if rows_filter is not None:
            df_display = df_display[rows_filter].copy()

        cols_to_drop_final = [
            col for col in columns_to_drop if col in df_display.columns
        ]
        if cols_to_drop_final:
            df_display = df_display.drop(columns=cols_to_drop_final)

        if user_level in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            if filter_status:
                df_display = df_display[
                    df_display["STATUS DO ALUNO"] == filter_status.upper()
                ]
            if (
                general_filter_text
                and filter_column
                and filter_column in df_display.columns
            ):
                search_term = general_filter_text.lower()
                df_display = df_display[
                    df_display[filter_column]
                    .astype(str)
                    .str.lower()
                    .str.contains(search_term, na=False)
                ]

        self.data_frame = df_display.reset_index(drop=True)
        self.mostrar_tabela(self.data_frame)

        if reload_csv and user_level in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            messagebox.showinfo(
                "Atualização", "Tabela recarregada a partir do arquivo CSV."
            )

    # =================================================================================
    # Exibe os dados na tela. Aluno tem cores/resultado; Outros têm visual padrão limpo

    def mostrar_tabela(self, df):
        for w in self.frame_tabela_dados.winfo_children():
            w.destroy()

        if df.empty:
            ctk.CTkLabel(self.frame_tabela_dados, text="Nenhum dado encontrado.").pack(
                pady=20
            )
            self.tabela_widget = None
            return

        # ==============================================================================
        # VISUALIZAÇÃO DO ALUNO (Customizada: Cores nas Células + Coluna Resultado)

        if self.current_user["NIVEL"] == "ALUNO":
            df_visual = df.copy()

            # Cria coluna RESULTADO (Apenas visual)
            df_visual["RESULTADO"] = df_visual["MEDIA"].apply(
                lambda x: "APROVADO" if float(x) >= 7.0 else "REPROVADO"
            )

            colunas = list(df_visual.columns)

            # Grid Rolável
            frame_grid = ctk.CTkScrollableFrame(
                self.frame_tabela_dados, orientation="horizontal", height=150
            )
            frame_grid.pack(fill="both", expand=True, padx=10, pady=10)

            # Cabeçalho
            for idx, col in enumerate(colunas):
                ctk.CTkLabel(frame_grid, text=col, font=("Arial", 14, "bold")).grid(
                    row=0, column=idx, padx=15, pady=5
                )

            # Linhas
            for r_idx, row in df_visual.iterrows():
                for c_idx, col in enumerate(colunas):
                    valor = row[col]
                    cor_texto = None  # Cor padrão

                    # Regra de Cores (Só para Aluno)
                    if col == "RESULTADO":
                        cor_texto = "#00C853" if valor == "APROVADO" else "#FF3D00"
                    elif col in ["NP1", "NP2", "PIM", "MEDIA"]:
                        try:
                            cor_texto = "#00C853" if float(valor) >= 7.0 else "#FF3D00"
                        except:
                            pass

                    ctk.CTkLabel(
                        frame_grid,
                        text=str(valor),
                        text_color=cor_texto if cor_texto else ("black", "white"),
                        font=("Arial", 14),
                    ).grid(row=r_idx + 1, column=c_idx, padx=15, pady=10)

            self.tabela_widget = None
            return

        # ==============================================================================
        # VISUALIZAÇÃO DE ADMIN / PROF / COORD (Padrão Treeview SEM CORES)

        colunas_padrao = list(df.columns)
        tree = ttk.Treeview(
            self.frame_tabela_dados, columns=colunas_padrao, show="headings"
        )

        # Scrollbars
        vsb = ttk.Scrollbar(
            self.frame_tabela_dados, orient="vertical", command=tree.yview
        )
        hsb = ttk.Scrollbar(
            self.frame_tabela_dados, orient="horizontal", command=tree.xview
        )
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # Cabeçalho
        for col in colunas_padrao:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        # Dados (Inserção Simples, sem tags de cor)
        for i, row in df.iterrows():
            vals = list(row)
            tree.insert("", "end", iid=i, values=vals)

        self.tabela_widget = tree

    def salvar_dados(self):
        """
        Salva o self.data_frame_full de volta no arquivo CSV.
        MODIFICAÇÃO: Garante que os floats sejam salvos com vírgula (,) como separador decimal.
        """
        if self.current_user["NIVEL"] not in [
            "ADMINISTRADOR",
            "COORDENADOR",
            "PROFESSOR",
        ]:
            messagebox.showwarning(
                "Permissão Negada",
                "Somente Admin, Coordenador ou Professor (para salvar notas) podem salvar alterações.",
            )
            return
        if self.data_frame_full is None or self.data_frame_full.empty:
            messagebox.showwarning(
                "Salvar",
                "Não foi possível salvar, o banco de dados está vazio ou não foi carregado.",
            )
            return
        try:
            df_to_save = self.data_frame_full.copy()
            column_map_save = {
                "ID": "id",
                "NOME": "nome",
                "EMAIL": "email",
                "SENHA": "senha",
                "IDADE": "idade",
                "NIVEL": "nivel",
                "CURSO": "curso",
                "TURMAS": "turma",
                "NP1": "np1",
                "NP2": "np2",
                "PIM": "pim",
                "MEDIA": "media",
                "STATUS DO ALUNO": "atividade",
            }
            df_to_save.rename(columns=column_map_save, inplace=True)
            final_csv_cols = [
                "id",
                "nome",
                "email",
                "senha",
                "nivel",
                "curso",
                "turma",
                "idade",
                "np1",
                "np2",
                "pim",
                "media",
                "atividade",
            ]
            df_to_save = df_to_save.reindex(columns=final_csv_cols)

            # Formata colunas numéricas para salvar com VÍRGULA (,)
            for col in ["np1", "np2", "pim", "media"]:
                if col in df_to_save.columns:
                    df_to_save[col] = df_to_save[col].apply(
                        lambda x: (
                            f"{x:.2f}".replace(".", ",")  # 1.23 -> "1.23" -> "1,23"
                            if pd.notna(x) and pd.notnull(x)
                            else ""
                        )
                    )

            Path(CAMINHO_ARQUIVO).parent.mkdir(parents=True, exist_ok=True)
            with open(CAMINHO_ARQUIVO, "w", encoding="utf-8", newline="") as f:
                f.write("[USUARIOS]\n")
                df_to_save.to_csv(
                    f, sep=";", index=False, header=True, lineterminator="\r\n"
                )
            messagebox.showinfo(
                "Salvo",
                "Todas as alterações (Status e Edições) foram salvas com sucesso no arquivo CSV.",
            )
            self.atualizar_tabela(reload_csv=True)

            # Atualiza a aba "Gerenciar Turmas" se ela existir
            for widget in self.abas.winfo_children():
                if isinstance(
                    widget, ctk.CTkFrame
                ) and "Gerenciar Turmas" in self.abas.tab(widget, "text"):
                    for child in widget.winfo_children():
                        if isinstance(child, GerenciarTurmasFrame):
                            child.atualizar_tabela_turmas()
                            break
        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar os dados: {e}"
            )

    # =================================================================================
    # Cria os widgets de filtro (Combobox e Entry) para Admin/Coord/Prof

    def criar_widgets_filtro(self, master_frame):
        ctk.CTkLabel(master_frame, text="Filtrar por:").grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="w"
        )
        colunas_filtro = ["Filtrar por Coluna..."]
        if self.data_frame_full is not None and not self.data_frame_full.empty:
            lista_completa_colunas = self.data_frame_full.columns.tolist()
            colunas_a_excluir = ["SENHA", "STATUS DO ALUNO"]
            colunas_filtradas = [
                coluna
                for coluna in lista_completa_colunas
                if coluna not in colunas_a_excluir
            ]
            colunas_filtro.extend(colunas_filtradas)

        self.combo_filtro_coluna = ctk.CTkComboBox(
            master_frame, values=colunas_filtro, width=180
        )
        self.combo_filtro_coluna.grid(row=0, column=1, padx=5, pady=10, sticky="w")
        self.entrada_filtro_geral = ctk.CTkEntry(
            master_frame, placeholder_text="Digite o valor...", width=180
        )
        self.entrada_filtro_geral.grid(row=0, column=2, padx=5, pady=10, sticky="w")
        ctk.CTkButton(
            master_frame,
            text="Buscar",
            command=self.filtrar_geral,
            width=80,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=3, padx=5, pady=10, sticky="w")
        ctk.CTkButton(
            master_frame,
            text="Limpar Filtros",
            command=self.limpar_filtros,
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=4, padx=(20, 10), pady=10, sticky="w")

    def filtrar_por_status(self, status):
        """Filtro rápido para status ATIVO/INATIVO."""
        if self.current_user["NIVEL"] in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            self.atualizar_tabela(reload_csv=False, filter_status=status)
        else:
            messagebox.showwarning(
                "Permissão Negada",
                "Filtros rápidos são exclusivos para Admin, Coordenador ou Professor.",
            )

    def filtrar_geral(self):
        """Filtro geral por coluna e texto."""
        if self.current_user["NIVEL"] not in [
            "ADMINISTRADOR",
            "COORDENADOR",
            "PROFESSOR",
        ]:
            messagebox.showwarning(
                "Permissão Negada",
                "Filtros são exclusivos para Admin, Coordenador ou Professor.",
            )
            return
        coluna = self.combo_filtro_coluna.get()
        texto = self.entrada_filtro_geral.get().strip()
        if coluna == "Filtrar por Coluna..." or not texto:
            messagebox.showwarning(
                "Filtro", "Selecione uma coluna e digite um valor de busca."
            )
            return
        self.atualizar_tabela(
            reload_csv=False, general_filter_text=texto, filter_column=coluna
        )

    def limpar_filtros(self):
        """Limpa todos os filtros aplicados na tabela principal."""
        if self.current_user["NIVEL"] in ["ADMINISTRADOR", "COORDENADOR", "PROFESSOR"]:
            self.combo_filtro_coluna.set("Filtrar por Coluna...")
            self.entrada_filtro_geral.delete(0, tk.END)
            self.atualizar_tabela(reload_csv=False)
        else:
            messagebox.showwarning(
                "Permissão Negada",
                "Limpar filtros é exclusivo para Admin, Coordenador ou Professor.",
            )

    def excluir_usuario(self):
        """Exclui permanentemente um usuário (Somente Admin)."""
        if self.current_user["NIVEL"] != "ADMINISTRADOR":
            messagebox.showwarning(
                "Permissão Negada", "Somente usuários ADMIN podem excluir usuários."
            )
            return
        if self.tabela_widget is None:
            return
        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione uma linha para excluir.")
            return
        try:
            idx_visible = int(selecionado)
            user_id = self.data_frame.loc[idx_visible, "ID"]
            user_nome = self.data_frame.loc[idx_visible, "NOME"]
            if not messagebox.askyesno(
                "Confirmação de Exclusão",
                f"Tem certeza que deseja EXCLUIR o usuário ID {user_id} ({user_nome})? Esta ação é permanente.",
            ):
                return
            idx_full_list = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index
            if not idx_full_list.empty:
                self.data_frame_full.drop(idx_full_list, inplace=True)
                self.salvar_dados()
                messagebox.showinfo(
                    "Sucesso", f"Usuário ID {user_id} excluído e arquivo CSV salvo."
                )
            else:
                messagebox.showwarning(
                    "Erro",
                    f"Usuário ID {user_id} não encontrado no banco de dados completo.",
                )
        except Exception as e:
            messagebox.showerror(
                "Erro de Exclusão", f"Ocorreu um erro ao excluir o usuário: {e}"
            )

    def _atualizar_status_aluno(self, novo_status):
        """Função para ativar ou desativar um aluno."""
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if self.tabela_widget is None:
            return

        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning(
                "Seleção", f"Selecione uma linha para {novo_status.lower()}."
            )
            return

        try:
            idx_visible = int(selecionado)
            user_id = self.data_frame.loc[idx_visible, "ID"]

            idx_full_list = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index

            if not idx_full_list.empty:
                idx_full = idx_full_list[0]
                self.data_frame_full.loc[idx_full, "STATUS DO ALUNO"] = novo_status

                if "STATUS DO ALUNO" in self.data_frame.columns:
                    self.data_frame.loc[idx_visible, "STATUS DO ALUNO"] = novo_status

                current_values = list(self.data_frame.loc[idx_visible].values)
                if "MEDIA" in self.data_frame.columns:
                    media_index = self.data_frame.columns.tolist().index("MEDIA")
                    current_values[media_index] = (
                        f"{float(current_values[media_index]):.2f}"
                    )
                self.tabela_widget.item(selecionado, values=current_values)

                messagebox.showinfo(
                    "Status",
                    f"Aluno ID {user_id} definido como {novo_status}. Lembre-se de SALVAR as alterações.",
                )
            else:
                messagebox.showwarning(
                    "Erro",
                    f"Não foi possível encontrar o usuário ID {user_id} no banco de dados completo.",
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar o status: {e}")

    def ativar_aluno(self):
        """Define o status do aluno selecionado como ATIVO."""
        self._atualizar_status_aluno("ATIVO")

    def desativar_aluno(self):
        """Define o status do aluno selecionado como INATIVO."""
        self._atualizar_status_aluno("INATIVO")

    # =================================================================================
    # Pop-ups de Edição e Visualização de Usuários ---
    # =================================================================================

    # =================================================================================
    # Abre uma janela mostrando os dados do usuário logado.

    def abrir_janela_meus_dados(self):
        user_data = self.current_user
        if user_data is None:
            messagebox.showwarning("Aviso", "Nenhum usuário logado.")
            return

        dados_window = ctk.CTkToplevel(self)
        dados_window.title("Meus Dados Cadastrais")
        dados_window.geometry("450x450")
        dados_window.transient(self)
        dados_window.grab_set()

        form_frame = ctk.CTkFrame(dados_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        is_notes_user = user_data.get("NIVEL") != "COORDENADOR"

        dados_para_exibir = [
            ("ID", "ID"),
            ("NOME", "Nome Completo"),
            ("EMAIL", "Email"),
            ("IDADE", "Idade"),
            ("NIVEL", "Nível de Acesso"),
            ("CURSO", "Curso"),
            ("TURMAS", "Turma"),
            ("STATUS DO ALUNO", "Status da Matrícula"),
        ]

        for i, (key, label_text) in enumerate(dados_para_exibir):
            label = ctk.CTkLabel(
                form_frame, text=f"{label_text}:", font=("Arial", 12, "bold")
            )
            label.grid(row=i, column=0, padx=10, pady=8, sticky="e")

            valor = user_data.get(key)
            valor_display = "N/A"

            if key == "STATUS DO ALUNO":
                valor_display = str(valor).upper() if valor else "N/A"
            elif key in ["NP1", "NP2", "PIM", "MEDIA"]:
                try:
                    valor_display = f"{float(valor):.2f}"
                except (ValueError, TypeError):
                    valor_display = str(valor)
            else:
                valor_display = str(valor)

            value_label = ctk.CTkLabel(
                form_frame, text=valor_display, text_color="gray"
            )
            value_label.grid(row=i, column=1, padx=10, pady=8, sticky="w")

        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=2)

    def abrir_janela_novo_usuario(self):
        """Abre o pop-up para adicionar um novo usuário (Admin/Coord)."""
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        add_window = ctk.CTkToplevel(self)
        add_window.title("Adicionar Novo Usuário")
        add_window.geometry("400x600")
        add_window.transient(self)
        add_window.grab_set()
        form_frame = ctk.CTkFrame(add_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        entries = {}
        editaveis = [
            "NOME",
            "EMAIL",
            "SENHA",
            "IDADE",
            "CURSO",
            "TURMAS",
            "NIVEL",
            "NP1",
            "NP2",
            "PIM",
        ]
        for i, col in enumerate(editaveis):
            label_text = "TURMA" if col == "TURMAS" else col.replace("_", " ")
            ctk.CTkLabel(form_frame, text=f"{label_text}:").grid(
                row=i, column=0, padx=10, pady=5, sticky="w"
            )
            entry = ctk.CTkEntry(form_frame, width=250)
            if col in ["NP1", "NP2", "PIM", "IDADE"]:
                entry.insert(0, "0")
            elif col == "NIVEL":
                entry.insert(0, "ALUNO")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[col] = entry
        ctk.CTkButton(
            form_frame,
            text="Adicionar e Salvar Usuário",
            command=lambda: self.salvar_novo_usuario(entries, add_window),
            fg_color="green",
        ).grid(
            row=len(editaveis), column=0, columnspan=2, padx=10, pady=20, sticky="ew"
        )

    def salvar_novo_usuario(self, entries, window):
        """Valida e salva o novo usuário no DataFrame e no CSV."""
        try:
            new_user_data = {}
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                if not new_value and col not in ["NP1", "NP2", "PIM", "IDADE"]:
                    messagebox.showerror(
                        "Erro de Validação", f"O campo '{col}' não pode estar vazio."
                    )
                    return
                if col in ["IDADE", "NP1", "NP2", "PIM"]:
                    try:
                        new_value_converted = 0 if not new_value else float(new_value)
                        if col in ["NP1", "NP2", "PIM"] and not (
                            0 <= new_value_converted <= 10
                        ):
                            messagebox.showerror(
                                "Erro", f"Notas devem estar entre 0 e 10."
                            )
                            return
                        new_user_data[col] = new_value_converted
                    except ValueError:
                        messagebox.showerror(
                            "Erro", f"O campo '{col}' deve ser um número."
                        )
                        return
                elif col in ["NOME", "NIVEL", "CURSO"]:
                    new_user_data[col] = new_value.upper()
                elif col == "EMAIL":
                    new_user_data[col] = new_value.lower()
                elif col == "TURMAS":
                    new_user_data[col] = new_value
                elif col == "SENHA":
                    new_user_data[col] = new_value

            turma_nova = new_user_data.get("TURMAS", "")
            curso_novo = new_user_data.get("CURSO", "")

            if turma_nova and curso_novo:
                valido, msg_erro = self._validar_turma_curso(turma_nova, curso_novo)
                if not valido:
                    messagebox.showerror(
                        "Erro de Validação de Turma", msg_erro, parent=window
                    )
                    return

            new_user_data["ID"] = self._gerar_novo_id()
            new_user_data["STATUS DO ALUNO"] = "ATIVO"
            np1 = new_user_data.get("NP1", 0)
            np2 = new_user_data.get("NP2", 0)
            pim = new_user_data.get("PIM", 0)
            media = (np1 * 4 + np2 * 4 + pim * 2) / 10
            new_user_data["MEDIA"] = round(media, 2)

            colunas_completas = self.data_frame_full.columns
            for col in colunas_completas:
                if col not in new_user_data:
                    new_user_data[col] = (
                        0 if col in ["IDADE", "NP1", "NP2", "PIM", "MEDIA"] else ""
                    )

            new_user_df = pd.DataFrame([new_user_data])
            new_user_df = new_user_df[colunas_completas]
            self.data_frame_full = pd.concat(
                [self.data_frame_full, new_user_df], ignore_index=True
            )
            self.salvar_dados()
            messagebox.showinfo(
                "Sucesso",
                f"Novo usuário '{new_user_data['NOME']}' (ID: {new_user_data['ID']}) adicionado com sucesso!",
            )
            window.destroy()
        except Exception as e:
            messagebox.showerror("Erro ao Salvar Novo Usuário", f"Ocorreu um erro: {e}")

    def abrir_janela_edicao_usuario(self):
        """Abre o pop-up para editar um usuário existente (Admin/Coord), com autenticação para edição de senha."""

        # --- (Verificações de Nível de Acesso e Seleção) ---
        if self.current_user["NIVEL"] not in ["ADMINISTRADOR", "COORDENADOR"]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return

        if not isinstance(self.tabela_widget, ttk.Treeview):
            messagebox.showwarning("Aviso", "A tabela não está carregada.")
            return

        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning("Seleção", "Selecione um usuário para editar.")
            return

        idx = int(selecionado)
        user_data_series = self.data_frame.loc[idx]
        user_id = user_data_series["ID"]
        full_user_data_row = self.data_frame_full[self.data_frame_full["ID"] == user_id]
        if full_user_data_row.empty:
            messagebox.showerror("Erro", "Dados completos do usuário não encontrados.")
            return

        full_user_data = full_user_data_row.iloc[0]
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Editar Usuário ID: {user_id}")
        edit_window.geometry("450x650")
        edit_window.transient(self)
        edit_window.grab_set()
        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        entries = {}

        editaveis = [
            "NOME",
            "EMAIL",
            "IDADE",
            "CURSO",
            "TURMAS",
            "NIVEL",
            "NP1",
            "NP2",
            "PIM",
        ]

        # Criação dos campos NOME a PIM
        for i, col in enumerate(editaveis):
            if col in full_user_data.index:
                label_text = "TURMA" if col == "TURMAS" else col.replace("_", " ")
                ctk.CTkLabel(form_frame, text=f"{label_text}:").grid(
                    row=i, column=0, padx=10, pady=5, sticky="w"
                )
                entry = ctk.CTkEntry(form_frame, width=250)
                entry.insert(0, str(full_user_data[col]))
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entries[col] = entry

        # --------------------------------------------------------------------
        # 🟢 NOVO FLUXO DE SEGURANÇA PARA EDIÇÃO DE SENHA
        # --------------------------------------------------------------------

        row_senha = len(editaveis)

        # 1. Campo de Senha - Inicialmente BLOQUEADO e OCULTO
        ctk.CTkLabel(form_frame, text="SENHA:").grid(
            row=row_senha, column=0, padx=10, pady=5, sticky="w"
        )
        senha_entry = ctk.CTkEntry(form_frame, width=250, show="*", state="disabled")
        senha_entry.insert(0, full_user_data["SENHA"])
        senha_entry.grid(row=row_senha, column=1, padx=10, pady=5, sticky="ew")
        entries["SENHA"] = senha_entry

        def abrir_janela_edicao_senha():
            """Abre uma janela para autenticar o usuário logado (Admin/Coord) antes de permitir a edição da senha."""

            auth_window = ctk.CTkToplevel(edit_window)
            auth_window.title("Autenticação de Segurança")
            auth_window.geometry("350x200")
            auth_window.transient(edit_window)
            auth_window.grab_set()

            ctk.CTkLabel(
                auth_window,
                text="Para habilitar a edição de senha, digite \n sua senha (Admin/Coord):",
            ).pack(pady=10)

            auth_senha_entry = ctk.CTkEntry(auth_window, width=250, show="*")
            auth_senha_entry.pack(pady=5)

            def check_and_enable():
                entered_password = auth_senha_entry.get()
                current_user_password = self.current_user.get("SENHA")

                if entered_password == current_user_password:
                    # Sucesso: Desbloqueia e mostra a senha

                    # Vazio a segurança, limpar o campo antes de re-inserir.
                    senha_entry.delete(0, ctk.END)

                    # Habilita e configura para mostrar o texto
                    senha_entry.configure(state="normal", show="")

                    # RE-INSERE A SENHA ORIGINAL EM TEXTO CLARO
                    senha_original = full_user_data["SENHA"]
                    senha_entry.insert(0, str(senha_original))

                    enable_button.configure(
                        text="SENHA HABILITADA (Editável)", state="disabled"
                    )
                    auth_window.destroy()
                    messagebox.showinfo(
                        "Sucesso", "Edição de senha habilitada e visível."
                    )
                else:
                    messagebox.showerror("Erro", "Senha de autenticação incorreta.")
                    auth_senha_entry.delete(0, ctk.END)

            ctk.CTkButton(
                auth_window,
                text="Confirmar Autenticação",
                command=check_and_enable,
                font=("Arial", 12, "bold"),
            ).pack(pady=10)

        # 2. Botão de Autenticação
        enable_button = ctk.CTkButton(
            form_frame,
            text="Habilitar Edição de Senha",
            font=("Arial", 12, "bold"),
            command=abrir_janela_edicao_senha,
        )
        enable_button.grid(
            row=row_senha + 1, column=1, padx=10, pady=(0, 15), sticky="w"
        )

        # --------------------------------------------------------------------
        # FIM DO NOVO FLUXO DE SEGURANÇA
        # --------------------------------------------------------------------

        ctk.CTkButton(
            form_frame,
            text="Salvar Alterações",
            command=lambda: self.salvar_edicao_usuario(user_id, entries, edit_window),
            font=("Arial", 12, "bold"),
        ).grid(row=row_senha + 2, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

    def salvar_edicao_usuario(self, user_id, entries, window):
        """Valida e salva as edições do usuário no DataFrame e no CSV."""
        try:
            # Precisamos pegar os valores *novos* antes de salvar
            turma_nova = entries.get("TURMAS").get().strip()
            curso_novo = entries.get("CURSO").get().strip().upper()

            if turma_nova and curso_novo:
                valido, msg_erro = self._validar_turma_curso(
                    turma_nova, curso_novo, user_id_to_ignore=user_id
                )
                if not valido:
                    messagebox.showerror(
                        "Erro de Validação de Turma", msg_erro, parent=window
                    )
                    return

            user_index = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index[0]
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                if col in ["IDADE", "NP1", "NP2", "PIM"]:
                    try:
                        new_value_converted = 0 if not new_value else float(new_value)
                        if col in ["NP1", "NP2", "PIM"] and not (
                            0 <= new_value_converted <= 10
                        ):
                            messagebox.showerror(
                                "Erro", f"Notas devem estar entre 0 e 10."
                            )
                            return
                        self.data_frame_full.loc[user_index, col] = new_value_converted
                    except ValueError:
                        messagebox.showerror(
                            "Erro", f"O campo '{col}' deve ser um número."
                        )
                        return
                elif col in ["NOME", "NIVEL", "CURSO"]:
                    self.data_frame_full.loc[user_index, col] = new_value.upper()
                elif col == "EMAIL":
                    self.data_frame_full.loc[user_index, col] = new_value.lower()
                elif col == "TURMAS":
                    self.data_frame_full.loc[user_index, col] = new_value
                elif col == "SENHA":
                    self.data_frame_full.loc[user_index, col] = new_value

            if all(
                col in self.data_frame_full.columns for col in ["NP1", "NP2", "PIM"]
            ):
                row = self.data_frame_full.loc[user_index]
                media = (row["NP1"] * 4 + row["NP2"] * 4 + row["PIM"] * 2) / 10
                self.data_frame_full.loc[user_index, "MEDIA"] = media

            self.salvar_dados()
            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            window.destroy()
        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar as alterações: {e}"
            )

    # ============================================
    # Abre o pop-up de edição de notas (Professor)

    def abrir_janela_edicao_notas(self):
        if self.current_user["NIVEL"] != "PROFESSOR":
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return
        if not isinstance(self.tabela_widget, ttk.Treeview):
            messagebox.showwarning("Aviso", "A tabela não está carregada.")
            return
        selecionado = self.tabela_widget.focus()
        if not selecionado:
            messagebox.showwarning(
                "Seleção", "Selecione um ALUNO para editar as notas."
            )
            return

        idx = int(selecionado)
        user_data_series = self.data_frame.loc[idx]
        if user_data_series["NIVEL"] != "ALUNO":
            messagebox.showwarning(
                "Ação Inválida",
                "Você só pode editar as notas de usuários do nível ALUNO.",
            )
            return

        user_id = user_data_series["ID"]
        full_user_data_row = self.data_frame_full[self.data_frame_full["ID"] == user_id]
        if full_user_data_row.empty:
            messagebox.showerror("Erro", "Dados completos do usuário não encontrados.")
            return

        full_user_data = full_user_data_row.iloc[0]
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Lançar Notas - Aluno ID: {user_id}")
        edit_window.geometry("400x300")
        edit_window.transient(self)
        edit_window.grab_set()
        form_frame = ctk.CTkFrame(edit_window)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        ctk.CTkLabel(form_frame, text="Aluno:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        ctk.CTkLabel(
            form_frame, text=f"{full_user_data['NOME']}", font=("Arial", 12, "bold")
        ).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        entries = {}
        editaveis = ["NP1", "NP2", "PIM"]
        for i, col in enumerate(editaveis):
            ctk.CTkLabel(form_frame, text=f"{col}:").grid(
                row=i + 1, column=0, padx=10, pady=5, sticky="w"
            )
            entry = ctk.CTkEntry(form_frame, width=250)
            entry.insert(0, str(full_user_data[col]))
            entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="ew")
            entries[col] = entry

        ctk.CTkButton(
            form_frame,
            text="Salvar Notas",
            command=lambda: self.salvar_edicao_notas(user_id, entries, edit_window),
            fg_color="green",
        ).grid(
            row=len(editaveis) + 1,
            column=0,
            columnspan=2,
            padx=10,
            pady=20,
            sticky="ew",
        )

    def salvar_edicao_notas(self, user_id, entries, window):
        """Valida e salva as notas do aluno no DataFrame e no CSV."""
        try:
            user_index = self.data_frame_full[
                self.data_frame_full["ID"] == user_id
            ].index[0]
            for col, entry_widget in entries.items():
                new_value = entry_widget.get().strip()
                try:
                    new_value_converted = 0 if not new_value else float(new_value)
                    if not (0 <= new_value_converted <= 10):
                        messagebox.showerror(
                            "Erro de Validação",
                            f"A nota {col} deve estar entre 0 e 10.",
                        )
                        return
                    self.data_frame_full.loc[user_index, col] = new_value_converted
                except ValueError:
                    messagebox.showerror(
                        "Erro de Validação",
                        f"O campo '{col}' deve ser um número (use . para decimais).",
                    )
                    return

            row = self.data_frame_full.loc[user_index]
            media = (row["NP1"] * 4 + row["NP2"] * 4 + row["PIM"] * 2) / 10
            self.data_frame_full.loc[user_index, "MEDIA"] = round(media, 2)
            self.salvar_dados()
            messagebox.showinfo("Sucesso", "Notas do aluno atualizadas com sucesso!")
            window.destroy()
        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar", f"Ocorreu um erro ao salvar as notas: {e}"
            )

    # ===========================================================
    # JANELA DE AUTENTICAÇÃO PARA VISIBILIDADE DA COLUNA SENHA - UI ADMIN

    def abrir_janela_visualizacao_senhas(self):
        # Variável para armazenar a senha digitada
        self.auth_password_input = None

        def popup_seguranca():
            """Cria e abre o pop-up de autenticação segura."""
            auth_window = ctk.CTkToplevel(self)
            auth_window.title("Autorização Necessária")
            auth_window.geometry("300x180")
            auth_window.transient(self)
            auth_window.grab_set()
            auth_window.resizable(False, False)

            # --- 1. UI da Pop-up ---

            ctk.CTkLabel(
                auth_window,
                text="Para desbloquear a coluna SENHAS, digite sua senha de acesso:",
                wraplength=250,
            ).pack(pady=(15, 10))

            # Campo de senha SEGURO (show="*")
            password_entry = ctk.CTkEntry(
                auth_window, placeholder_text="Senha", show="*", width=200
            )
            password_entry.pack(pady=5)
            password_entry.focus_set()

            def confirm_password():
                """Ação de confirmação da senha."""
                self.auth_password_input = password_entry.get()
                auth_window.destroy()

            ctk.CTkButton(auth_window, text="Confirmar", command=confirm_password).pack(
                pady=10
            )

            # Garante que pressionar Enter também funcione
            password_entry.bind("<Return>", lambda event: confirm_password())

            # Bloqueia a execução do código principal até a janela fechar
            self.wait_window(auth_window)

        # --- 1. Execução do Diálogo Seguro ---
        popup_seguranca()

        input_password = self.auth_password_input

        if not input_password:
            # Será None se o usuário fechar a janela ou clicar em fechar
            return

        # --- 2. Verificar a senha do admin logado ---
        admin_password = str(self.current_user.get("SENHA", ""))

        if input_password != admin_password:
            messagebox.showerror("Acesso Negado", "Senha incorreta.")
            return

        # --- 3. Senha correta, alternar o estado ---
        self.password_column_visible = not self.password_column_visible

        # --- 4. Atualizar o texto e a cor do botão ---
        if self.password_column_visible:
            self.btn_toggle_senhas.configure(
                text="🙈 Ocultar Senhas", fg_color="#4CAF50"
            )  # Verde
        else:
            self.btn_toggle_senhas.configure(
                text="👁️ Mostrar Senhas", fg_color="#E03C31"
            )  # Vermelho

        # --- 5. Recarregar a tabela ---
        self.atualizar_tabela(reload_csv=False)

    # --- 6. Lógica de Atividades (Aluno) ---

    # ==========================================================================
    # Abre o pop-up de envio de atividade para o Aluno (Estrutura: Curso > Turma> Disciplina)

    def janela_envio_atividade_aluno(self):
        user_name = self.current_user.get("NOME", "N/A")
        user_id = self.current_user.get("ID", "N/A")
        user_turma = self.current_user.get("TURMAS", "Turma_Desconhecida")

        # --- ALTERAÇÃO 1: Pegar o Curso do usuário ---
        user_curso = self.current_user.get("CURSO", "Curso_Desconhecido")

        disciplinas = ["Nenhuma disciplina encontrada..."]

        # --- ALTERAÇÃO 2: Incluir o Curso no caminho da pasta ---
        pasta_turma = os.path.join(DIR_ATIVIDADES, str(user_curso), str(user_turma))

        try:
            if os.path.exists(pasta_turma):
                itens_na_pasta = os.listdir(pasta_turma)
                pastas_disciplinas = [
                    item
                    for item in itens_na_pasta
                    if os.path.isdir(os.path.join(pasta_turma, item))
                ]
                if pastas_disciplinas:
                    disciplinas = sorted(pastas_disciplinas)
                    disciplinas.insert(0, "Selecione a Disciplina...")
            else:
                # Aviso adaptado para debug (mostra onde tentou procurar)
                print(f"Pasta não encontrada em: {pasta_turma}")
                # Opcional: não mostrar erro intrusivo na abertura, apenas deixar o combo vazio
                pass

        except Exception as e:
            messagebox.showerror(
                "Erro de Leitura",
                f"Falha ao ler as pastas de disciplina.\nErro: {e}",
                parent=self,
            )

        submission_window = ctk.CTkToplevel(self)
        submission_window.title("Envio de Atividades do Aluno")
        submission_window.geometry("500x400")  # Aumentei um pouco a altura
        submission_window.transient(self)
        submission_window.grab_set()

        frame = ctk.CTkFrame(submission_window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="Portal de Envio de Atividades", font=("Roboto", 18, "bold")
        ).pack(pady=10)

        # --- ALTERAÇÃO 3: Mostrar o Curso na interface ---
        ctk.CTkLabel(
            frame,
            text=f"Aluno: {user_name}\nCurso: {user_curso} | Turma: {user_turma}",
            text_color="#4CAF50",
            font=("Arial", 12, "bold"),
        ).pack(pady=(5, 10))

        ctk.CTkLabel(frame, text="Selecione a Disciplina:").pack(pady=(10, 0))
        self.discipline_combobox = ctk.CTkComboBox(frame, values=disciplinas, width=300)
        if "Selecione a Disciplina..." in disciplinas:
            self.discipline_combobox.set("Selecione a Disciplina...")
        else:
            self.discipline_combobox.set(disciplinas[0])
        self.discipline_combobox.pack(pady=(0, 10))

        self.current_file_path = None
        self.filepath_label = ctk.CTkLabel(
            frame, text="Nenhum arquivo selecionado.", text_color="gray"
        )
        self.filepath_label.pack(pady=(5, 0))

        ctk.CTkButton(
            frame, text="Anexar Arquivo...", command=self._anexar_arquivo_dialog
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="Enviar Atividade",
            command=lambda: self._enviar_atividade_action(submission_window),
            fg_color="green",
        ).pack(pady=20)

    def _anexar_arquivo_dialog(self):
        """Abre o seletor de arquivos para o ALUNO anexar."""
        filepath = filedialog.askopenfilename(
            title="Selecione o arquivo da sua atividade (PDF, DOCX, ZIP, etc.)",
            filetypes=(
                ("Documentos PDF", "*.pdf"),
                ("Documentos Word", "*.docx"),
                ("Arquivos Compactados", "*.zip"),
                ("Todos os Arquivos", "*.*"),
            ),
        )
        if filepath:
            self.filepath_label.configure(
                text=f"Arquivo: {os.path.basename(filepath)}", text_color="yellow"
            )
            self.current_file_path = filepath
        else:
            self.filepath_label.configure(
                text="Nenhum arquivo selecionado.", text_color="gray"
            )
            self.current_file_path = None

    def _enviar_atividade_action(self, window):
        """Processa o envio de atividade do ALUNO (Atualizado com hierarquia de Curso)."""
        disciplina_selecionada = self.discipline_combobox.get().strip()

        if (
            disciplina_selecionada == "Selecione a Disciplina..."
            or disciplina_selecionada == "Nenhuma disciplina encontrada..."
        ):
            messagebox.showwarning(
                "Aviso", "Por favor, selecione uma disciplina válida.", parent=window
            )
            return

        if not hasattr(self, "current_file_path") or not self.current_file_path:
            messagebox.showwarning(
                "Aviso", "Por favor, anexe o arquivo da atividade.", parent=window
            )
            return

        try:
            # 1. Coletar dados do usuário
            user_id = str(self.current_user.get("ID", "ID_Desconhecido"))
            user_turma = self.current_user.get("TURMAS", "Turma_Desconhecida")
            user_name = self.current_user.get("NOME", "Aluno_Desconhecido")
            # NOVA LINHA: Pegar o curso
            user_curso = self.current_user.get("CURSO", "Curso_Desconhecido")

            # 2. Gerar nome seguro para o arquivo
            nome_aluno_safe = user_name.replace(" ", "_").replace("-", "_")
            nome_aluno_safe = "".join(
                c for c in nome_aluno_safe if c.isalnum() or c in ("_")
            ).rstrip()

            nome_arquivo_original = os.path.basename(self.current_file_path)
            _, extensao = os.path.splitext(nome_arquivo_original)

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            novo_nome_arquivo = f"{nome_aluno_safe}_{user_id}_{timestamp_str}{extensao}"

            # 3. Montar o caminho com a NOVA HIERARQUIA: Curso > Turma > Matéria
            pasta_destino = os.path.join(
                DIR_ATIVIDADES,
                str(user_curso),  # <--- Curso entra aqui
                str(user_turma),  # <--- Turma
                str(disciplina_selecionada),  # <--- Matéria
                "ENTREGAS",
            )
            caminho_destino_final = os.path.join(pasta_destino, novo_nome_arquivo)

            # 4. Criar pasta e copiar arquivo
            os.makedirs(pasta_destino, exist_ok=True)
            shutil.copy(self.current_file_path, caminho_destino_final)

            messagebox.showinfo(
                "Envio Concluído",
                "Atividade enviada com sucesso!\n\n"
                f"Curso: {user_curso}\n"
                f"Turma: {user_turma}\n"
                f"Disciplina: {disciplina_selecionada}\n"
                f"Arquivo: {novo_nome_arquivo}",
                parent=window,
            )
            window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Erro no Envio",
                f"Falha ao copiar o arquivo.\n\nErro: {e}",
                parent=window,
            )

    # ==============================================================================
    # Abre o pop-up para o ALUNO visualizar suas entregas (Estrutura: Curso > Turma)

    def abrir_janela_atividades_enviadas(self):
        try:
            user_id = str(self.current_user.get("ID", "ID_Desconhecido"))
            user_turma = self.current_user.get("TURMAS", "Turma_Desconhecida")
            user_name = self.current_user.get("NOME", "Aluno_Desconhecido")

            # --- ALTERAÇÃO 1: Pegar o Curso ---
            user_curso = self.current_user.get("CURSO", "Curso_Desconhecido")

            nome_aluno_safe = user_name.replace(" ", "_").replace("-", "_")
            nome_aluno_safe = "".join(
                c for c in nome_aluno_safe if c.isalnum() or c in ("_")
            ).rstrip()

            prefixo_arquivo_aluno = f"{nome_aluno_safe}_{user_id}"

            # --- ALTERAÇÃO 2: Caminho base inclui o Curso ---
            pasta_base_turma = os.path.join(
                DIR_ATIVIDADES, str(user_curso), str(user_turma)
            )

            if not os.path.exists(pasta_base_turma):
                messagebox.showinfo(
                    "Minhas Entregas",
                    f"Nenhuma atividade encontrada.\n(A pasta da turma {user_turma} no curso {user_curso} não existe).",
                    parent=self,
                )
                return

            lista_de_arquivos = []

            # Itera sobre as pastas de disciplinas (Ex: POO, REDES, etc.)
            for nome_disciplina in os.listdir(pasta_base_turma):
                pasta_disciplina = os.path.join(pasta_base_turma, nome_disciplina)

                if os.path.isdir(pasta_disciplina):
                    # Dentro da disciplina, procura a pasta ENTREGAS
                    pasta_entregas = os.path.join(pasta_disciplina, "ENTREGAS")

                    if os.path.exists(pasta_entregas):
                        for nome_arquivo in os.listdir(pasta_entregas):
                            # Verifica se o arquivo pertence ao aluno pelo prefixo (Nome_ID)
                            if nome_arquivo.startswith(prefixo_arquivo_aluno):
                                full_path = os.path.join(pasta_entregas, nome_arquivo)
                                lista_de_arquivos.append(
                                    {
                                        "disciplina": nome_disciplina,
                                        "arquivo": nome_arquivo,
                                        "full_path": full_path,
                                    }
                                )
        except Exception as e:
            messagebox.showerror(
                "Erro ao Buscar Atividades",
                f"Ocorreu um erro ao tentar ler seus arquivos.\nErro: {e}",
                parent=self,
            )
            return

        window = ctk.CTkToplevel(self)
        window.title(f"Minhas Entregas - {user_name}")
        window.geometry("600x450")
        window.transient(self)
        window.grab_set()

        frame = ctk.CTkFrame(window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="Minhas Atividades Enviadas", font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))

        # Mostra Curso e Turma no topo para confirmação visual
        ctk.CTkLabel(
            frame,
            text=f"Curso: {user_curso} | Turma: {user_turma}",
            text_color="gray",
            font=("Arial", 12),
        ).pack(pady=(0, 5))

        frame_tabela = ctk.CTkFrame(frame)
        frame_tabela.pack(fill="both", expand=True, pady=(5, 10))

        colunas = ("Disciplina", "Arquivo")
        tree_entregas = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        vsb = ttk.Scrollbar(
            frame_tabela, orient="vertical", command=tree_entregas.yview
        )
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(
            frame_tabela, orient="horizontal", command=tree_entregas.xview
        )
        hsb.pack(side="bottom", fill="x")
        tree_entregas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree_entregas.heading("Disciplina", text="Disciplina")
        tree_entregas.heading("Arquivo", text="Arquivo Enviado")
        tree_entregas.column("Disciplina", width=180, anchor="w")
        tree_entregas.column("Arquivo", width=300, anchor="w")
        tree_entregas.pack(fill="both", expand=True)

        if not lista_de_arquivos:
            tree_entregas.insert(
                "", "end", iid=0, values=("Nenhum arquivo enviado...", "")
            )
        else:
            for i, item in enumerate(lista_de_arquivos):
                tree_entregas.insert(
                    "", "end", iid=i, values=(item["disciplina"], item["arquivo"])
                )

        ctk.CTkButton(
            frame,
            text="📥 Baixar Arquivo Selecionado",
            command=lambda: self._baixar_arquivo_aluno(
                tree_entregas, lista_de_arquivos
            ),
            fg_color="#007BFF",
        ).pack(pady=(10, 0), ipady=4)

    def _baixar_arquivo_aluno(self, tree_widget, lista_de_arquivos):
        """Permite ao ALUNO baixar um arquivo que ele enviou."""
        selecionado = tree_widget.focus()
        if not selecionado:
            messagebox.showwarning(
                "Seleção",
                "Por favor, selecione um arquivo na tabela para baixar.",
                parent=tree_widget.master.master,
            )
            return

        try:
            idx = int(selecionado)

            if idx >= len(lista_de_arquivos):
                messagebox.showerror(
                    "Erro",
                    "Erro ao ler o índice do arquivo.",
                    parent=tree_widget.master.master,
                )
                return

            arquivo_data = lista_de_arquivos[idx]
            source_path = arquivo_data["full_path"]
            source_filename = arquivo_data["arquivo"]

            _, extensao = os.path.splitext(source_filename)
            file_types = [
                (f"Arquivo {extensao.upper()}", f"*{extensao}"),
                ("Todos os arquivos", "*.*"),
            ]

            caminho_destino = filedialog.asksaveasfilename(
                parent=tree_widget.master.master,
                title="Salvar arquivo como...",
                initialfile=source_filename,
                filetypes=file_types,
                defaultextension=extensao,
            )

            if caminho_destino:
                shutil.copy(source_path, caminho_destino)
                messagebox.showinfo(
                    "Sucesso",
                    f"Arquivo salvo com sucesso em:\n{caminho_destino}",
                    parent=tree_widget.master.master,
                )

        except ValueError:
            messagebox.showwarning(
                "Seleção",
                "A seleção é inválida (nenhum arquivo para baixar).",
                parent=tree_widget.master.master,
            )
        except Exception as e:
            messagebox.showerror(
                "Erro no Download",
                f"Ocorreu um erro ao baixar o arquivo:\n{e}",
                parent=tree_widget.master.master,
            )

    # --- 7. Lógica de Atividades (Professor/Coord) - Pop-ups ---

    # Nota: A lógica de ENVIO de atividade do professor está na Classe GerenciarTurmasFrame

    # =====================================================================
    # Abre o pop-up para criar pastas de disciplina (Professor/Coord/Admin)

    def abrir_janela_criar_pasta_disciplina(self):
        """Abre o pop-up para criar pastas de disciplina (Professor/Coord/Admin)."""
        if self.current_user.get("NIVEL") not in [
            "PROFESSOR",
            "COORDENADOR",
            "ADMINISTRADOR",
        ]:
            messagebox.showwarning("Permissão Negada", "Acesso negado.")
            return

        df_full = self.data_frame_full
        turmas_list = []
        if df_full is not None and not df_full.empty and "TURMAS" in df_full.columns:
            turmas_list = df_full["TURMAS"].astype(str).str.strip().unique().tolist()
            turmas_list = [t.upper() for t in turmas_list if t and t.upper() != "GERAL"]
            turmas_list.sort()

        if not turmas_list:
            messagebox.showwarning(
                "Aviso", "Não há turmas cadastradas para criar pastas.", parent=self
            )
            return

        window = ctk.CTkToplevel(self)
        window.title("Criar Pasta de Disciplina")
        window.geometry("450x300")
        window.transient(self)
        window.grab_set()

        frame = ctk.CTkFrame(window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(
            frame, text="1. Selecione a Turma:", font=("Arial", 12, "bold")
        ).pack(pady=(5, 5))
        self.combo_turma_disciplina = ctk.CTkComboBox(
            frame, values=turmas_list, width=300
        )
        self.combo_turma_disciplina.set(turmas_list[0])
        self.combo_turma_disciplina.pack(pady=(0, 15))

        ctk.CTkLabel(
            frame,
            text="2. Nome da Disciplina/Módulo (Ex: POO_JAVA):",
            font=("Arial", 12, "bold"),
        ).pack(pady=(5, 5))
        self.entry_disciplina_nome = ctk.CTkEntry(frame, width=300)
        self.entry_disciplina_nome.pack(pady=(0, 15))

        ctk.CTkButton(
            frame,
            text="Criar Pasta",
            command=lambda: self._criar_pasta_disciplina_action(window),
            fg_color="#007BFF",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)

    # ===================================================
    # Lógica para criar a estrutura de pastas:
    # ATIVIDADES > NOME_CURSO > NOME_TURMA > NOME_MATERIA > (ENTREGAS / MATERIAL DE ESTUDO)

    def _criar_pasta_disciplina_action(self, window):
        turma_selecionada = self.combo_turma_disciplina.get().strip()
        nome_disciplina = self.entry_disciplina_nome.get().strip()

        # 2. Validações básicas
        if not turma_selecionada or not nome_disciplina:
            messagebox.showwarning(
                "Campos Vazios",
                "Por favor, selecione a Turma e digite o nome da Disciplina.",
                parent=window,
            )
            return

        try:
            # 3. Descobre o CURSO baseado na TURMA selecionada
            nome_curso = self._get_curso_da_turma(turma_selecionada)

            # 4. Sanitiza o nome da disciplina (remove caracteres proibidos)
            disciplina_safe = "".join(
                c for c in nome_disciplina if c.isalnum() or c in ("_", "-")
            ).rstrip()

            if not disciplina_safe:
                messagebox.showwarning(
                    "Nome Inválido",
                    "Use apenas letras, números e underline.",
                    parent=window,
                )
                return

            # 5. Monta o caminho completo com a NOVA LÓGICA
            # Ex: atividades / ANALISE_SISTEMAS / TURMA_A / JAVA_POO
            caminho_base_disciplina = os.path.join(
                DIR_ATIVIDADES, nome_curso, turma_selecionada, disciplina_safe
            )

            # 6. Define subpastas
            pasta_entregas = os.path.join(caminho_base_disciplina, "ENTREGAS")
            pasta_material = os.path.join(
                caminho_base_disciplina, "MATERIAL_PARA_ESTUDO"
            )

            # 7. Cria efetivamente as pastas (os.makedirs cria toda a árvore se não existir)
            os.makedirs(pasta_entregas, exist_ok=True)
            os.makedirs(pasta_material, exist_ok=True)

            # 8. Sucesso
            messagebox.showinfo(
                "Sucesso",
                f"Estrutura criada com sucesso!\n\n"
                f"Curso: {nome_curso}\n"
                f"Turma: {turma_selecionada}\n"
                f"Disciplina: {disciplina_safe}\n\n"
                f"Local: {caminho_base_disciplina}",
                parent=window,
            )
            window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Erro ao Criar",
                f"Não foi possível criar as pastas.\nErro: {e}",
                parent=window,
            )

    # =============================================================
    # Abre o Toplevel/janela 'Portal de Validação' para o professor

    def abrir_janela_validar_entregas(self):
        """
        Abre o portal de validação com a hierarquia: Curso > Turma > Disciplina.
        """
        # 1. Obter lista de cursos únicos do sistema
        if self.data_frame_full is not None and "CURSO" in self.data_frame_full.columns:
            cursos_brutos = self.data_frame_full["CURSO"].astype(str).unique().tolist()
            cursos_limpos = sorted(
                [c for c in cursos_brutos if c not in ["nan", "None", "", "GERAL"]]
            )
            cursos_com_prompt = ["Selecione o curso..."] + cursos_limpos
        else:
            cursos_com_prompt = ["Nenhum curso encontrado"]

        self.validation_window = ctk.CTkToplevel(self)
        self.validation_window.title("Portal de Validação de Entregas")
        self.validation_window.geometry("1000x700")
        self.validation_window.resizable(True, True)
        self.validation_window.after(
            100, lambda: self.validation_window.state("zoomed")
        )
        self.validation_window.transient(self)
        self.validation_window.grab_set()

        self.lista_entregas_prof = []

        # --- Frame de Filtros (Topo) ---
        frame_controles = ctk.CTkFrame(self.validation_window)
        frame_controles.pack(padx=20, pady=10, fill="x")

        # 1. CURSO
        ctk.CTkLabel(
            frame_controles, text="1. Curso:", font=("Arial", 12, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.prof_validar_curso_combo = ctk.CTkComboBox(
            frame_controles,
            values=cursos_com_prompt,
            width=200,
            command=self._update_turmas_validacao,  # Nova função de callback
        )
        self.prof_validar_curso_combo.set(cursos_com_prompt[0])
        self.prof_validar_curso_combo.grid(row=0, column=1, padx=5, pady=10)

        # 2. TURMA
        ctk.CTkLabel(
            frame_controles, text="2. Turma:", font=("Arial", 12, "bold")
        ).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.prof_validar_turma_combo = ctk.CTkComboBox(
            frame_controles,
            values=["Selecione um curso..."],
            width=150,
            state="disabled",
            command=self._update_disciplinas_validacao,  # Nova função de callback
        )
        self.prof_validar_turma_combo.grid(row=0, column=3, padx=5, pady=10)

        # 3. DISCIPLINA
        ctk.CTkLabel(
            frame_controles, text="3. Disciplina:", font=("Arial", 12, "bold")
        ).grid(row=0, column=4, padx=10, pady=10, sticky="w")
        self.prof_validar_disciplina_combo = ctk.CTkComboBox(
            frame_controles,
            values=["Selecione uma turma..."],
            width=200,
            state="disabled",
        )
        self.prof_validar_disciplina_combo.grid(row=0, column=5, padx=5, pady=10)

        # BOTÃO BUSCAR
        ctk.CTkButton(
            frame_controles,
            text="🔍 Buscar Entregas",
            command=self._buscar_entregas_prof,
            fg_color="#007BFF",
            font=("Arial", 12, "bold"),
        ).grid(row=0, column=6, padx=20, pady=10)

        # --- Tabela de Resultados ---
        frame_tabela = ctk.CTkFrame(self.validation_window)
        frame_tabela.pack(padx=20, pady=(5, 10), fill="both", expand=True)

        colunas = ("Status", "Aluno (Nome)", "ID Aluno", "Arquivo", "Data Envio")
        self.tree_entregas_prof = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings"
        )

        vsb = ttk.Scrollbar(
            frame_tabela, orient="vertical", command=self.tree_entregas_prof.yview
        )
        vsb.pack(side="right", fill="y")
        self.tree_entregas_prof.configure(yscrollcommand=vsb.set)

        # Configuração das colunas
        self.tree_entregas_prof.heading("Status", text="Status")
        self.tree_entregas_prof.heading("Aluno (Nome)", text="Aluno")
        self.tree_entregas_prof.heading("ID Aluno", text="ID")
        self.tree_entregas_prof.heading("Arquivo", text="Nome do Arquivo")
        self.tree_entregas_prof.heading("Data Envio", text="Data")

        self.tree_entregas_prof.column("Status", width=80, anchor="center")
        self.tree_entregas_prof.column("Aluno (Nome)", width=200, anchor="w")
        self.tree_entregas_prof.column("ID Aluno", width=60, anchor="center")
        self.tree_entregas_prof.column("Arquivo", width=250, anchor="w")
        self.tree_entregas_prof.column("Data Envio", width=120, anchor="center")

        self.tree_entregas_prof.pack(fill="both", expand=True)

        # Tags de cor
        self.tree_entregas_prof.tag_configure(
            "corrigido", foreground="#00B050", font=("Arial", 10, "bold")
        )  # Verde
        self.tree_entregas_prof.tag_configure(
            "pendente", foreground="#FF9800", font=("Arial", 10)
        )  # Laranja

        # --- Botões de Ação (Rodapé) ---
        frame_acoes = ctk.CTkFrame(self.validation_window)
        frame_acoes.pack(padx=20, pady=(0, 10), fill="x")
        frame_acoes.grid_columnconfigure(0, weight=1)
        frame_acoes.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame_acoes,
            text="📥 Baixar Selecionado",
            command=self._baixar_entrega_prof,
            fg_color="#555555",
        ).grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            frame_acoes,
            text="✅ Marcar como Corrigido",
            command=self._marcar_entrega_corrigida,
            fg_color="#28a745",
        ).grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    def _update_turmas_validacao(self, curso_selecionado):
        """
        Popula o combo de Turmas baseado no Curso selecionado.
        PADRONIZAÇÃO: Converte tudo para maiúsculo na comparação.
        """
        # Reseta os combos seguintes
        self.prof_validar_turma_combo.set("Selecione a turma...")
        self.prof_validar_turma_combo.configure(
            values=["Carregando..."], state="disabled"
        )
        self.prof_validar_disciplina_combo.set("...")
        self.prof_validar_disciplina_combo.configure(state="disabled")

        if not curso_selecionado or curso_selecionado == "Selecione o curso...":
            return

        try:
            df = self.data_frame_full

            # --- LÓGICA PADRONIZADA (CASE INSENSITIVE) ---
            # Compara CURSO do CSV (Maiúsculo) com CURSO SELECIONADO (Maiúsculo)
            mask = (
                df["CURSO"].astype(str).str.strip().str.upper()
                == str(curso_selecionado).strip().upper()
            )

            turmas_raw = df[mask]["TURMAS"].unique().tolist()

            turmas_validas = sorted(
                [
                    t
                    for t in turmas_raw
                    if str(t).lower() not in ["nan", "none", "", "geral"]
                ]
            )

            if not turmas_validas:
                self.prof_validar_turma_combo.configure(
                    values=["Nenhuma turma encontrada"], state="disabled"
                )
                self.prof_validar_turma_combo.set("Nenhuma turma encontrada")
                return

            valores = ["Selecione a turma..."] + turmas_validas
            self.prof_validar_turma_combo.configure(values=valores, state="normal")
            self.prof_validar_turma_combo.set(valores[0])

        except Exception as e:
            print(f"Erro ao buscar turmas: {e}")
            self.prof_validar_turma_combo.configure(values=["Erro"], state="disabled")

    # ====================================================================================================================
    # Preenche o segundo menu (Dropdown de Disciplinas) apenas com as matérias que existem dentro daquela turma selecionada
    # acionada automaticamente assim que o professor escolhe uma Turma no primeiro menu.

    def _update_disciplinas_validacao(self, turma_selecionada):
        """Popula o combo de Disciplinas baseado no Curso e Turma."""

        if turma_selecionada == "Selecione a turma...":
            self.prof_validar_disciplina_combo.configure(state="disabled")
            return

        curso_selecionado = self.prof_validar_curso_combo.get()

        # Monta o caminho direto: ATIVIDADES / CURSO / TURMA
        pasta_turma = os.path.join(
            DIR_ATIVIDADES, str(curso_selecionado), str(turma_selecionada)
        )

        print(f"DEBUG VALIDACAO: Lendo pasta {pasta_turma}")

        if not os.path.exists(pasta_turma):
            self.prof_validar_disciplina_combo.configure(
                values=["Pasta não criada"], state="disabled"
            )
            self.prof_validar_disciplina_combo.set("Pasta não criada")
            return

        itens = os.listdir(pasta_turma)
        disciplinas = sorted(
            [i for i in itens if os.path.isdir(os.path.join(pasta_turma, i))]
        )

        if not disciplinas:
            self.prof_validar_disciplina_combo.configure(
                values=["Nenhuma disciplina"], state="disabled"
            )
            self.prof_validar_disciplina_combo.set("Nenhuma disciplina")
            return

        valores = ["Selecione a disciplina..."] + disciplinas
        self.prof_validar_disciplina_combo.configure(values=valores, state="normal")
        self.prof_validar_disciplina_combo.set(valores[0])

    def _buscar_entregas_prof(self):
        """Busca arquivos na pasta ENTREGAS usando Curso > Turma > Disciplina."""

        # Limpa tabela
        for i in self.tree_entregas_prof.get_children():
            self.tree_entregas_prof.delete(i)
        self.lista_entregas_prof = []

        curso = self.prof_validar_curso_combo.get()
        turma = self.prof_validar_turma_combo.get()
        disciplina = self.prof_validar_disciplina_combo.get()

        # Validação básica
        if "Selecione" in [curso, turma, disciplina]:
            messagebox.showwarning(
                "Aviso",
                "Selecione Curso, Turma e Disciplina para buscar.",
                parent=self.validation_window,
            )
            return

        # Caminho exato
        pasta_entregas = os.path.join(
            DIR_ATIVIDADES, curso, turma, disciplina, "ENTREGAS"
        )

        if not os.path.exists(pasta_entregas):
            messagebox.showinfo(
                "Info",
                "Nenhuma pasta de entregas encontrada para esta disciplina.",
                parent=self.validation_window,
            )
            return

        arquivos = os.listdir(pasta_entregas)
        if not arquivos:
            messagebox.showinfo(
                "Info", "A pasta de entregas está vazia.", parent=self.validation_window
            )
            return

        # Processamento visual dos arquivos
        for i, filename in enumerate(arquivos):
            caminho_completo = os.path.join(pasta_entregas, filename)
            if not os.path.isfile(caminho_completo):
                continue

            # Ignora arquivos de sistema ou ocultos se necessário
            if filename.startswith("."):
                continue

            # Lógica de Status
            status = "Pendente"
            tag = "pendente"
            nome_limpo = filename

            if "_CORRIGIDO" in filename:
                status = "Corrigido"
                tag = "corrigido"
                nome_limpo = filename.replace("_CORRIGIDO", "")

            # Tenta extrair ID e Nome (Padrão: Nome_ID_Data)
            # Ex: Joao_Silva_101_20231010_120000.pdf
            parts = nome_limpo.rsplit(
                "_", 3
            )  # Divide de trás pra frente para tentar pegar ID e Data

            aluno_nome = "Desconhecido"
            aluno_id = "?"
            data_envio = "..."

            # Lógica simples de parse visual
            if len(parts) >= 3:
                # Tentativa de parsear
                aluno_nome = parts[0].replace("_", " ")
                aluno_id = parts[1]
                # Data pode estar nos ultimos parts, mas vamos simplificar:
                # Usar a data de modificação do arquivo é mais garantido para exibição
                timestamp = os.path.getmtime(caminho_completo)
                data_envio = datetime.fromtimestamp(timestamp).strftime(
                    "%d/%m/%Y %H:%M"
                )
            else:
                aluno_nome = filename  # Fallback

            self.tree_entregas_prof.insert(
                "",
                "end",
                iid=i,
                values=(status, aluno_nome, aluno_id, filename, data_envio),
                tags=(tag,),
            )

            self.lista_entregas_prof.append(
                {"full_path": caminho_completo, "filename": filename, "status": status}
            )

    def _baixar_entrega_prof(self):
        """Baixa o arquivo selecionado pelo professor."""
        selecionado = self.tree_entregas_prof.focus()
        if not selecionado:
            messagebox.showwarning(
                "Seleção",
                "Selecione um arquivo na tabela para baixar.",
                parent=self.validation_window,
            )
            return

        try:
            idx = int(selecionado)
            arquivo_data = self.lista_entregas_prof[idx]

            if arquivo_data is None:
                messagebox.showerror(
                    "Erro",
                    "Este arquivo não pode ser baixado (formato inválido).",
                    parent=self.validation_window,
                )
                return

            source_path = arquivo_data["full_path"]
            source_filename = arquivo_data["filename"]
            _, extensao = os.path.splitext(source_filename)

            caminho_destino = filedialog.asksaveasfilename(
                parent=self.validation_window,
                title="Salvar arquivo do aluno...",
                initialfile=source_filename,
                defaultextension=extensao,
                filetypes=[(f"Arquivo {extensao}", f"*{extensao}"), ("Todos", "*.*")],
            )

            if caminho_destino:
                shutil.copy(source_path, caminho_destino)
                messagebox.showinfo(
                    "Sucesso",
                    f"Arquivo salvo com sucesso em:\n{caminho_destino}",
                    parent=self.validation_window,
                )

        except Exception as e:
            messagebox.showerror(
                "Erro no Download",
                f"Ocorreu um erro ao baixar o arquivo:\n{e}",
                parent=self.validation_window,
            )

    def _marcar_entrega_corrigida(self):
        """Renomeia o arquivo selecionado adicionando _CORRIGIDO."""
        selecionado = self.tree_entregas_prof.focus()
        if not selecionado:
            return

        idx = int(selecionado)
        dados = self.lista_entregas_prof[idx]

        if dados["status"] == "Corrigido":
            messagebox.showinfo(
                "Info",
                "Este arquivo já está marcado como corrigido.",
                parent=self.validation_window,
            )
            return

        caminho_atual = dados["full_path"]
        diretorio = os.path.dirname(caminho_atual)
        nome_atual = dados["filename"]
        nome_base, ext = os.path.splitext(nome_atual)

        novo_nome = f"{nome_base}_CORRIGIDO{ext}"
        novo_caminho = os.path.join(diretorio, novo_nome)

        try:
            os.rename(caminho_atual, novo_caminho)
            messagebox.showinfo(
                "Sucesso", "Marcado como corrigido!", parent=self.validation_window
            )
            self._buscar_entregas_prof()  # Recarrega a lista
        except Exception as e:
            messagebox.showerror(
                "Erro", f"Erro ao renomear: {e}", parent=self.validation_window
            )


# === 6. CLASSES DAS ABAS (Turmas e Chatbot) ===


class GerenciarTurmasFrame(ctk.CTkFrame):
    """Frame que gerencia a aba 'Gerenciar Turmas'."""

    def __init__(self, master, main_app_instance):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_app = main_app_instance

        self.df_turmas = pd.DataFrame()
        self.tabela_turmas_widget = None

        self.entry_busca_turma = None

        frame_controles = ctk.CTkFrame(self)
        frame_controles.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            frame_controles,
            text="Gerenciamento de Turmas",
            font=("Arial", 16, "bold"),
        ).pack(pady=5)

        self.frame_filtros_acoes = ctk.CTkFrame(frame_controles)
        self.frame_filtros_acoes.pack(fill="x", padx=10, pady=(0, 10))

        self.criar_widgets_filtros()

        self.frame_tabela_turmas = ctk.CTkFrame(self)
        self.frame_tabela_turmas.pack(fill="both", expand=True, padx=0, pady=0)

        self.atualizar_tabela_turmas()

    # --- 1. Criação da UI e Filtros da Aba ---

    def criar_widgets_filtros(self):
        """Cria os filtros em cascata (Curso -> Turma) e botões de ação."""

        # --- Filtro 1: CURSO ---
        ctk.CTkLabel(self.frame_filtros_acoes, text="Filtrar Curso:").grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="w"
        )

        # Obtém lista única de cursos
        cursos = ["Todos os Cursos"] + self._get_unique_values("CURSO")

        self.combo_filtro_curso = ctk.CTkComboBox(
            self.frame_filtros_acoes,
            values=cursos,
            width=180,
            command=self._ao_selecionar_curso,
        )
        self.combo_filtro_curso.set(cursos[0])
        self.combo_filtro_curso.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        # --- Filtro 2: TURMA (Dinâmico) ---
        ctk.CTkLabel(self.frame_filtros_acoes, text="Filtrar Turma:").grid(
            row=0, column=2, padx=(15, 5), pady=10, sticky="w"
        )

        self.combo_filtro_turma = ctk.CTkComboBox(
            self.frame_filtros_acoes,
            values=["Todas as Turmas"],
            width=150,
            command=self.filtrar_turmas,  # Ao selecionar turma, filtra a tabela
        )
        self.combo_filtro_turma.set("Todas as Turmas")
        self.combo_filtro_turma.grid(row=0, column=3, padx=5, pady=10, sticky="w")

        # --- Botões de Ação ---

        botao_limpar = ctk.CTkButton(
            self.frame_filtros_acoes,
            text="Limpar Filtros",
            command=self.limpar_filtros,
            width=100,
            fg_color="#555555",
            font=("Arial", 12, "bold"),
        )
        botao_limpar.grid(row=0, column=4, padx=(15, 5), pady=10, sticky="w")

        botao_atualizar = ctk.CTkButton(
            self.frame_filtros_acoes,
            text="Recarregar",
            font=("Arial", 12, "bold"),
            command=lambda: self.atualizar_tabela_turmas(force_reload_csv=True),
            width=100,
        )
        botao_atualizar.grid(row=0, column=5, padx=(5, 10), pady=10, sticky="w")

        self.frame_filtros_acoes.grid_columnconfigure(6, weight=1)

        user_level = self.main_app.current_user.get("NIVEL")

        # GERENCIAR TURMAS PROFESSOR
        if user_level == "PROFESSOR":
            botao_criar_pasta = ctk.CTkButton(
                self.frame_filtros_acoes,
                text="Criar Pasta de Disciplina",
                command=self.main_app.abrir_janela_criar_pasta_disciplina,
                fg_color="#FF9800",
                width=180,
                font=("Arial", 12, "bold"),
            )
            botao_criar_pasta.grid(row=0, column=8, padx=(10, 5), pady=10, sticky="e")

            botao_enviar_atividade = ctk.CTkButton(
                self.frame_filtros_acoes,
                text="Enviar Atividade",
                command=self.abrir_janela_envio_atividade_professor,
                fg_color="#4CAF50",
                width=150,
                font=("Arial", 12, "bold"),
            )
            botao_enviar_atividade.grid(
                row=0, column=9, padx=(5, 10), pady=10, sticky="e"
            )

            botao_validar_entregas = ctk.CTkButton(
                self.frame_filtros_acoes,
                text="Validar Entregas",
                command=self.main_app.abrir_janela_validar_entregas,
                fg_color="#007BFF",
                width=150,
                font=("Arial", 12, "bold"),
            )
            botao_validar_entregas.grid(
                row=0, column=10, padx=(5, 10), pady=10, sticky="e"
            )

            self.frame_filtros_acoes.grid_columnconfigure(8, weight=0)
            self.frame_filtros_acoes.grid_columnconfigure(9, weight=0)
            self.frame_filtros_acoes.grid_columnconfigure(10, weight=0)

        # GERENCIAR TURMAS ADM E COORD
        if user_level in ["ADMINISTRADOR", "COORDENADOR"]:
            botao_relatorio = ctk.CTkButton(
                self.frame_filtros_acoes,
                text=" Gerar Relatório de Turmas",
                command=self.gerar_relatorio_turmas,
                font=("Arial", 12, "bold"),
                fg_color="#3A8A3A",
                width=200,
            )
            botao_relatorio.grid(row=0, column=8, padx=(10, 5), pady=10, sticky="e")
            self.frame_filtros_acoes.grid_columnconfigure(5, weight=0)

    def _ao_selecionar_curso(self, curso_selecionado):
        """
        Chamado quando o usuário escolhe um curso.
        Atualiza o ComboBox de Turmas apenas com as turmas daquele curso.
        """
        # 1. Resetar o combo de turmas
        self.combo_filtro_turma.set("Todas as Turmas")

        df_full = self.main_app.data_frame_full
        if df_full is None or df_full.empty:
            self.combo_filtro_turma.configure(values=["Todas as Turmas"])
            self.filtrar_turmas()
            return

        # 2. Filtrar o DataFrame base para pegar as turmas do curso
        # Normalizado para garantir que maiúsculas/minúsculas não atrapalhem
        curso_upper = str(curso_selecionado).upper().strip()

        if curso_upper == "TODOS OS CURSOS":
            # Se selecionou todos, pega todas as turmas únicas do sistema
            turmas_disponiveis = self._get_unique_values("TURMAS")
        else:
            # Filtra o DF principal onde NIVEL='ALUNO' e CURSO = Selecionado
            mask = (df_full["NIVEL"] == "ALUNO") & (
                df_full["CURSO"].astype(str).str.strip().str.upper() == curso_upper
            )
            df_curso = df_full[mask]

            if not df_curso.empty and "TURMAS" in df_curso.columns:
                lista_bruta = (
                    df_curso["TURMAS"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .unique()
                    .tolist()
                )
                # Remove inválidos
                turmas_disponiveis = [
                    t for t in lista_bruta if t not in ["", "N/A", "NAN", "GERAL"]
                ]
            else:
                turmas_disponiveis = []

        # 3. Ordenar e Atualizar o Combo
        turmas_disponiveis.sort()
        novos_valores = ["Todas as Turmas"] + turmas_disponiveis
        self.combo_filtro_turma.configure(values=novos_valores)

        # 4. Aplica o filtro na tabela visual
        self.filtrar_turmas()

    def _get_unique_values(self, column_name):
        """Obtém valores únicos de uma coluna do dataframe principal."""
        df_full = self.main_app.data_frame_full
        if df_full is not None and not df_full.empty and column_name in df_full.columns:
            return df_full[column_name].astype(str).str.strip().unique().tolist()
        return []

    def gerar_dados_turmas(self):
        """Gera um DataFrame de resumo com estatísticas por Turma (Versão Corrigida)."""
        df_full = self.main_app.data_frame_full

        # 1. Validação inicial de segurança
        if df_full is None or df_full.empty:
            return pd.DataFrame(
                columns=["TURMA", "CURSO", "TOTAL ALUNOS", "MÉDIA GERAL"]
            )

        # Previne erro se as colunas essenciais não existirem
        required_cols = ["NIVEL", "TURMAS", "MEDIA", "CURSO"]
        if not all(col in df_full.columns for col in required_cols):
            return pd.DataFrame(
                columns=["TURMA", "CURSO", "TOTAL ALUNOS", "MÉDIA GERAL"]
            )

        # 2. Filtrar apenas ALUNOS (Com tratamento de maiúsculas/espaços para garantir)
        # Normaliza a coluna NIVEL temporariamente para o filtro
        mask_alunos = df_full["NIVEL"].astype(str).str.strip().str.upper() == "ALUNO"
        df_alunos = df_full[mask_alunos].copy()

        if df_alunos.empty:
            return pd.DataFrame(
                columns=["TURMA", "CURSO", "TOTAL ALUNOS", "MÉDIA GERAL"]
            )

        # 3. Normalização das colunas de Texto (Evita "nan" literal e espaços)
        df_alunos["TURMAS"] = (
            df_alunos["TURMAS"].fillna("").astype(str).str.strip().str.upper()
        )
        df_alunos["CURSO"] = (
            df_alunos["CURSO"].fillna("").astype(str).str.strip().str.upper()
        )

        # 4. Remoção de Turmas Inválidas
        # Remove apenas se for realmente inválido. Mantém turmas novas ou digitadas parcialmente.
        invalidos = ["N/A", "", "GERAL", "NAN", "NONE"]
        df_alunos = df_alunos[~df_alunos["TURMAS"].isin(invalidos)]

        if df_alunos.empty:
            return pd.DataFrame(
                columns=["TURMA", "CURSO", "TOTAL ALUNOS", "MÉDIA GERAL"]
            )

        # 5. Agrupamento Inteligente (CORREÇÃO DA PERDA DE DADOS)
        # 'CURSO': Em vez de pegar o primeiro ('first'), pegamos o 'max'.
        # Como letras valem mais que string vazia, isso garante que se ALGUÉM na turma
        # tiver o curso preenchido, a turma inteira herda esse nome.
        df_resumo = (
            df_alunos.groupby("TURMAS")
            .agg(
                {
                    "ID": "count",
                    "MEDIA": "mean",
                    "CURSO": lambda x: x.max() if not x.empty else "N/A",
                }
            )
            .reset_index()
        )

        # 6. Renomeação e Formatação Final
        df_resumo.rename(
            columns={
                "TURMAS": "TURMA",
                "ID": "TOTAL ALUNOS",
                "MEDIA": "MÉDIA GERAL",
            },
            inplace=True,
        )

        # Arredonda e preenche vazios da média com 0
        df_resumo["MÉDIA GERAL"] = df_resumo["MÉDIA GERAL"].fillna(0).round(2)

        # Ordenação
        df_resumo.sort_values(by="TURMA", inplace=True)
        df_resumo.reset_index(drop=True, inplace=True)

        return df_resumo

    def filtrar_turmas(self, *args):
        """Aplica os filtros de Curso e Turma na tabela de resumo."""
        # Recalcula o resumo base (usando sua função corrigida anteriormente)
        df_resumo = self.gerar_dados_turmas()

        if df_resumo.empty:
            self.tabela_turmas(df_resumo)
            return

        # --- Aplica Filtro 1: Curso ---
        curso_selecionado = self.combo_filtro_curso.get()
        if curso_selecionado != "Todos os Cursos":
            df_resumo = df_resumo[df_resumo["CURSO"] == curso_selecionado.upper()]

        # --- Aplica Filtro 2: Turma ---
        turma_selecionada = self.combo_filtro_turma.get()
        if turma_selecionada != "Todas as Turmas":
            # Filtro exato da turma
            df_resumo = df_resumo[df_resumo["TURMA"] == turma_selecionada.upper()]

        # Exibe o resultado final
        self.tabela_turmas(df_resumo)

    def limpar_filtros(self):
        """Reseta os filtros e mostra tudo."""
        # Reseta Curso
        valores_cursos = ["Todos os Cursos"] + self._get_unique_values("CURSO")
        self.combo_filtro_curso.configure(values=valores_cursos)
        self.combo_filtro_curso.set("Todos os Cursos")

        # Reseta Turma (para mostrar todas as turmas possíveis ou genérico)
        self.combo_filtro_turma.configure(values=["Todas as Turmas"])
        self.combo_filtro_turma.set("Todas as Turmas")

        # Recarrega a tabela completa
        # Nota: Chamamos o _ao_selecionar_curso com "Todos..." para repopular a lista de turmas corretamente
        self._ao_selecionar_curso("Todos os Cursos")

    def atualizar_tabela_turmas(self, force_reload_csv=False):
        """Recarrega os dados, gera o resumo e exibe a tabela de turmas."""
        if force_reload_csv:
            self.main_app.data_frame_full = carregar_tabela(CAMINHO_ARQUIVO)
            cursos = ["Todos os Cursos"] + self._get_unique_values("CURSO")
            self.combo_filtro_curso.configure(values=cursos)
            self.combo_filtro_curso.set("Todos os Cursos")

        self.df_turmas = self.gerar_dados_turmas()
        self.tabela_turmas(self.df_turmas)

    def tabela_turmas(self, df):
        """Exibe o DataFrame de Turmas na Treeview."""
        for widget in self.frame_tabela_turmas.winfo_children():
            widget.destroy()

        if df.empty:
            ctk.CTkLabel(
                self.frame_tabela_turmas,
                text="Nenhuma turma encontrada ou dados insuficientes.",
                text_color="red",
            ).pack(pady=20)
            self.tabela_turmas_widget = None
            return

        colunas = list(df.columns)
        self.tabela_turmas_widget = ttk.Treeview(
            self.frame_tabela_turmas, columns=colunas, show="headings"
        )

        vsb = ttk.Scrollbar(
            self.frame_tabela_turmas,
            orient="vertical",
            command=self.tabela_turmas_widget.yview,
        )
        hsb = ttk.Scrollbar(
            self.frame_tabela_turmas,
            orient="horizontal",
            command=self.tabela_turmas_widget.xview,
        )
        self.tabela_turmas_widget.configure(
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tabela_turmas_widget.pack(fill="both", expand=True)

        for col in colunas:
            self.tabela_turmas_widget.heading(col, text=col.replace("_", " "))
            col_width = 150
            if col == "TURMA":
                col_width = 120
            elif col == "MÉDIA GERAL":
                col_width = 150
            elif col == "TOTAL ALUNOS":
                col_width = 120
            self.tabela_turmas_widget.column(
                col, anchor="center", width=col_width, minwidth=50
            )

        exceptions_turmas = []

        for i, row in df.iterrows():
            row_list = list(row)
            for j in range(len(row_list)):
                col_name = colunas[j]
                value = row_list[j]
                if isinstance(value, str) and col_name not in exceptions_turmas:
                    row_list[j] = value.upper()

            if "MÉDIA GERAL" in colunas:
                media_index = colunas.index("MÉDIA GERAL")
                try:
                    media_valor = float(row_list[media_index])
                    row_list[media_index] = f"{media_valor:.2f}"
                except (ValueError, TypeError):
                    pass

            self.tabela_turmas_widget.insert("", "end", iid=i, values=row_list)

    # --- 3. Lógica de Relatórios (Coord/Admin) ---

    def gerar_relatorio_turmas(self):
        """Exporta os dados atuais da tabela de turmas para Excel ou CSV."""
        if self.df_turmas is None or self.df_turmas.empty:
            messagebox.showwarning(
                "Nenhum Dado",
                "Não há dados na tabela de turmas para gerar um relatório.\n"
                "Tente limpar os filtros ou recarregar os dados.",
                parent=self,
            )
            return

        try:
            caminho_arquivo = filedialog.asksaveasfilename(
                parent=self,
                title="Salvar Relatório de Turmas como...",
                initialfile="Relatorio_Turmas.xlsx",
                filetypes=[
                    ("Arquivo Excel", "*.xlsx"),
                    ("Arquivo CSV (separado por ;)", "*.csv"),
                ],
                defaultextension=".xlsx",
            )

            if caminho_arquivo:
                if caminho_arquivo.endswith(".xlsx"):
                    self.df_turmas.to_excel(
                        caminho_arquivo, index=False, sheet_name="Relatorio_Turmas"
                    )
                elif caminho_arquivo.endswith(".csv"):
                    self.df_turmas.to_csv(
                        caminho_arquivo, sep=";", index=False, encoding="utf-8-sig"
                    )
                else:
                    messagebox.showwarning(
                        "Extensão Inválida",
                        "Por favor, salve como .xlsx ou .csv",
                        parent=self,
                    )
                    return

                messagebox.showinfo(
                    "Sucesso",
                    f"Relatório de turmas salvo com sucesso em:\n{caminho_arquivo}",
                    parent=self,
                )

        except Exception as e:
            messagebox.showerror(
                "Erro ao Salvar",
                f"Ocorreu um erro ao salvar o relatório:\n{e}",
                parent=self,
            )

    # --- 4. Lógica de Envio de Atividades (Professor) ---

    def _get_all_student_turmas(self):
        """Busca todas as turmas únicas que possuem alunos."""
        if self.main_app.data_frame_full is None or self.main_app.data_frame_full.empty:
            return []

        df_alunos = self.main_app.data_frame_full[
            self.main_app.data_frame_full["NIVEL"] == "ALUNO"
        ]
        if df_alunos.empty or "TURMAS" not in df_alunos.columns:
            return []

        turmas = df_alunos["TURMAS"].astype(str).str.strip().unique().tolist()
        turmas = [t for t in turmas if t and t.upper() != "GERAL"]
        turmas.sort()
        return turmas

    def abrir_janela_envio_atividade_professor(self):
        """Abre a janela para o professor ENVIAR uma atividade com hierarquia completa."""

        # 1. Buscar Cursos Únicos
        cursos_disponiveis = self._get_unique_values("CURSO")
        if not cursos_disponiveis:
            cursos_disponiveis = ["Nenhum curso encontrado"]

        cursos_com_prompt = ["Selecione o curso..."] + sorted(cursos_disponiveis)

        self.prof_current_file_path = None

        envio_window = ctk.CTkToplevel(self.main_app)
        envio_window.title("Enviar Atividade - Professor")
        envio_window.geometry("500x650")  # Aumentei a altura
        envio_window.transient(self.main_app)
        envio_window.grab_set()

        frame = ctk.CTkFrame(envio_window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Portal de Envio", font=("Roboto", 18, "bold")).pack(
            pady=10
        )

        # --- 1. Seleção de CURSO ---
        ctk.CTkLabel(
            frame, text="1. Selecione o Curso:", font=("Arial", 12, "bold")
        ).pack(pady=(5, 2))
        self.prof_curso_combo = ctk.CTkComboBox(
            frame,
            values=cursos_com_prompt,
            width=300,
            command=self._update_turmas_dropdown_prof,  # Nova função
        )
        self.prof_curso_combo.set(cursos_com_prompt[0])
        self.prof_curso_combo.pack(pady=(0, 10))

        # --- 2. Seleção de TURMA ---
        ctk.CTkLabel(
            frame, text="2. Selecione a Turma:", font=("Arial", 12, "bold")
        ).pack(pady=(5, 2))
        self.prof_turma_combobox = ctk.CTkComboBox(
            frame,
            values=["Selecione um curso primeiro..."],
            width=300,
            state="disabled",
            command=self._update_disciplinas_dropdown_prof,
        )
        self.prof_turma_combobox.pack(pady=(0, 10))

        # --- 3. Seleção de DISCIPLINA ---
        ctk.CTkLabel(
            frame, text="3. Selecione a Disciplina:", font=("Arial", 12, "bold")
        ).pack(pady=(5, 2))
        self.prof_disciplina_combobox = ctk.CTkComboBox(
            frame,
            values=["Selecione uma turma primeiro..."],
            width=300,
            state="disabled",
            command=self._update_destino_dropdown_prof,
        )
        self.prof_disciplina_combobox.pack(pady=(0, 10))

        # --- 4. Seleção de DESTINO ---
        ctk.CTkLabel(
            frame, text="4. Selecione o Destino:", font=("Arial", 12, "bold")
        ).pack(pady=(5, 2))
        self.prof_destino_combobox = ctk.CTkComboBox(
            frame,
            values=["Selecione uma disciplina primeiro..."],
            width=300,
            state="disabled",
        )
        self.prof_destino_combobox.pack(pady=(0, 15))

        # --- Anexo e Envio ---
        self.prof_filepath_label = ctk.CTkLabel(
            frame, text="Nenhum arquivo selecionado.", text_color="gray"
        )
        self.prof_filepath_label.pack(pady=(5, 0))

        ctk.CTkButton(
            frame, text="📎 Anexar Arquivo...", command=self._anexar_arquivo_prof_dialog
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="🚀 Enviar Atividade",
            command=lambda: self._enviar_atividade_professor_action(envio_window),
            fg_color="green",
            font=("Arial", 14, "bold"),
        ).pack(pady=20)

    def _force_initial_load(self, turma_nome):
        """
        Garante que a função de cascata seja chamada manualmente
        se a turma for definida por código (no caso de uma única opção).
        """
        # Define o ComboBox para o valor e, em seguida, dispara o comando
        self.prof_turma_combobox.set(turma_nome)
        self._update_disciplinas_dropdown_prof(turma_nome)

    def _update_disciplinas_dropdown_prof(self, turma_selecionada):
        """Carrega as disciplinas baseadas no CURSO e TURMA selecionados."""

        # Resetar destinos
        self.prof_destino_combobox.set("...")
        self.prof_destino_combobox.configure(state="disabled")

        if turma_selecionada == "Selecione a turma...":
            self.prof_disciplina_combobox.configure(state="disabled")
            return

        # PEGA O CURSO DO PRIMEIRO COMBOBOX (Mais seguro que buscar no CSV)
        curso_selecionado = self.prof_curso_combo.get()

        # Monta caminho: Atividades / Curso / Turma
        pasta_turma = os.path.join(
            DIR_ATIVIDADES, str(curso_selecionado), str(turma_selecionada)
        )

        print(f"DEBUG: Buscando disciplinas em: {pasta_turma}")

        if not os.path.exists(pasta_turma):
            self.prof_disciplina_combobox.configure(
                values=["Pasta da turma não criada"], state="disabled"
            )
            self.prof_disciplina_combobox.set("Pasta da turma não criada")
            return

        itens = os.listdir(pasta_turma)
        disciplinas = [i for i in itens if os.path.isdir(os.path.join(pasta_turma, i))]
        disciplinas.sort()

        if not disciplinas:
            self.prof_disciplina_combobox.configure(
                values=["Nenhuma disciplina criada"], state="disabled"
            )
            self.prof_disciplina_combobox.set("Nenhuma disciplina criada")
            return

        valores = ["Selecione a disciplina..."] + disciplinas
        self.prof_disciplina_combobox.configure(values=valores, state="normal")
        self.prof_disciplina_combobox.set(valores[0])

    def _update_turmas_dropdown_prof(self, curso_selecionado):
        """
        Carrega as turmas baseadas no CURSO selecionado.
        PADRONIZAÇÃO: Converte tudo para maiúsculo na comparação.
        """
        # Resetar os combos abaixo
        self.prof_turma_combobox.set("Selecione a turma...")
        self.prof_turma_combobox.configure(values=["Carregando..."], state="disabled")
        self.prof_disciplina_combobox.set("...")
        self.prof_disciplina_combobox.configure(state="disabled")
        self.prof_destino_combobox.set("...")
        self.prof_destino_combobox.configure(state="disabled")

        if not curso_selecionado or curso_selecionado == "Selecione o curso...":
            return

        try:
            df = self.main_app.data_frame_full

            # --- LÓGICA PADRONIZADA (CASE INSENSITIVE) ---
            # 1. Converte a coluna do DataFrame para string, remove espaços e põe em maiúsculo
            # 2. Faz o mesmo com o valor selecionado no combobox
            mask = (
                df["CURSO"].astype(str).str.strip().str.upper()
                == str(curso_selecionado).strip().upper()
            ) & (df["NIVEL"] == "ALUNO")

            turmas_filtradas = df[mask]["TURMAS"].unique().tolist()

            # Limpeza de dados (remove nulos/vazios)
            turmas_limpas = [
                t
                for t in turmas_filtradas
                if str(t).lower() not in ["nan", "none", "", "geral"]
            ]
            turmas_limpas.sort()

            if not turmas_limpas:
                self.prof_turma_combobox.configure(
                    values=["Nenhuma turma neste curso"], state="disabled"
                )
                self.prof_turma_combobox.set("Nenhuma turma neste curso")
                return

            valores = ["Selecione a turma..."] + turmas_limpas
            self.prof_turma_combobox.configure(values=valores, state="normal")
            self.prof_turma_combobox.set(valores[0])

        except Exception as e:
            print(f"Erro ao filtrar turmas: {e}")

    def _update_destino_dropdown_prof(self, disciplina_selecionada):
        """Define os destinos possíveis dentro da disciplina."""

        if disciplina_selecionada == "Selecione a disciplina...":
            self.prof_destino_combobox.configure(state="disabled")
            return

        curso = self.prof_curso_combo.get()
        turma = self.prof_turma_combobox.get()

        pasta_disciplina = os.path.join(
            DIR_ATIVIDADES, curso, turma, disciplina_selecionada
        )

        opcoes = ["[PASTA RAIZ DA DISCIPLINA]"]

        # Verifica se existe pasta de material
        if os.path.exists(os.path.join(pasta_disciplina, "MATERIAL_PARA_ESTUDO")):
            opcoes.append("MATERIAL_PARA_ESTUDO")

        # Verifica se existe pasta de entregas (opcional, geralmente prof não envia pra cá, mas pode)
        if os.path.exists(os.path.join(pasta_disciplina, "ENTREGAS")):
            opcoes.append("ENTREGAS")

        self.prof_destino_combobox.configure(values=opcoes, state="normal")
        self.prof_destino_combobox.set(opcoes[0])

    def _anexar_arquivo_prof_dialog(self):
        """Abre o seletor de arquivos para o professor."""
        filepath = filedialog.askopenfilename(
            title="Selecione o arquivo da atividade (PDF, DOCX, ZIP, etc.)",
            filetypes=(
                ("Documentos PDF", "*.pdf"),
                ("Documentos Word", "*.docx"),
                ("Arquivos Compactados", "*.zip"),
                ("Todos os Arquivos", "*.*"),
            ),
        )
        if filepath:
            self.prof_filepath_label.configure(
                text=f"Arquivo: {os.path.basename(filepath)}", text_color="yellow"
            )
            self.prof_current_file_path = filepath
        else:
            self.prof_filepath_label.configure(
                text="Nenhum arquivo selecionado.", text_color="gray"
            )
            self.prof_current_file_path = None

    def _enviar_atividade_professor_action(self, window):
        """Realiza o envio do arquivo."""
        curso = self.prof_curso_combo.get()
        turma = self.prof_turma_combobox.get()
        disciplina = self.prof_disciplina_combobox.get()
        destino = self.prof_destino_combobox.get()

        # Validações
        if "Selecione" in [curso, turma, disciplina]:
            messagebox.showwarning(
                "Aviso",
                "Preencha todos os campos (Curso, Turma e Disciplina).",
                parent=window,
            )
            return

        if (
            not hasattr(self, "prof_current_file_path")
            or not self.prof_current_file_path
        ):
            messagebox.showwarning("Aviso", "Anexe um arquivo.", parent=window)
            return

        try:
            # Define a pasta final
            pasta_base = os.path.join(DIR_ATIVIDADES, curso, turma, disciplina)

            if destino == "MATERIAL_PARA_ESTUDO":
                pasta_final = os.path.join(pasta_base, "MATERIAL_PARA_ESTUDO")
            elif destino == "ENTREGAS":
                pasta_final = os.path.join(pasta_base, "ENTREGAS")
            else:
                pasta_final = pasta_base  # Raiz

            os.makedirs(pasta_final, exist_ok=True)

            nome_arquivo = os.path.basename(self.prof_current_file_path)
            shutil.copy(
                self.prof_current_file_path, os.path.join(pasta_final, nome_arquivo)
            )

            messagebox.showinfo(
                "Sucesso",
                f"Arquivo enviado para:\n{curso} > {turma} > {disciplina}",
                parent=window,
            )
            window.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar: {e}", parent=window)


class Chatbot(ctk.CTkFrame):
    """
    Frame que gerencia a aba 'Assistente Acadêmico' (Chatbot).
    Modificado para REMOVER a entrada de texto livre.
    """

    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self, text="Assistente Acadêmico", font=("Arial", 18, "bold")
        ).pack(pady=10)

        # Área de Chat
        self.area_chat = tk.Text(
            self, height=12, state=tk.DISABLED, wrap=tk.WORD, font=("Arial", 10)
        )
        self.area_chat.pack(padx=10, pady=5, fill="both", expand=True)

        # --- REMOVIDO: frame_entrada, entry_pergunta e o botão "Enviar" ---

        # Frame de Perguntas Frequentes
        frame_botoes = ctk.CTkFrame(self)
        frame_botoes.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(
            frame_botoes, text="Perguntas Frequentes:", font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        canvas = tk.Canvas(
            frame_botoes,
            height=200,
            bg=self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
            ),
            highlightthickness=0,
        )
        v_scrollbar = ctk.CTkScrollbar(
            frame_botoes, orientation="vertical", command=canvas.yview
        )
        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_window_id = canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw"
        )
        canvas.configure(yscrollcommand=v_scrollbar.set)

        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(scrollable_window_id, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        v_scrollbar.grid(row=1, column=2, sticky="ns")
        canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_rowconfigure(1, weight=1)

        perguntas = list(respostas.keys())
        num_perguntas = len(perguntas)
        num_colunas = 2

        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

        for i in range(num_perguntas):
            pergunta = perguntas[i]
            row = i // num_colunas
            col = i % num_colunas
            btn = ctk.CTkButton(
                scrollable_frame,
                text=pergunta,
                command=lambda p=pergunta: self.fazer_pergunta_frequente(p),
                corner_radius=8,
                height=40,
            )
            btn.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

        self.mostrar_mensagem_boas_vindas()

    def mostrar_mensagem_boas_vindas(self):
        self.adicionar_mensagem(
            "Assistente",
            "Olá! Sou seu assistente acadêmico. Clique em uma pergunta para começar.",
        )

    def adicionar_mensagem(self, remetente, mensagem):
        self.area_chat.config(state=tk.NORMAL)
        tag_color = "blue" if remetente == "Assistente" else "green"
        self.area_chat.tag_config(
            remetente, foreground=tag_color, font=("Arial", 10, "bold")
        )
        self.area_chat.insert(tk.END, f"{remetente}: ", remetente)
        self.area_chat.insert(tk.END, f"{mensagem}\n\n")
        self.area_chat.config(state=tk.DISABLED)
        self.area_chat.see(tk.END)

    def fazer_pergunta_frequente(self, pergunta):
        """Responde a perguntas pré-definidas (botões)."""
        self.adicionar_mensagem("Você", pergunta)
        self.adicionar_mensagem("Assistente", respostas[pergunta])

    # --- REMOVIDO: enviar_mensagem_livre e seus componentes de validação ---


# === 7. PONTO DE ENTRADA (MAIN) ===

if __name__ == "__main__":
    Path("Output").mkdir(exist_ok=True)
    ctk.set_appearance_mode("Dark")

    ctk.set_default_color_theme("blue")

    app = MainApp()
    app.iniciar_lgpd_check()
    app.mainloop()

# atualizado em 20/11 ás 19:20

# implementar > se status do aluno for INATIVO, bloquear o acesso para login, com um messagebox "acesso bloqueado, entre em contato com a secretaria"
