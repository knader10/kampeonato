#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampeonato.settings')
django.setup()

from campeonato.models import TimeCampeonato, Campeonato

def fix_orphan_records():
    print("Verificando registros órfãos...")
    
    # Encontrar registros órfãos
    try:
        orfaos = TimeCampeonato.objects.filter(campeonato_id=5)
        print(f'Registros órfãos encontrados: {orfaos.count()}')
        
        for orfao in orfaos:
            print(f'TimeCampeonato ID: {orfao.id}, Campeonato ID: {orfao.campeonato_id}')
            orfao.delete()
            
        print('Registros órfãos removidos.')
        
        # Verificar se existem outros registros órfãos
        all_tc = TimeCampeonato.objects.all()
        valid_campeonato_ids = set(Campeonato.objects.values_list('id', flat=True))
        
        for tc in all_tc:
            if tc.campeonato_id not in valid_campeonato_ids:
                print(f'Removendo registro órfão: TimeCampeonato ID {tc.id} -> Campeonato ID {tc.campeonato_id}')
                tc.delete()
                
    except Exception as e:
        print(f'Erro: {e}')

if __name__ == '__main__':
    fix_orphan_records()
