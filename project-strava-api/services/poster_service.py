"""
Service de génération de posters Strava
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from models.user import User
from .svg_generator import SVGGenerator
import logging
# import cairosvg  # Temporairement désactivé

logger = logging.getLogger(__name__)


class PosterService:
    """Service pour la génération de posters"""
    
    def __init__(self, user: User):
        self.user = user
        self.output_dir = Path("generated_posters")
        self.output_dir.mkdir(exist_ok=True)
        
        # Template SVG path (relatif au projet)
        self.template_path = Path(__file__).parent.parent.parent / "poster_framework.svg"
    
    async def generate_poster(self, activity_data: Dict[str, Any], format_type: str = "png") -> Dict[str, Any]:
        """
        Générer un poster avec les données d'activité
        """
        start_time = time.time()
        logger.info(f"Poster generation requested by user {self.user.id}")
        
        try:
            # Générer le SVG
            svg_generator = SVGGenerator(str(self.template_path))
            svg_content = svg_generator.generate_poster(activity_data)
            
            # Nom de fichier unique
            timestamp = int(time.time())
            filename_base = f"strava_poster_user_{self.user.id}_{timestamp}"
            
            # Sauvegarder le SVG temporaire
            svg_path = self.output_dir / f"{filename_base}.svg"
            with open(svg_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            output_path = None
            file_size = 0
            
            if format_type.lower() == "png":
                output_path = await self._convert_to_png(svg_path, filename_base)
            else:
                # Garder le SVG
                output_path = svg_path
            
            # Calculer la taille du fichier
            if output_path and output_path.exists():
                file_size = output_path.stat().st_size
            
            generation_time = int((time.time() - start_time) * 1000)  # en ms
            
            # Nettoyer le SVG temporaire si format différent
            if format_type.lower() != "svg" and svg_path.exists():
                svg_path.unlink()
            
            return {
                "poster_id": timestamp,
                "filename": output_path.name if output_path else f"{filename_base}.{format_type}",
                "file_path": str(output_path) if output_path else None,
                "file_size": file_size,
                "generation_time": generation_time,
                "activities_count": 1,
                "download_url": f"/api/v1/poster/{timestamp}/download",
                "status": "generated" if output_path else "failed"
            }
            
        except Exception as e:
            logger.error(f"Error generating poster: {str(e)}")
            return {
                "poster_id": None,
                "filename": None,
                "file_path": None,
                "file_size": 0,
                "generation_time": int((time.time() - start_time) * 1000),
                "activities_count": 0,
                "download_url": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def _convert_to_png(self, svg_path: Path, filename_base: str) -> Optional[Path]:
        """Convertir SVG vers PNG (désactivé temporairement)"""
        try:
            # Temporairement désactivé - retourner le SVG à la place
            logger.warning("PNG conversion disabled - returning SVG file")
            return svg_path
            
        except Exception as e:
            logger.error(f"PNG conversion failed: {str(e)}")
            return None
    
    async def get_poster_configs(self) -> list:
        """
        Récupérer les configurations de poster de l'utilisateur
        TODO: Implémenter le stockage des configurations
        """
        return []
    
    async def get_poster_history(self) -> Dict[str, Any]:
        """
        Récupérer l'historique des posters générés
        TODO: Implémenter l'historique
        """
        return {
            "posters": [],
            "total": 0
        }