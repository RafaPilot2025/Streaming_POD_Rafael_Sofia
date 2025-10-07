# midia.py

from datetime import datetime
from pathlib import Path

class ArquivoDeMidia:
    """
    Classe de um arquivo de mídia genérico (música, podcast, álbum, etc.)
    A igualdade (__eq__) considera apenas título e artista, sendo case insensitive.
    Duração em segundos (int). Reproduções (int) inicia em zero.
    Atributos adicionais são definidos nas subclasses.
    """

    # Lista de instâncias de qualquer objeto de mídia
    # Utilizado para busca por título da midia, tanto para música quanto podcast
    # Utilizado na classe playlist para verificar se a mídia existe 
    # Atributo de classe (compartilhado por todas as instâncias)
    registroMidia = []  
    
    def __init__(self, titulo: str, duracao: int, artista: str, reproducoes: int = 0):
        
        self.titulo = titulo
        self.duracao = duracao               # duração em segundos (int)
        self.artista = artista
        self.reproducoes = reproducoes       # contador de execuções iniciado em zero
   
        # adiciona qualquer instância (música ou podcast) como objeto 
        # em um registro geral de mídia
        ArquivoDeMidia.registroMidia.append(self)

    @classmethod
    def buscar_por_titulo(cls, titulo: str):
        t = titulo.strip().lower()
        for m in cls.registroMidia:
            if m.titulo.strip().lower() == t:
                return m
        return None
   
    # Métodos obrigatórios especiais
    # Simula a execução do arquivo de mídia, mostra na tela as informações 
    # contendo título, artista e duração
    def reproduzir(self) -> None:
        """Simula a execução do arquivo de mídia, incrementando reproduções e exibindo info."""
        self.reproducoes += 1
        print(f"-> Reproduzindo: '{self.titulo}' — {self.artista} de {self.duracao} segundos. (Total de reproduções: {self.reproducoes})")

    #  Compara dois arquivos de mídia (mesmo título e artista).
    def __eq__(self, other) -> bool:
        """Dois arquivos são iguais se título e artista forem iguais, ignora espaços e case."""
        # Trata comparação com outros tipos 
        if not isinstance(other, ArquivoDeMidia):
            return NotImplemented
        
        #Retorna True se título e artista forem iguais, ignorando espaços e case
        return (self.titulo.strip().lower() == other.titulo.strip().lower() and
                self.artista.strip().lower() == other.artista.strip().lower())

    # Métodos obrigatórios para todos 
    # ToString
    def __str__(self) -> str:
        return (f"A midia {self.titulo} do artista {self.artista} | "
                f" com duração de {self.duracao} segundos | "
                f" tocou: {self.reproducoes} vezes")

    # Representação oficial
    def __repr__(self) -> str:
        cls = self.__class__.__name__
        return (f"{cls}(titulo='{self.titulo}', duracao={self.duracao}, "
                f"artista='{self.artista}', reproducoes={self.reproducoes})")


# Subclasse obrigatória: Música
class Musica(ArquivoDeMidia):
    """
    Classe música.
    - genero: string (Rock, Pop, Rap, Clássico, etc.)
    - avaliacoes: lista com notas inteiras de 0 a 5
    """

    def __init__(self, titulo: str, duracao: int, artista: str,
                 genero: str = "Desconhecido", reproducoes: int = 0,
                 avaliacoes=None):
        super().__init__(titulo, duracao, artista, reproducoes)
        self.genero = (genero or "Não informado").strip().title()
        self.avaliacoes = list(avaliacoes) if isinstance(avaliacoes, list) else []

    def avaliar(self, nota: int) -> bool:
        """
        Adiciona uma nota de 0 a 5. Caso fora do intervalo ou inválida, 
        retorna para o usuário                       
        Retorna True se adicionou; False caso contrário.
        """
        if not isinstance(nota, int):
             print(f"Nota não inteira '{nota}' para '{self.titulo}'.")
             return False
      
        if nota < 0 or nota > 5:
             print(f"Nota fora do intervalo 0 a 5 ({nota}) para '{self.titulo}'.")
             return False
       
        self.avaliacoes.append(nota)
        return True

    # Métodos obrigatórios gerais
    # ToString
    def __str__(self):
        avg = (sum(self.avaliacoes) / len(self.avaliacoes)) if self.avaliacoes else 0.0
        return (f"Música:\n"
                f"  Título       : {self.titulo}\n"
                f"  Artista      : {self.artista}\n"
                f"  Gênero       : {self.genero}\n"
                f"  Duração      : {self.duracao}s\n"
                f"  Reproduções  : {self.reproducoes}\n"
                f"  Avaliações   : {len(self.avaliacoes)} (média {avg:.2f})\n")

    # Representação oficial
    def __repr__(self) -> str:
        return (f"Musica(titulo='{self.titulo}', duracao={self.duracao}, artista='{self.artista}', "
                f"genero='{self.genero}', reproducoes={self.reproducoes}, "
                f"avaliacoes={self.avaliacoes})")


# Subclasse obrigatória: Podcast
class Podcast(ArquivoDeMidia):
    """
    Classe de episódio de podcast.
    - episodio: inteiro com o número do episódio
    - temporada: string com o nome da temporada
    - host: string com o nome do apresentador
    """

    def __init__(self, titulo: str, duracao: int, artista: str,
                 episodio: int, temporada: str, host: str,
                 reproducoes: int = 0):
        super().__init__(titulo, duracao, artista, reproducoes)

        # if not isinstance(episodio, int) or episodio < 1:
        #     _log_error(f"Podcast: número de episódio inválido '{episodio}' para '{self.titulo}'; ajustando para 1.")
        #     episodio = 1

        self.episodio = episodio
        self.temporada = (temporada or "Temporada").strip()
        self.host = (host or "Não informado").strip()

    # Métodos obrigatórios gerais
    # ToString
    def __str__(self) -> str:
        return (f"Podcast:\n"
                f"  Título       : {self.titulo}\n"
                f"  Host         : {self.host}\n"
                f"  Temporada    : {self.temporada}\n"
                f"  Episódio     : {self.episodio}\n"
                f"  Artista      : {self.artista}\n"
                f"  Duração      : {self.duracao}s\n"
                f"  Reproduções  : {self.reproducoes}\n")

    # Representação oficial
    def __repr__(self) -> str:
        return (f"Podcast(titulo='{self.titulo}', duracao={self.duracao}, artista='{self.artista}', "
                f"episodio={self.episodio}, temporada='{self.temporada}', host='{self.host}', "
                f"reproducoes={self.reproducoes})")