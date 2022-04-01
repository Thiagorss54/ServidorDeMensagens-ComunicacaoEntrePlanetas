OK = 1
ERROR = 2
HI = 3
KILL = 4
MSG = 5
CREQ = 6
CLIST = 7
ORIGIN = 8
PLANET = 9
PLANETLIST =10


TAMANHOMIN = 8
TAMANHOMAX = 4096


ID_SERVIDOR = 65535


class Mensagem:
    def __init__(self, tipo, origem, destino, sequencia, dados="", tamanho=0, listaDeClientes=[]):
        self.tipo = tipo
        self.origem = origem
        self.destino = destino
        self.sequencia = sequencia

        if tipo == MSG:
            self.tamanho = tamanho
            self.dados = dados


        elif tipo == CLIST:
            self.tamanho = tamanho
            self.listaDeClientes = listaDeClientes

        else:
            self.dados = dados

    @classmethod
    def desconstruir(cls, mensagemEmBytes):
        tipo = int.from_bytes(mensagemEmBytes[:2], "big")
        origem = int.from_bytes(mensagemEmBytes[2:4], "big")
        destino = int.from_bytes(mensagemEmBytes[4:6], "big")
        sequencia = int.from_bytes(mensagemEmBytes[6:8], "big")

        if tipo == MSG:
            tamanho = int.from_bytes(mensagemEmBytes[8:10], "big")
            dados = mensagemEmBytes[10:].decode("utf-8")
            return cls(tipo, origem, destino, sequencia, tamanho=tamanho, dados=dados)

        elif tipo == CLIST:
            listaDeClientes = []
            tamanho = int.from_bytes(mensagemEmBytes[8:10], "big")

            for cliente in range(10, 10 + (tamanho * 2), 2):
                listaDeClientes.append(int.from_bytes(mensagemEmBytes[cliente : (cliente + 2)], "big"))
            print(listaDeClientes)
            return cls(tipo, origem, destino, sequencia, tamanho=tamanho, listaDeClientes=listaDeClientes)

        else:
            dados = mensagemEmBytes[8:].decode("utf-8")
            return cls(tipo, origem, destino, sequencia, dados)

    def construir(self):
        tipo = self.tipo.to_bytes(2, "big")
        origem = self.origem.to_bytes(2, "big")
        destino = self.destino.to_bytes(2, "big")
        sequencia = self.sequencia.to_bytes(2, "big")

        if self.tipo == MSG:
            tamanho = self.tamanho.to_bytes(2, "big")
            msg = self.dados.encode("utf-8")
            return bytearray((tipo + origem + destino + sequencia + tamanho + msg))

        elif self.tipo == CLIST:
            ListaDeClientes = bytearray()
            tamanho = self.tamanho.to_bytes(2, "big")

            for cliente in self.listaDeClientes:
                ListaDeClientes += cliente.to_bytes(2, "big")

            return bytearray((tipo + origem + destino + sequencia + tamanho + ListaDeClientes))

        else:
            data = self.dados.encode("utf-8")
            return bytearray((tipo + origem + destino + sequencia + data))
