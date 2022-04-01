import socket
import sys
from mensagem import *


class Exibidor:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        self.identificador = 0

    def enviar(self, tipo=0):
        comprimento = TAMANHOMIN

        if tipo == HI:
            msg = Mensagem(HI, 0, ID_SERVIDOR, 0)
            
        if tipo == OK:
            msg = Mensagem(OK, self.identificador, ID_SERVIDOR, 0)

        if tipo == ERROR:
            msg = Mensagem(ERROR, self.identificador, ID_SERVIDOR, 0)

        mensagemEmBytes = msg.construir()
        enviado = 0

        while enviado < comprimento:
            enviando = self.sock.send(mensagemEmBytes[enviado:])
            enviado = enviado + enviando

            if enviando == 0:
                break

            if enviado == 0:
                raise RuntimeError("[ENVIAR]")

    def receber(self):
        self.sock.settimeout(1)

        partes = []
        recebido = 0

        try:
            while True:
                recebendo = self.sock.recv(TAMANHOMAX)
                recebido = recebido + len(recebendo)

                partes.append(recebendo)
                dados = dados = b"".join(partes)
                mensagem = Mensagem.desconstruir(dados)

                if recebendo == b"" or recebido == 8:
                    self.sock.settimeout(None)
                    return mensagem

                if recebido == 0:
                    break

        except socket.timeout:
            pass

        raise RuntimeError("[RECEBER]")
    
    def finalizar(self):
        self.sock.close()

    def iniciar(self):
        self.enviar(tipo=HI)
        res = self.receber()

        if res.tipo == ERROR:
            print("< Error")
            return

        elif res.tipo == OK:

            self.identificador = res.destino
            print(f"Exibidor (ID = {self.identificador})")

            self.exibir()
            
        self.finalizar()

    def exibir(self):
        exibir = True
        
        while exibir:
            partes = []
            recebido = 0

            while recebido < TAMANHOMAX:
                recebendo = self.sock.recv(TAMANHOMAX)
                recebido = recebido + len(recebendo)

                partes.append(recebendo)
                dados = dados = b"".join(partes)
                mensagem = Mensagem.desconstruir(dados)

                if mensagem.tipo == MSG:
                    if mensagem.tamanho == len(mensagem.dados):
                        self.enviar(tipo=OK)
                        print(f"< msg from {mensagem.origem}: {mensagem.dados}")
                        break
                    
                elif mensagem.tipo == CLIST:
                    if mensagem.tamanho == len(mensagem.listaDeClientes):
                        self.enviar(tipo=OK)
                        print(f"< clist: {mensagem.listaDeClientes}")
                        break
                    
                elif mensagem.tipo == KILL:
                    if recebido == 8:
                        self.enviar(tipo=OK)
                        print(f"< Kill ")
                        exibir = False
                        break
                
                else:
                    self.enviar(tipo=ERROR)
                
            if recebido > TAMANHOMAX:
                raise RuntimeError("[EXIBIR]")
        

ip = sys.argv[1]
divisor = ip.find(":")

host = ip[:divisor]
port = int(ip[divisor + 1 :])

cliente = Exibidor(host, port)
cliente.iniciar()
