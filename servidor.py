import socket
import threading
import sys
from mensagem import *

HOST = "127.0.0.1"


class Servidor:
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST, port))
        self.sock.listen(0)

        self.exibidores = dict()
        self.emissores = dict()

        self.indiceExibidor = 4096
        self.indiceEmissor = 1

        self.threadsAtivas = 0

        print(f"Servidor (ID = {ID_SERVIDOR} Porta = {port})")


    def enviar(
        self,
        conneccao,
        tipo=0,
        origem=0,
        destino=0,
        sequencia=0,
        tamanho=0,
        dados="",
        listaDeClientes=[],
    ):
        comprimento = TAMANHOMIN

        if tipo == OK:
            msg = Mensagem(OK, ID_SERVIDOR, destino, 0)

        if tipo == ERROR:
            msg = Mensagem(ERROR, ID_SERVIDOR, destino, 0)

        if tipo == KILL:
            msg = Mensagem(KILL, origem, destino, 0)

        if tipo == MSG:
            msg = Mensagem(MSG, origem, destino, sequencia, tamanho=len(dados), dados=dados)

        if tipo == CLIST:
            msg = Mensagem(CLIST, origem, destino, sequencia, tamanho=len(listaDeClientes), listaDeClientes=listaDeClientes)

        mensagemEmBytes = msg.construir()
        enviado = 0

        while enviado < comprimento:
            enviando = conneccao.send(mensagemEmBytes[enviado:])
            enviado = enviado + enviando

            if enviando == 0:
                break

            if enviado == 0:
                raise RuntimeError("[ENVIAR]")

    def resposta(self, conexao):
        conexao.settimeout(1)

        partes = []
        recebido = 0

        try:
            while True:
                recebendo = conexao.recv(TAMANHOMAX)
                recebido = recebido + len(recebendo)

                partes.append(recebendo)
                dados = dados = b"".join(partes)
                mensagem = Mensagem.desconstruir(dados)

                if recebendo == b"" or recebido == 8:
                    conexao.settimeout(None)
                    return mensagem

                if recebido == 0:
                    break

        except socket.timeout:
            pass

        raise RuntimeError("[RESPOSTA]")

    def receber(self, conexao):
        partes = []
        recebido = 0

        while recebido < TAMANHOMAX:
            recebendo = conexao.recv(TAMANHOMAX)
            recebido = recebido + len(recebendo)

            partes.append(recebendo)
            dados = dados = b"".join(partes)
            mensagem = Mensagem.desconstruir(dados)

            if mensagem.tipo == MSG:
                if mensagem.tamanho == len(mensagem.dados):
                    return mensagem

            elif mensagem.tipo == CREQ:
                if recebido == 8:
                    return mensagem

            elif mensagem.tipo == KILL:
                if recebido == 8:
                    return mensagem


           
            else:
                raise RuntimeError("[RECEBER]")

        raise RuntimeError("[RECEBER]")

    def iniciar(self, conexao):
        msg = self.resposta(conexao)

        if msg.tipo != HI:
            self.enviar(conexao, tipo=ERROR)
            print("< Error")
            return

        print("< recieved hi")

        if msg.origem == 0:

            identificador = self.indiceExibidor
            self.indiceExibidor += 1

            if self.indiceExibidor == 8192:
                self.indiceExibidor = 4096

            self.enviar(conexao, tipo=OK, destino=identificador)
            self.exibidores[identificador] = conexao

        else:

            if msg.origem == 0 and len(self.exibidores) == 0:
                print("< empty ")

            elif msg.origem not in self.exibidores.keys():
                self.enviar(conexao, tipo=ERROR)

            else:
                identificador = self.indiceEmissor
                self.indiceEmissor += 1

                if self.indiceEmissor == 4096:
                    self.indiceEmissor = 1

                self.emissores[identificador] = conexao
                self.enviar(conexao, tipo=OK, destino=identificador)
                self.tratarRequisicoes(conexao,identificador,msg.origem)


    def tratarRequisicoes(self,conexao, emissor,exibidor):

        sequencia = 0
        conectado = True

        while conectado:
            mensagem = self.receber(conexao)
            self.enviar(conexao, tipo=OK, destino=emissor)

            if mensagem.tipo == MSG and (mensagem.destino in self.exibidores or mensagem.destino == 0):
                if mensagem.destino == 0:
                        for con in self.exibidores:
                            
                            self.enviar(
                            self.exibidores[con],
                            tipo=MSG,
                            origem=emissor,
                            destino=con,
                            dados=mensagem.dados,
                            sequencia=sequencia,
                            )
                            print(f"sent message from {emissor} to {con}")
                            res = self.resposta(self.exibidores[con])
                            if(res.tipo != OK):
                                print("< Error")
                            
                            else:
                                print(f"< Ok from {res.origem}")
                                sequencia+=1

                else:
                    self.enviar(
                        self.exibidores[mensagem.destino],
                        tipo=MSG,
                        origem=emissor,
                        destino=mensagem.destino,
                        dados=mensagem.dados,
                        sequencia=sequencia,
                        )
                    print(f"sent message from {emissor} to {mensagem.destino}")
                    res = self.resposta(self.exibidores[mensagem.destino])
                    if(res.tipo != OK):
                        print("< Error")
                            
                    else:
                        print(f"< Ok from {res.origem}")
                        sequencia+=1

                        
            elif mensagem.tipo == KILL:
        
                self.enviar(self.exibidores[exibidor], tipo=KILL, origem=emissor, destino=exibidor)
                print(f"kill from {exibidor}")
                conectado = False

            elif mensagem.tipo == CREQ:
                listaDeClientes = []
                listaDeClientes += self.emissores.keys()
                listaDeClientes += self.exibidores.keys()
                print(f"< received creq from {emissor} to {exibidor}")
                self.enviar(self.exibidores[mensagem.destino], tipo=CLIST, origem=emissor, destino=mensagem.destino, listaDeClientes=listaDeClientes)
                sequencia+=1

            elif mensagem.tipo == ORIGIN:
                print("ORIGIN")
            elif mensagem.tipo == PLANET:
                print("PLANET")
            elif mensagem.tipo == PLANETLIST:
                print("PLANETLIST")

                

        self.emissores[emissor].close()
        self.exibidores[exibidor].close()

        del self.emissores[emissor]
        del self.exibidores[exibidor]

    def aceitaConexao(self):
        while True:
            conexao, addr = self.sock.accept()

            self.threadsAtivas += 1
            handle = threading.Thread(target=self.iniciar, args=(conexao,))
            handle.start()



port = int(sys.argv[1])

servidor = Servidor(port)
servidor.aceitaConexao()
