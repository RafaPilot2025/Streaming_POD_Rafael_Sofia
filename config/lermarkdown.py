# config/lermarkdown.py

# Importa as bibliotecas possíveis e/ou necessárias
from pathlib import Path
from datetime import datetime
import sys
import os
import math

# Adiciona o diretório raiz do projeto (exemplo notebook: "C:\Git_hub\Streaming_POD_Rafael_Sofia")
# ao sys.path para importar os módulos
raiz_sistema = str(Path(__file__).resolve().parent.parent)
if raiz_sistema not in sys.path:
    sys.path.insert(0, raiz_sistema)

# Importa os arquivos .py dentro da pasta Streaming e os seus respectivos métodos
from Streaming.usuarios import Usuario
from Streaming.arquivo_midia import Musica
from Streaming.arquivo_midia import Podcast
from Streaming.playlist import Playlist

class LerMarkdown:
    """
    Faz a leitura e instancia os objetos a partir de arquivos .md 
    no formato passado no arquivo markdown de exemplo.    
    - Resolve referências (playlists -> mídias e usuário)
    - Loga avisos/erros em logs/erros.log
    """

    # Construtor da classe LerMarkdown contendo apenas a sua preparação de endereçamento
    def __init__(self, strict: bool = False):
        self.strict = strict
        # Chama um outro método para inicializar ou criar os atributos dinâmicos
        self._reset_estados()
        # Guarda em atributos os caminhos (endereços) relativos ao projeto
        self._here = Path(__file__).resolve()             # No notebook: "C:\Git_hub\Streaming_POD_Rafael_Sofia\config\lermarkdown.py"
        self._project_root = self._here.parents[1]        # Sobe 2 níveis: "C:\Git_hub\Streaming_POD_Rafael_Sofia"
        self._logs_dir = self._project_root / "logs"      # No notebook: "C:\Git_hub\Streaming_POD_Rafael_Sofia\logs"
        self._logs_dir.mkdir(parents=True, exist_ok=True) # Cria a pasta logs/ se não existir
        self._log_file = self._logs_dir / "erros.log"     # Define o caminho para salvar erros

    # Método que vai inicializar ou limpar os atributos dinâmicos do LerMarkdown
    def _reset_estados(self):
        self.warnings = []
        self.errors = []       
        self._usuario = []
        self._musicas = []
        self._podcast = []        
        self._playlists = []
        # Criação de índices auxiliares para permitir buscas rápidas
        self._usuarios_by_nome = {}
        self._midias_by_titulo = {}
        self._playlist_by_titulo = {}
        
    # A partir do caminho raiz_do_md encontra o arquivo de nome passado, lê e coloca como
    # uma string em text
    def from_file(self, md_filename: str):
        """Lê um arquivo .md dentro de config/ e retorna dicionário com objetos e logs."""
        raiz_do_md = (self._here.parent / md_filename).resolve()
        if not raiz_do_md.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {raiz_do_md}")
        text = raiz_do_md.read_text(encoding="utf-8")
        return self.parse(text, raiz_arquivo_log=str(raiz_do_md))

    # Método que faz a leitura do texto .md e percorre os caracteres do arquivo
    def parse(self, text: str, raiz_arquivo_log: str = "<string>"):
        """Faz a leitura do texto .md 
        Percorre os carcateres do arquivo passado como .md
        Encontra a seção de cada objeto que deve começar com #
        Instancia os objetos colocando primeiro em um temporário
        Faz até encontrar o final da seção que deve começar com ---."""
        
        # Faz reset nos atributos no objeto LerMarkdown
        self._reset_estados()
        secao = None
        buf = []
        current = None
        # Faz reset nos logs
        self.warnings = []

        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].rstrip("\n")

            if line.strip() == "":
                i+=1
                continue
            
            # Encontra o início de cada seção (conjunto de ojetos) que começa com "# ..."
            if line.strip().startswith("# "):

                self._partes_secao(secao, buf)
                buf = []
                secao = line.strip()[2:].strip().lower()
                i += 1
                continue

            # Se encontrar '---', ele decreta o fim da seção
            if line.strip().startswith("---"):
                # Fecha o item em construção, se houver estiver aberto
                if current is not None:
                    buf.append(current)
                    current = None

                # Faz flush da seção atual
                if secao and buf:
                    self._partes_secao(secao, buf)
                buf = []

                # Encerra a seção, até encontrar com outra com '# '
                secao = None

                i += 1
                continue

            # Detecta o início de um item, se encontrar "- chave: valor"
            if line.strip().startswith("- "):
                # Verifica se há um item em construção ainda não feito                
                if current is not None:
                    # Caso exista, coloca ele no buffer
                    buf.append(current)
                
                # Inicia um novo dicionário
                current = {}
                # Faz a criação do dicionário com a chave e o seu valor
                # A chave tem inicio na 3 posição
                k, v = self._parse_key_value(line.strip()[2:])
                if k:
                    current[k] = v
                i += 1
                # consumir linhas indentadas (4 espaços ou tab)
                while i < len(lines) and self._is_indented(lines[i]):
                    kv_line = lines[i].strip()
                    k2, v2 = self._parse_key_value(kv_line)
                    if k2:
                        current[k2] = v2
                    i += 1
                continue

            i += 1

        if current is not None:
            buf.append(current)
        self._partes_secao(secao, buf)

        # Resolver vínculos (depois de todas as seções)
        self._resolve_links()

        # Gravar logs
        self._partes_logs_to_file(raiz_arquivo_log)

        return {
            "usuarios": list(self._usuarios_by_nome.values()),
            "musicas": [m for m in self._midias_by_titulo.values() if isinstance(m, Musica)],
            "podcasts": [p for p in self._midias_by_titulo.values() if isinstance(p, Podcast)],
            "playlists": self._playlists,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    # Métodos auxiliares de parsing
    # Normaliza strings (strip + lower)
    def _norm(self, s: str) -> str:
        return (s or "").strip().lower()
    
    # Verifica se a linha está indentada (4 espaços ou tab)
    def _is_indented(self, line: str) -> bool:
        if not line.strip():
            return False
        return line.startswith("    ") or line.startswith("\t")

    # Método que faz a separação da chave e do valor
    # A chave tem que possuir :
    # Também verifica se é lista ou string
    def _parse_key_value(self, line: str):        
        # A chave tem que possuir :
        # Ou seja, tem que ser "chave: valor" ou "itens: [A, B, C]"
        if ":" not in line:
            # Caso não tenha devolve nulo
            return None, None
        
        # Divide a string line em duas key tudo antes do :; e value o resto
        key, value = line.split(":", 1)

        # Normaliza as duas variáveis
        key = key.strip().lower()
        value = value.strip()

        # Se o value tiver entre colchetes, será uma lista
        if value.startswith("[") and value.endswith("]"):
            # Separa o que está dentro do colchete
            dentro = value[1:-1].strip()
            # Caso não tenha nada dentro, retorna vazio
            if not dentro:
                return key, []
            # Retorna a chave e o que está dentro dos [] em forma de lista
            return key, [s.strip() for s in dentro.split(",")]

        # Caso não haja parenteses o valor será devolvido como repartido
        return key, value

    # Método que identifica a seção e chama o carregador adequado
    # para cada seção (usuários, músicas, podcasts, playlists)
    def _partes_secao(self, secao, records):
        if not secao or not records:
            return
        s = secao.lower()
        if "usuário" in s or "usuarios" in s or "usuários" in s:
            self._load_usuarios(records)
        elif "música" in s or "musicas" in s or "músicas" in s:
            self._load_musicas(records)
        elif "podcast" in s or "podcasts" in s:
            self._load_podcasts(records)
        elif "playlist" in s or "playlists" in s:
            self._load_playlists(records)
        else:
            self._log_warn(f"Seção desconhecida ignorada: {secao!r}")

    # Métodos que fazem o carregamento de cada seção
    # Cada método recebe a lista de registros (dicionários) daquela seção
    # Carrega os usuários
    def _load_usuarios(self, records):
        for r in records:
            nome = (r.get("nome") or "").strip()
            if not nome:
                self._log_err("Usuário sem nome; registro ignorado.", r)
                continue
            if nome in self._usuarios_by_nome:
                self._log_warn(f"Usuário duplicado '{nome}'. Mantendo o primeiro e ignorando o duplicado.")
                continue
            
            # Extrai a lista de playlists do MD, podendo ser string ou lista
            pl_do_md = r.get("playlists") or r.get("playlist") or []
            if isinstance(pl_do_md, str):
                playlists_titles = [t.strip() for t in pl_do_md.split(",") if t.strip()]
            elif isinstance(pl_do_md, list):
                playlists_titles = [(t or "").strip() for t in pl_do_md if (t or "").strip()]
            else:
                playlists_titles = []

            # Detecta duplicatas
            seen, dups, unicos = set(), [], []
            for t in playlists_titles:
                key = self._norm(t)              # normaliza para comparar (strip+lower)
                if key in seen:
                    dups.append(t)               # guarda o texto original que se repetiu
                else:
                    seen.add(key)
                    unicos.append(t)

            # Loga erro se houver duplicatas
            if dups:
                self._log_err(
                    f"Usuário '{nome}' possui playlists duplicadas: {dups}. "
                    f"Mantendo uma ocorrência de cada."
                )

            playlists_titles = unicos

            # Cria o usuário 
            u = self.make_usuario(nome, playlists_titles)
            
            # Indexa o nome para depois comparar
            self._usuarios_by_nome[nome.strip().lower()] = u

    # Carrega as músicas
    def _load_musicas(self, records):
        for r in records:
            # Busca o valor (get) no dicionário criado no parse, com a chave criada em cada item
            # Ou seja, pegue o valor da chave "titulo" desse dicionário”
            # Se a chave não existir, retorna None e não dê erro
            titulo  = (r.get("titulo")  or "").strip()
            titulo_norm = self._norm(titulo)
            artista = (r.get("artista") or "").strip()
            genero  = (r.get("genero")  or "").strip()
            dur_raw = (r.get("duracao") or "").strip()

            if not titulo:
                self._log_err("Música sem título; ignorada.", r)
                continue
            if titulo_norm in self._midias_by_titulo:
                self._log_warn(f"Mídia com título duplicado '{titulo}'. Mantendo a primeira.")
                continue

            dur_int = self._to_int(dur_raw, default=None)
            if dur_int is None or dur_int <= 0:
                msg = f"Duração inválida para música '{titulo}': {dur_raw!r}."
                if self.strict:
                    self._log_err(msg + " Registro ignorado.", r)
                    continue
                else:
                    self._log_warn(msg + " Ignorada (strict=False).")
                    continue

            m = self._make_musica(titulo, artista, genero, dur_int)
            self._midias_by_titulo[titulo_norm] = m

    # Carrega os podcasts
    def _load_podcasts(self, records):
        for r in records:
            titulo     = (r.get("titulo")     or "").strip()
            titulo_norm = self._norm(titulo)
            temporada  = (r.get("temporada")  or "").strip()
            ep_raw     = (r.get("episodio")   or "").strip()
            host       = (r.get("host")       or "").strip()
            dur_raw    = (r.get("duracao")    or "").strip()

            if not titulo:
                self._log_err("Podcast sem título; ignorado.", r)
                continue
            if titulo_norm in self._midias_by_titulo:
                self._log_warn(f"Mídia com título duplicado '{titulo}'. Mantendo a primeira.")
                continue

            ep_int = self._to_int(ep_raw, default=None)
            if ep_int is None or ep_int < 0:
                if self.strict:
                    self._log_err(f"Episódio inválido em '{titulo}': {ep_raw!r}.", r)
                    continue
                else:
                    self._log_warn(f"Episódio inválido em '{titulo}': {ep_raw!r}. Usando 0.")
                    ep_int = 0

            dur_int = self._to_int(dur_raw, default=None)
            if dur_int is None or dur_int <= 0:
                msg = f"Duração inválida para podcast '{titulo}': {dur_raw!r}."
                if self.strict:
                    self._log_err(msg + " Registro ignorado.", r)
                    continue
                else:
                    self._log_warn(msg + " Ignorado (strict=False).")
                    continue

            p = self._make_podcast(titulo, temporada, ep_int, host, dur_int)
            self._midias_by_titulo[titulo_norm] = p

    # Carrega as playlists
    def _load_playlists(self, records):
        for r in records:
            nome  = (r.get("nome") or "").strip()
            dono_mkd = r.get("dono") or r.get("usuario")
            dono  = (dono_mkd or "").strip().lower()
            itens = [ (x or "").strip() for x in (r.get("itens") or []) ]

            # Playlist sem dono NÃO é adicionada
            if not nome:
                self._log_warn(f"Playlist '{nome}' ignorada: sem dono/usuario informado.")
                continue

            # Se o dono não é um usuário conhecido, tb NÃO adiciona            
            usuario_obj = self._usuarios_by_nome.get(dono)
            if not usuario_obj:
                self._log_warn(f"Playlist '{nome}' ignorada: usuário '{dono}' inexistente no banco de dados.")
                continue            
            
            # Verificação das duplicatas na lista
            # Verificação de nomes únicos, preservando ordem
            seen, dups, itens_unicos = set(), [], []
            for t in itens:
                if t in seen:
                    dups.append(t)
                else:
                    seen.add(t)
                    itens_unicos.append(t)
            if dups:
                self._log_warn(
                    f"Playlist '{nome}' tem itens repetidos: {dups}. Mantendo uma ocorrência de cada."
                )

            # Cria a playlist com nome, dono (string) e lista de musicas em string
            pl = self._make_playlist(nome, dono, itens_unicos)

            # Guarda os títulos originais para posterior verificação
            try:
                setattr(pl, "_titulos_md", list(itens_unicos))
            except Exception:
                pass

            self._playlists.append(pl)


    # Resolve vínculos (playlists -> strings e usuários)
    def _resolve_links(self):
        # 1) Resolver itens de cada playlist por título (e checar dono)
        for pl in self._playlists:
            # a) dono (apenas valida/loga; não anexa objetos ao usuário aqui)
            uname = self._get_playlist_owner_name(pl)
            if not uname:
                self._log_warn(
                    f"Playlist '{self._get_playlist_name(pl)}' sem usuário definido no objeto; "
                    f"tentando o nome do MD se disponível."
                )
            elif uname not in self._usuarios_by_nome:
                self._log_warn(
                    f"Playlist '{self._get_playlist_name(pl)}' referencia usuário inexistente '{uname}'."
                )

            # b) itens por título -> objetos de mídia
            titles = self._get_playlist_titles(pl)
            resolved, missing = [], []
            for t in titles:
                obj = self._midias_by_titulo.get(self._norm(t))
                if obj is None:
                    missing.append(t)
                else:
                    resolved.append(obj)

            if missing:
                self._log_warn(
                    f"Playlist '{self._get_playlist_name(pl)}' contém itens inexistentes: {missing}. Ignorados."
                )

            self._set_playlist_items(pl, resolved)

        # 2) Fora do loop de playlists: propagar NOME das playlists para o usuário (strings)
        usuarios_norm = {k.strip().lower(): v for k, v in self._usuarios_by_nome.items()}

        for pl in self._playlists:
            pl_nome = (getattr(pl, "nome", "") or "").strip()
            if not pl_nome:
                continue

            dono = getattr(pl, "usuario", None) or getattr(pl, "dono", None)
            dono_nome = (getattr(dono, "nome", None) if dono and hasattr(dono, "nome") else dono) or ""
            dono_nome = (dono_nome or "").strip()
            if not dono_nome:
                continue

            u = usuarios_norm.get(dono_nome.lower())
            if not u:
                # dono não encontrado; ignora
                continue

            # garante lista e adiciona o NOME da playlist
            lst = getattr(u, "playlists", None)
            if not isinstance(lst, list):
                lst = []
            lst.append(pl_nome)
            u.playlists = lst

            # mantém também a cópia md para conciliação final
            md_titles = getattr(u, "_playlists_md", None) or []
            md_titles.append(pl_nome)
            setattr(u, "_playlists_md", md_titles)

        # 3) Conciliação final: manter apenas STRINGS e sem duplicatas (ordem estável)
        for u in self._usuarios_by_nome.values():
            nomes_a = getattr(u, "playlists", []) or []
            nomes_b = getattr(u, "_playlists_md", []) or []
            merged, seen = [], set()
            for t in list(nomes_a) + list(nomes_b):
                if isinstance(t, str):
                    key = t.strip()
                    if key and key not in seen:
                        merged.append(key)
                        seen.add(key)
            u.playlists = merged


    # Faz as criações dos diversos objetos lidos nos markdown
    # Faz a criação dos usuários lidos
    def make_usuario(self, nome, playlists_titles=None):
        """
        Cria o usuário com nome depois coloca as string de nome no construtor.
        Faz a criação apenas pelo nome para evitar problemas com o consrutor e a existência
        de playlist duplicadas ou mesmo inexistentes
        """
        u = Usuario(nome)
        
        # Retira os espaços (normaliza) da lista de títulos recebida
        titulos = [(t or "").strip() for t in (playlists_titles or []) if (t or "").strip()]

        # Guarda apenas NOMES (strings) no atributo do usuário playlis [nomes:string]
        u.playlists = list(titulos)
        
        # Guarda cópia do MD para futura conciliação
        setattr(u, "_playlists_md", list(titulos))

        return u
        
    # Faz a criação das músicas lidas
    def _make_musica(self, titulo, artista, genero, duracao):
        return Musica(
                titulo=titulo, 
                duracao=duracao, 
                artista=artista, 
                genero=genero)

    # Faz a criação dos podcasts lidos
    def _make_podcast(self, titulo, temporada, episodio, host, duracao):
        """
        Assinatura alinhada ao que vem do Markdown:
        titulo (str), temporada (str), episodio (int), host (str), duracao (int)
        Mapeia para o construtor:
        Podcast(titulo, duracao, artista, episodio, temporada, host)
        Usamos host como 'artista' por falta desse campo no .md.
        """
        return Podcast(
            titulo=titulo,
            duracao=duracao,
            artista=host,       # <- aqui host cumpre o papel de 'artista'
            episodio=episodio,
            temporada=temporada,
            host=host
        )

    # Faz a criação das playlists lidas
    def _make_playlist(self, nome, dono_nome, itens_titles):
        """
        Cria a Playlist com o seguinte formato:
        - dono: criador da playlist como string 
            (validação: se o usuário não existe, coloca como 'Não Informado' e ERRO)
        - itens: lista de nomes das musicas (strings), filtrando só os que existem no catálogo
                (validação: se a música não existente, coloca ERRO e remove)
        """

        # Faz a validação dono (como string em usuário) ---
        dono_val = (dono_nome or "").strip()
        if not dono_val:
            dono_val = "Não Informado"
        elif dono_val not in self._usuarios_by_nome:
            self._log_err(f"Playlist '{nome}' referencia usuário inexistente '{dono_val}'; usando 'Não Informado'.")
            dono_val = "Não Informado"

        # Faz a validação das musicas (string) passadas em lista
        # Se ainda não há catálogo, não arranque tudo à força (evita falso-positivo):
        # mantém os nomes e deixa a limpeza fina para _resolve_links().
        filtrados = []
        if self._midias_by_titulo:
            for t in (itens_titles or []):
                tt = (t or "").strip()                
                if not tt:
                    continue
                # Faz a normalização para buscar no catálogo 
                tt_norm = self._norm(tt)
                if tt_norm in self._midias_by_titulo:
                    filtrados.append(tt)
                else:
                    self._log_err(f"Playlist '{nome}' contém item inexistente '{tt}'; removido.")
        else:
            # catálogo ainda vazio: não validar agora, apenas normalizar
            filtrados = [ (t or "").strip() for t in (itens_titles or []) if (t or "").strip() ]

        # Cria a Playlist passando as strings (dono + lista de musicas)
        try:
            pl = Playlist(nome, dono_val, filtrados)
        except TypeError:
            try:
                pl = Playlist(nome, dono_val)
                # Mantendo só nomes no estado "bruto" (sem objetos)
                setattr(pl, "itens", list(filtrados))
            except TypeError:
                pl = Playlist(nome=nome, dono=dono_val, itens=filtrados)

        return pl


    # Funções auxiliares para resolver vínculos
    # (playlists -> strings e usuários)
    def _get_playlist_owner_name(self, pl):
        """Retorna o nome do dono da playlist como string (ou None)."""
        # modelo atual: campo 'dono' é string
        d = getattr(pl, "dono", None)
        if isinstance(d, str) and d.strip():
            return d.strip()

        # compat. legada: algumas instâncias antigas podem ter 'usuario'
        u = getattr(pl, "usuario", None)
        if isinstance(u, str) and u.strip():
            return u.strip()
        if u is not None and hasattr(u, "nome"):
            nm = getattr(u, "nome", None)
            if isinstance(nm, str) and nm.strip():
                return nm.strip()

        return None

    # Nome da playlist para logs/mensagens
    def _get_playlist_name(self, pl):
        """Nome da playlist para logs/mensagens."""
        return (getattr(pl, "nome", None) or "").strip() or str(pl)

    
    def _get_playlist_titles(self, pl):
        """
        Devolve os títulos 'brutos' que vieram do MD:
        1) se pl._titulos_md existir, usa-o;
        2) senão, se itens/midias tiver strings, retorna as strings;
        3) senão, se tiver objetos (Musica/Podcast), retorna obj.titulo.
        """
        titles = getattr(pl, "_titulos_md", None)
        if isinstance(titles, list):
            return [ (t or "").strip() for t in titles if (t or "").strip() ]

        itens = getattr(pl, "itens", None) or getattr(pl, "midias", None) or []
        out = []
        for obj in itens:
            if isinstance(obj, str):
                tt = (obj or "").strip()
                if tt:
                    out.append(tt)
            else:
                t = getattr(obj, "titulo", None)
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
        return out

    def _set_playlist_items(self, pl, objetos):
        """
        Define a lista de itens RESOLVIDOS (objetos Musica/Podcast) na playlist.
        Tenta métodos/atributos comuns, sem quebrar caso a classe seja diferente.
        """
        # método em lote
        for mname in ("set_itens", "definir_itens", "adicionar_itens", "add_itens"):
            if hasattr(pl, mname):
                try:
                    getattr(pl, mname)(list(objetos))
                    return
                except Exception:
                    pass

        # atributo comum
        for aname in ("itens", "midias"):
            if hasattr(pl, aname):
                try:
                    setattr(pl, aname, list(objetos))
                    return
                except Exception:
                    pass

        # fallback hard, força no __dict__
        try:
            pl.__dict__["itens"] = list(objetos)
        except Exception:
            # não impede o fluxo; apenas registra
            self._log_warn(
                f"Não foi possível anexar itens na playlist '{self._get_playlist_name(pl)}' "
                f"(adicione um método/atributo de itens na sua classe)."
            )

    def _attach_playlist_to_user(self, user_obj, playlist_obj):
        """
        Anexa a playlist ao usuário.
        Helper que adiciona o NOME da playlist (string) na lista do usuário.
        """
        pl_nome = (getattr(playlist_obj, "nome", "") or "").strip()
        if not pl_nome:
            return
        lst = getattr(user_obj, "playlists", None)
        if not isinstance(lst, list):
            lst = []
        lst.append(pl_nome)
        user_obj.playlists = lst

    # Retorna um int ou None
    def _to_int(self, value, default=None):
        try:
            return int(str(value).strip())
        except Exception:
            return default

    # Métodos de log
    # Adiciona mensagens de aviso ou erro nas listas internas
    def _log_warn(self, msg: str):
        self.warnings.append(msg)

    # Adiciona mensagens de erro nas listas internas
    def _log_err(self, msg: str, record=None):
        if record is not None:
            msg = f"{msg} | Registro: {record}"
        self.errors.append(msg)

    # Grava os logs em arquivo
    # Se não houver avisos ou erros, não grava nada
    def _partes_logs_to_file(self, raiz_arquivo_log: str):
        if not self.warnings and not self.errors:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"[{now}] Fonte: {raiz_arquivo_log}"]
        if self.warnings:
            lines.append("WARNINGS:")
            lines.extend(f" - {w}" for w in self.warnings)
        if self.errors:
            lines.append("ERRORS:")
            lines.extend(f" - {e}" for e in self.errors)
        lines.append("")  # quebra de linha final
        existing = self._log_file.exists()
        with self._log_file.open("a", encoding="utf-8") as f:
            if not existing:
                f.write("# Log de erros/avisos do parser Markdown\n\n")
            f.write("\n".join(lines))
