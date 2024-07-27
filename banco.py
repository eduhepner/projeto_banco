import os
import re
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import sha256
from pathlib import Path

ROOT_PATH = Path(__file__).parent
conexao = sqlite3.connect(ROOT_PATH / "db" / "database.db")
cursor = conexao.cursor()
cursor.row_factory = sqlite3.Row


class Cliente:
    def __init__(self, cpf, senha, nome, telefone, email):
        self.cpf = cpf
        self.senha = senha
        self.nome = nome
        self.telefone = telefone
        self.email = email

    @staticmethod
    def cadastrar_usuario(cpf, senha, nome, telefone, email):
        data = cpf, senha, nome, telefone, email
        try:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS cliente (id INTEGER PRIMARY KEY AUTOINCREMENT, cpf VARCHAR(11) NOT NULL, senha VARCHAR(32) NOT NULL, nome VARCHAR(100) NOT NULL, telefone VARCHAR(20) NOT NULL, email VARCHAR(100) NOT NULL);"
            )
            cursor.execute(
                "INSERT INTO cliente (cpf, senha, nome, telefone, email) VALUES (?,?,?,?,?);",
                data,
            )

            conexao.commit()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            conexao.rollback()


class Conta:
    def __init__(self, cpf, id, saldo=0, agencia="0001"):
        self.cpf = cpf
        self._saldo = saldo
        self._agencia = agencia
        self._id = id
        self._numero = f"{self._agencia}-{self._id}"

    def cadastrar_conta(self):
        try:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS contas (id INTEGER PRIMARY KEY AUTOINCREMENT, conta VARCHAR(10) NOT NULL, agencia VARCHAR(10) NOT NULL, saldo FLOAT NOT NULL, id_cliente INTEGER NOT NULL, FOREIGN KEY(id_cliente) REFERENCES cliente(id));"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, id_conta INTEGER NOT NULL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tipo VARCHAR NOT NULL, valor FLOAT NOT NULL, FOREIGN KEY(id_conta) REFERENCES contas(id));"
            )
            cursor.execute(
                "SELECT id FROM cliente WHERE cpf = ?;",
                (self.cpf,),
            )
            id_cliente = cursor.fetchone()
            data = self._agencia, self._saldo, id_cliente[0]
            cursor.execute(
                "INSERT INTO contas (agencia, saldo, id_cliente) VALUES (?,?,?);",
                data,
            )

            conexao.commit()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            conexao.rollback()
        return print("  Conta criada com sucesso!  ".center(40, "#"))

    def sacar(self, valor):
        self._valor = valor
        if self._valor > self._saldo:
            print("  Saldo insuficiente.  ".center(40, "#"))
            return
        if self._valor <= self._saldo and self._valor > 0:
            self._saldo -= self._valor
            try:
                cursor.execute(
                    "SELECT id FROM cliente WHERE cpf = ?;",
                    (self.cpf,),
                )
                id_cliente = cursor.fetchone()
                cursor.execute(
                    "UPDATE contas SET saldo = ? WHERE id_cliente = ?;",
                    (
                        self._saldo,
                        id_cliente[0],
                    ),
                )
                conexao.commit()
            except Exception as e:
                print(f"Ocorreu um erro: {e}")
                conexao.rollback()
            transacao = Saque(self._id, self._valor)
            transacao.realizar_transacao()
            os.system("clear")
            print("  Saque realizado.  ".center(40, "#"))
        else:
            print("  Valor inválido.  ".center(40, "#"))

    def depositar(self, valor):
        self._valor = valor
        if valor > 0:
            self._saldo += valor
            try:
                cursor.execute(
                    "SELECT id FROM cliente WHERE cpf = ?;",
                    (self.cpf,),
                )
                id_cliente = cursor.fetchone()
                cursor.execute(
                    "UPDATE contas SET saldo = ? WHERE id_cliente = ?;",
                    (
                        self._saldo,
                        id_cliente[0],
                    ),
                )
                conexao.commit()
            except Exception as e:
                print(f"Ocorreu um erro: {e}")
                conexao.rollback()
            transacao = Deposito(self._id, self._valor)
            transacao.realizar_transacao()
            os.system("clear")
            print("  Depósito realizado.  ".center(40, "#"))
        else:
            print("  Valor inválido.  ".center(40, "#"))

    @property
    def mostrar_saldo(self):
        return self._saldo

    @property
    def mostrar_numero(self):
        return self._numero


class Transacoes(ABC):
    @abstractmethod
    def realizar_transacao(self):
        pass


class Saque(Transacoes):
    def __init__(self, id, valor):
        super().__init__()
        self._valor = valor
        self._id = id

    def realizar_transacao(self):
        date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        tipo = "Saque"
        try:
            data = self._id, date, tipo, self._valor
            print(data)
            cursor.execute(
                "INSERT INTO transacoes (id_conta, data, tipo, valor) VALUES (?,?,?,?);",
                data,
            )
            conexao.commit()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            conexao.rollback()


class Deposito(Transacoes):
    def __init__(self, id, valor):
        super().__init__()
        self._valor = valor
        self._id = id

    def realizar_transacao(self):
        date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        tipo = "Depósito"
        try:
            data = self._id, date, tipo, self._valor
            print(data)
            cursor.execute(
                "INSERT INTO transacoes (id_conta, data, tipo, valor) VALUES (?,?,?,?);",
                data,
            )
            conexao.commit()
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            conexao.rollback()


class Extrato:
    def __init__(self) -> None:
        pass

    @staticmethod
    def filtro_transacao(id, tipo):
        try:
            if tipo:
                cursor.execute(
                    "SELECT * FROM transacoes WHERE id_conta = ? and tipo = ?;",
                    (id, tipo),
                )
            elif tipo == None:
                cursor.execute("SELECT * FROM transacoes WHERE id_conta = ? ;", (id,))
            resultado = cursor.fetchall()
            os.system("clear")
            print("  EXTRATO  ".center(40, "=") + "\n")
            if resultado:
                for i in resultado:
                    print(f"[{i['data']}] {i['tipo'].upper()} R$ {i['valor']:.2f}")
            else:
                print("Sem movimentações.")
            print("\n" + "=" * 40)

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            conexao.rollback()


def login(cpf, senha):
    try:
        senha_cript = cursor.execute(
            "SELECT senha FROM cliente WHERE cpf = ?;",
            (cpf,),
        )
        resultado = senha_cript.fetchone()
        if senha == resultado["senha"]:
            procurar = cursor.execute(
                "SELECT * FROM cliente WHERE cpf = ?;",
                (cpf,),
            )
            resultado = procurar.fetchone()
            cliente = Cliente(
                cpf=resultado["cpf"],
                senha=resultado["senha"],
                nome=resultado["nome"],
                telefone=resultado["telefone"],
                email=resultado["email"],
            )
            return cliente
        return False
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        conexao.rollback()


def checar_cpf(cpf):
    # padrao = "\d{11}"
    # if re.match(padrao, cpf):
    #     print("Válido")
    #     return True
    # return False
    return True


def achar_cpf(cpf):
    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS cliente (id INTEGER PRIMARY KEY AUTOINCREMENT, cpf VARCHAR(11) NOT NULL, senha VARCHAR(32) NOT NULL, nome VARCHAR(100) NOT NULL, telefone VARCHAR(20) NOT NULL, email VARCHAR(100) NOT NULL);"
        )
        conexao.commit()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        conexao.rollback()
    try:
        procurar = cursor.execute(
            "SELECT * FROM cliente WHERE cpf = ?;",
            (cpf,),
        )
        resultado = procurar.fetchone()
        if resultado:
            return True
        else:
            return False
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        conexao.rollback()


def achar_conta(cpf):
    try:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS contas (id INTEGER PRIMARY KEY AUTOINCREMENT, agencia VARCHAR(10) NOT NULL, saldo FLOAT NOT NULL, id_cliente INTEGER NOT NULL, FOREIGN KEY(id_cliente) REFERENCES cliente(id));"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS transacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, id_conta INTEGER NOT NULL, data TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tipo VARCHAR NOT NULL, valor FLOAT NOT NULL, FOREIGN KEY(id_conta) REFERENCES contas(id));"
        )
        conexao.commit()

        cursor.execute(
            "SELECT id FROM cliente WHERE cpf = ?;",
            (cpf,),
        )
        id_cliente = cursor.fetchone()

        cursor.execute(
            "SELECT * from contas WHERE id_cliente = ?;",
            (id_cliente[0],),
        )

        resultado = cursor.fetchone()
        if resultado:
            conta = Conta(
                cpf=cpf,
                saldo=resultado["saldo"],
                agencia=resultado["agencia"],
                id=resultado["id"],
            )
            return conta
        return resultado
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        conexao.rollback()


def menu():
    if not logado:

        opcao = input(
            """Escolha uma opção:
[1] Login
[2] Criar usuário
[0] Sair

>>> """
        )
        return opcao
    else:
        opcao = input(
            f"""
Olá {cliente.nome}, escolha uma opção:

[Saldo: R${conta.mostrar_saldo:.2f}]

[1] Depósito
[2] Saque
[3] Extrato
[4] Criar conta
[0] Sair

>>> """
        )
    return opcao


print("  Bem vindo  ".center(40, "#"))
logado = False
while True:
    opcao = menu()

    if opcao == "1" and not logado:
        cpf = input("Digite seu CPF: ")
        valido = checar_cpf(cpf)
        if valido:
            cliente = achar_cpf(cpf)
            if cliente:
                senha = input("Digite sua senha: ")
                senha_cript = sha256(senha.encode()).digest()
                cliente = login(cpf, senha_cript)
                if cliente:

                    logado = True
                    conta = achar_conta(cpf)
                    print("  Login realizado com sucesso!  ".center(40, "#"))
                else:

                    print("  Senha incorreta.  ".center(40, "#"))
            else:

                print("  Cliente não encontrado.  ".center(40, "#"))
        else:
            print("CPF inválido.")
    elif opcao == "2" and not logado:
        cpf = input("Digite seu CPF: ")
        valido = checar_cpf(cpf)
        if valido:
            cliente = achar_cpf(cpf)
            if cliente:
                print("  CPF já cadastrado no sistema.  ".center(40, "#"))
            else:
                senha = input("Digite uma senha: ")
                senha = sha256(senha.encode()).digest()
                nome = input("Digite seu nome completo: ")
                telefone = input("Digite seu telefone (somente números): ")
                email = input("Digite seu email: ")
                if cpf and senha and nome and telefone and email:
                    cliente = Cliente(
                        cpf=cpf,
                        senha=senha,
                        nome=nome,
                        telefone=telefone,
                        email=email,
                    )
                    Cliente.cadastrar_usuario(
                        cpf,
                        senha,
                        nome,
                        telefone,
                        email,
                    )
                    logado = True
                else:
                    print("Dados não preenchidos por completo")
        else:
            print("CPF inválido.")
    # Depositar
    elif opcao == "1" and logado:
        valor = float(input("Digite o valor que deseja depositar: "))
        transacao = conta.depositar(valor)
        # os.system("clear")

    # Sacar
    elif opcao == "2" and logado:
        valor = float(input("Digite o valor que deseja sacar: "))
        transacao = conta.sacar(valor)
        # os.system("clear")

    # Extrato
    elif opcao == "3" and logado:

        opcao = input(
            """[1] Entradas
[2] Saídas
[3] Todas

>>> """
        )
        if opcao == "1":
            tipo = "Depósito"
        elif opcao == "2":
            tipo = "Saque"
        elif opcao == "3":
            tipo = None
        Extrato.filtro_transacao(conta._id, tipo)

        # os.system("clear")

    # Criar conta
    elif opcao == "4" and logado:
        resultado = achar_conta(cpf)
        if resultado:
            os.system("clear")
            print("  Você já possui uma conta!  ".center(40, "#"))
        else:
            try:
                id = cursor.execute("SELECT MAX(id) FROM contas")
                id = cursor.fetchone()
                id = id[0] + 1
                conta = Conta(cpf=cpf, id=id)
                conta.cadastrar_conta()
            except Exception as e:
                print(f"Ocorreu um erro: {e}")
                conexao.rollback()

    # Sair
    elif opcao == "0":
        if logado == True:
            logado = False
        else:
            break
    # Opção inválida
    else:
        print("Opção inválida. Selecione outra opção:\n")
