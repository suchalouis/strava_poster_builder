#!/usr/bin/env python3
"""
Script simplifié de test pour la génération de posters SVG avec données réelles
Utilise le module commun poster_generator.py
"""

import sys
import os
from pathlib import Path

# Importer le module commun
from poster_generator import PosterGenerator, load_strava_test_data, get_first_activity_with_splits

def test_svg_generation_simple():
    """Test de génération SVG simple avec le module commun"""
    print("🎨 Test génération SVG avec module commun")
    print("=" * 50)
    
    # Charger les données
    data_result = load_strava_test_data()
    if not data_result:
        return False
    
    user_data, activities_data = data_result
    
    # Prendre la première activité avec splits
    activity = get_first_activity_with_splits(activities_data)
    if not activity:
        activity = activities_data[0] if activities_data else None
    
    if not activity:
        print("❌ Aucune activité trouvée")
        return False
    
    print(f"👤 Utilisateur: {user_data.get('firstname')} {user_data.get('lastname')}")
    print(f"🏃 Activité: {activity.get('name', 'Sans nom')}")
    print(f"📏 Distance: {activity.get('distance', 0) / 1000:.1f} km")
    print(f"📍 Points GPS: {len(activity.get('coordinates', []))}")
    
    try:
        # Générer le poster avec le module commun
        print(f"\n🎨 Génération du poster SVG...")
        generator = PosterGenerator()
        output_path = generator.generate_poster(activity, "test_poster_simple.svg")
        
        # Vérifier le fichier généré
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Poster généré avec succès:")
            print(f"   📁 Fichier: {output_path}")
            print(f"   📊 Taille: {file_size} bytes")
            
            # Afficher les fonctionnalités incluses
            print(f"\n📋 Fonctionnalités incluses:")
            stats = generator.format_activity_statistics(activity)
            print(f"   ✅ Statistiques: {stats['DISTANCE']}, {stats['DURATION']}")
            
            if activity.get('km_splits'):
                print(f"   ✅ Histogramme d'allure: {len(activity['km_splits'])} splits")
            else:
                print(f"   ⚠️ Histogramme d'allure: Pas de splits disponibles")
            
            if activity.get('coordinates'):
                print(f"   ✅ Carte GPS: {len(activity['coordinates'])} points")
            else:
                print(f"   ⚠️ Carte GPS: Pas de coordonnées disponibles")
            
            return True
        else:
            print(f"❌ Échec: Fichier non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur génération SVG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_activities():
    """Test avec plusieurs activités"""
    print("\n🔄 Test avec plusieurs activités")
    print("=" * 50)
    
    # Charger les données
    data_result = load_strava_test_data()
    if not data_result:
        return False
    
    user_data, activities_data = data_result
    
    # Prendre les 3 premières activités avec splits
    activities_with_splits = [a for a in activities_data if a.get('km_splits')]
    test_activities = activities_with_splits[:3] if activities_with_splits else activities_data[:3]
    
    if not test_activities:
        print("❌ Aucune activité trouvée")
        return False
    
    print(f"📊 Test avec {len(test_activities)} activités")
    
    generator = PosterGenerator()
    success_count = 0
    
    for i, activity in enumerate(test_activities):
        activity_name = activity.get('name', f'Activité {i+1}')
        safe_name = activity_name.replace(' ', '_').replace('/', '_')[:20]
        output_path = f"poster_multi_{i+1}_{safe_name}.svg"
        
        try:
            print(f"\n   🎨 Génération poster {i+1}: {activity_name}")
            result_path = generator.generate_poster(activity, output_path)
            
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"   ✅ Créé: {result_path} ({file_size} bytes)")
                success_count += 1
            else:
                print(f"   ❌ Échec: {activity_name}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {activity_name} - {e}")
    
    print(f"\n📊 Résultats: {success_count}/{len(test_activities)} posters générés")
    return success_count > 0

def main():
    """Point d'entrée principal"""
    import sys
    
    print("🧪 Tests de génération SVG simplifiés")
    print("=" * 60)
    print("🎯 Objectif: Valider le module commun poster_generator.py")
    print()
    
    # Mode de test
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        try:
            mode = input("Mode: simple (s), multi (m), ou tous (t) ? [s]: ").lower().strip()
        except EOFError:
            mode = 's'
    
    if not mode:
        mode = 's'
    
    # Exécuter les tests
    success = False
    if mode in ['s', 'simple']:
        success = test_svg_generation_simple()
    elif mode in ['m', 'multi']:
        success = test_multiple_activities()
    else:  # tous
        success1 = test_svg_generation_simple()
        success2 = test_multiple_activities()
        success = success1 and success2
    
    if success:
        print(f"\n🎉 Tests réussis ! Le module commun fonctionne correctement.")
    else:
        print(f"\n❌ Certains tests ont échoué.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())