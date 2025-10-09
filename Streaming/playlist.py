#\Streaming\playlist.py
from pathlib import Path
from datetime import datetime
from Streaming.arquivo_midia import ArquivoDeMidia

class Playlist:
    """
    Classe de uma playlist de mídias contendo músicas e podcasts.
    Com os seguintes atributos:
        nome (str): com o nome da playlist
        dono (str): com o nome do criador da playlist
        itens (list): lista de objetos de ArquivoDeMidia
        reproducoes (int): um contador de execuções da playlist
    """
    
    # Método construtor
    def __init__(self, nome: str, dono: str = "Não Informado", itens=None, reproducoes: int = 0):
        self.nome = (nome or "Sem nome").strip()
        # Força que o atributo dono seja uma string
        dono_str = (dono.nome if hasattr(dono, "nome") else str(dono or "Não informado")).strip()
        self.dono = dono_str

        self.itens = list(itens) if itens else []
        self.reproducoes = reproducoes

    # Métodos obrigatórios
    # Adiciona uma mídia à playlist a partir do nome (título)
    def adicionar_midia(self, nome_midia: str) -> bool:
        """
        Recebe o nome da mídia e consulta a classe ArquivoDeMidia, 
        através do método ArquivoDeMidia.buscar_por_titulo(titulo)
        - Se achar, adiciona a mídia (nomes) à playlist.
        - Se não achar, não adiciona e retorna False.
        """
        titulo = (nome_midia or "").strip()

        midia = ArquivoDeMidia.buscar_por_titulo(titulo)

        if midia is None:
            print ("Midia não adicionada!")
            print(f"'{titulo}' não foi encontrada no cadastro! (playlist '{self.nome}').")
            return False
        else:
            print(f"Mídia '{titulo}' adicionada à playlist '{self.nome}'.")
            self.itens.append(midia)
            return True

    # Remove uma mídia da playlist a partir do nome (título)
    def remover_midia(self, nome_midia: str) -> bool:
        """
        Remove a 1ª ocorrência de uma mídia com o título informado.
        - Compara o título (nome) da mídia com o atributo 'titulo' do objeto.   
        Retorna: True se removeu, False se não encontrou.
        """
        titulo = (nome_midia or "").strip()        

        for i, m in enumerate(self.itens):
            # Compara o título passado com o título das mídias armazenadas
            if m.titulo.strip() == titulo:
                print (f"A mídia '{titulo}' foi removida da playlist '{self.nome}'.")
                del self.itens[i]                
                return True
            else:
                print(f"A mídia '{titulo}' não foi encontrada na playlist '{self.nome}'.")
                return False

    # Reproduz a playlist
    def reproduzir(self) -> None:
        """
        Simula tocar todas as mídias da lista.
        - Incrementa 1 na contagem de reproduções da Playlist.
        - Incrementa 1 em cada midia tocada.
        - Exibe as informações de cada mídia tocada.
        """
        # Incrementa o contador de reproduções da playlist
        self.reproducoes += 1
        
        for midia in self.itens:
            # verifica se a mídia não é None (pode ser None se o catálogo estiver incompleto)
            if midia is not None:                
                # Chama o método reproduzir() do ArquivoDeMidia
                # Tanto musica quanto podcast possuem o método
                # O próprio método reproduzir() já exibe as informações
                # O próprio método já incrementa o contador de reproduções
                midia.reproduzir()
            
    # Métodos obrigatório de sobrecarga de operadores
    # Método para somar duas playlists
    def __add__(self, outra):
        """
        Concatena duas playlists usando 'playlist1 + playlist2' e coloca em 'playlist1'.
        Soma as reproduções de ambas as listas
        """        
        # Adiciona os objetos da playlist2 com os itens (ojetos: midia)
        # da playlist1 e coloca em playlist1          
        self.itens.extend(outra.itens)
        
        # Soma as reproduções
        self.reproducoes = int(self.reproducoes) + int(outra.reproducoes)
        
        # Cria a terceira playlist - cópia do estado atual de self
        terceira = Playlist(nome=self.nome, dono=self.dono,
                            itens=list(self.itens), reproducoes=self.reproducoes)
        return terceira

    # Método para informar o tamanho da playlist
    def __len__(self):
        """Retorna o número de itens na playlist."""
        return len(self.itens)

    # Método para acessar itens pelo índice através de playlist[indice]
    def __getitem__(self, indice):
        """
        Permite acessar itens pelo índice passado: playlist[indice].
        Retorna o objeto de mídia na posição indicada.
        """
        return self.itens[indice]

    # Método para comparar duas playlists
    def __eq__(self, outra):
        """
        Método que compara se duas playlist são iguais
        Duas playlists são iguais se:
        - Possui o mesmo nome do criador (dono)
        - Possui o mesmo nome (nome)
        - Possui a mesma quantidade de mídias
        - Possui os mesmos nomes das mídias (ordem não importa)
        """
        
        # Compara se o outro objeto é uma instância de Playlist
        if not isinstance(outra, Playlist):
            return False
        
        # Faz as comparações necessárias pelos atributos
        # Nome da playlist e do usuário (criador)
        if (self.nome or "").strip().lower() != (outra.nome or "").strip().lower():
            return False
        
        # Nome do usuário (criador)
        if (self.dono or "").strip().lower() != (outra.dono or "").strip().lower():
            return False

        # Quantidade de mídias
        if len(self.itens) != len(outra.itens):
            return False

        # Método que cria uma lista de nomes ordenados para comparação posterior
        def nomesOrdenados(playlistOrdem):
            nomes_ordem = []
            for m in playlistOrdem.itens:
                t = m.titulo.strip().lower()
                nomes_ordem.append(t)
                
            # Faz a ordenação dos nomes para comparação posterior
            nomes_ordem.sort()
            return nomes_ordem

        return nomesOrdenados(self) == nomesOrdenados(outra)

    # Métodos obrigatorios de classe comum a todas
    # Método __str__
    def __str__(self):
        midias_str = "\n    ".join(str(m).strip() for m in self.itens) if self.itens else "    Nenhuma mídia"
        return (f"Playlist:\n"
                f"  Nome         : {self.nome}\n"
                f"  Usuário      : {self.dono}\n"
                f"  Total Mídias : {len(self.itens)}\n"
                f"  Reproduções  : {self.reproducoes}\n"
                f"  Itens:\n    {midias_str}\n")

    # Método __repr__
    def __repr__(self):
        return (f"Playlist(nome={self.nome!r}, dono={self.dono!r}, "
                f"itens={len(self.itens)} itens, reproducoes={self.reproducoes})")

    
