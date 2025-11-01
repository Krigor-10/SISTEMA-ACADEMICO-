#ifndef SISTEMA_ACADEMICO_UNIFICADO_H
#define SISTEMA_ACADEMICO_UNIFICADO_H

/*
  sistemaAcademico_unificado.h
  Vers�o unificada:
  - Mant�m Usu�rios, Turmas e Notas
  - Remove comandos ZIP (export/import)
  - Mant�m otimiza��es e corre��es da vers�o final (sem 'static inline')
  - Cria usu�rio admin padr�o caso n�o exista
  - Compat�vel Windows / Linux (GCC/MinGW)
*/

#define _CRT_SECURE_NO_WARNINGS

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <locale.h>

#ifdef _WIN32
#include <windows.h>
#include <direct.h>
#include <conio.h>
#define MKDIR(p) _mkdir(p)
#define PATH_SEP "\\"
#define STRCASECMP _stricmp
#else
#include <unistd.h>
#include <sys/stat.h>
#include <strings.h> // for strcasecmp
#define MKDIR(p) mkdir((p), 0700)
#define PATH_SEP "/"
#define STRCASECMP strcasecmp
#endif

#define ARQ_SISTEMA "sistemaAcademico.csv"
#define DIR_BACKUPS "backups"
#define TMP_DIR "tmp_import"
#define MAX_LINE 2048

/* ----------------- UTILITARIOS ----------------- */

void initSistema(void)
{
    setlocale(LC_ALL, "");
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    system("chcp 65001 > nul");
#endif
}

void removerBOM(char *linha)
{
    if (!linha)
        return;
    if ((unsigned char)linha[0] == 0xEF &&
        (unsigned char)linha[1] == 0xBB &&
        (unsigned char)linha[2] == 0xBF)
    {
        memmove(linha, linha + 3, strlen(linha + 3) + 1);
    }
}

void lerSenhaOculta(char *senha, size_t maxLen)
{
    if (!senha || maxLen == 0)
        return;
#ifdef _WIN32
    size_t idx = 0;
    int ch;
    while ((ch = _getch()) != '\r' && ch != '\n' && idx + 1 < maxLen)
    {
        if (ch == '\b')
        {
            if (idx > 0)
            {
                idx--;
                printf("\b \b");
            }
        }
        else
        {
            senha[idx++] = (char)ch;
            printf("*");
        }
    }
    senha[idx] = '\0';
    printf("\n");
#else
    if (fgets(senha, (int)maxLen, stdin))
    {
        senha[strcspn(senha, "\n")] = '\0';
    }
    else
        senha[0] = '\0';
#endif
}

int arquivoExiste(const char *nome)
{
    if (!nome)
        return 0;
    FILE *f = fopen(nome, "r");
    if (f)
    {
        fclose(f);
        return 1;
    }
    return 0;
}

void garantirPasta(const char *pasta)
{
    if (!pasta)
        return;
    if (!arquivoExiste(pasta))
        MKDIR(pasta);
}

void now_str(char *dest, size_t n)
{
    time_t t = time(NULL);
    struct tm tm;
#ifdef _WIN32
    struct tm *tptr = localtime(&t);
    if (tptr)
        tm = *tptr;
    else
        memset(&tm, 0, sizeof(tm));
#else
    localtime_r(&t, &tm);
#endif
    strftime(dest, n, "%Y%m%d_%H%M%S", &tm);
}

void trim(char *s)
{
    if (!s)
        return;
    char *p = s;
    while (*p && isspace((unsigned char)*p))
        p++;
    if (p != s)
        memmove(s, p, strlen(p) + 1);
    size_t L = strlen(s);
    while (L > 0 && isspace((unsigned char)s[L - 1]))
        s[--L] = '\0';
}

int validarEmail(const char *email)
{
    if (!email)
        return 0;
    const char *at = strchr(email, '@');
    if (!at || at == email)
        return 0;
    const char *dot = strchr(at + 1, '.');
    if (!dot || dot == at + 1)
        return 0;
    if (*(dot + 1) == '\0')
        return 0;
    return 1;
}

/* ----------------- ESTRUTURAS ----------------- */

const char *MATERIAS_DISPONIVEIS[] = {
    "ENGENHARIA DE SOFT AGIL",
    "ALGORITIMO E ESTRTURUA PYTHON",
    "PROGRAMAÇÃO C",
    "ANALISE E PROJETOS DE SISTEMA"};
const int NUM_MATERIAS = sizeof(MATERIAS_DISPONIVEIS) / sizeof(MATERIAS_DISPONIVEIS[0]);
const char *TURNOS[] = {"MANHÃ", "TARDE", "NOITE"};
const char *TURNOS_CODIGOS[] = {"A", "B", "C"};

typedef struct
{
    int id;
    char nome[256];
    char email[256];
    char senha[128];
    int idade;
    char nivel[64];

    char curso[128];         // Para o nome do curso fixo
    char listaMaterias[256]; // Para as matérias/lista de matérias (usado para salvar e carregar)
    char idsTurmas[256];
    float np1, np2, pim, media;
    char atividade[32];
} UsuarioCSV;

/* Turma */
typedef struct
{
    int id;
    char nome[256];
    char curso[128];
    int idProfessor;
    char idsAlunos[1024]; // lista separada por ','
} TurmaCSV;

/* Nota */
typedef struct
{
    int idAluno;
    char curso[128];
    char materia[128];
    float np1, np2, pim, media;
} NotaCSV;

/* ----------------- BACKUP ----------------- */

int backupSistema(void)
{
    garantirPasta(DIR_BACKUPS);
    char stamp[64];
    now_str(stamp, sizeof(stamp));
    char dest[512];
    snprintf(dest, sizeof(dest), "%s%ssistemaAcademico_backup_%s.csv", DIR_BACKUPS, PATH_SEP, stamp);

    FILE *fs = fopen(ARQ_SISTEMA, "rb");
    if (!fs)
        return 0;
    FILE *fd = fopen(dest, "wb");
    if (!fd)
    {
        fclose(fs);
        return 0;
    }

    char buf[4096];
    size_t r;
    while ((r = fread(buf, 1, sizeof(buf), fs)) > 0)
        fwrite(buf, 1, r, fd);
    fclose(fs);
    fclose(fd);
    return 1;
}

/* ----------------- LER/ESCREVER ARQUIVO UNICO (SE��ES) ----------------- */

char *readFileAll(const char *path)
{
    if (!path)
        return NULL;
    FILE *f = fopen(path, "rb");
    if (!f)
        return NULL;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc((size_t)sz + 1);
    if (!buf)
    {
        fclose(f);
        return NULL;
    }
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);
    return buf;
}

int writeFileAll(const char *path, const char *buf)
{
    if (!path || !buf)
        return 0;
    FILE *f = fopen(path, "wb");
    if (!f)
        return 0;
    fwrite(buf, 1, strlen(buf), f);
    fclose(f);
    return 1;
}

char *find_section_start(char *buf, const char *sec)
{
    if (!buf || !sec)
        return NULL;
    char pattern[128];
    snprintf(pattern, sizeof(pattern), "[%s]", sec);
    char *p = buf;
    while (*p)
    {
        char *lb = strchr(p, '[');
        if (!lb)
            return NULL;
        if (strncmp(lb, pattern, strlen(pattern)) == 0)
        {
            char *nl = strchr(lb, '\n');
            if (!nl)
                return nl + 1;
            return nl + 1;
        }
        p = lb + 1;
    }
    return NULL;
}

char *find_next_section(char *p)
{
    if (!p)
        return NULL;
    while (*p)
    {
        if (*p == '[')
            return p;
        p++;
    }
    return NULL;
}

char *read_section_content(const char *sec)
{
    if (!arquivoExiste(ARQ_SISTEMA))
        return NULL;
    char *buf = readFileAll(ARQ_SISTEMA);
    if (!buf)
        return NULL;
    char *start = find_section_start(buf, sec);
    if (!start)
    {
        free(buf);
        return NULL;
    }
    char *next = find_next_section(start);
    size_t len = next ? (size_t)(next - start) : strlen(start);
    char *out = malloc(len + 1);
    if (!out)
    {
        free(buf);
        return NULL;
    }
    strncpy(out, start, len);
    out[len] = '\0';
    // remove leading CR/LF
    while (*out == '\n' || *out == '\r')
        memmove(out, out + 1, strlen(out));
    free(buf);
    return out;
}

/*
 write_section_content: substitui somente o conte�do (ap�s header line) de uma se��o mantendo
 o cabe�alho [SECAO] e o restante do arquivo.
*/
int write_section_content(const char *sec, const char *conteudo)
{
    if (!arquivoExiste(ARQ_SISTEMA))
        return 0;
    char *buf = readFileAll(ARQ_SISTEMA);
    if (!buf)
        return 0;
    char pattern[128];
    snprintf(pattern, sizeof(pattern), "[%s]", sec);
    char *p = buf;
    char *found = NULL;
    while ((p = strstr(p, "[")) != NULL)
    {
        if (strncmp(p, pattern, strlen(pattern)) == 0)
        {
            found = p;
            break;
        }
        p++;
    }
    if (!found)
    {
        free(buf);
        return 0;
    }
    char *afterHeader = strchr(found, '\n');
    if (!afterHeader)
    {
        free(buf);
        return 0;
    }
    afterHeader++;
    char *next = afterHeader;
    while (*next)
    {
        if (*next == '[')
            break;
        next++;
    }
    size_t headlen = (size_t)(afterHeader - buf);
    size_t newcap = strlen(buf) + (conteudo ? strlen(conteudo) : 0) + 1024;
    char *out = malloc(newcap);
    if (!out)
    {
        free(buf);
        return 0;
    }
    out[0] = '\0';
    strncat(out, buf, headlen);
    if (conteudo && conteudo[0] != '\0')
    {
        strcat(out, conteudo);
        if (conteudo[strlen(conteudo) - 1] != '\n' && conteudo[strlen(conteudo) - 1] != '\r')
            strcat(out, "\n");
    }
    else
    {
        strcat(out, "\n");
    }
    if (*next)
        strcat(out, next);
    int ok = writeFileAll(ARQ_SISTEMA, out);
    free(buf);
    free(out);
    return ok;
}

/* ----------------- PARSER USU�RIOS ----------------- */

/* parseLinhaUsuario: usa c�pia local da linha para n�o destruir o buffer original */
#define _POSIX_C_SOURCE 200809L // Mantido, caso necessário para outras coisas
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
// ... inclua aqui outros cabeçalhos necessários (como "sistemaAcademico_unificado.h")

// As definições de removerBOM, trim, MAX_LINE, UsuarioCSV, TurmaCSV e NotaCSV
// são assumidas no arquivo sistemaAcademico_unificado.h ou em outro lugar.

int parseLinhaUsuario(char *line, UsuarioCSV *u)
{
    if (!line || !u)
        return 0;
    removerBOM(line);

    char local[MAX_LINE];
    strncpy(local, line, sizeof(local) - 1);
    local[sizeof(local) - 1] = '\0';
    trim(local);
    if (local[0] == '\0' || strncmp(local, "ID;", 3) == 0)
        return 0;

    char *tok;

    // 1. ID
    tok = strtok(local, ";");
    if (!tok)
        return 0;
    u->id = atoi(tok);

    // 2-6. Nome, Email, Senha, Idade, Nível
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->nome, tok, sizeof(u->nome) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->email, tok, sizeof(u->email) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->senha, tok, sizeof(u->senha) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    u->idade = atoi(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->nivel, tok, sizeof(u->nivel) - 1);

    // 7. CURSO
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->curso, tok, sizeof(u->curso) - 1);

    // 8. MATERIA (u.listaMaterias)
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->listaMaterias, tok, sizeof(u->listaMaterias) - 1);

    // 🌟 9. IDSTURMAS (NOVO CAMPO) 🌟
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(u->idsTurmas, tok, sizeof(u->idsTurmas) - 1);

    // 10-13. NP1, NP2, PIM, Media (A contagem de campos NP1 em diante foi ajustada)
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    u->np1 = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    u->np2 = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    u->pim = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    u->media = (float)atof(tok);

    // 14. Atividade
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "Ativo";
    strncpy(u->atividade, tok, sizeof(u->atividade) - 1);

    trim(u->nome);
    trim(u->email);
    trim(u->senha);
    trim(u->nivel);
    trim(u->curso);
    trim(u->listaMaterias);
    trim(u->idsTurmas); // 🌟 Adicionado trim para o novo campo
    trim(u->atividade);

    return 1;
}

/* ----------------- PARSER TURMAS/NOTAS ----------------- */

int parseLinhaTurma(char *line, TurmaCSV *t)
{
    if (!line || !t)
        return 0;
    removerBOM(line);

    char local[MAX_LINE];
    strncpy(local, line, sizeof(local) - 1);
    local[sizeof(local) - 1] = '\0';
    trim(local);
    if (local[0] == '\0' || strncmp(local, "ID;", 3) == 0)
        return 0;

    // VARIÁVEL saveptr REMOVIDA
    char *tok; // Não é mais saveptr

    // Primeira chamada
    tok = strtok(local, ";");
    if (!tok)
        return 0;
    t->id = atoi(tok);

    // Chamadas subsequentes
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(t->nome, tok, sizeof(t->nome) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(t->curso, tok, sizeof(t->curso) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    t->idProfessor = atoi(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        t->idsAlunos[0] = '\0';
    else
        strncpy(t->idsAlunos, tok, sizeof(t->idsAlunos) - 1);

    trim(t->nome);
    trim(t->curso);
    trim(t->idsAlunos);
    return 1;
}

int parseLinhaNota(char *line, NotaCSV *n)
{
    if (!line || !n)
        return 0;
    removerBOM(line);
    char local[MAX_LINE];
    strncpy(local, line, sizeof(local) - 1);
    local[sizeof(local) - 1] = '\0';
    trim(local);
    if (local[0] == '\0' || strncmp(local, "IDAluno;", 8) == 0)
        return 0;

    // VARIÁVEL saveptr REMOVIDA
    char *tok; // Não é mais saveptr

    // Primeira chamada
    tok = strtok(local, ";");
    if (!tok)
        return 0;
    n->idAluno = atoi(tok);

    // Chamadas subsequentes
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(n->curso, tok, sizeof(n->curso) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        return 0;
    strncpy(n->materia, tok, sizeof(n->materia) - 1);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    n->np1 = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    n->np2 = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    n->pim = (float)atof(tok);
    tok = strtok(NULL, ";");
    if (!tok)
        tok = "0";
    n->media = (float)atof(tok);

    trim(n->curso);
    trim(n->materia);
    return 1;
}

/* ----------------- OPERACOES USUARIOS ----------------- */

int verificarLoginUnico(const char *email, const char *senha, UsuarioCSV *u_out)
{
    if (!email || !senha || !arquivoExiste(ARQ_SISTEMA))
        return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f)
        return 0;

    char linha[1024];
    int inUsuarios = 0;

    char emailTrim[256];
    char senhaTrim[128];
    strncpy(emailTrim, email, sizeof(emailTrim) - 1);
    emailTrim[sizeof(emailTrim) - 1] = 0;
    strncpy(senhaTrim, senha, sizeof(senhaTrim) - 1);
    senhaTrim[sizeof(senhaTrim) - 1] = 0;
    emailTrim[strcspn(emailTrim, "\r\n ")] = 0;
    senhaTrim[strcspn(senhaTrim, "\r\n ")] = 0;

    while (fgets(linha, sizeof(linha), f))
    {
        if (strncmp(linha, "[USUARIOS]", 10) == 0)
        {
            inUsuarios = 1;
            continue;
        }
        if (inUsuarios && linha[0] == '[')
            break;
        if (!inUsuarios || strncmp(linha, "ID;", 3) == 0)
            continue;

        linha[strcspn(linha, "\r\n")] = 0;
        char temp[MAX_LINE];
        strncpy(temp, linha, sizeof(temp) - 1);
        temp[sizeof(temp) - 1] = 0;
        UsuarioCSV u;
        memset(&u, 0, sizeof(u));
        if (parseLinhaUsuario(temp, &u))
        {
            // 🚨 AJUSTE AQUI: Removendo limpezas redundantes, confiando no parseLinhaUsuario

            // Compara os campos já limpos pela u.email (agora limpo pelo trim no parse)
            if (strcmp(u.email, emailTrim) == 0 && strcmp(u.senha, senhaTrim) == 0)
            {
                if (u_out)
                    *u_out = u;
                fclose(f);
                return 1;
            }
        }
    }

    fclose(f);
    return 0;
}

int obterUltimoIDUsuariosUnico(void)
{
    if (!arquivoExiste(ARQ_SISTEMA))
        return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f)
        return 0;
    char line[MAX_LINE];
    int inUsuarios = 0;
    int maxID = 0;
    while (fgets(line, sizeof(line), f))
    {
        removerBOM(line);
        line[strcspn(line, "\r\n")] = '\0';
        trim(line);
        if (line[0] == '\0')
            continue;
        if (!inUsuarios)
        {
            if (strncmp(line, "[USUARIOS]", 10) == 0)
            {
                inUsuarios = 1;
            }
            continue;
        }
        else
        {
            if (line[0] == '[')
                break;
            if (strncmp(line, "ID;", 3) == 0)
                continue;
            const char *p = line;
            while (*p && isspace((unsigned char)*p))
                p++;
            if (!isdigit((unsigned char)*p))
                continue;
            char idbuf[32] = {0};
            int i = 0;
            while (*p && *p != ';' && i < (int)sizeof(idbuf) - 1)
                idbuf[i++] = *p++;
            idbuf[i] = '\0';
            if (i == 0)
                continue;
            int id = atoi(idbuf);
            if (id > maxID)
                maxID = id;
        }
    }
    fclose(f);
    return maxID;
}

int emailDuplicado(const char *email)
{
    if (!email)
        return 0;
    if (!arquivoExiste(ARQ_SISTEMA))
        return 0;
    char *sec = read_section_content("USUARIOS");
    if (!sec)
        return 0;
    char *p = sec;
    if (strncmp(p, "ID;", 3) == 0)
    {
        char *nl = strchr(p, '\n');
        if (nl)
            p = nl + 1;
    }
    char linebuf[MAX_LINE];
    while (p && *p)
    {
        char *nl = strchr(p, '\n');
        size_t len = nl ? (size_t)(nl - p) : strlen(p);
        if (len >= sizeof(linebuf))
            len = sizeof(linebuf) - 1;
        strncpy(linebuf, p, len);
        linebuf[len] = '\0';
        UsuarioCSV u;
        if (parseLinhaUsuario(linebuf, &u))
        {
            if (STRCASECMP(u.email, email) == 0)
            {
                free(sec);
                return 1;
            }
        }
        p = nl ? nl + 1 : NULL;
    }
    free(sec);
    return 0;
}

int adicionarUsuarioUnicoValidado(const UsuarioCSV *u_in)
{
    if (!u_in)
        return 0;
    if (strlen(u_in->nome) == 0 || strlen(u_in->email) == 0 || strlen(u_in->senha) == 0 || strlen(u_in->nivel) == 0)
    {
        printf("Campos obrigatorios vazios.\n");
        return 0;
    }
    if (!validarEmail(u_in->email))
    {
        printf("Email invalido.\n");
        return 0;
    }
    if (emailDuplicado(u_in->email))
    {
        printf("Email ja cadastrado.\n");
        return 0;
    }

    int novoID = obterUltimoIDUsuariosUnico() + 1;
    char linha[1024];

    // Valor fixo do Curso
    const char *cursoFixo = "ANALISE E DESENVOLVIMENTO DE SISTEMA";

    // 🌟 1. CORREÇÃO SNPRINTF: AGORA COM 14 CAMPOS 🌟
    // O formato da string agora tem 14 campos: ...;Nivel;Curso;Materia;IDsTurmas;NP1;...
    snprintf(linha, sizeof(linha), "%d;%s;%s;%s;%d;%s;%s;%s;%s;%.2f;%.2f;%.2f;%.2f;%s\r\n",
             novoID,
             u_in->nome,
             u_in->email,
             u_in->senha,
             u_in->idade,
             u_in->nivel,
             u_in->curso,         // 7º Campo: CURSO (u_in->curso)
             u_in->listaMaterias, // 8º Campo: MATERIA (u_in->listaMaterias)
             u_in->idsTurmas,     // 🌟 9º Campo: IDSTURMAS (u_in->idsTurmas) 🌟
             u_in->np1, u_in->np2, u_in->pim, u_in->media,
             (u_in->atividade && u_in->atividade[0]) ? u_in->atividade : "Ativo");

    // O restante do código de I/O do arquivo permanece o mesmo

    char *sec_content = read_section_content("USUARIOS");
    if (!sec_content)
        sec_content = strdup("");

    // 🌟 2. CORREÇÃO HEADER: ADICIONANDO IDS TURMAS 🌟
    const char *header = "ID;Nome;Email;Senha;Idade;Nivel;Curso;Materia;IDsTurmas;NP1;NP2;PIM;Media;Atividade\r\n";

    size_t newcap = strlen(header) + strlen(sec_content) + strlen(linha) + 16;
    char *new_section = malloc(newcap);
    if (!new_section)
    {
        free(sec_content);
        return 0;
    }
    new_section[0] = '\0';
    strcat(new_section, header);
    char *pcontent = sec_content;
    if (strncmp(pcontent, "ID;", 3) == 0)
    {
        char *nl = strchr(pcontent, '\n');
        if (nl)
            pcontent = nl + 1;
    }
    // append existing content (normalize endings) then new line
    strcat(new_section, pcontent);
    strcat(new_section, linha);

    backupSistema();
    int ok = write_section_content("USUARIOS", new_section);
    free(sec_content);
    free(new_section);

    if (ok)
    {
        printf("Usuario adicionado com ID %d\n", novoID);
        return 1;
    }
    printf("Erro ao adicionar usuario.\n");
    return 0;
}

int alterarUsuarioPorIDUnicoValidated(int idBusca, const UsuarioCSV *novo)
{
    if (!arquivoExiste(ARQ_SISTEMA) || !novo)
        return 0;
    char *body = read_section_content("USUARIOS");
    if (!body)
        return 0;
    size_t len = strlen(body);
    char *outBody = malloc(len + 1024);
    if (!outBody)
    {
        free(body);
        return 0;
    }
    outBody[0] = '\0';

    char *p = body;
    char line[MAX_LINE];
    int replaced = 0;
    while (p && *p)
    {
        char *nl = strchr(p, '\n');
        size_t l = nl ? (size_t)(nl - p) : strlen(p);
        if (l >= sizeof(line))
            l = sizeof(line) - 1;
        strncpy(line, p, l);
        line[l] = '\0';
        if (l > 0 && line[l - 1] == '\r')
            line[l - 1] = 0;
        if (line[0] == '\0')
        {
            p = nl ? nl + 1 : NULL;
            continue;
        }
        if (strncmp(line, "ID;", 3) == 0)
        {
            strcat(outBody, line);
            strcat(outBody, "\r\n");
        }
        else
        {
            char copy[MAX_LINE];
            strncpy(copy, line, sizeof(copy) - 1);
            copy[sizeof(copy) - 1] = 0;

            // 🚨 CORREÇÃO 1: Removendo a declaração de char *saveptr = NULL; (Apenas 'char *tk = strtok(copy, ";")' permanece)
            char *tk = strtok(copy, ";");

            int id = tk ? atoi(tk) : -1;

            if (id == idBusca)
            {
                char novoLine[1024];

                // 🚨 CORREÇÃO 2: Atualizando o snprintf para 14 campos (adicionando %s para idsTurmas)
                snprintf(novoLine, sizeof(novoLine), "%d;%s;%s;%s;%d;%s;%s;%s;%s;%.2f;%.2f;%.2f;%.2f;%s",
                         novo->id,
                         novo->nome,
                         novo->email,
                         novo->senha,
                         novo->idade,
                         novo->nivel,
                         novo->curso,         // 7º Campo
                         novo->listaMaterias, // 8º Campo
                         novo->idsTurmas,     // 🌟 9º Campo: NOVO IDSTURMAS 🌟
                         novo->np1, novo->np2, novo->pim, novo->media,
                         novo->atividade[0] ? novo->atividade : "Ativo");

                strcat(outBody, novoLine);
                strcat(outBody, "\r\n");
                replaced = 1;
            }
            else
            {
                strcat(outBody, line);
                strcat(outBody, "\r\n");
            }
        }
        p = nl ? nl + 1 : NULL;
    }

    backupSistema();
    int ok = write_section_content("USUARIOS", outBody);
    free(body);
    free(outBody);
    if (ok && replaced)
    {
        printf("Usuário ID %d alterado com sucesso.\n", idBusca);
    }
    else if (!replaced)
    {
        printf("Usuário ID %d não encontrado.\n", idBusca);
    }
    else
    {
        printf("Erro ao salvar alterações.\n");
    }
    return ok && replaced;
}

int excluirUsuarioPorIDUnico(int idBusca)

{
    if (!arquivoExiste(ARQ_SISTEMA))
        return 0;
    char *body = read_section_content("USUARIOS");
    if (!body)
        return 0;
    size_t len = strlen(body);
    char *outBody = malloc(len + 1);
    if (!outBody)
    {
        free(body);
        return 0;
    }
    outBody[0] = '\0';
    char *p = body;
    char line[MAX_LINE];
    int removed = 0;
    while (p && *p)
    {
        char *nl = strchr(p, '\n');
        size_t l = nl ? (size_t)(nl - p) : strlen(p);
        if (l >= sizeof(line))
            l = sizeof(line) - 1;
        strncpy(line, p, l);
        line[l] = '\0';
        if (l > 0 && line[l - 1] == '\r')
            line[l - 1] = 0;
        if (line[0] == '\0')
        {
            p = nl ? nl + 1 : NULL;
            continue;
        }
        if (strncmp(line, "ID;", 3) == 0)
        {
            strcat(outBody, line);
            strcat(outBody, "\r\n");
        }
        else
        {
            char copy[MAX_LINE];
            strncpy(copy, line, sizeof(copy) - 1);
            copy[sizeof(copy) - 1] = 0;
            char *saveptr = NULL;
            char *tk = strtok(copy, ";");
            int id = tk ? atoi(tk) : -1;
            if (id == idBusca)
            {
                removed = 1;
            }
            else
            {
                strcat(outBody, line);
                strcat(outBody, "\r\n");
            }
        }
        p = nl ? nl + 1 : NULL;
    }

    backupSistema();
    int ok = write_section_content("USUARIOS", outBody);
    free(body);
    free(outBody);
    if (ok && removed)
    {
        printf("Usu�rio ID %d exclu�do com sucesso.\n", idBusca);
    }
    else if (!removed)
    {
        printf("Usu�rio ID %d n�o encontrado.\n", idBusca);
    }
    else
    {
        printf("Erro ao salvar altera��es.\n");
    }
    return ok && removed;
}

/* ----------------- TURMAS ----------------- */

void listarTurmasUnico(void)
{
    if (!arquivoExiste(ARQ_SISTEMA))
    {
        printf("Arquivo do sistema nao encontrado.\n");
        return;
    }
    char *sec = read_section_content("TURMAS");
    if (!sec)
    {
        printf("Nenhuma turma.\n");
        return;
    }
    printf("\n=== TURMAS ===\n%s\n", sec);
    free(sec);
}

int adicionarTurmaUnico(const char *nome, const char *curso, int idProf, const char *idsAlunos)

{
    if (!nome || !curso)
        return 0;
    if (strlen(nome) == 0 || strlen(curso) == 0)
    {
        printf("Nome e curso s�o obrigat�rios.\n");
        return 0;
    }
    char *body = read_section_content("TURMAS");
    if (!body)
        body = strdup("");
    int maior = 0;
    char *tmp = strdup(body);
    char *ln = strtok(tmp, "\n");
    while (ln)
    {
        if (strncmp(ln, "ID;", 3) == 0)
        {
            ln = strtok(NULL, "\n");
            continue;
        }
        char cpy[MAX_LINE];
        strncpy(cpy, ln, sizeof(cpy) - 1);
        cpy[sizeof(cpy) - 1] = 0;
        char *saveptr = NULL;
        char *tk = strtok(cpy, ";");
        if (tk)
        {
            int id = atoi(tk);
            if (id > maior)
                maior = id;
        }
        ln = strtok(NULL, "\n");
    }
    free(tmp);
    int novoID = maior + 1;
    char novaLinha[1024];
    snprintf(novaLinha, sizeof(novaLinha), "%d;%s;%s;%d;%s\n", novoID, nome, curso, idProf, idsAlunos ? idsAlunos : "");
    const char *header = "ID;Nome;Curso;IDProfessor;IDsAlunos\n";
    size_t outcap = strlen(header) + strlen(body) + strlen(novaLinha) + 8;
    char *out = malloc(outcap);
    out[0] = '\0';
    strcat(out, header);
    if (strlen(body) > 0)
    {
        strcat(out, body);
        if (body[strlen(body) - 1] != '\n')
            strcat(out, "\n");
    }
    strcat(out, novaLinha);
    backupSistema();
    int ok = write_section_content("TURMAS", out);
    free(body);
    free(out);
    return ok;
}

/* ----------------- NOTAS ----------------- */

void listarNotasUnico(void)
{
    if (!arquivoExiste(ARQ_SISTEMA))
    {
        printf("Arquivo nao encontrado.\n");
        return;
    }
    char *sec = read_section_content("NOTAS");
    if (!sec)
    {
        printf("Nenhuma nota.\n");
        return;
    }
    printf("\n=== NOTAS ===\n%s\n", sec);
    free(sec);
}

int adicionarNotaUnico(int idAluno, const char *curso, const char *materia, float np1, float np2, float pim)
{
    if (!curso || !materia)
        return 0;
    if (strlen(curso) == 0 || strlen(materia) == 0)
    {
        printf("Curso e mat�ria s�o obrigat�rios.\n");
        return 0;
    }
    char *body = read_section_content("NOTAS");
    if (!body)
        body = strdup("");
    float media = (np1 + np2 + pim) / 3.0f;
    char novaLinha[512];
    snprintf(novaLinha, sizeof(novaLinha), "%d;%s;%s;%.2f;%.2f;%.2f;%.2f\n", idAluno, curso, materia, np1, np2, pim, media);
    const char *header = "IDAluno;Curso;Materia;NP1;NP2;PIM;Media\n";
    size_t outcap = strlen(header) + strlen(body) + strlen(novaLinha) + 8;
    char *out = malloc(outcap);
    out[0] = '\0';
    strcat(out, header);
    if (strlen(body) > 0)
    {
        strcat(out, body);
        if (body[strlen(body) - 1] != '\n')
            strcat(out, "\n");
    }
    strcat(out, novaLinha);
    backupSistema();
    int ok = write_section_content("NOTAS", out);
    free(body);
    free(out);
    return ok;
}

/* ----------------- CRIA��O DO ARQUIVO INICIAL (LIMPO) ----------------- */

void criarArquivoSistemaSeNaoExiste(void)
{
    if (arquivoExiste(ARQ_SISTEMA))
        return;
    FILE *f = fopen(ARQ_SISTEMA, "wb");
    if (!f)
    {
        printf("Erro ao criar arquivo do sistema!\n");
        return;
    }

    // 🚨 CORREÇÃO PARA 14 COLUNAS: Adicionando 'IDsTurmas' no cabeçalho e na linha de dados 🚨
    fprintf(f,
            "[USUARIOS]\r\n"
            "ID;Nome;Email;Senha;Idade;Nivel;Curso;Materia;IDsTurmas;NP1;NP2;PIM;Media;Atividade\r\n"                    // 14 Colunas aqui
            "1;Administrador do Sistema;admin@admin.com;admin;30;Administrador;Sistema;Sistema;;0;0;0;0;Ativo\r\n\r\n"); // IDsTurmas é deixado vazio (;;)

    fclose(f);
    printf("Arquivo de sistema criado com usuário padrão (ADMIN) e a seção [USUARIOS] completa.\n");
}

/* ----------------- MENU DE ADMINISTRACAO ----------------- */
/* Mant�m a vers�o nova do menu (melhoria), estendendo com Turmas/Notas. */

void gerenciarUsuariosUnico(void); // forward (implemente no .c principal ou aqui se quiser UI)
// void gerenciarTurmasUnico(void);   // forward
void gerenciarNotasUnico(void); // forward

/* ----------------- LOGIN ----------------- */

int loginUnico(UsuarioCSV *logado)
{
    char email[256], senha[128];
    printf("Email: ");
    fflush(stdout);
    if (!fgets(email, sizeof(email), stdin))
        return 0;
    email[strcspn(email, "\r\n")] = '\0';
    trim(email);
    while (strlen(email) == 0)
    {
        printf("Email inv�lido, digite novamente: ");
        fflush(stdout);
        if (!fgets(email, sizeof(email), stdin))
            return 0;
        email[strcspn(email, "\r\n")] = '\0';
        trim(email);
    }

    printf("Senha: ");
    fflush(stdout);
    lerSenhaOculta(senha, sizeof(senha));
    senha[strcspn(senha, "\r\n")] = '\0';
    trim(senha);

    if (strlen(email) == 0 || strlen(senha) == 0)
    {
        printf("Campos obrigat�rios vazios.\n");
        return 0;
    }
    if (!validarEmail(email))
    {
        printf("Email inv�lido.\n");
        return 0;
    }

    UsuarioCSV u;
    if (verificarLoginUnico(email, senha, &u))
    {
        if (logado)
            *logado = u;
        printf("Login bem-sucedido! Bem-vindo, %s.\n", u.nome);
        return 1;
    }
    else
    {
        printf("Email ou senha incorretos, ou usu�rio inativo.\n");
        return 0;
    }
}

/* ----------------- CONSULTAS UTILES ----------------- */

void listarTodosUsuarios(void)
{
    char *sec = read_section_content("USUARIOS");
    if (!sec)
    {
        printf("Nenhum usuário cadastrado.\n");
        return;
    }
    printf("\n==================================== LISTAGEM DE USUÁRIOS ====================================\n");
    // Adicionar colunas para Curso e Matérias
    printf("%-5s | %-20s | %-20s | %-12s | %-15s | %-20s | %-6s\n", "ID", "Nome", "Email", "Nível", "Curso", "Matérias/Matéria", "Ativ.");
    printf("----------------------------------------------------------------------------------------------------------------------------------\n");
    char *p = sec;
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
        if (parseLinhaUsuario(line, &u))
        {
            // 🌟 NOVO PRINTF COM NOVOS CAMPOS 🌟
            printf("%-5d | %-20.20s | %-20.20s | %-12.12s | %-15.15s | %-20.20s | %-6.6s\n",
                   u.id, u.nome, u.email, u.nivel, u.curso, u.listaMaterias, u.atividade);
        }
        p = nl ? nl + 1 : NULL;
    }
    free(sec);
}

/* ----------------- FIM ----------------- */

#endif // SISTEMA_ACADEMICO_UNIFICADO_H
