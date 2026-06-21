#!/bin/bash
# Script para executar testes

echo "🧪 Executando testes com pytest..."
echo ""

source venv/bin/activate
pytest -v --cov-report=term-missing --cov-report=html

echo ""
echo "✅ Testes concluídos!"
echo ""
echo "📊 Relatório HTML de cobertura gerado em: htmlcov/index.html"
echo "   Para ver: firefox htmlcov/index.html"
echo ""
