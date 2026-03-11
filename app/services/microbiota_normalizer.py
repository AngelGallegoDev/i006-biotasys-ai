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
    normalized: dict[str, Any] = {}

    for key, value in data.items():
        new_key = FIELD_ALIASES.get(key, key)

        if isinstance(value, dict):
            value = normalize_field_names(value)

        normalized[new_key] = value

    return normalized


def detect_phyla(data: dict[str, Any]) -> dict[str, Any] | None:
    detected: list[dict[str, Any]] = []

    for key, value in data.items():
        if key in KNOWN_PHYLA:
            detected.append({"name": key, "abundance": value})

    if detected:
        return {"phyla": detected}

    return None


def detect_genera(data: dict[str, Any]) -> dict[str, Any] | None:
    detected: list[dict[str, Any]] = []

    for key, value in data.items():
        if key in KNOWN_GENERA:
            detected.append({"name": key, "abundance": value})

    if detected:
        return {"predominant_genera": detected}

    return None


def normalize_taxonomy_structure(taxonomy: dict[str, Any]) -> dict[str, Any]:
    # Normalizar phyla
    if "phyla" in taxonomy:
        phyla = taxonomy["phyla"]

        # dict -> lista de {name, abundance}
        if isinstance(phyla, dict):
            taxonomy["phyla"] = [
                {"name": k, "abundance": v}
                for k, v in phyla.items()
            ]

        # lista -> renombrar campos comunes
        elif isinstance(phyla, list):
            for item in phyla:
                if "taxon" in item:
                    item["name"] = item.pop("taxon")
                if "percentage" in item:
                    item["abundance"] = item.pop("percentage")
                if "value" in item:
                    item["abundance"] = item.pop("value")

    # Normalizar predominant_genera con misma lógica, por si vienen en dict
    if "predominant_genera" in taxonomy:
        genera = taxonomy["predominant_genera"]

        if isinstance(genera, dict):
            taxonomy["predominant_genera"] = [
                {"name": k, "abundance": v}
                for k, v in genera.items()
            ]
        elif isinstance(genera, list):
            for item in genera:
                if "taxon" in item:
                    item["name"] = item.pop("taxon")
                if "percentage" in item:
                    item["abundance"] = item.pop("percentage")
                if "value" in item:
                    item["abundance"] = item.pop("value")

    return taxonomy


def normalize_percentage(value: Any) -> Any:
    # Si viene como 0.x (float), pásalo a %.
    if isinstance(value, float) and value <= 1:
        return round(value * 100, 2)
    return value


def normalize_abundances(data: dict[str, Any]) -> dict[str, Any]:
    taxonomy = data.get("taxonomy")
    if not taxonomy:
        return data

    # phyla
    for phylum in taxonomy.get("phyla", []):
        value = phylum.get("abundance")
        phylum["abundance"] = normalize_percentage(value)

    # genera
    for genus in taxonomy.get("predominant_genera", []):
        value = genus.get("abundance")
        genus["abundance"] = normalize_percentage(value)

    return data


def prenormalize_microbiota(raw_json: dict[str, Any]) -> dict[str, Any]:
    # 1) Renombrar campos conocidos en todo el árbol
    data = normalize_field_names(raw_json)

    # 2) Aplanar raw_json al nivel raíz (para la IA)
    inner = data.pop("raw_json", None)
    if isinstance(inner, dict):
        # merge superficial; si hay claves duplicadas, las de inner pisan
        for k, v in inner.items():
            # mantenemos los nombres normalizados (ya pasó normalize_field_names)
            data[k] = v

    taxonomy_block: dict[str, Any] = {}

    # 3) Intentar detectar phyla/géneros tanto en data["taxonomy"] como en el nivel raíz
    direct_taxonomy = data.get("taxonomy", {})
    phyla = detect_phyla(direct_taxonomy or data)
    genera = detect_genera(direct_taxonomy or data)

    if phyla:
        taxonomy_block.update(phyla)
    if genera:
        taxonomy_block.update(genera)

    if taxonomy_block:
        data.setdefault("taxonomy", {}).update(taxonomy_block)

    # 4) Normalizar estructura de taxonomy (dict -> lista, etc.)
    if "taxonomy" in data and isinstance(data["taxonomy"], dict):
        data["taxonomy"] = normalize_taxonomy_structure(data["taxonomy"])

    # 5) Normalizar porcentajes (0.x -> 0.x*100)
    data = normalize_abundances(data)

    return data
