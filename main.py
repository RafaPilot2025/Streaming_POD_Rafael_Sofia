# main.py
from pathlib import Path

# Importações das classes do pacote
from Streaming.menu import Menu
from Streaming.usuarios import Usuario
from Streaming.arquivo_midia import ArquivoDeMidia
from Streaming.arquivo_midia import Musica
from Streaming.arquivo_midia import Podcast
from Streaming.playlist import Playlist
from Streaming.analises import Analises
from config.lermarkdown import LerMarkdown


def importar_markdowns_para_main(app):
    """
    Método anterior ao main para poder ler todos os .md da pasta /config
    usando LerMarkdown e consolida em app. Evita duplicatas.
    """
    # Pega todos os arquivos .md da pasta config
    base_config = Path(__file__).parent / "config"
    arquivos = sorted(base_config.glob("*.md"))
    
    # Se não houver arquivos, avisa e retorna
    if not arquivos:
        print("Nenhum .md encontrado em /config.")
        return

    # índices para deduplicação
    usuarios_por_nome   = {u.nome.strip().lower(): u for u in app.usuarios}
    musicas_por_titulo  = {m.titulo.strip().lower(): m for m in app.musicas}
    podcasts_por_titulo = {p.titulo.strip().lower(): p for p in app.podcasts}
    playlists_chaves    = {((getattr(pl, "nome", "") or "").strip().lower(), 
                            (getattr(pl, "dono", "") or "").strip().lower()) 
                            for pl in app.playlists}


    novos_u = novos_m = novos_p = novos_pl = 0

    # Instancia o leitor como um objeto LerMarkdown
    leitor = LerMarkdown(strict=False)

    # Lê todos os arquivos .md da lista arquivos
    for arq in arquivos:
        print(f"\n=== Lendo: {arq.name} ===")
        try:
            # o LerMarkdown já resolve caminho relativo a /config
            result = leitor.from_file(arq.name)  
        except Exception as e:
            print(f"[ERRO] {arq.name}: {e}")
            continue

        # 1) usuários        
        for u in result.get("usuarios", []):
            k = u.nome.strip().lower()
            if k not in usuarios_por_nome:
                app.usuarios.append(u)
                usuarios_por_nome[k] = u
                novos_u += 1

        # 2) músicas    
        for m in result.get("musicas", []):
            k = m.titulo.strip().lower()
            if k not in musicas_por_titulo:
                app.musicas.append(m)
                musicas_por_titulo[k] = m
                novos_m += 1

        # 3) podcasts
        for p in result.get("podcasts", []):
            k = p.titulo.strip().lower()
            if k not in podcasts_por_titulo:
                app.podcasts.append(p)
                podcasts_por_titulo[k] = p
                novos_p += 1

        # 4) playlists
        for pl in result.get("playlists", []):
            # pegue o dono como string para exibir/armazenar (sem lower aqui!)
            dono_nome = (getattr(pl, "dono", "") or "").strip() or "Usuário não informado"
            # crie uma chave normalizada para deduplicar
            dono_key  = dono_nome.lower()

            chave_pl = (pl.nome.strip().lower(), dono_key)
            if chave_pl in playlists_chaves:
                continue

            itens = list(getattr(pl, "itens", []) or [])
            reproducoes = int(getattr(pl, "reproducoes", 0) or 0)

            # armazene 'dono' com a capitalização original
            nova = Playlist(pl.nome, dono_nome, itens=itens, reproducoes=reproducoes)
            app.playlists.append(nova)
            playlists_chaves.add(chave_pl)
            novos_pl += 1



        # exibir avisos/erros do parser (opcional)
        for w in result.get("warnings", []):
            print(" - WARN:", w)
        for e in result.get("errors", []):
            print(" - ERRO:", e)

    print("\n--- Importação concluída ---")
    print(f"Novos usuários:   {novos_u}")
    print(f"Novas músicas:    {novos_m}")
    print(f"Novos podcasts:   {novos_p}")
    print(f"Novas playlists:  {novos_pl}")


# Controlador do APP (local de toda a regra de negócio)
class StreamingApp:
    def __init__(self):
        self.usuarios: list[Usuario] = []
        self.musicas: list[Musica] = []
        self.podcasts: list[Podcast] = []
        self.playlists: list[Playlist] = []

    # Método para criar um novo usuário e adicioná-lo à lista
    def criar_novo_usuario(self, nome: str) -> Usuario:
        u = Usuario(nome)
        self.usuarios.append(u)
        return u

    def salvar_relatorio_txt(self, caminho: Path = Path("relatorios/relatorio.txt")):
        linhas = []
        linhas.append("Relatório do Streaming")
        linhas.append(f"Usuários: {len(self.usuarios)}")
        linhas.append(f"Músicas: {len(self.musicas)}")
        linhas.append(f"Podcasts: {len(self.podcasts)}")
        linhas.append(f"Playlists: {len(self.playlists)}")
        linhas.append("")
        for pl in self.playlists:
            dono = pl.usuario.nome if pl.usuario else "Desconhecido"
            linhas.append(f"- {pl.nome} (dono: {dono})")
            for m in pl.itens:
                cls = m.__class__.__name__
                artista_ou_autor = getattr(m, "artista", getattr(m, "autor", ""))
                linhas.append(f"    * [{cls}] {m.titulo} - {artista_ou_autor}")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("\n".join(linhas), encoding="utf-8")
        print("Relatório salvo em relatorios/relatorio.txt")

def main():
    menu = Menu()
    app = StreamingApp()

    # # (opcional) dados de exemplo para testar rápido
    # app.musicas.append(Musica("Song A", 180, "Artist X"))
    # app.musicas.append(Musica("Song B", 200, "Artist Y"))
    # app.podcasts.append(Podcast("Pod 1", 1200, "Host Z"))

    importar_markdowns_para_main(app)
    print("Importação concluída.")
 
    # Para manter a compatibilidade com fluxo atual
    usuarios = app.usuarios          
    usuario_logado = None 
    
    while True:
        if not usuario_logado:
            # Manipulação do menu inicial: menu.py exibe; main.py controla
            opcao = menu.exibir_menu_inicial()

            match opcao:
                # "1": Fazer login":
                case "1":
                    if not usuarios:
                        print("Nenhum usuário cadastrado. Crie um novo usuário primeiro.")
                    else:
                        print("Usuários disponíveis:")
                        for i, u in enumerate(usuarios, start=1):
                            print(f"{i} - {u.nome}")
                        try:
                            escolha = int(input("Digite o número do usuário: "))
                        except ValueError:
                            print("Entrada inválida. Digite apenas números.")
                            continue
                        if 1 <= escolha <= len(usuarios):
                            usuario_logado = usuarios[escolha - 1]
                            print(f"Usuário '{usuario_logado.nome}' logado com sucesso!")
                        else:
                            print("Opção inválida.")

                # "2": "Criar novo usuário":
                case "2":
                    novo_nome = input("Digite o nome do novo usuário: ").strip()
                    if novo_nome:
                        u = app.criar_novo_usuario(novo_nome)
                        print(f"Usuário '{u.nome}' criado com sucesso!")
                    else:
                        print("Nome de usuário não pode ser vazio.")

                # "3": "Listar usuários":
                case "3":
                    if not usuarios:
                        print("Nenhum usuário cadastrado.")
                    else:
                        print("=== LISTA DE USUÁRIOS ===")
                        for u in usuarios:
                            print("-", u.nome)

                # "4": "Sair do sistema":
                case "4":
                    print("Saindo do sistema...")
                    return

                case _:
                    print("Opção inválida. Tente novamente.")

        else:
            # Menus se houver usuário logado
            opcao = menu.exibir_menu_usuario(usuario_logado.nome)

            match opcao:
                # "1": "Reproduzir uma música":
                case "1":
                    titulo = input("Título da música a reproduzir: ").strip()
                    midia = ArquivoDeMidia.buscar_por_titulo(titulo)
                    if midia:
                        midia.reproduzir()
                    else:
                        print("Música não encontrada.")

                # "2": "Listar músicas":
                case "2":
                    if not app.musicas:
                        print("Nenhuma música cadastrada.")
                    else:
                        print("\nMÚSICAS:")
                        for m in app.musicas:
                            # Usa o toString __str__ de Musica
                            print(m)

                # "3": "Listar podcasts":
                case "3":
                    if not app.podcasts:
                        print("Nenhum podcast cadastrado.")
                    else:
                        print("\nPODCASTS:")
                        for p in app.podcasts:
                            # Usa o toString __str__ de Podcast
                            print(p)

                # "4": "Listar playlists":
                case "4":
                    if not app.playlists:
                        print("Nenhuma playlist cadastrada.")
                    else:
                        print("\nPLAYLISTS:")
                        for pl in app.playlists:
                            # Usa o toString __str__ de Playlist
                            print(pl)

                # "5": "Reproduzir uma playlist":
                case "5":
                    # Reproduz uma playlist chamando o método reproduzir() da playlist (placeholder)                    
                    # Solicita o nome da playlist
                    nome_pl = input("Nome da playlist a reproduzir: ").strip()
                    if not nome_pl:
                            print("Nome inválido.")
                            continue
                    
                    pl = next((p for p in app.playlists if p.nome == nome_pl), None)
                    
                    if pl:
                        print(f"Reproduzindo playlist '{pl.nome}':")
                        pl.reproduzir()   # chama o método da classe Playlist
                    else:
                        print("Playlist não encontrada.")

                # "6": "Criar nova playlist":
                case "6":
                        nome = input("Nome da nova playlist: ").strip()
                        if not nome:
                            print("Nome inválido.")
                            continue

                        # Chama o construtor da playlist
                        pl = Playlist(nome, usuario_logado.nome)
                        app.playlists.append(pl)
                        print(f"Playlist '{pl.nome}' criada.")

                        add = input("Adicionar uma mídia agora? (s/N) ").strip().lower()
                        if add == "s":
                            titulo = input("Título exato da música/podcast: ").strip()
                            # Chama o método adicionar_midia_da_playlist
                            pl.adicionar_midia(titulo) 

                # "7": "Concatenar playlists":
                case "7":
                    # Solicita os nomes das playlists
                    destino = input("Playlist 1 destino: ").strip()
                    juntar = input("Playlist 2 a ser juntada: ").strip()

                    # Encontra as playlists pelos nomes
                    p1_destino = next((p for p in app.playlists if p.nome == destino), None)
                    p2_juntar  = next((p for p in app.playlists if p.nome == juntar), None)

                    if p1_destino and p2_juntar:
                        # Chama o método __add__ para concatenar
                        nova = p1_destino + p2_juntar

                        # Remove a antiga da lista e põe a nova concatenada no mesmo lugar de p1_destino
                        app.playlists = [p if p is not p1_destino else nova for p in app.playlists]

                        print(f"Playlists '{p1_destino.nome}' e '{p2_juntar.nome}' concatenadas em '{p1_destino.nome}'.")
                        print(f"A nova playlist tem {len(nova)} mídias.")   # usa __len__
                    
                    else:    
                        # Caso não encontre um ou ambos nomes das playlists
                        print("Playlist de destino ou origem não encontrada.")

                # "8": "Gerar relatório":
                case "8":
                    destino = Analises.salvar_relatorio(
                        musicas=app.musicas,
                        playlists=app.playlists,
                        usuarios=app.usuarios,
                        top_n=10,               
                        pasta="Relatório",
                        arquivo="relatorio.txt",
                    )
                    print(f"Relatório salvo em {destino}")               

                #"9: Ler arquivo markdown e importar mídias":
                case "9":
                    importar_markdowns_para_main(app)
                    print("Importação concluída.")

                # "10": "Sair":
                case "10":
                    print(f"👤 Usuário '{usuario_logado.nome}' saiu da conta.")
                    usuario_logado = None

                case _:
                    print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
