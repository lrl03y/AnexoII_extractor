# Anexo II PDF Extractor (Estructura Matricial T1_ij)

Este proyecto permite extraer automáticamente los datos desde formularios PDF del Anexo II, donde las tablas de gastos están organizadas por campos de formulario con nombre `T1_ij`, representando una matriz.

## 🧮 Mapeo de columnas

| Columna visible        | Campo T1_ij |
|------------------------|-------------|
| Tipo                   | T1_i1       |
| Descripción            | T1_i2       |
| Vertical               | T1_i3       |
| Nº Sensores            | T1_i4       |
| Importe del gasto      | T1_i5       |
| Importe solicitado     | T1_i6       |

## 📁 Estructura

```
anexoII_extractor_matriz/
├── formularios/              # PDFs a procesar
├── resultados/               # Salidas CSV
├── main.py                   # Script principal
├── requirements.txt
└── README.md
```

## 🧪 Ejecución

1. Coloca los PDFs en `formularios/`.
2. Instala dependencias:
```bash
pip install -r requirements.txt
```
3. Ejecuta:
```bash
python main.py
```

## 📤 Salidas generadas

- `cuerpo_anexoII.csv`: Datos técnicos por plantilla.
- `gastos_globales.csv`: Todas las filas de gastos consolidadas.
- `*.csv`: Un archivo de gastos por cada PDF, con nombre de ayuntamiento.

## 🔧 Notas

- Separador CSV: `;`
- Detecta automáticamente filas activas mientras haya contenido en la fila `i`.
