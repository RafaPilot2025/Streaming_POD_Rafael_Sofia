#menu.py

class Menu:
    def __init__(self):
        self.opcoes_iniciais = {
            "1": "Entrar como usuário",
            "2": "Criar novo usuário",
            "3": "Listar usuários",
            "4": "Sair"
        }
        self.opcoes_usuario = {
            "1": "Reproduzir uma música",
            "2": "Listar músicas",
            "3": "Listar podcasts",
            "4": "Listar playlists",
            "5": "Reproduzir uma playlist",
            "6": "Criar nova playlist",
            "7": "Concatenar playlists",
            "8": "Gerar relatório",
            "9": "Carregar dados via arquvivos markdown",
            "10": "Sair"
        }

    def exibir_menu_inicial(self):
        print("\n=== MENU INICIAL ===")
        for k, v in self.opcoes_iniciais.items():
            print(f"{k} - {v}")
        return input("Escolha uma opção: ")

    def exibir_menu_usuario(self, usuario_nome):
        print(f"\n=== MENU DO USUÁRIO ({usuario_nome}) ===")
        for k, v in self.opcoes_usuario.items():
            print(f"{k} - {v}")
        return input("Escolha uma opção: ")

    def __str__(self):
        return "Classe responsável por gerenciar os menus do sistema de streaming."

    def __repr__(self):
        return f"Menu(opcoes_iniciais={len(self.opcoes_iniciais)}, opcoes_usuario={len(self.opcoes_usuario)})"


