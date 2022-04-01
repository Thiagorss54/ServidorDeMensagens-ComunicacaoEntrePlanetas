import socket
import re
import sys
from mensagem import *


class Emissor:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

        self.identificador = 0
        self.sequencia = 0

    def enviar(self, tipo=0, origem=1, destino=0, dados="", tamanho=0):
        comprimento = TAMANHOMIN

        if tipo == HI:
            msg = Mensagem(HI, origem, ID_SERVIDOR, 0)

        if tipo == KILL:
            msg = Mensagem(KILL, self.identificador, ID_SERVIDOR, self.sequencia)

        if tipo == CREQ:
            msg = Mensagem(CREQ, self.identificador, destino, self.sequencia)

        if tipo == MSG:
            msg = Mensagem(MSG, self.identificador, destino, self.sequencia, tamanho=len(dados), dados=dados)
            comprimento += len(dados) + 2


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

    def iniciar(self, exibidor=1):
        self.enviar(tipo=HI, origem=exibidor)
        res = self.receber()

        if res.tipo == ERROR:
            return

        elif res.tipo != OK:
            return

        else:
            
            self.identificador = res.destino
            print(f"Emissor (ID = {self.identificador})")
            self.emitir()

        self.finalizar()

    def emitir(self):
        emitir = True

        while emitir:
            comando = input("> ")

            if comando[0:3] == "msg":
                destino = re.search(r"\d+", comando)
                msg = re.search(r'(").+', comando)

                if destino != None and msg != None:
                    self.enviar(tipo=MSG, destino=int(destino.group()), dados=msg.group())

            elif comando[:4] == "kill":
                self.enviar(tipo=KILL)
                emitir = False

            elif comando[0:4] == "creq":
                destino = re.search(r"\d+", comando)

                if destino != None:
                    self.enviar(tipo=CREQ, destino=int(destino.group()))

            elif comando[:6] == "origin":
                origem = re.search(r"\d+", comando)
                msg = re.search(r'(").+', comando)

                if origem != None:
                    self.enviar(tipo=ORIGIN, origem=int(origem.group(),dados = msg.group()))
            
            elif comando[:6] == "planet":
                destino = re.search(r"\d+", comando)
                if destino != None:
                    self.enviar(tipo = PLANET,destino = int(destino.group()))

            elif comando[:10] == "planetlist":
                self.enviar(tipo = PLANETLIST)

            else:
                raise RuntimeError("Comando invalido")

            res = self.receber()

            if res.tipo != OK:
                print("< Error ")
            else:
                 print("< Ok")
                 
            self.sequencia += 1

       


ip = sys.argv[1]
divisor = ip.find(":")

host = ip[:divisor]
port = int(ip[divisor + 1 :])

exibidor = int(sys.argv[2])

cliente = Emissor(host, port)
cliente.iniciar(exibidor)
