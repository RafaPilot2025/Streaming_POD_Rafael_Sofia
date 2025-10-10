# Streaming de Mídia — Trabalho de Programação Orientada a Dados (PUCRS)

## O Projeto:
Este repositório contém a implementação do sistema de streaming de mídia "Streaming POD", desenvolvido como trabalho da disciplina Programação Orientada a Dados (PUCRS), sob orientação do Prof. Me. Otávio Parraga.

O projeto é inspirado em plataformas como Spotify, aplicando os principais conceitos de Programação Orientada a Dados — como herança, encapsulamento e abstração — aliados a tratamento de erros, relatórios automáticos e inovação.

---

## Estrutura do Projeto:

```
Streaming_POD_Rafael_Sofia/
│
├── main.py                         # Arquivo principal do sistema
├── README.md                       # Documentação do projeto
│
├── Streaming/
│   ├── __init__.py
│   ├── arquivo_midia.py            # Classe abstrata e subclasses de mídia
│   ├── playlist.py                 # Classe Playlist (concatenação, reprodução)
│   ├── usuario.py                  # Classe Usuário
│   ├── analises.py                 # Geração de estatísticas e relatórios
│   ├── menu.py                     # Menu interativo em terminal
│
├── config/
│   ├── Exemplo Entrada - 1.md      # Arquivo de entrada Markdown
│   ├── Exemplo Entrada - 2.md      # Arquivo de entrada Markdown
│   ├── lermarkdown.py              # Leitura e validação dos arquivos .md
│   ├── Bohemian Rhapsody.txt       # Exemplo de letra de música
│   ├── Cinema em Debate.txt        # Exemplo de conteúdo de PodCast
│
├── logs/
│   └── erros.log                   # Registro de erros e inconsistências
│
└── relatorios/
    └── relatorio.txt               # Relatório final de execuções e estatísticas
```

---

## Funcionalidades:

O sistema permite que usuários criem contas, montem playlists, reproduzam mídias e acompanhem relatórios, tudo via linha de comando.

### Usuários
- Criação e listagem de contas.
- Histórico automático de músicas e podcasts reproduzidos.
- Associação direta entre playlists e usuário criador.

### Músicas e Podcasts
- Leitura automática de mídias a partir de arquivos Markdown.
- Exibição das letras das músicas durante a reprodução **(inovação)**.
- Sistema de avaliações interativas com notas de 0 a 5 **(inovação)**.
- Tratamento de dados ausentes e normalização de títulos.

### Playlists
- Criação, listagem e reprodução completa.
- Adição e remoção de mídias.
- Concatenação de playlists via operador `+` (`__add__`), preservando o nome da primeira.
- Contagem de mídias via `len()`.
- Comparação de playlists e itens com `__eq__`.

### Relatórios e Análises
Geração de relatórios contendo:
- Músicas mais reproduzidas  
- Usuário mais ativo  
- Playlist mais popular  
- Médias de avaliação das músicas  
- Total de reproduções no sistema  

O relatório é salvo em:  relatorios/relatorio.txt

### Logs e Tratamento de Erros
Erros e inconsistências são registrados em:  logs/erros.log

Tratando validações como:
- Músicas inexistentes em playlists.  
- Avaliações fora do intervalo 0–5.  
- Usuários ou playlists duplicados.  

---

## Entrada de Dados via arquivo markdown .md:

Os dados iniciais são carregados automaticamente da pasta `config/`.  
Todos os arquivos da pasta são lidos e processados.  
Cada arquivo `.md` pode conter blocos de:
- Usuários  
- Músicas  
- Podcasts  
- Playlists  

O leitor `LerMarkdown` realiza a leitura, validação e integração, evitando duplicatas e registrando inconsistências no log.

---

## Como Executar:

1. Certifique-se de estar na raiz do projeto:
   ```bash
   cd Streaming_POD_Rafael_Sofia
   ```

2. Execute o arquivo principal:
   ```bash
   python main.py
   ```

3. Use o menu interativo para navegar entre as opções do sistema.

---

## Exemplo de Execução:

### Reproduzir Música

```
Digite o título da música a reproduzir: Bohemian Rhapsody
Reproduzindo: Bohemian Rhapsody - Queen
Duração: 354 segundos

Letra:
Is this the real life?  
Is this just fantasy?  
Caught in a landslide,  
No escape from reality...

( ... )
```

Após a reprodução:
```
Deseja avaliar esta música? (0 a 5): 5
Obrigado! Sua avaliação foi registrada.
```

---

### Reproduzir Playlist

```
Nome da playlist a reproduzir: Favoritas
Reproduzindo playlist 'Favoritas':
1. Bohemian Rhapsody - Queen
2. Imagine - John Lennon

Exibindo letras durante a reprodução...
Playlist finalizada com sucesso!
```

---

### Gerar Relatório

```
>>> Opção 8 - Gerar Relatório
Relatório salvo em relatorios/relatorio.txt
```

Conteúdo resumido:
```
Relatório do Streaming
Usuários: 3
Músicas: 10
Podcasts: 2
Playlists: 4

Top 3 músicas mais reproduzidas:
1. Bohemian Rhapsody - Queen (12x)
2. Imagine - John Lennon (8x)
3. Rolling in the Deep - Adele (7x)

Usuário mais ativo: Sofia
Playlist mais popular: Favoritas
```

---

## Inovações:

1. **Exibição do conteúdo do PodCast e da letra da música durante a reprodução das músicas**  
   O sistema localiza automaticamente o arquivo `.txt` correspondente ao título da mídia e exibe todo o conteúdo ou a letra da mídia.

2. **Sistema de Avaliação Interativo**  
   Após a reprodução, o usuário é convidado a avaliar a música (nota de 0 a 5).  
   Essas avaliações alimentam as análises estatísticas e são registradas no relatório final.

Essas duas inovações tornam o projeto mais imersivo e personalizado, estendendo as funcionalidades originais do enunciado.

---

## Créditos

**Desenvolvido por:**  
**Rafael Magalhães**  
**Sofia Lahham**  

Orientação: Prof. Me. Otávio Parraga  
PUCRS — Escola Politécnica  
Disciplina: *Programação Orientada a Dados*
