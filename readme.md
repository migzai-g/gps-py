# 🛰️ GPS Simples em Python

Programa didático que lê os dados de um módulo GPS (NEO-6M, NEO-M8N, GPS USB etc.) e mostra sua posição na tela.

Mostra:

- Latitude e longitude (em graus decimais)
- Altitude, número de satélites e precisão (HDOP)
- Link direto para o Google Maps
- Distância percorrida desde o primeiro ponto

Não tem um GPS? Use o **modo simulado**, que gera dados falsos para você testar e aprender.

---

## Requisitos

- Python 3.8 ou superior
- Biblioteca `pyserial` (só necessária para usar um GPS de verdade)

```bash
pip install -r requirements.txt
```

---

## Como usar

### 1. Modo simulado (sem GPS)

```bash
python gps.py --simulado
```

### 2. Com GPS real

**a)** Conecte o GPS ao computador (USB ou adaptador USB-Serial).

**b)** Descubra o nome da porta:

| Sistema | Como achar | Exemplo |
|---------|------------|---------|
| Windows | Gerenciador de Dispositivos → Portas (COM) | `COM3` |
| Linux   | `ls /dev/ttyUSB* /dev/ttyACM*` | `/dev/ttyUSB0` |
| macOS   | `ls /dev/tty.usb*` | `/dev/tty.usbserial-1410` |

**c)** Execute:

```bash
python gps.py --porta COM3
python gps.py --porta /dev/ttyUSB0 --baud 9600
```

Para parar, pressione `Ctrl + C`.

### 3. Sem nenhuma opção

Se você rodar apenas `python gps.py` (ou clicar em "Run" no VS Code), o programa pergunta se você quer usar o modo simulado ou um GPS real. Basta apertar `Enter` para escolher o modo simulado.

### Opções

| Opção | Descrição |
|-------|-----------|
| `--porta PORTA` | Porta serial do GPS |
| `--baud N` | Velocidade da serial (padrão: `9600`) |
| `--simulado` | Usa dados simulados, sem hardware |

---

## Exemplo de saída

```
[12:35:19 UTC]
  Latitude    : -22.281872
  Longitude   : -42.531063
  Altitude    : 850.0 m
  Satélites   : 8  (HDOP 0.9)
  Percorrido  : 3.2 m
  Mapa        : https://www.google.com/maps?q=-22.281872,-42.531063
```

---

## Dicas e problemas comuns

- **Não aparece nada na tela:** o GPS ainda não achou satélites. Use ao ar livre ou perto de uma janela. A primeira busca (*cold start*) pode levar alguns minutos.
- **`Permission denied` no Linux:** rode `sudo usermod -a -G dialout $USER` e reinicie a sessão.
- **Caracteres estranhos:** a velocidade (`--baud`) provavelmente está errada. Tente `4800`, `9600` ou `38400`.
- **Porta não abre:** feche outros programas que possam estar usando a mesma porta.

---

## Como funciona (resumo)

O GPS envia "frases" de texto pela porta serial no padrão **NMEA 0183**:

```
$GPGGA,123519,2257.3000,S,04223.4000,W,1,08,0.9,850.0,M,,,,*5A
```

| Campo | Significado |
|-------|-------------|
| `123519` | Hora UTC (12:35:19) |
| `2257.3000,S` | Latitude: 22° 57,3' Sul |
| `04223.4000,W` | Longitude: 42° 23,4' Oeste |
| `1` | Qualidade do sinal (0 = sem sinal) |
| `08` | Número de satélites |
| `0.9` | Precisão horizontal (HDOP) |
| `850.0,M` | Altitude em metros |
| `*5A` | Checksum (verificação de erros) |

O NMEA manda coordenadas em **graus e minutos**; o programa converte para **graus decimais** (ex.: `22° 57,3' S` → `-22.955`), que é o formato usado por mapas.

### Estrutura do código (`gps.py`)

| Função | O que faz |
|--------|-----------|
| `checksum_valido()` | Confere se a frase chegou sem erro |
| `nmea_para_decimal()` | Converte graus/minutos em graus decimais |
| `interpretar_gga()` | Extrai os dados úteis da frase GGA |
| `distancia_haversine()` | Calcula a distância entre dois pontos na Terra |
| `ler_serial()` / `simular()` | Fontes de dados (GPS real ou falso) |
| `main()` | Junta tudo e mostra na tela |

---

## Ideias para evoluir

- Salvar o trajeto em CSV ou GPX
- Interpretar também a frase `$GPRMC` (velocidade e direção)
- Desenhar o trajeto em um mapa com a biblioteca `folium`
- Disparar um alerta ao chegar perto de um destino

---

## Licença

Livre para estudar, usar e modificar.