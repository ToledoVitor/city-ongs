"""Local validation of a built Fase V payload against the official AUDESP
JSON Schema files (downloaded from the TCESP documentation page, version
1.14) — catches structural/format errors before ever calling the webservice.

The schema files live in docs/audesp/, one subdirectory per ajuste type,
matching AudespSubmission.AjusteTypeChoices.
"""

import json
from fractions import Fraction
from pathlib import Path

import jsonschema
from jsonschema.exceptions import ValidationError
from jsonschema.validators import extend

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs" / "audesp"

SCHEMA_PATHS = {
    "CONTRATO_GESTAO": DOCS_DIR
    / "prestacao_contas_contrato_gestao_v1_14"
    / "prestacao_contas_contrato_gestao_schema_v1_14.json",
    "CONVENIO": DOCS_DIR
    / "prestacao_contas_convenio_v1_14"
    / "prestacao_contas_convenio_schema_v1_14.json",
    "TERMO_COLABORACAO": DOCS_DIR
    / "prestacao_contas_termo_colaboracao_v1_14"
    / "prestacao_contas_termo_colaboracao_schema_v1_14.json",
    "TERMO_FOMENTO": DOCS_DIR
    / "prestacao_contas_termo_fomento_v1_14"
    / "prestacao_contas_termo_fomento_schema_v1_14.json",
    "TERMO_PARCERIA": DOCS_DIR
    / "prestacao_contas_termo_parceria_v1_14"
    / "prestacao_contas_termo_parceria_schema_v1_14.json",
    "DECLARACAO_NEGATIVA": DOCS_DIR
    / "declaracao_negativa_v1_14"
    / "declaracao_negativa_schema_v1_14.json",
}


def _load_schema(ajuste_type):
    path = SCHEMA_PATHS[ajuste_type]
    with open(path, encoding="utf-8") as schema_file:
        return json.load(schema_file)


def _multiple_of_via_fraction(validator, dB, instance, schema):
    """Replaces jsonschema's built-in `multipleOf` keyword.

    The stock implementation divides raw floats (`instance / dB`), which
    misfires on values like 4.56 / 0.01 (IEEE 754 gives 455.99999999999994,
    not 456) — a false positive that would hit nearly every AUDESP money
    field, since every `multipleOf` in these schemas is 0.01. Comparing via
    `Fraction(str(x))` reconstructs the intended decimal value instead of
    its imprecise binary float, so 4.56 correctly divides evenly by 0.01.
    """
    if not validator.is_type(instance, "number") or validator.is_type(
        instance, "boolean"
    ):
        return
    quotient = Fraction(str(instance)) / Fraction(str(dB))
    if quotient.denominator != 1:
        yield ValidationError(f"{instance!r} is not a multiple of {dB!r}")


_AudespValidator = extend(
    jsonschema.Draft7Validator,
    {"multipleOf": _multiple_of_via_fraction},
)


def validate_payload(payload, ajuste_type):
    """Validate `payload` (a dict) against the AUDESP JSON Schema for
    `ajuste_type` (one of AudespSubmission.AjusteTypeChoices' values).

    Returns a list of {"message": str, "path": str} dicts — empty means the
    payload is structurally valid per the JSON Schema (still no guarantee it
    passes AUDESP's server-side data-validation rules from the manual, which
    aren't expressible in JSON Schema and run only after submission).
    """
    schema = _load_schema(ajuste_type)
    validator = _AudespValidator(schema)
    errors = []
    for error in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
        errors.append(
            {
                "message": error.message,
                "path": ".".join(str(part) for part in error.path) or "(root)",
            }
        )
    return errors
