#\Streaming\usuarios.py

from datetime import datetime

class Usuario:
    
    # Atributo de classe para contar instâncias
    qtde_instancias = 0

    # Construtor
    def __init__(self, nome='Usuario não informado'):
        self.nome = nome.strip().title()  # Formata o nome
        self.playlists = []
        self.historico = []
        Usuario.qtde_instancias += 1
        #self.id = id(self)  # ID único baseado no endereço de memória do objeto
        self.data_criacao = datetime.now()
    
    # Métodos obrigatorios __str__ e __repr__
    def __str__(self):
        return (f"Usuário: {self.nome} | "
                f"Listas de reprodução: {len(self.playlists)} | "
                f"Musicas no histórico: {len(self.historico)} | "
               # f"ID: {self.id}, | "
                f"Criado em: {self.data_criacao.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def __repr__(self):
        return (f"Usuário: {self.nome} | "
                f"Número de Playlists: {self.playlists} | "
                f"Quantidade de músicas no histórico: {self.historico} | "
              #  f"Identificador único: {self.id} | "
                f"Usuário criado em: {self.data_criacao}")
    
    #Métodos obrogatórios do exercício
    # Cria uma lista: parâmetro seu nome
    def criar_playlist(self, nome: str):
        """Adiciona uma playlist criada ao usuário corrente."""
        if nome.strip().title() in self.playlists:
            print(f"A playlist '{nome.strip().title()}' já existe.")
        elif not nome.strip():
            print("O nome da playlist não pode ser vazio.")
        else:
            self.playlists.append(nome.strip().title())
            print(f"Playlist '{nome.strip().title()}' criada com sucesso!")

    #Ouvir uma música: parâmetro o nome da música
    def ouvir_musica(self, musica: str):
        """Simula a reprodução de uma música e registra no histórico."""
        if not musica.strip():
            print("O nome da música não pode ser vazio.")
        else:
            print(f"Reproduzindo a música: {musica.strip().title()}")
            self.registrar_reproducao(musica.strip().title())

    # Outros métodos    
    # Registra a reprodução de uma música
    def registrar_reproducao(self, musica: str):
        """Adiciona uma música escutada ao histórico de reproduções."""
        self.historico.append(musica)
    

if __name__ == "__main__":
    u = Usuario("Ana Silva")
    print(u)
