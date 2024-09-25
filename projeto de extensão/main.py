import sqlite3
import csv
from time import sleep
import os

# conexão com o banco de dados
def conectar_banco():
    try:
        conn = sqlite3.connect('templo.db')
        return conn
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        sleep(3)
        return None

conn = conectar_banco()
if conn:
    cursor = conn.cursor()

    # Criar tabela 'pessoas'
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            email CHAR(100) NOT NULL UNIQUE,
            data_nascimento DATE,
            participar_culto CHAR(1) CHECK(participar_culto IN ('s', 'n')) NOT NULL
        )
        ''')
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela 'pessoas': {e}")
        sleep(3)

    # Criar tabela 'bloqueados'
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bloqueados (
            id INTEGER PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email CHAR(100) NOT NULL UNIQUE,
            motivo TEXT
        )
        ''')
    except sqlite3.Error as e:
        print(f"Erro ao criar a tabela 'bloqueados': {e}")
        sleep(3)

#inserir registros do arquivo csv no banco de dados
def inserir_do_csv(csv_file:str):
    if not os.path.exists(csv_file):
        print(f"Arquivo {csv_file} não encontrado.")
        sleep(3)
        return

    try:
        with open(csv_file, 'r') as file:

            reader = csv.DictReader(file)
            for row in reader:
                try:
                    #verificar se o -email está registrado em bloqueados
                    cursor.execute('SELECT * FROM bloqueados WHERE email = ?', (row['email'],))
                    registro_bloqueado = cursor.fetchone()
                    
                    if registro_bloqueado:
                        print(f"O registro está bloqueado! {registro_bloqueado}")
                        sleep(4)
                        continue
                    
                    # Verificar se o e-mail já está registrado em pessoas
                    cursor.execute('SELECT * FROM pessoas WHERE email = ?', (row['email'],))
                    registro = cursor.fetchone()

                    if registro:
                        # Atualizar apenas a coluna 'participar_culto' para 's' se já existir
                        alterar_participacao(row['email'], participar='s')
                    else:
                        # Inserir novo registro
                        cursor.execute('''
                            INSERT INTO pessoas (nome, email, data_nascimento, participar_culto)
                            VALUES (?, ?, ?, 's')
                        ''', (row['nome'], row['email'], row['data_nascimento']))
                        
                except sqlite3.Error as e:
                    print(f"Erro ao inserir/atualizar o registro: {e}")
                    sleep(3)
        conn.commit()
        print("Registros inseridos ou atualizados com sucesso!")
        sleep(3)

    except Exception as e:
        print(f"Erro ao processar o arquivo CSV: {e}")
        sleep(3)

#mostrar todas as pessoas, grupo ou pessoa em especifico 
def mostrar_registros(email_list=None):
    try:
        if email_list:
            # Construir consulta SQL para buscar registros específicos
            query = f"SELECT * FROM pessoas WHERE email IN ({','.join('?' for _ in email_list)})"
            cursor.execute(query, email_list)
        else:
            # Buscar todos os registros
            cursor.execute("SELECT * FROM pessoas")
        
        registros = cursor.fetchall()

        if registros:
            print("\n=== Registros Encontrados ===")
            for registro in registros:
                print(f"ID: {registro[0]}, Nome: {registro[1]}, E-mail: {registro[2]}, Data de Nascimento: {registro[3]}, Participar do Culto: {registro[4]}")
                print()
            if voltar_main():return
        else:
            print("Nenhum registro encontrado.")
            sleep(3)
    except sqlite3.Error as e:
        print(f"Erro ao buscar registros: {e}")
        sleep(3)
    except KeyboardInterrupt:
        pass

#remover um registro
def remover_registro(email:str, bloq:bool=False):
    try:
        cursor.execute('DELETE FROM pessoas WHERE email = ?', (email,))
        if cursor.rowcount == 0:
            print("Nenhum registro encontrado para remover.")
        else:
            if bloq:
                print(f"Registro com o e-mail {email} removido e bloqueado com sucesso!")
            else:
                print(f"Registro com o e-mail {email} removido com sucesso!")
            conn.commit()
        sleep(3)
    except sqlite3.Error as e:
        print(f"Erro ao remover o registro: {e}")
        sleep(3)

#mostrar todos os registros bloqueados
def mostrar_bloqueados():
    try:
        cursor.execute('SELECT * FROM bloqueados')
        bloqueados = cursor.fetchall()
        if bloqueados:
            print("\n=== Lista de Pessoas Bloqueadas ===")
            for pessoa in bloqueados:
                print(f"ID: {pessoa[0]}, Nome: {pessoa[1]}, E-mail: {pessoa[2]}, Motivo: {pessoa[3]}")
            voltar_main()
        else:
            print("Nenhuma pessoa bloqueada encontrada.")
            sleep(3)
    except sqlite3.Error as e:
        print(f"Erro ao buscar pessoas bloqueadas: {e}")
        sleep(3)

#bloquear uma pessoa
def bloquear_pessoa(email:str, motivo:str) -> None:
    cursor.execute('SELECT * FROM pessoas WHERE email = ?', (email,))
    pessoa = cursor.fetchone()
    
    if pessoa:
        # mover para a tabela bloqueados
        cursor.execute('''
            INSERT INTO bloqueados (id, nome, email, motivo)
            VALUES (?, ?, ?, ?)
        ''', (pessoa[0], pessoa[1], pessoa[2], motivo))
        # remover da tabela pessoas
        remover_registro(email, bloq=True)
    else:
        print('Pessoa não encontrada!')
        sleep(3)
    conn.commit()

#desbloquear uma pessoa
def desbloquear_pessoa(email:str):
    cursor.execute('SELECT * FROM bloqueados WHERE email = ?', (email,))
    bloqueado = cursor.fetchone()

    if bloqueado:
        # mover de volta para a tabela pessoas
        cursor.execute('''
            INSERT INTO pessoas (id, nome, email, participar_culto)
            VALUES (?, ?, ?, 'n')
        ''', (bloqueado[0], bloqueado[1], bloqueado[2]))
        # remover da tabela bloqueados
        cursor.execute('DELETE FROM bloqueados WHERE email = ?', (email,))
    
    conn.commit()

#alterar a coluna 'participar_culto' para um registro específico
def alterar_participacao(email:str, participar:str):
    cursor.execute('''
        UPDATE pessoas
        SET participar_culto = ?
        WHERE email = ?
    ''', (participar, email))
    conn.commit()

#mostrar a quantidade de registros no banco de dados
def mostrar_quantidade_registros():

    cursor.execute('SELECT COUNT(*) FROM pessoas')
    total_p = cursor.fetchone()[0]
    print(f"Registros Pesoas: {total_p}")

    cursor.execute('SELECT COUNT(*) FROM bloqueados')
    total_b = cursor.fetchone()[0]
    print(f"Registros Bloqueados: {total_b}")

    print(f'Total de Registros: {total_p + total_b}')
    sleep(4)

# fechar a conexão com o banco de dados
def fechar_conexao():
    conn.close()

def limpar_terminal():
    # Verifica o sistema operacional
    if os.name == 'nt':  # para windows
        os.system('cls')
    else:  # para macOS ou linux
        os.system('clear')

def voltar_main() -> bool:
    """Para o usuário passar quanto tempo quiser olhando o resultado da pesquisa e digitar para sair quando estiver terminado de ler.
    """
    while True:
        if input("digite 's' para sair: ").strip().lower().startswith('s'):
            return True
        else:
            print('VALOR INVÁLIDO!')
            sleep(3)
        
def main():
    while True:
        limpar_terminal()
        #remover registro: deve ser de um a varios ou resetar o registro
        # alterar participação: deve ser de um a varios
        print("\n=== Menu Principal ===")
        print("1. Inserir registros do formulário (CSV)")
        print("2. Mostrar todos os registros, um grupo espcífico ou apenas um")
        print("3. Mostrar quantidade de registros")
        print("4. Remover um registro")
        print("5. Mostrar todos as pessoas bloqueadas")
        print("6. Bloquear uma pessoa")
        print("7. Desbloquear uma pessoa")
        print("8. Alterar participação no culto")
        print("9. Fechar o programa")

        try:
            opcao = input("Escolha uma opção (1-9): ").strip()

            if opcao == '1':
                csv_file = input("Digite o caminho do arquivo CSV: ").strip()

                if not csv_file:
                    print("Caminho do arquivo CSV não pode ser vazio.")
                    sleep(3)
                else:
                    inserir_do_csv(csv_file)
                
            elif opcao == '2':
                escolha = input("Deseja mostrar registros específicos? (s/n): ").strip().lower()
                
                if escolha == 's':
                    emails = input("Digite o(s) e-mail(s) separados por vírgula: ").strip().split(',')
                    mostrar_registros(emails)
                else:
                    mostrar_registros()

            elif opcao == '3':
                mostrar_quantidade_registros()

            elif opcao == '4':
                email = input("Digite o e-mail da pessoa a ser removida: ").strip()

                if not email:
                    print("O e-mail não pode ser vazio.")
                    sleep(3)
                else:
                    remover_registro(email)
                
            elif opcao == '5':
                mostrar_bloqueados()

            elif opcao == '6':
                email = input("Digite o e-mail da pessoa a ser bloqueada: ").strip()
                
                motivo = input("Digite o motivo do bloqueio: ").strip()

                if not email or not motivo:
                    print("E-mail e motivo do bloqueio não podem ser vazios.")
                    sleep(3)
                else:
                    bloquear_pessoa(email, motivo)
                sleep(3)   

            elif opcao == '7':
                email = input("Digite o e-mail da pessoa a ser desbloqueada: ").strip()

                if not email:
                    print("O e-mail não pode ser vazio.")
                    sleep(3)
                else:
                    desbloquear_pessoa(email)

            elif opcao == '8':
                email = input("Digite o e-mail da pessoa cuja participação será alterada: ").strip()
                
                participar = input("Digite 's' para participar ou 'n' para não participar: ").strip().lower()
                
                if not email or participar not in ['s', 'n']:
                    print("E-mail inválido ou opção de participação inválida ('s' ou 'n').")
                    sleep(3)
                else:
                    alterar_participacao(email, participar)
                
            elif opcao == '9':
                fechar_conexao()
                print("Programa encerrado.")
                break

            else:
                print("Opção inválida. Por favor, escolha entre 1 e 9.")
                sleep(3)

        except KeyboardInterrupt:
            print('Saindo do programa...')
            sleep(1)
            break
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            sleep(3)

if __name__ == '__main__':
    main()
