"""Gera indicadores e gráfico do IPCA anual a partir do recorte do IBGE."""

import csv
import sqlite3
from math import isfinite, prod
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent


def ler_dados():
    with (ROOT / "ipca_anual.csv").open(encoding="utf-8", newline="") as arquivo:
        dados = [(int(linha["ano"]), float(linha["ipca_pct"])) for linha in csv.DictReader(arquivo)]
    if sorted(ano for ano, _ in dados) != list(range(2015, 2026)):
        raise ValueError("O recorte deve conter uma observação para cada ano de 2015 a 2025.")
    if any(not isfinite(taxa) or taxa <= -100 for _, taxa in dados):
        raise ValueError("Há uma taxa anual inválida na base.")
    return dados


def analisar(dados):
    with sqlite3.connect(":memory:") as conexao:
        conexao.execute("CREATE TABLE ipca (ano INTEGER PRIMARY KEY, ipca_pct REAL NOT NULL)")
        conexao.executemany("INSERT INTO ipca VALUES (?, ?)", dados)
        return conexao.execute((ROOT / "analise.sql").read_text(encoding="utf-8")).fetchall()


def gerar_grafico(linhas, destino):
    anos, taxas, _ = zip(*linhas)
    figura, eixo = plt.subplots(figsize=(10, 4.7), layout="constrained")
    cores = ["#c05027" if taxa >= 10 else "#176a85" for taxa in taxas]
    barras = eixo.bar(anos, taxas, color=cores, width=0.65)
    eixo.bar_label(barras, labels=[numero(taxa) for taxa in taxas], padding=4)
    eixo.set(title="Inflação anual no Brasil | 2015–2025", ylabel="IPCA acumulado no ano", ylim=(0, 12))
    eixo.set_xticks(anos)
    eixo.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f"{valor:g}%"))
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(axis="y", alpha=0.22)
    eixo.set_axisbelow(True)
    figura.text(0.99, 0.01, "Fonte: IBGE · SNIPC", ha="right", color="#405464")
    figura.savefig(destino, dpi=160)
    plt.close(figura)


def numero(valor):
    return f"{valor:.2f}".replace(".", ",")


def main():
    linhas = analisar(ler_dados())
    saida = ROOT

    with (saida / "indicadores.csv").open("w", encoding="utf-8", newline="") as arquivo:
        tabela = csv.writer(arquivo)
        tabela.writerow(["ano", "ipca_pct", "variacao_pp"])
        tabela.writerows(linhas)

    acumulado = (prod(1 + taxa / 100 for _, taxa, _ in linhas) - 1) * 100
    ano_pico, pico, _ = max(linhas, key=lambda linha: linha[1])
    print(f"Pico: {numero(pico)}% em {ano_pico}")
    print(f"Variação 2025 vs. 2024: {numero(linhas[-1][2])} p.p.")
    print(f"Inflação acumulada no recorte: aproximadamente {numero(acumulado)}%")
    gerar_grafico(linhas, saida / "ipca-anual.png")


if __name__ == "__main__":
    main()
