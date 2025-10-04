# Streaming/analises.py

# Importação das bibliotecas permitidas
import sys
import os
import math

from datetime import datetime
from pathlib import Path


# Evita dependências externas; assume que Musica, Playlist e Usuario
# já estão definidos no pacote Streaming
from .arquivo_midia import ArquivoDeMidia  # para contexto de tipos/atributos
from .playlist import Playlist
from .usuarios import Usuario  # seu arquivo chama 'usuarios.py' (classe Usuario)

class Analises:
    """
    Classe que possui os métodos estáticos para análises.
    As saídas são destinadas a relatórios ou estatísticas.
    Apenas calcula a partir das coleções fornecidas, sem alterar o estado dos objetos.
    """

    # Estatísticas e relatórios solicitados
    @staticmethod
    def top_musicas_reproduzidas(musicas, top_n = 10):
        """
        Retorna uma lista com as n = 10 músicas mais reproduzidas.
        Critério: ordena por atributo  decrescente de reproducoes.
        """
        # cópia para não alterar a lista original
        ordenadas = list(musicas)
        # ordena decrescente por 'reproducoes'; usa 0 se atributo não existir
        ordenadas.sort(key=lambda m: m.reproducoes, reverse=True)
        return ordenadas[:max(0, int(top_n))]

    @staticmethod
    def playlist_mais_popular(playlists):
        """
        Retorna a playlist mais ouvida ou a de maior reproducoes.        
        Se playlists for vazia, retorna None.
        """
        if not playlists:
            return None
        return max(playlists, key=lambda p: p.reproducoes) if playlists else None

    @staticmethod
    def usuario_mais_ativo(usuarios):
        """
        Retorna o usuário que mais ouviu músicas ou o que tem maior tamanho de 'historico'.
        Se usuarios for vazio, retorna None.
        """
        if not usuarios:
            return None
        return max(usuarios, key=lambda u: len(u.historico)) if usuarios else None

    @staticmethod
    def media_avaliacoes(musicas):
        """
        Retorna um dicionário com as médias {titulo_da_musica: media_avaliacao(float)}.
        Média simples das notas em avaliacoes; se vazio, média 0.0.
        """
        medias = {}
        for m in musicas:
            avals = m.avaliacoes or []
            medias[m.titulo.strip()] = (sum(avals) / len(avals)) if avals else 0.0
        return medias

    @staticmethod
    def total_reproducoes(usuarios):
        """
        Retorna a total de reproduções feitas por todos os usuários.
        """
        return sum(len(u.historico or []) for u in usuarios)


    @staticmethod
    def salvar_relatorio(musicas, playlists, usuarios, top_n=10, pasta="Relatório", arquivo="relatorio.txt"):       

        # Coletas a partir dos próprios métodos da classe
        top = Analises.top_musicas_reproduzidas(musicas, top_n)
        pl_pop = Analises.playlist_mais_popular(playlists)
        user_ativo = Analises.usuario_mais_ativo(usuarios)
        medias = Analises.media_avaliacoes(musicas)
        total_rep = Analises.total_reproducoes(usuarios)

        # Monta o texto
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linhas = []
        linhas.append("=== Relatório de Análises ===")
        linhas.append(f"Gerado em: {ts}")
        linhas.append("")
        linhas.append("— Resumo —")
        linhas.append(f"Total de usuários: {len(usuarios)}")
        linhas.append(f"Total de músicas: {len(musicas)}")
        linhas.append(f"Total de playlists: {len(playlists)}")
        linhas.append(f"Total de reproduções (históricos de usuários): {total_rep}")
        linhas.append("")

        linhas.append(f"— Top {top_n} músicas por reproduções —")
        if top:
            for i, m in enumerate(top, start=1):
                linhas.append(f"{i:02d}. '{m.titulo}' — {m.artista} | reproduções: {m.reproducoes}")
        else:
            linhas.append("Nenhuma música cadastrada.")
        linhas.append("")

        linhas.append("— Playlist mais popular —")
        if pl_pop:
            linhas.append(f"'{pl_pop.nome}' — criador: {pl_pop.dono} | itens: {len(pl_pop)} | reproduções: {pl_pop.reproducoes}")
        else:
            linhas.append("Nenhuma playlist cadastrada.")
        linhas.append("")

        linhas.append("— Usuário mais ativo —")
        if user_ativo:
            linhas.append(f"{user_ativo.nome} — músicas no histórico: {len(getattr(user_ativo, 'historico', []))}")
        else:
            linhas.append("Nenhum usuário cadastrado.")
        linhas.append("")

        linhas.append("— Médias de avaliações por música —")
        if medias:
            for titulo, media in medias.items():
                linhas.append(f"'{titulo}': {media:.2f}")
        else:
            linhas.append("Nenhuma música com avaliações.")
        linhas.append("")

        # Grava no arquivo Relatório/relatorio.txt
        dirp = Path(pasta)
        dirp.mkdir(parents=True, exist_ok=True)
        destino = dirp / arquivo
        destino.write_text("\n".join(linhas), encoding="utf-8")
        return destino

 
