SELECT
  FORMAT(v.DatumVA, 'dd.MM.yyyy') AS "date"
  ,v.DatumVA AS "datetime"
  ,p.Produktion + ' ' + CONVERT(varchar, v.DatumVA, 108) AS event_name
FROM
  [data-warehouse].[dbo].[veranstaltung] v
INNER JOIN
  produktion p
ON
  v.ProduktionID = p.ProduktionID
WHERE
  v.ProduktionID = 31
  AND DatumVA >= '2025-01-03'
ORDER BY
  DatumVA;
