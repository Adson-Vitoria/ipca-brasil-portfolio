WITH serie AS (
    SELECT
        ano,
        ipca_pct,
        LAG(ipca_pct) OVER (ORDER BY ano) AS ipca_anterior
    FROM ipca
)
SELECT
    ano,
    ipca_pct,
    ROUND(ipca_pct - ipca_anterior, 2) AS variacao_pp
FROM serie
ORDER BY ano;
