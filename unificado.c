#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sistemaAcademico_unificado.h"

/*
 * ProgramaFinalTeste.c
 * Sistema Acadêmico Integrado
 * - MODIFICADO: Sistema limpo. Removida a criação e o gerenciamento de TURMAS e NOTAS.
 * - MODIFICADO: Saída de listarTodosDadosUnificado AGORA usa o CABEÇALHO CSV PURO.
 */

// --- PROTÓTIPOS (DECLARAÇÕES) ---
void gerenciarUsuariosUnico(void);
void menuCoordenadorUnificado(const UsuarioCSV *u);

// --- NOVAS FUNÇÕES ADICIONADAS ---
void menuAlunoUnificado(const UsuarioCSV *u);
void acessarVideoAula(const UsuarioCSV *u);
void listarTodosDadosUnificado(void);
// --- FIM DOS PROTÓTIPOS ---

// ------------------- FUNÇÃO DE JUNÇÃO: LISTAR TODOS OS DADOS UNIFICADO (COM CABEÇALHO CSV) -------------------
/**
 * Realiza a listagem unificada, formatando a saída com ponto e vírgula (CSV) e o cabeçalho solicitado.
 */
void listarTodosDadosUnificado(void)
{
    // Tenta ler USUARIOS e NOTAS. (Notas deve ser NULL)
    char *usuarios_sec = read_section_content("USUARIOS");
    char *notas_sec = read_section_content("NOTAS");

    if (!usuarios_sec)
    {
        printf("Nenhum usuario cadastrado.\n");
        if (notas_sec)
            free(notas_sec);
        return;
    }

    char *notas_copy = notas_sec ? strdup(notas_sec) : NULL;

    // NOVO CABEÇALHO EXATO SOLICITADO (Saída no formato CSV com ponto e vírgula)
    printf("\nID;EMAIL;SENHA;IDADE;NIVEL;CURSO;TURMA;MATÉRIA;NP1;NP2;PIM;MÉDIA;STATUS\n");

    char *p = usuarios_sec;
    char *next_line;
    char line_buffer[MAX_LINE];

    // Itera sobre CADA USUÁRIO
    while (p && *p)
    {
        next_line = strchr(p, '\n');
        size_t line_len;
        if (next_line)
        {
            line_len = (size_t)(next_line - p);
        }
        else
        {
            line_len = strlen(p);
        }

        if (line_len >= sizeof(line_buffer))
        {
            line_len = sizeof(line_buffer) - 1;
        }
        strncpy(line_buffer, p, line_len);
        line_buffer[line_len] = '\0';

        if (strncmp(line_buffer, "ID;", 3) != 0 && line_buffer[0] != '\0' && line_buffer[0] != '\r')
        {

            char temp_line_for_parse[MAX_LINE];
            strncpy(temp_line_for_parse, line_buffer, sizeof(temp_line_for_parse) - 1);
            temp_line_for_parse[sizeof(temp_line_for_parse) - 1] = '\0';

            UsuarioCSV u;
            memset(&u, 0, sizeof(u));

            if (parseLinhaUsuario(temp_line_for_parse, &u))
            {
            int encontrou_nota = 0;

                // Lógica de Notas mantida no if (notas_copy), mas não deve ser executada
                // se o arquivo CSV não tiver a seção [NOTAS].

                // --- IMPRESSÃO NO FORMATO CSV PURO (Com N/A para campos de nota/turma) ---
                printf("%d;%s;%s;%d;%s;%s;N/A;N/A;N/A;N/A;N/A;N/A;%s\n",
                       u.id, u.email, u.senha, u.idade, u.nivel, u.cursoMateria, u.atividade);
            }
        }

        p = next_line ? next_line + 1 : NULL;
    }

    if (usuarios_sec)
        free(usuarios_sec);
    if (notas_sec)
        free(notas_sec);
    if (notas_copy)
        free(notas_copy);
}

// ------------------- FUNÇÃO NOVA: ACESSAR VIDEO AULA -------------------
void acessarVideoAula(const UsuarioCSV *u)
{
    const char *url = "https://teams.microsoft.com/equipes";

    printf("\nRedirecionando para a video aula do curso '%s'...\n", u->cursoMateria);

#ifdef _WIN32
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "start \"\" \"%s\"", url);
    system(cmd);
#else
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "xdg-open \"%s\" 2>/dev/null || open \"%s\"", url, url);
    system(cmd);
#endif

    printf("Se o navegador não abriu, acesse manualmente: %s\n", url);
    printf("\nPressione Enter para voltar ao menu...");
}

// ------------------- FUNÇÃO NOVA: MENU ALUNO (Corrigida) -------------------
// ------------------- FUNÇÃO NOVA: MENU ALUNO (Corrigida e Expandida) -------------------
void menuAlunoUnificado(const UsuarioCSV *u)
{
    int opc;
    do
    {
        printf("\n=== MENU ALUNO: %s (Curso: %s) ===\n", u->nome, u->cursoMateria);
        printf("1 - Ver meus dados (ID, Nome, Email, Idade, Curso)\n");
        printf("2 - Ver notas e medias (NP1, NP2, PIM, Media)\n");
        printf("3 - Acessar video aula da turma\n");
        printf("0 - Sair (Logout)\n");
        printf("Opção: ");

        if (scanf("%d", &opc) != 1)
        {
            while (getchar() != '\n')
                ;
            opc = -1;
        }
        while (getchar() != '\n')
            ;

        if (opc == 1)
        {
            printf("\n--- Meus Dados ---\n");
            printf("ID: %d\n", u->id);
            printf("Nome: %s\n", u->nome);
            printf("Email: %s\n", u->email);
            printf("Idade: %d\n", u->idade);
            printf("Curso: %s\n", u->cursoMateria);
        }
        else if (opc == 2)
        {
            printf("\n--- Notas e Medias ---\n");
            printf("NP1: %.2f\n", u->np1);
            printf("NP2: %.2f\n", u->np2);
            printf("PIM: %.2f\n", u->pim);
            printf("MÉDIA FINAL: %.2f\n", u->media);
        }
        else if (opc == 3)
        {
            acessarVideoAula(u);
        }
        else if (opc == 0)
        {
            break;
        }
        else
        {
            printf("Opção inválida.\n");
        }
    } while (1);
}
// ------------------- FUNÇÕES DE USUÁRIO (Corrigida a dependência de extern) -------------------
void gerenciarUsuariosUnico(void)
{
    int opc;
    do
    {
        printf("\n===== GERENCIAR USUÁRIOS =====\n");
        printf("1 - Listar Usuarios\n");
        printf("2 - Adicionar Usuario\n");
        printf("3 - Alterar Usuario\n");
        printf("4 - Excluir Usuario\n");
        printf("5 - Listar TODOS os Dados (Tabela Unificada)\n");
        printf("0 - Voltar\n");
        printf("Opção: ");
        if (scanf("%d", &opc) != 1)
        {
            while (getchar() != '\n')
                ;
            opc = -1;
        }
        while (getchar() != '\n')
            ;

        if (opc == 1)
        {
            // Omitindo 'extern' - a função é global no .h
            listarTodosUsuarios();
        }
        else if (opc == 2)
        {
            UsuarioCSV u;
            memset(&u, 0, sizeof(u));
            int opc_menu = -1;

            printf("Nome: ");
            fgets(u.nome, sizeof(u.nome), stdin);
            u.nome[strcspn(u.nome, "\r\n")] = 0;

            printf("Email: ");
            fgets(u.email, sizeof(u.email), stdin);
            u.email[strcspn(u.email, "\r\n")] = 0;

            printf("Senha: ");
            extern void lerSenhaOculta(char *senha, size_t max_len);
            lerSenhaOculta(u.senha, sizeof(u.senha));
            u.senha[strcspn(u.senha, "\r\n")] = 0;

            printf("Idade: ");
            while (scanf("%d", &u.idade) != 1)
            {
                while (getchar() != '\n')
                    ;
                printf("Entrada inválida. Digite apenas números para a idade: ");
            }
            while (getchar() != '\n')
                ;

            // --- 1. Seleção de Nível ---
            printf("Nível do Usuário:\n");
            printf("1 - Aluno\n");
            printf("2 - Professor\n");
            printf("3 - Coordenador\n");
            printf("4 - Administrador\n");

            opc_menu = -1;
            while (1)
            {
                printf("Opção: ");
                if (scanf("%d", &opc_menu) != 1)
                {
                    while (getchar() != '\n')
                        ;
                    opc_menu = -1;
                    printf("Entrada inválida. Digite apenas números.\n");
                }
                else
                {
                    while (getchar() != '\n')
                        ;
                    if (opc_menu >= 1 && opc_menu <= 4)
                    {
                        break;
                    }
                    else
                    {
                        printf("Opção inválida. Digite um número entre 1 e 4.\n");
                    }
                }
            }

            // --- 2. Definir Nível (string) e Curso/Matéria (automático/input) ---
            switch (opc_menu)
            {
            case 1:
                strcpy(u.nivel, "Aluno");
                strcpy(u.cursoMateria, "ANALISE E DESENVOLVIMENTO DE SISTEMAS");
                printf("-> Curso definido automaticamente como: %s\n", u.cursoMateria);
                break;
            case 2:
                strcpy(u.nivel, "Professor");
                printf("Matéria do Professor: ");
                fgets(u.cursoMateria, sizeof(u.cursoMateria), stdin);
                u.cursoMateria[strcspn(u.cursoMateria, "\r\n")] = 0;
                break;
            case 3:
                strcpy(u.nivel, "Coordenador");
                strcpy(u.cursoMateria, "ANALISE E DESENVOLVIMENTO DE SISTEMAS");
                printf("-> Curso do Coordenador definido automaticamente como: %s\n", u.cursoMateria);
                break;
            case 4:
                strcpy(u.nivel, "Administrador");
                strcpy(u.cursoMateria, "Sistema");
                printf("-> Curso/Matéria definido automaticamente como: Sistema\n");
                break;
            }

            // --- 3. Seleção de Atividade ---
            printf("Status do Usuário:\n");
            printf("1 - Ativo\n");
            printf("2 - Inativo\n");

            opc_menu = -1;
            while (1)
            {
                printf("Opção: ");
                if (scanf("%d", &opc_menu) != 1)
                {
                    while (getchar() != '\n')
                        ;
                    opc_menu = -1;
                    printf("Entrada inválida. Digite apenas números.\n");
                }
                else
                {
                    while (getchar() != '\n')
                        ;
                    if (opc_menu == 1 || opc_menu == 2)
                    {
                        break;
                    }
                    else
                    {
                        printf("Opção inválida. Digite 1 ou 2.\n");
                    }
                }
            }

            if (opc_menu == 1)
            {
                strcpy(u.atividade, "Ativo");
            }
            else
            {
                strcpy(u.atividade, "Inativo");
            }

            printf("-> Status definido como: %s\n", u.atividade);

            // Omitindo 'extern int' - a função é global no .h
            adicionarUsuarioUnicoValidado(&u);
        }
        else if (opc == 3)
        {
            // Omitindo 'extern int' - a função é global no .h
            int id;
            printf("ID do usuario a alterar: ");
            scanf("%d", &id);
            while (getchar() != '\n')
                ;
            UsuarioCSV novo;
            memset(&novo, 0, sizeof(novo));
            novo.id = id;
            printf("Novo nome: ");
            fgets(novo.nome, sizeof(novo.nome), stdin);
            novo.nome[strcspn(novo.nome, "\r\n")] = 0;
            printf("Novo email: ");
            fgets(novo.email, sizeof(novo.email), stdin);
            novo.email[strcspn(novo.email, "\r\n")] = 0;
            printf("Nova senha: ");
            extern void lerSenhaOculta(char *senha, size_t max_len);
            lerSenhaOculta(novo.senha, sizeof(novo.senha));
            novo.senha[strcspn(novo.senha, "\r\n")] = 0;
            printf("Nova idade: ");
            scanf("%d", &novo.idade);
            while (getchar() != '\n')
                ;
            printf("Novo nivel: ");
            fgets(novo.nivel, sizeof(novo.nivel), stdin);
            novo.nivel[strcspn(novo.nivel, "\r\n")] = 0;
            printf("Novo curso/materia: ");
            fgets(novo.cursoMateria, sizeof(novo.cursoMateria), stdin);
            novo.cursoMateria[strcspn(novo.cursoMateria, "\r\n")] = 0;
            printf("Atividade (Ativo/Inativo): ");
            fgets(novo.atividade, sizeof(novo.atividade), stdin);
            novo.atividade[strcspn(novo.atividade, "\r\n")] = 0;
            alterarUsuarioPorIDUnicoValidated(id, &novo);
        }
        else if (opc == 4)
        {
            // Omitindo 'extern int' - a função é global no .h
            int id;
            printf("ID do usuario a excluir: ");
            scanf("%d", &id);
            while (getchar() != '\n')
                ;
            printf("Confirmar exclusao (s/N): ");
            char resp[4];
            fgets(resp, sizeof(resp), stdin);
            if (resp[0] == 's' || resp[0] == 'S')
                excluirUsuarioPorIDUnico(id);
        }
        else if (opc == 5)
        {
            listarTodosDadosUnificado();
        }
        else if (opc == 0)
            break;
        else
            printf("Opção inválida.\n");
    } while (1);
}

// ------------------- MENU COORDENADOR (SIMPLIFICADO) -------------------
void menuCoordenadorUnificado(const UsuarioCSV *u)
{
    int opc;
    do
    {
        // Única linha de cabeçalho
        printf("\n=== MENU COORDENADOR: %s (Curso: %s) ===\n", u->nome, u->cursoMateria);
        printf("1 - Ver Minhas Informacoes\n");
        printf("0 - Sair\n");
        printf("Opção: ");
        if (scanf("%d", &opc) != 1)
        {
            while (getchar() != '\n')
                ;
            opc = -1;
        }
        while (getchar() != '\n')
            ;

        if (opc == 1)
        {
            printf("ID: %d | Nome: %s | Email: %s | Nivel: %s | Curso: %s | Atividade: %s\n",
                   u->id, u->nome, u->email, u->nivel, u->cursoMateria, u->atividade);
        }
        else if (opc == 0)
            break;
        else
            printf("Opção inválida.\n");
    } while (1);
}

// ------------------- MAIN -------------------
int main(void)
{
    // Funções globais definidas no .h
    extern void initSistema(void);
    extern void criarArquivoSistemaSeNaoExiste(void);
    // loginUnico não é static inline, então é global.
    // extern int loginUnico(UsuarioCSV *u);

    initSistema();
    criarArquivoSistemaSeNaoExiste();

    printf("\n=== SISTEMA ACADEMICO UNIFICADO ===\n");

    UsuarioCSV logado;
    int tentativas = 0;
    const int MAX_TENTATIVAS = 3;

    while (!loginUnico(&logado))
    {
        tentativas++;

        if (tentativas >= MAX_TENTATIVAS)
        {
            printf("\nNúmero máximo de tentativas (%d) atingido.\n", MAX_TENTATIVAS);
            printf("Encerrando o sistema por segurança.\n");
            return 0;
        }

        printf("Por favor, tente novamente. (Tentativa %d de %d)\n\n", tentativas + 1, MAX_TENTATIVAS);
    }

    extern int STRCASECMP(const char *s1, const char *s2);

    if (STRCASECMP(logado.nivel, "Administrador") == 0)
    {
        extern void menuAdministradorUnificado(const UsuarioCSV *u);
        menuAdministradorUnificado(&logado);
    }
    else if (STRCASECMP(logado.nivel, "Coordenador") == 0)
    {
        menuCoordenadorUnificado(&logado);
    }
    else if (STRCASECMP(logado.nivel, "Professor") == 0)
    {
        printf("Bem-vindo, Professor %s! O gerenciamento de dados foi removido.\n", logado.nome);
    }
    else
    {
        menuAlunoUnificado(&logado);
    }

    printf("Saindo do sistema. Ate logo!\n");
    return 0;
}