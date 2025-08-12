#!/usr/bin/env python3
"""
Test des données d'altitude collectées
"""

import sys
import os
import json
sys.path.append('src')

def main():
    print('🏔️ Analyse des données d\'altitude')
    print('=' * 40)
    
    # Charger les données
    if not os.path.exists('test_strava_data.json'):
        print("❌ Fichier test_strava_data.json non trouvé")
        print("   Exécute d'abord: python collect_test_data_oauth.py")
        return
    
    with open('test_strava_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    activities = data['activities_data']
    
    print(f"📊 {len(activities)} activités analysées")
    print()
    
    for i, activity in enumerate(activities):
        name = activity.get('name', 'Sans nom')[:35]
        activity_type = activity.get('type', 'Unknown')
        
        # Données GPS
        gps_count = len(activity.get('coordinates', []))
        
        # Données d'altitude
        alt_count = len(activity.get('altitudes', []))
        elevation_stats = activity.get('elevation_stats', {})
        
        print(f"{i+1:2d}. {name:35} ({activity_type})")
        
        if gps_count > 0:
            print(f"     📍 {gps_count:,} points GPS")
        else:
            print(f"     📍 Pas de GPS")
            
        if alt_count > 0:
            print(f"     🏔️  {alt_count:,} points altitude")
            
            if elevation_stats:
                d_plus = elevation_stats.get('denivele_positif', 0)
                d_minus = elevation_stats.get('denivele_negatif', 0)
                alt_min = elevation_stats.get('altitude_min', 0)
                alt_max = elevation_stats.get('altitude_max', 0)
                
                print(f"     📈 D+: {d_plus:.0f}m, D-: {d_minus:.0f}m")
                print(f"     📏 Alt: {alt_min:.0f}m → {alt_max:.0f}m")
        else:
            print(f"     🏔️  Pas d'altitude")
        
        print()
    
    # Résumé global
    activities_with_gps = [a for a in activities if a.get('coordinates')]
    activities_with_alt = [a for a in activities if a.get('altitudes')]
    activities_with_stats = [a for a in activities if a.get('elevation_stats')]
    
    print("📋 Résumé global:")
    print(f"   📍 {len(activities_with_gps)} activités avec GPS")
    print(f"   🏔️  {len(activities_with_alt)} activités avec données altitude")
    print(f"   📊 {len(activities_with_stats)} activités avec stats élévation")
    
    if activities_with_stats:
        total_d_plus = sum(a['elevation_stats']['denivele_positif'] for a in activities_with_stats)
        total_d_minus = sum(a['elevation_stats']['denivele_negatif'] for a in activities_with_stats)
        
        print(f"   📈 Total D+: {total_d_plus:.0f}m")
        print(f"   📉 Total D-: {total_d_minus:.0f}m")

if __name__ == "__main__":
    main()