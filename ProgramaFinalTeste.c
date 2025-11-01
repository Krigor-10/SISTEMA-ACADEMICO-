#define _POSIX_C_SOURCE 200809L // Tente esta linha primeiro, ou _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sistemaAcademico_unificado.h"
#include <strings.h> // ⬅️ ADICIONE ESTA LINHA para strcasecmp

// === Declara��es antecipadas (corrigem implicit declaration) ===
void verNotasAlunoUnico(void);
void verMediaTurmaPorMateria(void);
void listarDadosMatriculaUsuarios(void);

// Certifique-se de que a estrutura UsuarioCSV e MAX_LINE estão disponíveis.
// Esta função assume que a função read_section_content() e parseLinhaUsuario() existem.
// A função STRCASECMP (para ignorar caixa) também deve estar disponível (strings.h).

void listarDadosMatriculaUsuarios(void)
{
    char *sec = read_section_content("USUARIOS");
    if (!sec)
    {
        printf("Nenhum usuário cadastrado ou seção [USUARIOS] não encontrada.\n");
        return;
    }

    printf("\n=== VISÃO DE MATRÍCULA DE ALUNOS ===\n");

    // Cabeçalho dos 4 campos solicitados
    printf("%-5s | %-20s | %-50s | %-40s\n",
           "ID", "CURSO", "MATÉRIA", "TURMA (Cód. Longo)");
    printf("--------------------------------------------------------------------------------------------------------------------------------\n");

    char *p = sec;
    int alunos_encontrados = 0;

    // Pula o cabeçalho
    if (strncmp(p, "ID;", 3) == 0)
    {
        char *nl = strchr(p, '\n');
        if (nl)
            p = nl + 1;
    }

    while (p && *p)
    {
        char *nl = strchr(p, '\n');
        size_t l = nl ? (size_t)(nl - p) : strlen(p);
        char line[MAX_LINE];
        if (l >= sizeof(line))
            l = sizeof(line) - 1;
        strncpy(line, p, l);
        line[l] = '\0';
        if (l > 0 && line[l - 1] == '\r')
            line[l - 1] = 0;

        UsuarioCSV u;
        // Faz uma cópia da linha para o parser, já que strtok modifica o buffer
        char line_copy[MAX_LINE];
        strncpy(line_copy, line, MAX_LINE - 1);
        line_copy[MAX_LINE - 1] = '\0';

        if (parseLinhaUsuario(line_copy, &u))
        {
            // Filtra: Mostra SÓ SE o Nível for "Aluno"
            if (STRCASECMP(u.nivel, "Aluno") == 0)
            {
                printf("%-5d | %-20.20s | %-50.50s | %-40.40s\n",
                       u.id,
                       u.curso,
                       u.listaMaterias,
                       u.idsTurmas);

                alunos_encontrados++;
            }
        }
        p = nl ? nl + 1 : NULL;
    }

    if (alunos_encontrados == 0)
    {
        printf("Nenhum Aluno encontrado com dados de matrícula.\n");
    }

    free(sec);
}

void listarTurmasFiltradas(const char *materia_filtro, const char *turno_filtro)
{
    char *sec = read_section_content("TURMAS");
    if (!sec)
    {
        printf("Nenhuma turma cadastrada ou seção [TURMAS] não encontrada.\n");
        return;
    }

    // Variáveis de controle de filtro
    int materia_nao_vazia = (materia_filtro && materia_filtro[0] != '\0');
    int turno_nao_vazia = (turno_filtro && turno_filtro[0] != '\0');
    int turmas_encontradas = 0;

    printf("\n=== TURMAS ENCONTRADAS ===\n");

    // Cabeçalho da tabela
    printf("%-5s | %-50s | %-20s | %-10s | %-10s\n", "ID", "Nome da Turma", "Curso", "ID Prof", "Alunos IDs");
    printf("--------------------------------------------------------------------------------------------------------------------------------\n");

    char *p = sec;
    // Pula o cabeçalho
    if (strncmp(p, "ID;", 3) == 0)
    {
        char *nl = strchr(p, '\n');
        if (nl)
            p = nl + 1;
    }

    while (p && *p)
    {
        char *nl = strchr(p, '\n');
        size_t l = nl ? (size_t)(nl - p) : strlen(p);
        char line[MAX_LINE];
        if (l >= sizeof(line))
            l = sizeof(line) - 1;
        strncpy(line, p, l);
        line[l] = '\0';
        if (l > 0 && line[l - 1] == '\r')
            line[l - 1] = 0;

        TurmaCSV t;
        // Precisamos de uma cópia para o parser, mas aqui não precisamos de uma cópia extra.
        if (parseLinhaTurma(line, &t))
        {
            int passou_materia = 1;
            int passou_turno = 1;

            // 1. Filtragem por Matéria (Usando STRCASECMP para ignorar caixa)
            if (materia_nao_vazia)
            {
                // Verifica se o NOME da turma CONTÉM o nome da matéria (case-insensitive)
                // Usamos strstr para buscar a substring da matéria dentro do nome da turma
                if (STRCASECMP(t.nome, materia_filtro) != 0 && strstr(t.nome, materia_filtro) == NULL)
                {
                    passou_materia = 0;
                }
            }

            // 2. Filtragem por Turno
            if (turno_nao_vazia)
            {
                // O nome do turno (MANHÃ, TARDE, NOITE) aparece na parte final da string " - XX_TURNO"
                // Buscamos a string "_TURNO" no nome da turma.
                char busca_turno[20];
                snprintf(busca_turno, sizeof(busca_turno), "_%s", turno_filtro);

                if (strstr(t.nome, busca_turno) == NULL)
                {
                    passou_turno = 0;
                }
            }

            // Se passar em ambos os filtros, exibe
            if (passou_materia && passou_turno)
            {
                printf("%-5d | %-50.50s | %-20.20s | %-10d | %-10.10s\n",
                       t.id, t.nome, t.curso, t.idProfessor, t.idsAlunos);
                turmas_encontradas++;
            }
        }
        p = nl ? nl + 1 : NULL;
    }

    if (turmas_encontradas == 0)
    {
        printf("Nenhuma turma corresponde aos critérios de filtro.\n");
    }

    free(sec);
}

void gerenciarNotasUnico(void)
{
    int opc;
    do
    {
        printf("\n===== GERENCIAR NOTAS =====\n");
        printf("1 - Listar Notas\n");
        printf("2 - Adicionar Nota\n");
        printf("3 - Ver Notas de Aluno\n");
        printf("4 - Ver M�dia da Turma por Mat�ria\n");
        printf("0 - Voltar\n");
        printf("Op��o: ");
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
            listarNotasUnico();
        }
        else if (opc == 2)
        {
            int idAluno;
            char curso[128], materia[128];
            float np1, np2, pim;
            printf("ID do aluno: ");
            scanf("%d", &idAluno);
            while (getchar() != '\n')
                ;
            printf("Curso: ");
            fgets(curso, sizeof(curso), stdin);
            curso[strcspn(curso, "\r\n")] = 0;
            printf("Mat�ria: ");
            fgets(materia, sizeof(materia), stdin);
            materia[strcspn(materia, "\r\n")] = 0;
            printf("NP1: ");
            scanf("%f", &np1);
            while (getchar() != '\n')
                ;
            printf("NP2: ");
            scanf("%f", &np2);
            while (getchar() != '\n')
                ;
            printf("PIM: ");
            scanf("%f", &pim);
            while (getchar() != '\n')
                ;
            adicionarNotaUnico(idAluno, curso, materia, np1, np2, pim);
        }
        else if (opc == 3)
        {
            verNotasAlunoUnico();
        }
        else if (opc == 4)
        {
            verMediaTurmaPorMateria();
        }
        else if (opc == 0)
            break;
        else
            printf("Op��o inv�lida.\n");
    } while (1);
}

void gerenciarTurmasUnico(void)
{
    int opc;
    do
    {
        printf("\n===== RELATÓRIOS DE TURMAS E MATRÍCULA =====\n");
        printf("1 - Listar Dados de Matrícula (ID, Curso, Matéria, Turma)\n"); // NOVO NOME
        printf("2 - Adicionar Turma (Aviso: Turmas estão desabilitadas no CSV)\n");
        printf("3 - Filtrar Turmas (Aviso: Funcionalidade desabilitada no CSV)\n");
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
            // 🚨 Chama a nova função 🚨
            listarDadosMatriculaUsuarios();
        }
        else if (opc == 2)
        {
            printf("\n[AVISO] A adição de turmas está desabilitada no modo apenas [USUARIOS].\n");
        }
        else if (opc == 3)
        {
            printf("\n[AVISO] A filtragem de turmas está desabilitada no modo apenas [USUARIOS].\n");
        }
        else if (opc == 0)
            break;
        else
            printf("Opção inválida.\n");
    } while (1);
}

void gerenciarUsuariosUnico(void)
{
    int opc;
    do
    {
        printf("\n===== GERENCIAR USUÁRIOS =====\n");
        printf("1 - Listar Usuários\n");
        printf("2 - Adicionar Usuário\n");
        printf("3 - Alterar Usuário\n");
        printf("4 - Excluir Usuário\n");
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
            listarTodosUsuarios();
        }
        else if (opc == 2)
        {
            UsuarioCSV u;
            memset(&u, 0, sizeof(u));
            printf("Nome: ");
            fgets(u.nome, sizeof(u.nome), stdin);
            u.nome[strcspn(u.nome, "\r\n")] = 0;
            printf("Email: ");
            fgets(u.email, sizeof(u.email), stdin);
            u.email[strcspn(u.email, "\r\n")] = 0;
            printf("Senha: ");
            fgets(u.senha, sizeof(u.senha), stdin);
            u.senha[strcspn(u.senha, "\r\n")] = 0;
            printf("Idade: ");
            scanf("%d", &u.idade);
            while (getchar() != '\n')
                ;

            printf("Nível (Aluno/Professor/Coordenador/Administrador): ");
            fgets(u.nivel, sizeof(u.nivel), stdin);
            u.nivel[strcspn(u.nivel, "\r\n")] = 0;

            // 🌟 LÓGICA DE ESCOLHA (MATÉRIAS + TURMAS) 🌟
            if (strcasecmp(u.nivel, "Aluno") == 0)
            {
                // 1. Curso Fixo
                strcpy(u.curso, "ANALISE E DESENVOLVIMENTO DE SISTEMA");
                printf("\n>>> CURSO FIXO: %s <<<\n", u.curso);

                // 2. Opções de Matérias (SELEÇÃO NUMERADA)
                printf("\n==================================\n");
                printf("SELEÇÃO DE MATÉRIA\n");
                for (int i = 0; i < NUM_MATERIAS; i++)
                {
                    printf("%d - %s\n", i + 1, MATERIAS_DISPONIVEIS[i]);
                }
                printf("Digite o NÚMERO da ÚNICA matéria que deseja cursar: ");

                int escolha_materia_idx;

                if (scanf("%d", &escolha_materia_idx) != 1)
                {
                    escolha_materia_idx = -1;
                }
                while (getchar() != '\n')
                    ; // Limpa o buffer de entrada

                if (escolha_materia_idx < 1 || escolha_materia_idx > NUM_MATERIAS)
                {
                    printf("Opção de matéria inválida. Cadastro cancelado.\n");
                    return; // Sai da função ou do bloco de adição
                }

                // Matéria escolhida (String)
                const char *materia_nome = MATERIAS_DISPONIVEIS[escolha_materia_idx - 1];

                // Copia a matéria única para a listaMaterias
                strncpy(u.listaMaterias, materia_nome, sizeof(u.listaMaterias) - 1);
                u.listaMaterias[sizeof(u.listaMaterias) - 1] = '\0';
                printf("-> Matéria registrada: %s\n", u.listaMaterias);

                // --- 3. SELEÇÃO DE TURMA POR TURNO (Montagem do CÓDIGO LONGO) ---
                printf("\n==================================\n");
                printf("SELEÇÃO DE TURMA (Turnos para %s)\n", materia_nome);

                for (int i = 0; i < 3; i++)
                {
                    printf("%d%s - %s\n", escolha_materia_idx, TURNOS_CODIGOS[i], TURNOS[i]);
                }

                printf("Digite o CÓDIGO da turma desejada (Ex: %dA ou %dC): ",
                       escolha_materia_idx, escolha_materia_idx);

                char codigo_turma_str[4];
                if (!fgets(codigo_turma_str, sizeof(codigo_turma_str), stdin))
                {
                    printf("Falha na leitura do código da turma.\n");
                    strcpy(u.idsTurmas, "");
                    return;
                }
                codigo_turma_str[strcspn(codigo_turma_str, "\r\n ")] = 0;

                // Processamento do Código (Ex: 4C)
                int id_digitado = atoi(codigo_turma_str);
                char turno_char = toupper((unsigned char)codigo_turma_str[strlen(codigo_turma_str) - 1]);
                int turno_idx = -1;

                if (id_digitado == escolha_materia_idx)
                {
                    if (turno_char == 'A')
                        turno_idx = 0;
                    else if (turno_char == 'B')
                        turno_idx = 1;
                    else if (turno_char == 'C')
                        turno_idx = 2;
                }

                if (turno_idx != -1)
                {
                    // 🚨 CORREÇÃO NO FORMATO 🚨: [NOME_MATERIA] - [ID_TURMA]_[NOME_TURNO]
                    // Exemplo: "PROGRAMAÇÃO C - 4C_NOITE"
                    snprintf(u.idsTurmas, sizeof(u.idsTurmas), "%s - %s_%s",
                             materia_nome,
                             codigo_turma_str,
                             TURNOS[turno_idx]);

                    printf("-> Nomenclatura Turma registrada: %s\n", u.idsTurmas);
                }
                else
                {
                    printf("Código de turma inválido ou não corresponde à matéria escolhida. Turma não registrada.\n");
                    strcpy(u.idsTurmas, ""); // Garante que o campo fique vazio
                }
            }
            else if (strcasecmp(u.nivel, "Professor") == 0)
            {
                // Se for professor/coordenador/admin, pede listaMaterias e zera idsTurmas (ou permite entrada livre)
                printf("Lista de matérias/matéria (Ex: Matéria A,Matéria B): ");
                fgets(u.listaMaterias, sizeof(u.listaMaterias), stdin);
                u.listaMaterias[strcspn(u.listaMaterias, "\r\n")] = 0;
                strcpy(u.idsTurmas, "");
            }
            else if (strcasecmp(u.nivel, "Coordenador") == 0)
            {
                printf("Lista de matérias/matéria (Ex: Matéria A,Matéria B): ");
                fgets(u.listaMaterias, sizeof(u.listaMaterias), stdin);
                u.listaMaterias[strcspn(u.listaMaterias, "\r\n")] = 0;
                strcpy(u.idsTurmas, "");
            }
            else
            { // Admin
                strcpy(u.listaMaterias, "");
                strcpy(u.idsTurmas, "");
            }
            // 🌟 FIM DA LÓGICA DE ESCOLHA 🌟

            strcpy(u.atividade, "Ativo");

            adicionarUsuarioUnicoValidado(&u);
        }
        else if (opc == 3)
        {
            int id;
            printf("ID do usuário a alterar: ");
            scanf("%d", &id);
            while (getchar() != '\n')
                ;
            UsuarioCSV novo;
            memset(&novo, 0, sizeof(novo));
            novo.id = id;

            // --- ENTRADA DE DADOS BÁSICOS ---
            printf("Novo nome: ");
            fgets(novo.nome, sizeof(novo.nome), stdin);
            novo.nome[strcspn(novo.nome, "\r\n")] = 0;
            printf("Novo email: ");
            fgets(novo.email, sizeof(novo.email), stdin);
            novo.email[strcspn(novo.email, "\r\n")] = 0;
            printf("Nova senha: ");
            fgets(novo.senha, sizeof(novo.senha), stdin);
            novo.senha[strcspn(novo.senha, "\r\n")] = 0;
            printf("Nova idade: ");
            scanf("%d", &novo.idade);
            while (getchar() != '\n')
                ;
            printf("Novo nível: ");
            fgets(novo.nivel, sizeof(novo.nivel), stdin);
            novo.nivel[strcspn(novo.nivel, "\r\n")] = 0;
            printf("Novo curso: ");
            fgets(novo.curso, sizeof(novo.curso), stdin);
            novo.curso[strcspn(novo.curso, "\r\n")] = 0;

            // --- LÓGICA DE ALTERAÇÃO DE MATÉRIA/TURMA (PADRONIZADA) ---
            if (strcasecmp(novo.nivel, "Aluno") == 0)
            {
                // ** LÓGICA DE SELEÇÃO NUMERADA PARA ALUNO (REUTILIZADA) **

                // 1. SELEÇÃO DE MATÉRIA (ÚNICA)
                printf("\n--- SELEÇÃO DE NOVA MATÉRIA PARA ALUNO ---\n");
                for (int i = 0; i < NUM_MATERIAS; i++)
                {
                    printf("%d - %s\n", i + 1, MATERIAS_DISPONIVEIS[i]);
                }
                printf("Digite o NÚMERO da ÚNICA matéria: ");

                int escolha_materia_idx;
                if (scanf("%d", &escolha_materia_idx) != 1)
                {
                    escolha_materia_idx = -1;
                }
                while (getchar() != '\n')
                    ;

                if (escolha_materia_idx < 1 || escolha_materia_idx > NUM_MATERIAS)
                {
                    printf("Opção de matéria inválida. Matéria não alterada.\n");
                    strcpy(novo.listaMaterias, "");
                    strcpy(novo.idsTurmas, "");
                }
                else
                {
                    const char *materia_nome = MATERIAS_DISPONIVEIS[escolha_materia_idx - 1];
                    strncpy(novo.listaMaterias, materia_nome, sizeof(novo.listaMaterias) - 1);
                    novo.listaMaterias[sizeof(novo.listaMaterias) - 1] = '\0';
                    printf("-> Matéria alterada para: %s\n", novo.listaMaterias);

                    // 2. SELEÇÃO DE TURMA POR TURNO (Nomenclatura Longa)
                    printf("\n--- SELEÇÃO DE NOVA TURMA ---\n");
                    for (int i = 0; i < 3; i++)
                    {
                        printf("%d%s - %s\n", escolha_materia_idx, TURNOS_CODIGOS[i], TURNOS[i]);
                    }
                    printf("Digite o CÓDIGO da nova turma (Ex: %dA ou %dC): ",
                           escolha_materia_idx, escolha_materia_idx);

                    char codigo_turma_str[4];
                    if (!fgets(codigo_turma_str, sizeof(codigo_turma_str), stdin))
                    {
                        strcpy(novo.idsTurmas, "");
                        return;
                    }
                    codigo_turma_str[strcspn(codigo_turma_str, "\r\n ")] = 0;

                    // Processamento do Código (Ex: 4C) e Montagem da String
                    int id_digitado = atoi(codigo_turma_str);
                    char turno_char = toupper((unsigned char)codigo_turma_str[strlen(codigo_turma_str) - 1]);
                    int turno_idx = -1;

                    if (id_digitado == escolha_materia_idx)
                    {
                        if (turno_char == 'A')
                            turno_idx = 0;
                        else if (turno_char == 'B')
                            turno_idx = 1;
                        else if (turno_char == 'C')
                            turno_idx = 2;
                    }

                    if (turno_idx != -1)
                    {
                        // 🚨 APLICAÇÃO DO PADRÃO LONGO 🚨
                        // Formato: [NOME_MATERIA] - [ID_TURMA]_[NOME_TURNO]
                        snprintf(novo.idsTurmas, sizeof(novo.idsTurmas), "%s - %s_%s",
                                 materia_nome,
                                 codigo_turma_str,
                                 TURNOS[turno_idx]);

                        printf("-> Nomenclatura Turma alterada para: %s\n", novo.idsTurmas);
                    }
                    else
                    {
                        printf("Código de turma inválido. Turma não alterada.\n");
                        strcpy(novo.idsTurmas, "");
                    }
                }
            }
            else // PROFESSOR / COORDENADOR / ADMIN
            {
                // Para não-alunos, mantemos a entrada simples para materias e turmas
                printf("Nova lista de matérias/matéria: ");
                fgets(novo.listaMaterias, sizeof(novo.listaMaterias), stdin);
                novo.listaMaterias[strcspn(novo.listaMaterias, "\r\n")] = 0;

                printf("Novo campo IDs Turmas (Se necessário, digite o novo valor): ");
                fgets(novo.idsTurmas, sizeof(novo.idsTurmas), stdin);
                novo.idsTurmas[strcspn(novo.idsTurmas, "\r\n")] = 0;
            }

            // --- ENTRADA DE ATIVIDADE (Final) ---
            printf("Atividade (Ativo/Inativo): ");
            fgets(novo.atividade, sizeof(novo.atividade), stdin);
            novo.atividade[strcspn(novo.atividade, "\r\n")] = 0;

            alterarUsuarioPorIDUnicoValidated(id, &novo);
        }
        else if (opc == 4)
        {
            int id;
            printf("ID do usuário a excluir: ");
            scanf("%d", &id);
            while (getchar() != '\n')
                ;
            printf("Confirmar exclusão (s/N): ");
            char resp[4];
            fgets(resp, sizeof(resp), stdin);
            if (resp[0] == 's' || resp[0] == 'S')
                excluirUsuarioPorIDUnico(id);
        }
        else if (opc == 0)
            break;
        else
            printf("Opção inválida.\n");
    } while (1);
}
/*
  ProgramaFinalTeste.c
  Sistema Acad�mico Unificado
  - Corrigido para compatibilidade total com sistemaAcademico_unificado.h
  - Inclui 3 tentativas de login
  - Mant�m todas as funcionalidades (Usu�rios, Turmas, Notas)
*/

// ------------------- CONSULTAS AUXILIARES -------------------
void verNotasAlunoUnico(void)
{
    int id;
    printf("Digite o ID do aluno: ");
    scanf("%d", &id);
    while (getchar() != '\n')
        ;

    listarNotasUnico();
}

void verTurmasProfessor(void)
{
    printf("Fun��o futura: listar turmas do professor.\n");
}

void verMediaTurmaPorMateria(void)
{
    char materia[128];
    printf("Digite o nome da mat�ria: ");
    fgets(materia, sizeof(materia), stdin);
    materia[strcspn(materia, "\r\n")] = 0;

    // Fallback gen�rico usando listarNotasUnico()
    printf("\n=== Notas da mat�ria '%s' ===\n", materia);
    listarNotasUnico();
}

// ------------------- MENU COORDENADOR -------------------
void menuCoordenadorUnificado(const UsuarioCSV *u)
{
    int opc;
    do
    {
        printf("\n=== MENU COORDENADOR (%s) ===\n", u->nome);
        printf("1 - Ver Minhas Informações\n");
        // ... (resto do menu)
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
            // 🌟 AJUSTE AQUI para exibir os dois novos campos
            printf("ID: %d | Nome: %s | Email: %s | Nível: %s | Curso: %s | Matérias/Matéria: %s | Atividade: %s\n",
                   u->id, u->nome, u->email, u->nivel, u->curso, u->listaMaterias, u->atividade);
        }
        else if (opc == 2)
        {
            gerenciarTurmasUnico();
        }
        else if (opc == 3)
        {
            gerenciarNotasUnico();
        }
        else if (opc == 0)
            break;
        else
            printf("Opção inválida.\n");
    } while (1);
}

// NO ARQUIVO: sistemaAcademico_unificado.h (ou onde o menu está definido)

void menuAdministradorUnificado(const UsuarioCSV *u)
{
    int opc;
    do
    {
        printf("\n=== MENU ADMINISTRADOR (%s) ===\n", u->nome);
        printf("1 - Ver minhas informacoes\n");
        printf("2 - Gerenciar usuarios\n");
        printf("3 - Gerenciar turmas/Relatórios\n"); // NOME ATUALIZADO
        printf("4 - Gerenciar notas (Desabilitado)\n");
        printf("5 - Criar backup manual\n");
        printf("0 - Sair\n");
        printf("Opcao: ");
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
            printf("ID: %d | Nome: %s | Email: %s | Nivel: %s | Curso: %s | Materias/Materia: %s | Atividade: %s\n",
                   u->id, u->nome, u->email, u->nivel, u->curso, u->listaMaterias, u->atividade);
        }
        else if (opc == 2)
        {
            gerenciarUsuariosUnico();
        }
        else if (opc == 3)
        {
            // 🚨 CHAMADA CORRETA para o menu que contém a listagem de matrículas 🚨
            gerenciarTurmasUnico();
        }
        else if (opc == 4)
        {
            // Mantendo a chamada, que deve levar à função que avisa que está desabilitada
            gerenciarNotasUnico();
        }
        else if (opc == 5)
        {
            if (backupSistema())
                printf("Backup criado.\n");
            else
                printf("Falha ao criar backup.\n");
        }
        else if (opc == 0)
            break;
        else
            printf("Opcao invalida.\n");
    } while (1);
}

// ------------------- MAIN -------------------
int main(void)
{
    initSistema();
    criarArquivoSistemaSeNaoExiste();

    printf("\n=== SISTEMA ACAD�MICO UNIFICADO ===\n");

    UsuarioCSV logado;
    int tentativas = 0;
    int autenticado = 0;

    while (tentativas < 3)
    {
        if (loginUnico(&logado))
        {
            autenticado = 1;
            break;
        }
        else
        {
            tentativas++;
            if (tentativas < 3)
            {
                printf("Tentativa %d de 3 falhou. Tente novamente.\n", tentativas);
            }
            else
            {
                printf("N�mero m�ximo de tentativas atingido. Encerrando o sistema.\n");
                return 0;
            }
        }
    }

    if (!autenticado)
    {
        printf("Encerrando o sistema.\n");
        return 0;
    }

    if (strcasecmp(logado.nivel, "Administrador") == 0)
    {
        menuAdministradorUnificado(&logado);
    }
    else if (strcasecmp(logado.nivel, "Coordenador") == 0)
    {
        menuCoordenadorUnificado(&logado);
    }
    else if (strcasecmp(logado.nivel, "Professor") == 0)
    {
        printf("Bem-vindo, Professor %s!\n", logado.nome);
        verTurmasProfessor();
    }
    else
    {
        printf("Bem-vindo, Aluno %s!\n", logado.nome);
        verNotasAlunoUnico();
    }

    printf("Saindo do sistema. At� logo!\n");
    return 0;
}
