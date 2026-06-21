#!/bin/bash
# Script simples para limpar dados

echo "🗑️  Limpando dados do banco..."
echo ""

source venv/bin/activate
python manage.py limpar_dados --confirmar

echo ""
echo "✅ Dados limpos!"
echo ""
echo "Agora você pode:"
echo "  1. Criar dados manualmente via interface"
echo "  2. Executar: ./reset_db.sh (para criar automático)"
echo "  3. Executar: python criar_dados_teste.py"
echo ""
