# Classificação de redes para aplicações de IoT

Classificação geral de tipos de redes para aplicações de IoT, com atributos de topologia, banda, frequência e casos de uso.

| Tipo | Sigla | Alcance | Topologia típica | Banda / Taxa | Frequência (rádio) | Aplicações IoT típicas |
|---|---|---|---|---|---|---|
| Body Area Network | `BAN` | < 2 m | estrela | ≤ 1 Mbps (NB-PHY); até 10 Mbps em PHYs de banda larga¹ | 2,4 GHz / 400 MHz (IEEE 802.15.6) | Wearables, monitoramento de saúde, implantes |
| Personal Area Network | `PAN` | 1 – 10 m | estrela, ponto a ponto | 1 – 3 Mbps | 2,4 GHz (Bluetooth Classic) | Periféricos, áudio sem fio, controles |
| Wireless PAN (IEEE 802.15.1/4) | `WPAN` | 1 – 100 m | estrela, malha | 20 kbps – 3 Mbps² | 2,4 GHz · 868/915 MHz | Automação predial, sensores domésticos (Zigbee, Z-Wave) |
| Low-Rate WPAN (IEEE 802.15.4) | `LR-WPAN` | ~10 m (nominal); 10 – 100 m na prática³ | estrela, árvore, malha | 20 – 250 kbps | 868 / 915 MHz · 2,4 GHz | Medição inteligente, redes de sensores industriais |
| Local Area Network | `LAN` | 10 m – 1 km | estrela, barramento, anel | 10 Mbps – 100 Gbps | — (cabeada; Ethernet) | Fábricas, data centers IoT, gateways locais |
| Wireless LAN (IEEE 802.11) | `WLAN` | 20 – 300 m | infraestrutura, ad hoc, malha | 1 Mbps – 9,6 Gbps (Wi-Fi 6) | 2,4 / 5 / 6 GHz | Câmeras IP, smart TVs, dispositivos domésticos conectados |
| Metropolitan Area Network | `MAN` | 1 – 50 km | anel, malha | Até 75 Mbps (802.16-2004); até 1 Gbps fixo / 100 Mbps móvel (802.16m)⁴ | WiMAX: 2 – 66 GHz | Cidades inteligentes, transporte urbano, semáforos conectados |
| Low-Power Wide Area Network | `LPWAN` | 2 – 15 km (urbano) / 45 km (rural) | estrela de estrelas | 0,3 – 50 kbps (LoRa/Sigfox); até 200 kbps no downlink NB-IoT⁵ | Sub-GHz: 433 / 868 / 915 MHz (LoRa, Sigfox); licenciada ~800/900 MHz (NB-IoT) | Medidores de água/gás, rastreamento de ativos, agricultura de precisão |
| Wide Area Network | `WAN` | Regional / global | malha, hub-and-spoke | Kbps – Gbps | Celular: 600 MHz – 3,5 GHz (4G/5G sub-6); 24 – 50+ GHz (5G mmWave)⁶; satélite: Ka/Ku | Telemetria veicular, IoT industrial remota, contêineres em trânsito |

**Legenda de categorias:** PAN/WPAN/LR-WPAN · WAN · MAN · LAN · WLAN · LPWAN

---

## Notas de verificação

A tabela original foi conferida contra fontes técnicas (normas IEEE, documentação de fabricantes e artigos). Em geral os valores se confirmaram; os ajustes abaixo foram feitos onde a pesquisa indicou imprecisão:

1. **BAN (IEEE 802.15.6):** o padrão define PHYs de banda estreita (NB) com taxas de ~75,9 kbps a 485,7 kbps conforme a faixa de frequência, mas também PHYs de banda larga/UWB e Human Body Communication que alcançam até 10 Mbps — a tabela original citava apenas "≤ 1 Mbps", o que subestima o teto do padrão.
2. **WPAN (802.15.1/4 combinados):** o valor original "250 kbps – 2 Mbps" não refletia bem a combinação de Bluetooth Classic (1–3 Mbps) com Zigbee/802.15.4 (20–250 kbps); corrigido para "20 kbps – 3 Mbps".
3. **LR-WPAN (802.15.4):** o padrão define um alcance *nominal* de projeto de ~10 m com linha de visada; o intervalo "10–75 m" da tabela original reflete alcances observados na prática (Zigbee: 10–100 m), não o valor normativo — por isso a tabela agora distingue os dois.
4. **MAN (WiMAX/802.16):** este foi o maior erro da tabela original — "1–10 Gbps" não corresponde a nenhuma revisão do padrão. O 802.16-2004 especifica até ~75 Mbps compartilhados; o 802.16m ("WiMAX 2") visa 1 Gbps fixo e 100 Mbps móvel. A faixa de frequência também foi corrigida de "2,5–66 GHz" para "2–66 GHz".
5. **LPWAN:** confirmado para LoRa (0,3–27/50 kbps, a depender do *spreading factor*/canal) e Sigfox (~0,1–0,6 kbps). NB-IoT, porém, alcança até 200 kbps no downlink — acima do teto "50 kbps" da tabela original — e usa espectro licenciado (não apenas sub-GHz não licenciado, como sugeria a tabela).
6. **WAN (celular):** o teto "3,5 GHz" da tabela original cobre bem as faixas low/mid-band de 4G/5G, mas ignora o 5G mmWave (24–50+ GHz), usado para altíssima taxa em curto alcance; adicionado como faixa complementar.

Os demais valores (PAN/Bluetooth Classic, WLAN/Wi-Fi 6, alcance e topologias) foram corroborados pelas fontes abaixo sem necessidade de correção.

## Referências

- [IEEE 802.15.6-2026 — Standards page](https://standards.ieee.org/ieee/802.15.6/10941/) — descrição oficial do padrão WBAN, taxas de dados e faixas de frequência (ISM e bandas médicas).
- [IEEE 802.15.4 — Wikipedia](https://en.wikipedia.org/wiki/IEEE_802.15.4) — alcance nominal de projeto, taxas por banda (868/915 MHz, 2,4 GHz) e histórico de revisões.
- [Zigbee — Wikipedia](https://en.wikipedia.org/wiki/Zigbee) — taxa de 250 kbps e faixa de 2,4 GHz do Zigbee.
- [Bluetooth Classic (BR/EDR): Profiles, Specs & Testing — IB Lenhardt](https://ib-lenhardt.com/kb/glossary/bluetooth-classic-br-edr) — taxas BR (1 Mbps) e EDR (2–3 Mbps), banda de 2,4 GHz.
- [Zigbee vs. Z-Wave vs. Z-Wave LR: Range Compared — Aeotec](https://aeotec.com/zigbee-vs-zwave-vs-zwave-lr-range/) — comparação de alcance, taxa e frequência entre Zigbee e Z-Wave.
- [What Is Wi-Fi 6? — Intel](https://www.intel.com/content/www/us/en/gaming/resources/wifi-6.html) — bandas 2,4/5/6 GHz e taxas de pico do Wi-Fi 6/6E.
- [IEEE 802.11ax: Wi-Fi 6 — Electronics Notes](https://www.electronics-notes.com/articles/connectivity/wifi-ieee-802-11/802-11ax.php) — detalhamento de taxas por configuração de canal/MIMO.
- [IEEE 802.16 — Wikipedia](https://en.wikipedia.org/wiki/IEEE_802.16) — faixa de frequência (2–66 GHz) e metas de taxa do 802.16m (1 Gbps fixo / 100 Mbps móvel).
- [WiMax in Computer Network — GeeksforGeeks](https://www.geeksforgeeks.org/computer-networks/wimax-in-computer-network/) — alcance de até 50 km e taxa de até 75 Mbps do 802.16-2004.
- [LPWAN technologies: NB-IoT, LoRaWAN, Sigfox — Thinger.io](https://thinger.io/lpwan-technologies-nb-iot-lorawan-sigfox/) — comparação de alcance, taxa e espectro (licenciado vs. não licenciado).
- [NB-IoT vs LoRa vs Sigfox: LPWAN Protocol Comparison — Zbotic](https://zbotic.in/nb-iot-vs-lora-vs-sigfox-lpwan-protocol-comparison/) — taxas de downlink/uplink do NB-IoT (até 200/20 kbps).
- [LoRa — Wikipedia](https://en.wikipedia.org/wiki/LoRa) — alcance urbano/rural e taxa (0,3–27 kbps) da camada física LoRa.
- [5G Bands, Explained — IoT For All](https://www.iotforall.com/5g-bands-explained) — faixas low/mid/high-band (mmWave) do 5G e seus casos de uso em IoT.
- [Understanding Cellular Frequency Bands: LTE, 5G & NB-IoT — Cavli Wireless](https://www.cavliwireless.com/blog/not-mini/cellular-frequency-bands-wireless-connectivity) — faixas de frequência de LTE (600 MHz–2,6 GHz) e 5G.
