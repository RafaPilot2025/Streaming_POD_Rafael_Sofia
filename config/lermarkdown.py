# config/lermarkdown.py
# Importa as bibliotecas possíveis e/ou necessárias
from pathlib import Path
from datetime import datetime
import sys
import os
import math

# Adiciona o diretório raiz do projeto ao sys.path para importar os módulos
root = str(Path(__file__).resolve().parent.parent)
if root not in sys.path:
    sys.path.insert(0, root)

from Streaming.usuarios import Usuario
from Streaming.arquivo_midia import Musica, Podcast
from Streaming.playlist import Playlist

class LerMarkdown:
    """
    Faz a leitura e instancia de objetos a partir de arquivos .md 
    no formato passado no arquivo markdown de exemplo.    
    - Resolve referências (playlists -> mídias e usuário)
    - Loga avisos/erros em logs/erros.log
    """

    def __init__(self, strict: bool = False):
        self.strict = strict
        self._reset_state()

        # caminhos (relativos ao projeto)
        self._here = Path(__file__).resolve()              # .../config/lermarkdown.py
        self._project_root = self._here.parents[1]         # (seu-projeto)/
        self._logs_dir = self._project_root / "logs"
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._logs_dir / "erros.log"

    # ------------------- API pública -------------------
    def from_file(self, md_filename: str):
        """Lê um arquivo .md dentro de config/ e retorna dicionário com objetos e logs."""
        path_md = (self._here.parent / md_filename).resolve()
        if not path_md.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path_md}")
        text = path_md.read_text(encoding="utf-8")
        return self.parse(text, source=str(path_md))

    def parse(self, text: str, source: str = "<string>"):
        """Faz parsing do texto .md e instancia objetos."""
        self._reset_state()
        section = None
        buf = []
        current = None

        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].rstrip("\n")

            # Header de seção "# ..."
            if line.strip().startswith("# "):
                self._flush_section(section, buf)
                buf = []
                section = line.strip()[2:].strip().lower()
                i += 1
                continue

            # Separador visual '---' é ignorado
            if line.strip().startswith("---"):
                i += 1
                continue

            # Início de item "- chave: valor"
            if line.strip().startswith("- "):
                if current is not None:
                    buf.append(current)
                current = {}
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
        self._flush_section(section, buf)

        # Resolver vínculos (depois de todas as seções)
        self._resolve_links()

        # Gravar logs
        self._flush_logs_to_file(source)

        return {
            "usuarios": list(self._usuarios_by_nome.values()),
            "musicas": [m for m in self._midias_by_titulo.values() if isinstance(m, Musica)],
            "podcasts": [p for p in self._midias_by_titulo.values() if isinstance(p, Podcast)],
            "playlists": self._playlists,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    # ------------------- Parsing helpers -------------------
    def _reset_state(self):
        self.warnings = []
        self.errors = []
        self._usuarios_by_nome = {}
        self._midias_by_titulo = {}
        self._playlists = []

    def _is_indented(self, line: str) -> bool:
        if not line.strip():
            return False
        return line.startswith("    ") or line.startswith("\t")

    def _parse_key_value(self, line: str):
        # "chave: valor" ou "itens: [A, B, C]"
        if ":" not in line:
            return None, None
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        # lista entre colchetes (assumindo que itens não têm vírgula no título)
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return key, []
            return key, [s.strip() for s in inner.split(",")]

        return key, value

    def _flush_section(self, section, records):
        if not section or not records:
            return
        s = section.lower()
        if "usuário" in s or "usuarios" in s or "usuários" in s:
            self._load_usuarios(records)
        elif "música" in s or "musicas" in s or "músicas" in s:
            self._load_musicas(records)
        elif "podcast" in s or "podcasts" in s:
            self._load_podcasts(records)
        elif "playlist" in s or "playlists" in s:
            self._load_playlists(records)
        else:
            self._log_warn(f"Seção desconhecida ignorada: {section!r}")

    # ------------------- Carregadores de seção -------------------
    def _load_usuarios(self, records):
        for r in records:
            nome = (r.get("nome") or "").strip()
            if not nome:
                self._log_err("Usuário sem nome; registro ignorado.", r)
                continue
            if nome in self._usuarios_by_nome:
                self._log_warn(f"Usuário duplicado '{nome}'. Mantendo o primeiro e ignorando o duplicado.")
                continue
            u = self._make_usuario(nome)
            # playl. listadas no md serão associadas na _resolve_links
            self._usuarios_by_nome[nome] = u

    def _load_musicas(self, records):
        for r in records:
            titulo  = (r.get("titulo")  or "").strip()
            artista = (r.get("artista") or "").strip()
            genero  = (r.get("genero")  or "").strip()
            dur_raw = (r.get("duracao") or "").strip()

            if not titulo:
                self._log_err("Música sem título; ignorada.", r)
                continue
            if titulo in self._midias_by_titulo:
                self._log_warn(f"Mídia (título) duplicada '{titulo}'. Mantendo a primeira.")
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
            self._midias_by_titulo[titulo] = m

    def _load_podcasts(self, records):
        for r in records:
            titulo     = (r.get("titulo")     or "").strip()
            temporada  = (r.get("temporada")  or "").strip()
            ep_raw     = (r.get("episodio")   or "").strip()
            host       = (r.get("host")       or "").strip()
            dur_raw    = (r.get("duracao")    or "").strip()

            if not titulo:
                self._log_err("Podcast sem título; ignorado.", r)
                continue
            if titulo in self._midias_by_titulo:
                self._log_warn(f"Mídia (título) duplicada '{titulo}'. Mantendo a primeira.")
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
            self._midias_by_titulo[titulo] = p

    def _load_playlists(self, records):
        for r in records:
            nome    = (r.get("nome") or "").strip()
            dono    = (r.get("dono") or "").strip()
            itens   = [ (x or "").strip() for x in (r.get("itens") or []) ]

            if not nome:
                self._log_err("Playlist sem nome; ignorada.", r)
                continue

            # Verifica os itens únicos e os itens duplicados dentro da mesma playlist
            seen, dups, itens_unicos = set(), [], []
            for t in itens:
                if t in seen:
                    dups.append(t)
                else:
                    seen.add(t)
                    itens_unicos.append(t)
            if dups:
                self._log_warn(f"Playlist '{nome}' tem itens repetidos: {dups}. Mantendo uma ocorrência de cada.")

            # Instancia playlist (dono agora é string)
            print (itens_unicos)            
            pl = self._make_playlist(nome, dono, itens_unicos)
            self._playlists.append(pl)

    # ------------------- Resolvedor de vínculos -------------------
    def _resolve_links(self):
        # Vincular playlists ao usuário e aos itens (músicas/podcasts)
        for pl in self._playlists:
            # 1) usuário
            uname = self._get_playlist_owner_name(pl)
            if not uname:
                self._log_warn(f"Playlist '{self._get_playlist_name(pl)}' sem usuário definido no objeto; tentando o nome do MD se disponível.")
            if uname and uname not in self._usuarios_by_nome:
                self._log_warn(f"Playlist '{self._get_playlist_name(pl)}' referencia usuário inexistente '{uname}'.")
                owner = None
            else:
                owner = self._usuarios_by_nome.get(uname)
                if owner:
                    self._attach_playlist_to_user(owner, pl)

            # 2) itens (por título)
            titles = self._get_playlist_titles(pl)
            resolved, missing = [], []
            for t in titles:
                obj = self._midias_by_titulo.get(t)
                if obj is None:
                    missing.append(t)
                else:
                    resolved.append(obj)
            if missing:
                self._log_warn(f"Playlist '{self._get_playlist_name(pl)}' contém itens inexistentes: {missing}. Ignorados.")

            self._set_playlist_items(pl, resolved)

    # ------------------- Criação segura de objetos -------------------
    def _make_usuario(self, nome):
        try:
            return Usuario(nome)
        except TypeError:
            # Caso sua classe exija mais args, tente variações simples aqui
            return Usuario(nome=nome)

    def _make_musica(self, titulo, artista, genero, duracao):
        return Musica(
                titulo=titulo, 
                duracao=duracao, 
                artista=artista, 
                genero=genero)

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

    def _make_playlist(self, nome, dono_nome, itens_titles):
        """
        Assinaturas compatíveis com o novo modelo (dono:str):
        1) Playlist(nome, dono_nome, itens_titles)
        2) Playlist(nome, dono_nome)
        3) Playlist(nome=..., dono=..., itens=...)
        4) Playlist(nome=..., dono=...)
        """
        # 1) posicional com itens
        try:
            return Playlist(nome, dono_nome, itens_titles)
        except TypeError:
            pass
        # 2) posicional sem itens
        try:
            return Playlist(nome, dono_nome)
        except TypeError:
            pass
        # 3) nomeado com itens
        try:
            return Playlist(nome=nome, dono=dono_nome, itens=itens_titles)
        except TypeError:
            # 4) nomeado sem itens
            return Playlist(nome=nome, dono=dono_nome)

    # ------------------- Operações robustas de Playlist/Usuario -------------------
    def _get_playlist_owner_name(self, pl):
        # 1) novo campo: dono (sempre string no seu modelo)
        d = getattr(pl, "dono", None)
        if isinstance(d, str) and d.strip():
            return d.strip()

        # # 2) compat legada (se por acaso alguma instância antiga ainda tiver 'usuario')
        # u = getattr(pl, "usuario", None)
        # if isinstance(u, str) and u.strip():
        #     return u.strip()
        # if u is not None and hasattr(u, "nome"):
        #     return getattr(u, "nome")

        return None

    def _get_playlist_name(self, pl):
        return (getattr(pl, "nome", None) or "").strip() or str(pl)

    def _get_playlist_titles(self, pl):
        """Retorna a lista de títulos que veio do MD (antes da resolução) 
        ou, se não houver, os nomes das mídias já anexadas."""
        # se a classe guardou temporariamente títulos em atributo auxiliar:
        titles = getattr(pl, "_titulos_md", None)
        if isinstance(titles, list):
            return titles

        # se já há objetos na playlist, retorna seus títulos (melhor esforço)
        itens = getattr(pl, "itens", None) or getattr(pl, "midias", None) or []
        titles = []
        for obj in itens:
            t = getattr(obj, "titulo", None)
            if t:
                titles.append(t)
        return titles

    def _set_playlist_items(self, pl, objetos):
        """
        Define os itens resolvidos na playlist tentando:
        - método adicionar_item / add_item por elemento
        - método adicionar_itens / set_itens em lote
        - atributo lista 'itens' / 'midias'
        Além disso, guarda títulos originais do MD em pl._titulos_md (para depuração).
        """
        # preserva títulos originais para debug
        orig = getattr(pl, "_titulos_md", None)
        if orig is None:
            # melhor esforço de descobrir títulos originais
            setattr(pl, "_titulos_md", [getattr(o, "titulo", "") for o in objetos])

        # métodos de adição unitária
        if hasattr(pl, "adicionar_item"):
            for o in objetos:
                try:
                    pl.adicionar_item(o)
                except Exception:
                    pass
            return

        if hasattr(pl, "add_item"):
            for o in objetos:
                try:
                    pl.add_item(o)
                except Exception:
                    pass
            return

        # métodos/lotes
        for mname in ("adicionar_itens", "set_itens", "set_midias"):
            if hasattr(pl, mname):
                try:
                    getattr(pl, mname)(objetos)
                    return
                except Exception:
                    pass

        # atributos mutáveis
        for aname in ("itens", "midias"):
            if hasattr(pl, aname):
                try:
                    setattr(pl, aname, list(objetos))
                    return
                except Exception:
                    pass

        # se nada funcionou, tente __dict__ direto
        try:
            pl.__dict__["itens"] = list(objetos)
        except Exception:
            self._log_warn(f"Não foi possível anexar itens na playlist '{self._get_playlist_name(pl)}' (adicione um método add/adicionar_itens na sua classe).")

    def _attach_playlist_to_user(self, user_obj, playlist_obj):
        """Acopla a playlist ao usuário, tentando os métodos/atributos mais comuns."""
        # método
        for mname in ("adicionar_playlist", "add_playlist", "registrar_playlist"):
            if hasattr(user_obj, mname):
                try:
                    getattr(user_obj, mname)(playlist_obj)
                    return
                except Exception:
                    pass
        # atributo lista
        for aname in ("playlists", "listas", "colecoes"):
            lst = getattr(user_obj, aname, None)
            if isinstance(lst, list):
                if playlist_obj not in lst:
                    lst.append(playlist_obj)
                return

    # ------------------- Utilidades -------------------
    def _to_int(self, value, default=None):
        try:
            return int(str(value).strip())
        except Exception:
            return default

    def _log_warn(self, msg: str):
        self.warnings.append(msg)

    def _log_err(self, msg: str, record=None):
        if record is not None:
            msg = f"{msg} | Registro: {record}"
        self.errors.append(msg)

    def _flush_logs_to_file(self, source: str):
        if not self.warnings and not self.errors:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"[{now}] Fonte: {source}"]
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

# ------------------- Execução direta (opcional p/ teste rápido) -------------------
if __name__ == "__main__":
    leitor = LerMarkdown(strict=False)
    # se nenhum argumento, tenta um dos exemplos na pasta config
    args = sys.argv[1:]
    if not args:
        candidatos = [
            Path(__file__).parent / "Exemplo Entrada - 1.md",
            Path(__file__).parent / "Exemplo Entrada - 2.md",
            Path(__file__).parent / "dados.md",
        ]
        arquivos = [p for p in candidatos if p.exists()]
        if not arquivos:
            print("Informe o caminho do .md (relativo à pasta config). Ex.:")
            print("  python lermarkdown.py 'Exemplo Entrada - 1.md'")
            sys.exit(0)
    else:
        arquivos = [ (Path(__file__).parent / a) for a in args ]

    for arq in arquivos:
        print(f"\n=== Lendo: {arq.name} ===")
        result = leitor.from_file(arq.name)
        print(f"Usuarios:  {len(result['usuarios'])}")
        print(f"Musicas:   {len(result['musicas'])}")
        print(f"Podcasts:  {len(result['podcasts'])}")
        print(f"Playlists: {len(result['playlists'])}")
        if result["warnings"]:
            print("Warnings:")
            for w in result["warnings"]:
                print(" -", w)
        if result["errors"]:
            print("Errors:")
            for e in result["errors"]:
                print(" -", e)
