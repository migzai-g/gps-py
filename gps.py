import argparse
import math
import random
import sys
import time


def calcular_checksum(corpo: str) -> str:
    """
    O checksum NMEA é um XOR de todos os caracteres entre '$' e '*'.
    Retorna 2 dígitos hexadecimais (ex.: '5A').
    """
    valor = 0
    for caractere in corpo:
        valor ^= ord(caractere)
    return f"{valor:02X}"


def checksum_valido(frase: str) -> bool:
    """Confere se a frase NMEA está íntegra (sem erro de transmissão)."""
    frase = frase.strip()
    if not frase.startswith("$") or "*" not in frase:
        return False
    corpo, _, recebido = frase[1:].partition("*")
    return calcular_checksum(corpo) == recebido.upper()[:2]



def nmea_para_decimal(valor: str, hemisferio: str) -> float:
    """
    Converte 'ddmm.mmmm' (ou 'dddmm.mmmm') para graus decimais.

    Exemplo: '2257.3000', 'S'
        graus   = 22
        minutos = 57.3
        decimal = 22 + 57.3/60 = 22.955  -> como é Sul, fica -22.955
    """
    ponto = valor.index(".")
    graus = int(valor[: ponto - 2])      
    minutos = float(valor[ponto - 2:])   
    decimal = graus + minutos / 60
    if hemisferio in ("S", "W"):         
        decimal = -decimal
    return decimal


def decimal_para_nmea(decimal: float, eh_latitude: bool):
    """Faz o caminho inverso (usado só pelo modo simulado)."""
    hemisferio = ("N" if decimal >= 0 else "S") if eh_latitude else ("E" if decimal >= 0 else "W")
    decimal = abs(decimal)
    graus = int(decimal)
    minutos = (decimal - graus) * 60
    largura = 2 if eh_latitude else 3
    return f"{graus:0{largura}d}{minutos:07.4f}", hemisferio



def interpretar_gga(frase: str):
    """
    Recebe uma frase $GPGGA / $GNGGA e devolve um dicionário com os dados.
    Devolve None se a frase for inválida ou se o GPS ainda não tem sinal.
    """
    if not checksum_valido(frase):
        return None

    campos = frase.split("*")[0].split(",")
    if not campos[0].endswith("GGA") or len(campos) < 10:
        return None

    qualidade = int(campos[6] or 0)
    if qualidade == 0 or not campos[2] or not campos[4]:
        return None  

    return {
        "hora_utc": f"{campos[1][0:2]}:{campos[1][2:4]}:{campos[1][4:6]}",
        "latitude": nmea_para_decimal(campos[2], campos[3]),
        "longitude": nmea_para_decimal(campos[4], campos[5]),
        "qualidade": qualidade,
        "satelites": int(campos[7] or 0),
        "hdop": float(campos[8] or 0),
        "altitude": float(campos[9] or 0),
    }



def distancia_haversine(lat1, lon1, lat2, lon2) -> float:
    """
    Distância em METROS entre dois pontos na superfície da Terra.
    Como a Terra é (quase) uma esfera, não dá para usar Pitágoras:
    a fórmula de Haversine considera a curvatura.
    """
    raio_terra = 6_371_000  
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * raio_terra * math.asin(math.sqrt(a))



def ler_serial(porta: str, baud: int):
    """Gerador: entrega, uma a uma, as linhas que o GPS envia pela serial."""
    try:
        import serial  
    except ImportError:
        sys.exit("Erro: instale a biblioteca com  ->  pip install pyserial")

    try:
        conexao = serial.Serial(porta, baud, timeout=2)
    except serial.SerialException as erro:
        sys.exit(f"Não consegui abrir a porta {porta}: {erro}")

    print(f"Conectado em {porta} a {baud} baud. Aguardando dados...\n")
    with conexao:
        while True:
            linha = conexao.readline().decode("ascii", errors="ignore").strip()
            if linha:
                yield linha


def simular():
    """
    Gerador: cria frases GGA falsas simulando alguém andando
    (ponto inicial: Nova Friburgo - RJ).
    """
    lat, lon = -22.2819, -42.5311
    while True:
        lat += random.uniform(0.00001, 0.00004)
        lon += random.uniform(0.00001, 0.00004)

        lat_txt, lat_h = decimal_para_nmea(lat, True)
        lon_txt, lon_h = decimal_para_nmea(lon, False)
        hora = time.strftime("%H%M%S", time.gmtime())

        corpo = f"GPGGA,{hora},{lat_txt},{lat_h},{lon_txt},{lon_h},1,08,0.9,850.0,M,,,,"
        yield f"${corpo}*{calcular_checksum(corpo)}"
        time.sleep(1)



def main():
    parser = argparse.ArgumentParser(description="Leitor de GPS simples (NMEA).")
    parser.add_argument("--porta", help="porta serial (ex.: COM3 ou /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=9600, help="velocidade (padrão 9600)")
    parser.add_argument("--simulado", action="store_true", help="usar dados simulados")
    args = parser.parse_args()

    if not args.simulado and not args.porta:
        print("Nenhuma opção informada. Escolha:")
        print("  1) Modo simulado (sem GPS)")
        print("  2) GPS real (informar a porta)")
        escolha = input("Opção [1]: ").strip() or "1"
        if escolha == "2":
            args.porta = input("Porta (ex.: COM3 ou /dev/ttyUSB0): ").strip()
            if not args.porta:
                sys.exit("Nenhuma porta informada.")
        else:
            args.simulado = True
        print()

    if args.simulado:
        print("MODO SIMULADO (dados falsos). Ctrl+C para sair.\n")
        fonte = simular()
    else:
        fonte = ler_serial(args.porta, args.baud)

    ponto_inicial = None
    distancia_total = 0.0
    ponto_anterior = None

    try:
        for linha in fonte:
            dados = interpretar_gga(linha)
            if dados is None:
                continue  

            lat, lon = dados["latitude"], dados["longitude"]

            if ponto_inicial is None:
                ponto_inicial = (lat, lon)
            if ponto_anterior:
                distancia_total += distancia_haversine(*ponto_anterior, lat, lon)
            ponto_anterior = (lat, lon)

            print(f"[{dados['hora_utc']} UTC]")
            print(f"  Latitude    : {lat:.6f}")
            print(f"  Longitude   : {lon:.6f}")
            print(f"  Altitude    : {dados['altitude']:.1f} m")
            print(f"  Satélites   : {dados['satelites']}  (HDOP {dados['hdop']})")
            print(f"  Percorrido  : {distancia_total:.1f} m")
            print(f"  Mapa        : https://www.google.com/maps?q={lat:.6f},{lon:.6f}")
            print()
    except KeyboardInterrupt:
        print("\nEncerrado. Até a próxima!")


if __name__ == "__main__":
    main()
