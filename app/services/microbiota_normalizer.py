from typing import Any

FIELD_ALIASES = {
    "study_id": "study_code",
    "report_id": "study_code",
    "analysis_id": "study_code",

    "patient_code": "patient_id",
    "patient_identifier": "patient_id",

    "reads": "total_reads",
    "read_count": "total_reads",
    "total_sequences": "total_reads",

    "filtered_sequences": "filtered_reads",
    "clean_reads": "filtered_reads",

    "seq_technology": "technology",
    "sequencing_method": "technology",

    "shannon": "shannon_index",
    "shannon_diversity": "shannon_index",

    "simpson": "simpson_index",
    "simpson_diversity": "simpson_index",

    "otus": "observed_otus",
    "observed_species": "observed_otus",

    "phylum": "phyla",
    "phylum_distribution": "phyla",

    "genus": "predominant_genera",
    "genera": "predominant_genera",

    "species": "detected_species",

    "antibiotics": "antibiotic_use",
    "antibiotic": "antibiotic_use",
    "antibiotics_last_6_months": "antibiotic_use",

    "diet": "dietary_pattern",
    "diet_type": "dietary_pattern",
}

KNOWN_PHYLA = {
    "Firmicutes",
    "Bacteroidetes",
    "Actinobacteria",
    "Proteobacteria",
    "Verrucomicrobia",
    "Fusobacteria",
}

KNOWN_GENERA = {
    "Bacteroides",
    "Faecalibacterium",
    "Prevotella",
    "Bifidobacterium",
    "Roseburia",
    "Akkermansia",
}


def normalize_field_names(data: dict[str, Any]) -> dict[str, Any]:
    """Recorre recursivamente el dict y cambia las claves según FIELD_ALIASES."""
    normalized: dict[str, Any] = {}

    for key, value in data.items():
        new_key = FIELD_ALIASES.get(key, key)

        if isinstance(value, dict):
            value = normalize_field_names(value)
        elif isinstance(value, list):
            # Si es una lista de diccionarios, normalizar cada uno
            value = [normalize_field_names(item) if isinstance(item, dict) else item for item in value]

        normalized[new_key] = value

    return normalized


def normalize_taxonomy_structure(taxonomy: dict[str, Any]) -> dict[str, Any]:
    """Convierte los diccionarios de abundancia en listas de objetos {name, abundance}."""
    
    # Normalizar phyla
    if "phyla" in taxonomy:
        phyla = taxonomy["phyla"]
        
        # Si viene como dict {"Firmicutes": 46.2, "Bacteroidetes": 39.5} -> Convertir a lista
        if isinstance(phyla, dict):
            taxonomy["phyla"] = [
                {"name": k, "abundance": v}
                for k, v in phyla.items()
            ]
        # Si ya es lista, asegurarse de que las claves internas sean correctas
        elif isinstance(phyla, list):
            for item in phyla:
                if isinstance(item, dict):
                    if "taxon" in item: item["name"] = item.pop("taxon")
                    if "percentage" in item: item["abundance"] = item.pop("percentage")
                    if "value" in item: item["abundance"] = item.pop("value")

    # Normalizar predominant_genera
    if "predominant_genera" in taxonomy:
        genera = taxonomy["predominant_genera"]
        
        # Si viene como dict {"Bacteroides": 18.5} -> Convertir a lista
        if isinstance(genera, dict):
            taxonomy["predominant_genera"] = [
                {"name": k, "abundance": v}
                for k, v in genera.items()
            ]
        elif isinstance(genera, list):
            for item in genera:
                if isinstance(item, dict):
                    if "taxon" in item: item["name"] = item.pop("taxon")
                    if "percentage" in item: item["abundance"] = item.pop("percentage")
                    if "value" in item: item["abundance"] = item.pop("value")

    return taxonomy


def normalize_percentage(value: Any) -> Any:
    """Si viene como 0.x (float), pásalo a % multiplicando por 100."""
    if isinstance(value, float) and value <= 1.0:
        return round(value * 100, 2)
    return value


def normalize_abundances(data: dict[str, Any]) -> dict[str, Any]:
    """Asegura que las abundancias estén en porcentaje (0-100)."""
    taxonomy = data.get("taxonomy")
    if not taxonomy:
        return data

    for phylum in taxonomy.get("phyla", []):
        if isinstance(phylum, dict) and "abundance" in phylum:
            phylum["abundance"] = normalize_percentage(phylum["abundance"])

    for genus in taxonomy.get("predominant_genera", []):
        if isinstance(genus, dict) and "abundance" in genus:
            genus["abundance"] = normalize_percentage(genus["abundance"])

    return data


def prenormalize_microbiota(raw_json: dict[str, Any]) -> dict[str, Any]:
    # 1) Aplanar el diccionario PRIMERO. Si viene "raw_json", sacamos su contenido al nivel raíz.
    data = raw_json.copy()
    inner = data.pop("raw_json", None)
    if isinstance(inner, dict):
        for k, v in inner.items():
            # No pisamos campos que ya existan en la raíz (ej. study_code) si inner los tiene duplicados vacíos
            if k not in data or not data[k]:
                data[k] = v

    # 2) Renombrar campos conocidos en todo el árbol (incluyendo phylum -> phyla)
    data = normalize_field_names(data)

    # 3) Normalizar estructura de taxonomy (Convertir dict a lista [{name, abundance}])
    if "taxonomy" in data and isinstance(data["taxonomy"], dict):
        data["taxonomy"] = normalize_taxonomy_structure(data["taxonomy"])

    # 4) Normalizar porcentajes (0.x -> 0.x*100)
    data = normalize_abundances(data)

    return data
