#!/usr/bin/env python3
"""
Script de test pour la génération de posters SVG avec données réelles
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Ajouter project-strava-api au path Python
project_root = Path(__file__).parent / "project-strava-api"
sys.path.insert(0, str(project_root))

from services.svg_generator import SVGGenerator
from services.poster_service import PosterService
from models.user import User


def load_real_activity_data():
    """Charger la première activité depuis test_strava_data.json"""
    
    test_data_file = Path(__file__).parent / 'test_strava_data.json'
    
    if not test_data_file.exists():
        print(f"❌ Fichier {test_data_file} non trouvé")
        print("   Exécute d'abord: python collect_test_data_oauth.py")
        return None, None
    
    try:
        with open(test_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_data = data['user_data']
        first_activity = data['activities_data'][0]  # Première activité
        
        # Créer l'objet User
        user = User(
            id=user_data['id'],
            strava_id=user_data['id'],
            username=f"{user_data['firstname']}{user_data['lastname']}".lower(),
            first_name=user_data['firstname'],
            last_name=user_data['lastname'],
            profile_picture=user_data.get('profile', ''),
            created_at=datetime.now()
        )
        
        # Préparer les données d'activité
        activity_data = {
            'name': first_activity['name'],
            'type': first_activity['type'],
            'distance': first_activity['distance'],
            'moving_time': first_activity['moving_time'],
            'elapsed_time': first_activity['elapsed_time'],
            'total_elevation_gain': first_activity['total_elevation_gain'],
            'average_speed': first_activity['average_speed'],
            'max_speed': first_activity['max_speed'],
            'start_date': first_activity['start_date'],
            'average_heartrate': first_activity.get('average_heartrate'),
            'max_heartrate': first_activity.get('max_heartrate'),
            'coordinates': []
        }
        
        # Extraire les coordonnées (lat, lon) et ajouter altitude fictive
        coordinates = first_activity.get('coordinates', [])
        for i, coord in enumerate(coordinates):
            if len(coord) >= 2:
                lat, lon = coord[0], coord[1]
                # Altitude fictive basée sur la position dans le parcours
                alt = 50 + (i % 20) * 2  # Variation d'altitude fictive
                activity_data['coordinates'].append((lat, lon, alt))
        
        print(f"📊 Données activité chargées:")
        print(f"   👤 Utilisateur: {user.first_name} {user.last_name}")
        print(f"   🏃 Activité: {activity_data['name']}")
        print(f"   📏 Distance: {activity_data['distance'] / 1000:.1f} km")
        print(f"   ⏱️ Temps: {activity_data['moving_time'] // 60} min")
        print(f"   📍 Points GPS: {len(activity_data['coordinates'])}")
        
        return user, activity_data
        
    except Exception as e:
        print(f"❌ Erreur chargement données: {e}")
        import traceback
        traceback.print_exc()
        return None, None


async def test_svg_generation():
    """Test de génération SVG uniquement"""
    print("🎨 Test génération SVG avec données réelles")
    print("=" * 50)
    
    # Template SVG path
    template_path = Path(__file__).parent / "poster_framework.svg"
    
    if not template_path.exists():
        print(f"❌ Template SVG non trouvé: {template_path}")
        return False
    
    try:
        # Charger les vraies données
        user, activity_data = load_real_activity_data()
        if not user or not activity_data:
            return False
        
        # Générer le SVG
        print(f"\n🎨 Génération du SVG...")
        svg_generator = SVGGenerator(str(template_path))
        svg_content = svg_generator.generate_poster(activity_data)
        
        # Sauvegarder
        output_path = Path("test_poster_real.svg")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        file_size = output_path.stat().st_size
        print(f"   ✅ SVG généré: {output_path} ({file_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération SVG: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_png_generation():
    """Test de génération PNG via PosterService"""
    print("\n🖼️ Test génération PNG avec PosterService")
    print("=" * 50)
    
    try:
        # Charger les vraies données
        user, activity_data = load_real_activity_data()
        if not user or not activity_data:
            return False
        
        # Service de poster
        poster_service = PosterService(user)
        
        print(f"🚀 Génération poster PNG...")
        result = await poster_service.generate_poster(activity_data, format_type="png")
        
        print(f"📊 Résultat:")
        print(f"   Status: {result['status']}")
        print(f"   Fichier: {result['filename']}")
        print(f"   Taille: {result['file_size']} bytes")
        print(f"   Temps: {result['generation_time']} ms")
        
        if result['status'] == 'generated':
            print(f"   ✅ PNG créé: {result['file_path']}")
            return True
        else:
            print(f"   ❌ Échec: {result.get('error', 'Erreur inconnue')}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur génération PNG: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_pipeline():
    """Test complet de la pipeline"""
    print("\n🔄 Test pipeline complète")
    print("=" * 50)
    
    # Test SVG
    svg_success = await test_svg_generation()
    
    # Test PNG seulement si SVG réussi
    png_success = False
    if svg_success:
        png_success = await test_png_generation()
    
    print(f"\n📊 Résultats des tests:")
    print(f"   SVG: {'✅' if svg_success else '❌'}")
    print(f"   PNG: {'✅' if png_success else '❌'}")
    
    if svg_success and png_success:
        print(f"\n🎉 Tous les tests réussis!")
        print(f"💡 La génération de posters fonctionne avec les vraies données Strava")
        return True
    else:
        print(f"\n❌ Certains tests ont échoué")
        return False


def main():
    """Point d'entrée principal"""
    import sys
    
    print("🧪 Tests de génération de posters Strava")
    print("=" * 60)
    print("🎯 Objectif: Valider la génération SVG → PNG avec vraies données")
    print()
    
    # Mode de test
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        try:
            mode = input("Mode: svg (s), png (p), ou complet (c) ? [c]: ").lower().strip()
        except EOFError:
            mode = 'c'
    
    if not mode:
        mode = 'c'
    
    # Exécuter les tests
    success = False
    if mode in ['s', 'svg']:
        success = asyncio.run(test_svg_generation())
    elif mode in ['p', 'png']:
        success = asyncio.run(test_png_generation())
    else:
        success = asyncio.run(test_complete_pipeline())
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())