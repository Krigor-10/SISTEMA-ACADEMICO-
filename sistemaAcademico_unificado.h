#ifndef SISTEMA_ACADEMICO_UNIFICADO_H
#define SISTEMA_ACADEMICO_UNIFICADO_H

/*
 * sistemaAcademico_unificado.h
 * VERSÃO FINAL E CORRIGIDA: Funções essenciais sem 'static inline' para resolver
 * erros de linkagem (undefined reference). Apenas módulo USUARIOS ativo.
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
#define DIR_EXPORT "export"
#define TMP_DIR "tmp_import"
#define MAX_LINE 2048

/* ----------------- UTILITÁRIOS ----------------- */

void initSistema(void) {
    setlocale(LC_ALL, "");
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);
    system("chcp 65001 > nul");
#endif
}

void removerBOM(char *linha) {
    if (!linha) return;
    if ((unsigned char)linha[0] == 0xEF &&
        (unsigned char)linha[1] == 0xBB &&
        (unsigned char)linha[2] == 0xBF) {
        memmove(linha, linha + 3, strlen(linha + 3) + 1);
    }
}

void lerSenhaOculta(char *senha, size_t maxLen) {
    if (!senha || maxLen == 0) return;
#ifdef _WIN32
    size_t idx = 0;
    int ch;
    while ((ch = _getch()) != '\r' && ch != '\n' && idx + 1 < maxLen) {
        if (ch == '\b') {
            if (idx > 0) { idx--; printf("\b \b"); }
        } else {
            senha[idx++] = (char)ch;
            printf("*");
        }
    }
    senha[idx] = '\0';
    printf("\n");
#else
    if (fgets(senha, (int)maxLen, stdin)) {
        senha[strcspn(senha, "\n")] = '\0';
    } else senha[0] = '\0';
#endif
}

int arquivoExiste(const char *nome) {
    FILE *f = fopen(nome, "r");
    if (f) { fclose(f); return 1; }
    return 0;
}

void garantirPasta(const char *pasta) {
    if (!arquivoExiste(pasta)) MKDIR(pasta);
}

void now_str(char *dest, size_t n) {
    time_t t = time(NULL);
    struct tm tm;
    struct tm *tm_ptr;

#ifdef _WIN32
    tm_ptr = localtime(&t);
    if (tm_ptr) { tm = *tm_ptr; } else { memset(&tm, 0, sizeof(tm)); }
#else
    localtime_r(&t, &tm);
#endif
    
    strftime(dest, n, "%Y%m%d_%H%M%S", &tm);
}


void trim(char *s) {
    if (!s) return;
    char *p = s;
    while (*p && isspace((unsigned char)*p)) p++;
    if (p != s) memmove(s, p, strlen(p)+1);
    size_t L = strlen(s);
    while (L > 0 && isspace((unsigned char)s[L-1])) s[--L] = '\0';
}

int validarEmail(const char *email) {
    if (!email) return 0;
    const char *at = strchr(email, '@');
    if (!at || at == email) return 0;
    const char *dot = strchr(at+1, '.');
    if (!dot || dot == at+1) return 0;
    if (*(dot+1) == '\0') return 0;
    return 1;
}

/* ----------------- ESTRUTURAS ----------------- */

typedef struct {
    int id;
    char nome[256];
    char email[256];
    char senha[128];
    int idade;
    char nivel[64];
    char cursoMateria[256];
    float np1, np2, pim, media;
    char atividade[32];
} UsuarioCSV;

/* ----------------- BACKUP ----------------- */

int backupSistema(void) {
    garantirPasta(DIR_BACKUPS);
    char stamp[64]; now_str(stamp, sizeof(stamp));
    char dest[512];
    snprintf(dest, sizeof(dest), "%s%ssistemaAcademico_backup_%s.csv", DIR_BACKUPS, PATH_SEP, stamp);

    FILE *fs = fopen(ARQ_SISTEMA, "rb");
    if (!fs) return 0;
    FILE *fd = fopen(dest, "wb");
    if (!fd) { fclose(fs); return 0; }

    char buf[4096]; size_t r;
    while ((r = fread(buf,1,sizeof(buf),fs))>0) fwrite(buf,1,r,fd);
    fclose(fs); fclose(fd);
    return 1;
}

/* ----------------- LER/ESCREVER ARQUIVO UNICO (SEÇÕES) ----------------- */

char *readFileAll(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return NULL; }
    fread(buf,1,sz,f);
    buf[sz] = '\0';
    fclose(f);
    return buf;
}

int writeFileAll(const char *path, const char *buf) {
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    fwrite(buf,1,strlen(buf),f);
    fclose(f);
    return 1;
}

char *find_section_start(char *buf, const char *sec) {
    if (!buf || !sec) return NULL;
    char pattern[128]; snprintf(pattern, sizeof(pattern), "[%s]", sec);
    char *p = buf;
    while (*p) {
        char *lb = strchr(p, '[');
        if (!lb) return NULL;
        if (strncmp(lb, pattern, strlen(pattern)) == 0) {
            char *nl = strchr(lb, '\n');
            if (!nl) return nl+1;
            return nl+1;
        }
        p = lb + 1;
    }
    return NULL;
}

char *find_next_section(char *p) {
    if (!p) return NULL;
    while (*p) {
        if (*p == '[') return p;
        p++;
    }
    return NULL;
}

char *read_section_content(const char *sec) {
    if (!arquivoExiste(ARQ_SISTEMA)) return NULL;
    char *buf = readFileAll(ARQ_SISTEMA);
    if (!buf) return NULL;
    char *start = find_section_start(buf, sec);
    if (!start) { free(buf); return NULL; }
    char *next = find_next_section(start);
    size_t len = next ? (size_t)(next - start) : strlen(start);
    char *out = malloc(len + 1);
    if (!out) { free(buf); return NULL; }
    strncpy(out, start, len);
    out[len] = '\0';
    // remove leading CR/LF
    while (*out == '\n' || *out == '\r') memmove(out, out+1, strlen(out));
    free(buf);
    return out;
}

int write_section_content(const char *sec, const char *conteudo) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    char *buf = readFileAll(ARQ_SISTEMA);
    if (!buf) return 0;
    char pattern[128]; snprintf(pattern, sizeof(pattern), "[%s]", sec);
    char *p = buf;
    char *found = NULL;
    while ((p = strstr(p, "[")) != NULL) {
        if (strncmp(p, pattern, strlen(pattern)) == 0) { found = p; break; }
        p++;
    }
    if (!found) { free(buf); return 0; }
    char *afterHeader = strchr(found, '\n');
    if (!afterHeader) { free(buf); return 0; }
    afterHeader++;
    char *next = afterHeader;
    while (*next) { if (*next == '[') break; next++; }
    size_t headlen = (size_t)(afterHeader - buf);
    size_t newcap = strlen(buf) + (conteudo ? strlen(conteudo) : 0) + 1024;
    char *out = malloc(newcap);
    if (!out) { free(buf); return 0; }
    out[0] = '\0';
    strncat(out, buf, headlen);
    if (conteudo && conteudo[0] != '\0') {
        strcat(out, conteudo);
        if (conteudo[strlen(conteudo)-1] != '\n' && conteudo[strlen(conteudo)-1] != '\r') strcat(out, "\n");
    } else {
        strcat(out, "\n");
    }
    if (*next) strcat(out, next);
    int ok = writeFileAll(ARQ_SISTEMA, out);
    free(buf); free(out);
    return 1;
}

/* ----------------- PARSER USUÁRIOS ----------------- */

int parseLinhaUsuario(char *line, UsuarioCSV *u) {
    if (!line || !u) return 0;
    removerBOM(line);
    
    char local_copy[MAX_LINE];
    strncpy(local_copy, line, sizeof(local_copy) - 1);
    local_copy[sizeof(local_copy) - 1] = '\0';
    
    trim(local_copy); 

    if (local_copy[0] == '\0' || strncmp(local_copy, "ID;", 3) == 0) return 0;

    char *tok = strtok(local_copy, ";");
    if (!tok) return 0;
    u->id = atoi(tok);

    tok = strtok(NULL, ";"); if (!tok) return 0; strncpy(u->nome, tok, sizeof(u->nome)-1); u->nome[sizeof(u->nome)-1]='\0';
    tok = strtok(NULL, ";"); if (!tok) return 0; strncpy(u->email, tok, sizeof(u->email)-1); u->email[sizeof(u->email)-1]='\0';
    tok = strtok(NULL, ";"); if (!tok) return 0; strncpy(u->senha, tok, sizeof(u->senha)-1); u->senha[sizeof(u->senha)-1]='\0';
    tok = strtok(NULL, ";"); if (!tok) return 0; u->idade = atoi(tok);
    tok = strtok(NULL, ";"); if (!tok) return 0; strncpy(u->nivel, tok, sizeof(u->nivel)-1); u->nivel[sizeof(u->nivel)-1]='\0';
    tok = strtok(NULL, ";"); if (!tok) return 0; strncpy(u->cursoMateria, tok, sizeof(u->cursoMateria)-1); u->cursoMateria[sizeof(u->cursoMateria)-1]='\0';
    
    // Tentando extrair as notas (NP1, NP2, PIM, Media) e Atividade
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->np1 = atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->np2 = atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->pim = atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "0"; u->media = atof(tok);
    tok = strtok(NULL, ";"); if (!tok) tok = "Ativo"; strncpy(u->atividade, tok, sizeof(u->atividade)-1); u->atividade[sizeof(u->atividade)-1]='\0';

    // remove espaços residuais
    trim(u->nome);
    trim(u->email);
    trim(u->senha);
    trim(u->nivel);
    trim(u->cursoMateria);
    trim(u->atividade);

    return 1;
}

/* ----------------- OPERACOES USUARIOS ----------------- */

int verificarLoginUnico(const char *email, const char *senha, UsuarioCSV *u_out) {
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;

    char linha[1024];
    int inUsuarios = 0;

    char emailTrim[128], senhaTrim[128];
    strcpy(emailTrim, email);
    strcpy(senhaTrim, senha);
    emailTrim[strcspn(emailTrim, "\r\n ")] = 0;
    senhaTrim[strcspn(senhaTrim, "\r\n ")] = 0;

    while (fgets(linha, sizeof(linha), f)) {
        if (strncmp(linha, "[USUARIOS]", 10) == 0) { inUsuarios = 1; continue; }
        if (inUsuarios && linha[0] == '[') break;
        if (!inUsuarios || strncmp(linha, "ID;", 3) == 0) continue;

        linha[strcspn(linha, "\r\n")] = 0;

        char temp_line[MAX_LINE];
        strncpy(temp_line, linha, sizeof(temp_line)-1); temp_line[sizeof(temp_line)-1]='\0';

        UsuarioCSV u;
        memset(&u, 0, sizeof(u));

        if (parseLinhaUsuario(temp_line, &u)) {
            u.email[strcspn(u.email, "\r\n ")] = 0;
            u.senha[strcspn(u.senha, "\r\n ")] = 0;

            if (strcmp(u.email, emailTrim) == 0 && strcmp(u.senha, senhaTrim) == 0) {
                *u_out = u;
                fclose(f);
                return 1;
            }
        }
    }

    fclose(f);
    return 0;
}

int obterUltimoIDUsuariosUnico(void) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    FILE *f = fopen(ARQ_SISTEMA, "r");
    if (!f) return 0;

    char line[MAX_LINE];
    int inUsuarios = 0;
    int maxID = 0;

    while (fgets(line, sizeof(line), f)) {
        removerBOM(line);
        line[strcspn(line, "\r\n")] = '\0';
        trim(line);

        if (line[0] == '\0') continue;

        if (!inUsuarios) {
            if (strncmp(line, "[USUARIOS]", 10) == 0) { inUsuarios = 1; }
            continue;
        } else {
            if (line[0] == '[') break;
            if (strncmp(line, "ID;", 3) == 0) continue;

            const char *p = line;
            while (*p && isspace((unsigned char)*p)) p++;
            if (!isdigit((unsigned char)*p)) continue;

            char idbuf[32] = {0};
            int i = 0;
            while (*p && *p != ';' && i < (int)sizeof(idbuf)-1) { idbuf[i++] = *p++; }
            idbuf[i] = '\0';
            if (i == 0) continue;
            int id = atoi(idbuf);
            if (id > maxID) maxID = id;
        }
    }

    fclose(f);
    return maxID;
}

int emailDuplicado(const char *email) {
    if (!email) return 0;
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    char *sec = read_section_content("USUARIOS");
    if (!sec) return 0;
    
    char *p = sec; 
    char *next_line;
    char line_buffer[MAX_LINE];
    
    if (strncmp(p, "ID;", 3) == 0) { 
        char *nl = strchr(p, '\n'); 
        if (nl) p = nl + 1; 
    }
    
    while (p && *p) {
        next_line = strchr(p, '\n');
        size_t line_len;
        if (next_line) { line_len = (size_t)(next_line - p); } else { line_len = strlen(p); }
        if (line_len >= sizeof(line_buffer)) { line_len = sizeof(line_buffer) - 1; }
        strncpy(line_buffer, p, line_len);
        line_buffer[line_len] = '\0';
        
        UsuarioCSV u;
        if (parseLinhaUsuario(line_buffer, &u)) {
            if (STRCASECMP(u.email, email) == 0) { free(sec); return 1; }
        }
        
        p = next_line ? next_line + 1 : NULL;
    }
    
    free(sec);
    return 0;
}

int adicionarUsuarioUnicoValidado(const UsuarioCSV *u_in) {
    if (!u_in) return 0;

    if (strlen(u_in->nome) == 0 || strlen(u_in->email) == 0 || strlen(u_in->senha) == 0 || strlen(u_in->nivel) == 0) {
        printf("Campos obrigatorios vazios.\n"); return 0;
    }
    if (!validarEmail(u_in->email)) { printf("Email invalido.\n"); return 0; }
    if (emailDuplicado(u_in->email)) { printf("Email ja cadastrado.\n"); return 0; }

    int novoID = obterUltimoIDUsuariosUnico() + 1;

    char linha[1024];
    snprintf(linha, sizeof(linha), "%d;%s;%s;%s;%d;%s;%s;%.2f;%.2f;%.2f;%.2f;%s\r\n",
             novoID,
             u_in->nome,
             u_in->email,
             u_in->senha,
             u_in->idade,
             u_in->nivel,
             u_in->cursoMateria,
             u_in->np1, u_in->np2, u_in->pim, u_in->media,
             (u_in->atividade && u_in->atividade[0]) ? u_in->atividade : "Ativo");

    char *sec_content = read_section_content("USUARIOS");
    if (!sec_content) sec_content = strdup("");
    
    const char *header = "ID;Nome;Email;Senha;Idade;Nivel;Curso;NP1;NP2;PIM;Media;Atividade\r\n";
    size_t new_cap = strlen(header) + strlen(sec_content) + strlen(linha) + 10;
    char *new_section = malloc(new_cap);
    
    if (!new_section) { free(sec_content); return 0; }
    new_section[0] = '\0';
    
    strcat(new_section, header);
    
    char *p_content = sec_content;
    if (strncmp(p_content, "ID;", 3) == 0) {
        char *nl = strchr(p_content, '\n');
        if (nl) p_content = nl + 1;
    }
    strcat(new_section, p_content);
    strcat(new_section, linha);
    
    backupSistema();
    int ok = write_section_content("USUARIOS", new_section);

    free(sec_content);
    free(new_section);
    
    if (ok) {
        printf("Usuario adicionado com ID %d\n", novoID);
        return 1;
    }
    printf("Erro ao adicionar usuario.\n");
    return 0;
}

int alterarUsuarioPorIDUnicoValidated(int idBusca, const UsuarioCSV *novo) {
    if (!arquivoExiste(ARQ_SISTEMA) || !novo) return 0;
    
    char *body = read_section_content("USUARIOS");
    if (!body) return 0;

    size_t len = strlen(body);
    char *outBody = malloc(len + 1024);
    if (!outBody) { free(body); return 0; }
    outBody[0] = '\0';

    int replaced = 0;
    char *p = body;
    char *next_line_ptr;
    char line_buffer[MAX_LINE]; 

    while (p && *p) {
        next_line_ptr = strchr(p, '\n');
        size_t line_len;

        if (next_line_ptr) { line_len = (size_t)(next_line_ptr - p); } else { line_len = strlen(p); }

        if (line_len >= sizeof(line_buffer)) { line_len = sizeof(line_buffer) - 1; }
        strncpy(line_buffer, p, line_len);
        line_buffer[line_len] = '\0';

        if (line_len > 0 && line_buffer[line_len-1] == '\r') { line_buffer[line_len-1] = '\0'; }

        if (line_buffer[0] == '\0') {
            p = next_line_ptr ? next_line_ptr + 1 : NULL;
            continue;
        }

        if (strncmp(line_buffer, "ID;", 3) == 0) {
            strcat(outBody, line_buffer);
            strcat(outBody, "\r\n");
        } else {
            char copia[MAX_LINE]; 
            strncpy(copia, line_buffer, sizeof(copia)-1); copia[sizeof(copia)-1] = '\0';

            char *tk = strtok(copia, ";"); 
            int id = tk ? atoi(tk) : -1;

            if (id == idBusca) {
                char novoLine[1024];
                snprintf(novoLine, sizeof(novoLine), "%d;%s;%s;%s;%d;%s;%s;%.2f;%.2f;%.2f;%.2f;%s",
                         novo->id, novo->nome, novo->email, novo->senha, novo->idade,
                         novo->nivel, novo->cursoMateria, novo->np1, novo->np2, novo->pim, novo->media,
                         novo->atividade[0] ? novo->atividade : "Ativo");
                
                strcat(outBody, novoLine);
                strcat(outBody, "\r\n");
                replaced = 1;
            } else {
                strcat(outBody, line_buffer);
                strcat(outBody, "\r\n");
            }
        }
        
        p = next_line_ptr ? next_line_ptr + 1 : NULL;
    }

    backupSistema();
    int ok = write_section_content("USUARIOS", outBody); 

    free(body); 
    free(outBody); 
    
    if (ok && replaced) {
        printf("Usuário ID %d alterado com sucesso.\n", idBusca);
    } else if (!replaced) {
        printf("Usuário ID %d não encontrado.\n", idBusca);
    } else {
        printf("Erro ao salvar alterações.\n");
    }
    
    return ok && replaced;
}

int excluirUsuarioPorIDUnico(int idBusca) {
    if (!arquivoExiste(ARQ_SISTEMA)) return 0;
    
    char *body = read_section_content("USUARIOS");
    if (!body) return 0;

    size_t len = strlen(body);
    char *outBody = malloc(len + 1); 
    if (!outBody) { free(body); return 0; }
    outBody[0] = '\0';

    int removed = 0;
    char *p = body;
    char *next_line_ptr;
    char line_buffer[MAX_LINE]; 

    while (p && *p) {
        next_line_ptr = strchr(p, '\n');
        size_t line_len;

        if (next_line_ptr) { line_len = (size_t)(next_line_ptr - p); } else { line_len = strlen(p); }

        if (line_len >= sizeof(line_buffer)) { line_len = sizeof(line_buffer) - 1; }
        strncpy(line_buffer, p, line_len);
        line_buffer[line_len] = '\0';

        if (line_len > 0 && line_buffer[line_len-1] == '\r') { line_buffer[line_len-1] = '\0'; }
        
        if (line_buffer[0] == '\0') {
            p = next_line_ptr ? next_line_ptr + 1 : NULL;
            continue;
        }

        if (strncmp(line_buffer, "ID;", 3) == 0) {
            strcat(outBody, line_buffer);
            strcat(outBody, "\r\n");
        } else {
            char copia[MAX_LINE]; 
            strncpy(copia, line_buffer, sizeof(copia)-1); copia[sizeof(copia)-1] = '\0';

            char *tk = strtok(copia, ";"); 
            int id = tk ? atoi(tk) : -1;

            if (id == idBusca) {
                removed = 1;
            } else {
                strcat(outBody, line_buffer);
                strcat(outBody, "\r\n");
            }
        }
        
        p = next_line_ptr ? next_line_ptr + 1 : NULL;
    }

    backupSistema();
    int ok = write_section_content("USUARIOS", outBody);
    
    free(body); 
    free(outBody); 
    
    if (ok && removed) {
        printf("Usuário ID %d excluído com sucesso.\n", idBusca);
    } else if (!removed) {
        printf("Usuário ID %d não encontrado.\n", idBusca);
    } else {
        printf("Erro ao salvar alterações.\n");
    }
    
    return ok && removed;
}

/* ----------------- CRIAÇÃO DO ARQUIVO INICIAL (LIMPO) ----------------- */

void criarArquivoSistemaSeNaoExiste(void) {
    if (arquivoExiste(ARQ_SISTEMA)) return;
    FILE *f = fopen(ARQ_SISTEMA, "wb");
    if (!f) {
        printf("Erro ao criar arquivo do sistema!\n");
        return;
    }

    // Apenas seção USUARIOS
    fprintf(f,
        "[USUARIOS]\r\n"
        "ID;Nome;Email;Senha;Idade;Nivel;Curso;NP1;NP2;PIM;Media;Atividade\r\n"
        "1;Administrador do Sistema;admin@admin.com;admin;30;Administrador;Sistema;0;0;0;0;Ativo\r\n\r\n");
    fclose(f);
    printf("Arquivo de sistema criado com usuário padrão: admin@admin.com / senha: admin\n");
}

/* ----------------- MENU DE ADMINISTRAÇÃO (LIMPO) ----------------- */

void menuAdministradorUnificado(const UsuarioCSV *u) {
    int opc;
    do {
        printf("\n=== MENU ADMINISTRADOR (%s) ===\n", u->nome);
        printf("1 - Ver minhas informacoes\n");
        printf("2 - Gerenciar usuarios\n");
        printf("3 - Criar backup manual\n");
        printf("0 - Sair\n");
        printf("Opcao: ");
        if (scanf("%d",&opc)!=1) { while(getchar()!='\n'); opc=-1; }
        while(getchar()!='\n');
        
        if (opc==1) {
            printf("ID: %d | Nome: %s | Email: %s | Nivel: %s | Curso: %s | Atividade: %s\n",
                     u->id, u->nome, u->email, u->nivel, u->cursoMateria, u->atividade);
        } else if (opc==2) {
            extern void gerenciarUsuariosUnico(void);
            gerenciarUsuariosUnico();
        } else if (opc==3) {
            if (backupSistema()) printf("Backup criado.\n"); else printf("Falha ao criar backup.\n");
        } else if (opc==0) break;
        else printf("Opcao invalida.\n");
    } while (1);
}

/* ----------------- LOGIN ----------------- */

int loginUnico(UsuarioCSV *logado) {
    char email[256], senha[128];
    printf("Email: ");
    fflush(stdout);
    if (!fgets(email, sizeof(email), stdin)) return 0;
    email[strcspn(email, "\r\n")] = '\0';
    trim(email);
    while (strlen(email) == 0) {
        printf("Email inválido, digite novamente: ");
        fflush(stdout);
        if (!fgets(email, sizeof(email), stdin)) return 0;
        email[strcspn(email, "\r\n")] = '\0';
        trim(email);
    }

    printf("Senha: ");
    fflush(stdout);
    lerSenhaOculta(senha, sizeof(senha));
    senha[strcspn(senha, "\r\n")] = '\0';
    trim(senha);

    if (strlen(email) == 0 || strlen(senha) == 0) {
        printf("Campos obrigatórios vazios.\n");
        return 0;
    }
    if (!validarEmail(email)) {
        printf("Email inválido.\n");
        return 0;
    }

    UsuarioCSV u;
    if (verificarLoginUnico(email, senha, &u)) {
        if (logado) *logado = u;
        printf("Login bem-sucedido! Bem-vindo, %s.\n", u.nome);
        return 1;
    } else {
        printf("Email ou senha incorretos, ou usuário inativo.\n");
        return 0;
    }
}

/* ----------------- CONSULTAS (Limpa de Notas/Turmas) ----------------- */

void listarTodosUsuarios(void) {
    char *sec = read_section_content("USUARIOS");
    if (!sec) { printf("Nenhum usuário cadastrado.\n"); return; }
    
    printf("\n============================================ LISTAGEM DE USUÁRIOS ============================================\n");
    printf("%-5s | %-30s | %-30s | %-15s | %-20s | %-10s\n", "ID", "Nome", "Email", "Nível", "Curso/Matéria", "Atividade");
    printf("------+--------------------------------+--------------------------------+-----------------+----------------------+------------\n");
    
    char *p = sec;
    char *next_line;
    char line_buffer[MAX_LINE];

    while (p && *p) {
        next_line = strchr(p, '\n');
        
        size_t line_len;
        if (next_line) { line_len = (size_t)(next_line - p); } else { line_len = strlen(p); }

        if (line_len >= sizeof(line_buffer)) { line_len = sizeof(line_buffer) - 1; }
        strncpy(line_buffer, p, line_len);
        line_buffer[line_len] = '\0';

        if (strncmp(line_buffer, "ID;", 3) != 0 && line_buffer[0] != '\0' && line_buffer[0] != '\r') {
            
            UsuarioCSV u;
            memset(&u, 0, sizeof(u)); 

            if (parseLinhaUsuario(line_buffer, &u)) {
                printf("%-5d | %-30.30s | %-30.30s | %-15.15s | %-20.20s | %-10.10s\n",
                         u.id, u.nome, u.email, u.nivel, u.cursoMateria, u.atividade);
            }
        }
        
        p = next_line ? next_line + 1 : NULL;
    }

    printf("================================================================================================================\n");
    free(sec);
}


/* ----------------- FIM DO HEADER ----------------- */

#endif // SISTEMA_ACADEMICO_UNIFICADO_H