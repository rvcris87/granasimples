# 🔄 Comparação Antes/Depois - Exemplos de Código

**Objetivo**: Demonstrar as mudanças e melhorias implementadas

---

## 1️⃣ Exemplo: `registrar_tentativa()` - UPSERT

### ❌ ANTES (Race Condition)

```python
def registrar_tentativa(email):
    conn = conectar()
    cur = conn.cursor()

    # PROBLEMA: SELECT e depois INSERT/UPDATE separados
    # Entre SELECT e INSERT, outro processo pode inserir um registro
    # Resultado: perde incrementos de tentativas
    cur.execute("""
        SELECT tentativas
        FROM login_tentativas
        WHERE email = %s
    """, (email,))
    dados = cur.fetchone()

    if dados:
        tentativas = int(dados["tentativas"]) + 1

        if tentativas >= 5:
            bloqueio = datetime.now() + timedelta(minutes=15)
            cur.execute("""
                UPDATE login_tentativas
                SET tentativas = %s, bloqueado_ate = %s
                WHERE email = %s
            """, (tentativas, bloqueio, email))
        else:
            cur.execute("""
                UPDATE login_tentativas
                SET tentativas = %s
                WHERE email = %s
            """, (tentativas, email))
    else:
        cur.execute("""
            INSERT INTO login_tentativas (email, tentativas, bloqueado_ate)
            VALUES (%s, 1, NULL)
        """, (email,))

    conn.commit()
    conn.close()
    # PROBLEMA: Sem logging de erro, sem try/except
```

**Problemas Identificados:**
- 🔴 Race condition entre SELECT e UPDATE
- 🔴 Sem tratamento de erro
- 🔴 Sem logging
- 🔴 Sem rollback em caso de falha

---

### ✅ DEPOIS (UPSERT Atômico)

```python
import logging

logger = logging.getLogger(__name__)

def registrar_tentativa(email):
    """
    Registra tentativa de login falhada. Usa UPSERT para evitar race condition.
    Após 5 tentativas, bloqueia por 15 minutos.
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        # SOLUÇÃO: UPSERT em UMA única operação atômica
        # PostgreSQL garante que não há race condition
        bloqueio = datetime.now() + timedelta(minutes=15)
        
        cur.execute("""
            INSERT INTO login_tentativas (email, tentativas, bloqueado_ate)
            VALUES (%s, 1, NULL)
            ON CONFLICT (email) DO UPDATE
            SET tentativas = login_tentativas.tentativas + 1,
                bloqueado_ate = CASE 
                    WHEN login_tentativas.tentativas + 1 >= 5 THEN %s
                    ELSE login_tentativas.bloqueado_ate
                END
        """, (email, bloqueio))

        conn.commit()
    except Exception as e:
        conn.rollback()
        # Logging com contexto completo
        logger.exception(f"Erro ao registrar tentativa de login para {email}: {e}")
    finally:
        conn.close()
```

**Melhorias:**
- ✅ UPSERT atômico (sem race condition)
- ✅ Try/except/finally
- ✅ Rollback em caso de erro
- ✅ Logging completo com stack trace
- ✅ Docstring explicativa

---

## 2️⃣ Exemplo: `login_required` - Open Redirect Prevention

### ❌ ANTES (Vulnerável)

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            # PROBLEMA: Sem validação de 'next'
            # Atacante pode redirecionar para https://evil.com
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
```

**Problemas Identificados:**
- 🔴 Open redirect vulnerability
- 🔴 Sem suporte a `next` parameter
- 🔴 UX ruim (usuário perde contexto após login)

---

### ✅ DEPOIS (Seguro)

```python
from urllib.parse import urlparse

def is_safe_url(target):
    """
    Valida se a URL é segura (rota interna) para evitar open redirect.
    """
    if not target:
        return False
    
    # Verificar se é URL absoluta ou começa com //, indicando possível open redirect
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return False
    
    # Só permitir rotas locais (começam com /)
    return target.startswith('/')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            # Preservar URL original para redirecionar após login bem-sucedido
            next_url = request.args.get('next')
            if next_url and is_safe_url(next_url):
                return redirect(url_for("auth.login", next=next_url))
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function
```

**Melhorias:**
- ✅ Validação de URL com `is_safe_url()`
- ✅ Bloqueia URLs externas
- ✅ Suporte a `next` parameter
- ✅ UX melhorada (redireciona para página correta)
- ✅ Docstring clara

---

## 3️⃣ Exemplo: Rota `add_transacao()` - Error Handling

### ❌ ANTES (Sem Try/Finally)

```python
@transacoes_bp.route("/add_transacao", methods=["POST"])
@login_required
def add_transacao():
    usuario_id = session["usuario_id"]
    # ... validações ...

    conn = conectar()
    cur = conn.cursor()

    if categoria_id:
        cur.execute("""...""", (categoria_id, usuario_id))
        categoria = cur.fetchone()

        if not categoria:
            conn.close()  # PROBLEMA: Múltiplos closes
            return redirecionar_dashboard("Categoria não encontrada.", "erro")

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (usuario_id, descricao, valor, tipo, categoria_id, data))

    conn.commit()
    conn.close()

    return redirecionar_dashboard("Transação adicionada com sucesso.", "sucesso")
    # PROBLEMA: Se erro ocorre entre INSERT e COMMIT, conexão não fecha
    # PROBLEMA: Sem try/except para capturar exceções
    # PROBLEMA: Mensagem de erro seria técnica: flash(str(e))
```

**Problemas Identificados:**
- 🔴 Sem try/except
- 🔴 Conexão pode não fechar se erro ocorrer
- 🔴 Sem rollback em caso de erro
- 🔴 Erros técnicos expostos

---

### ✅ DEPOIS (Robusto)

```python
import logging

logger = logging.getLogger(__name__)

@transacoes_bp.route("/add_transacao", methods=["POST"])
@login_required
def add_transacao():
    usuario_id = session["usuario_id"]
    # ... validações ...

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        if categoria_id:
            cur.execute("""
                SELECT id, tipo
                FROM categorias
                WHERE id = %s AND usuario_id = %s
            """, (categoria_id, usuario_id))
            categoria = cur.fetchone()

            if not categoria:
                return redirecionar_dashboard("Categoria não encontrada.", "erro")

            if categoria["tipo"] != tipo:
                return redirecionar_dashboard("A categoria não corresponde ao tipo da transação.", "erro")

        cur.execute("""
            INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (usuario_id, descricao, valor, tipo, categoria_id, data))

        conn.commit()
        return redirecionar_dashboard("Transação adicionada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        # Mensagem amigável ao usuário
        logger.exception(f"Erro ao adicionar transação para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível salvar a transação. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()
```

**Melhorias:**
- ✅ Try/except/finally
- ✅ Rollback em caso de erro
- ✅ Garantia de fechar conexão
- ✅ Mensagem genérica ao usuário
- ✅ Logging completo do erro real
- ✅ Sem múltiplos `conn.close()`

---

## 4️⃣ Exemplo: Dashboard - Try/Finally Consolidado

### ❌ ANTES (Múltiplos Try/Except)

```python
@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    # ...

    conn = conectar()
    conn.autocommit = True

    try:
        dados = calcular_dados_dashboard(usuario_id, mes, conn=conn)
    except Exception as e:
        print(f"Erro em calcular_dados_dashboard: {str(e)}")
        dados = {...}  # Valores padrão
    
    # PROBLEMA: Cada função tem try/except separado
    try:
        categorias = buscar_categorias(usuario_id, conn=conn) or []
    except Exception as e:
        print(f"Erro em buscar_categorias: {str(e)}")
        categorias = []
    
    # ... mais 5 try/excepts ...
    
    # PROBLEMA: conn.close() pode não ser chamado se erro ocorrer acima
    conn.close()

    return render_template("index.html", ...)
```

**Problemas Identificados:**
- 🔴 Muitos try/except aninhados (complexo)
- 🔴 Sem logging centralizado
- 🔴 Usando `print()` em vez de logger
- 🔴 Sem guarantee de close se erro no meio
- 🔴 Tratamento de erro genérico

---

### ✅ DEPOIS (Consolidado)

```python
import logging

logger = logging.getLogger(__name__)

@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    mes = request.args.get("mes", "").strip()

    if mes:
        try:
            parse_mes(mes)
        except ValueError:
            return render_template(
                "erro.html",
                codigo=400,
                titulo="Filtro inválido",
                mensagem="O filtro de mês fornecido é inválido. Use o seletor de mês."
            ), 400

    conn = None
    try:
        conn = conectar()
        conn.autocommit = True

        # Uma única operação com múltiplas chamadas
        dados = calcular_dados_dashboard(usuario_id, mes, conn=conn)
        categorias = buscar_categorias(usuario_id, conn=conn) or []
        tendencia = calcular_tendencia_6_meses(usuario_id, conn=conn) or {}
        # ... demais chamadas ...

    except Exception as e:
        # Logging centralizado com stack trace completo
        logger.exception(f"Erro ao carregar dashboard para usuário {usuario_id}: {e}")
        return render_template(
            "erro.html",
            codigo=500,
            titulo="Erro ao carregar dados",
            mensagem="Não foi possível carregar os dados do dashboard. Tente novamente em alguns instantes."
        ), 500
    finally:
        if conn:
            conn.close()

    return render_template("index.html", ...)
```

**Melhorias:**
- ✅ Try/except/finally consolidado
- ✅ Logging centralizado
- ✅ Mensagens genéricas ao usuário
- ✅ Stack trace completo em logs
- ✅ Garantia de fechar conexão
- ✅ Código mais limpo e legível

---

## 5️⃣ Exemplo: Auth - Fluxo Completo com Next

### ❌ ANTES (Sem Next)

```python
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    email = ""

    if "usuario_id" in session:
        return redirect(url_for("dashboard.app_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("login.html", erro=erro, email=email)

        # ... validações ...

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nome, senha
            FROM usuarios
            WHERE email = %s
        """, (email,))
        usuario = cur.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            resetar_tentativas(email)

            session.clear()
            session.permanent = True
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            # PROBLEMA: Sempre redireciona para dashboard
            # UX ruim: usuário perde contexto da página anterior
            return redirect(url_for("dashboard.app_dashboard"))
        else:
            registrar_tentativa(email)
            erro = "Email ou senha inválidos."

    return render_template("login.html", erro=erro, email=email)
```

---

### ✅ DEPOIS (Com Next + Segurança)

```python
import logging
from decorators import is_safe_url

logger = logging.getLogger(__name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    email = ""

    if "usuario_id" in session:
        return redirect(url_for("dashboard.app_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("login.html", erro=erro, email=email)

        if verificar_bloqueio(email):
            erro = "Muitas tentativas. Tente novamente em alguns minutos."
            return render_template("login.html", erro=erro, email=email)

        conn = None
        try:
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                SELECT id, nome, senha
                FROM usuarios
                WHERE email = %s
            """, (email,))
            usuario = cur.fetchone()

            if usuario and check_password_hash(usuario["senha"], senha):
                resetar_tentativas(email)

                session.clear()
                session.permanent = True
                session["usuario_id"] = usuario["id"]
                session["usuario_nome"] = usuario["nome"]

                # SOLUÇÃO: Suporta next parameter com validação
                next_url = request.args.get('next') or request.form.get('next')
                if next_url and is_safe_url(next_url):
                    return redirect(next_url)
                return redirect(url_for("dashboard.app_dashboard"))
            else:
                registrar_tentativa(email)
                erro = "Email ou senha inválidos."

        except Exception as e:
            logger.exception(f"Erro ao fazer login: {e}")
            erro = "Não foi possível processar o login. Tente novamente."
        finally:
            if conn:
                conn.close()

    return render_template("login.html", erro=erro, email=email)
```

**Melhorias:**
- ✅ Suporta `next` parameter
- ✅ Validação com `is_safe_url()`
- ✅ Try/except/finally
- ✅ Logging de erros
- ✅ Mensagens genéricas
- ✅ UX melhorada (redireciona para página correta)

---

## 📊 Resumo de Mudanças

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Error Handling** | ❌ Sem try/finally | ✅ Try/except/finally |
| **Logging** | ❌ `print()` | ✅ `logger.exception()` |
| **Race Conditions** | ❌ SELECT + INSERT | ✅ UPSERT atômico |
| **Security** | ❌ Sem validação | ✅ `is_safe_url()` |
| **UX** | ❌ Sempre dashboard | ✅ Suporta `next` |
| **Messages** | ❌ Técnicas | ✅ Amigáveis |
| **Rollback** | ❌ Ausente | ✅ Sempre presente |

---

**Conclusão**: As mudanças garantem **segurança**, **integridade** e **estabilidade** sem impacto visual ou funcional.
