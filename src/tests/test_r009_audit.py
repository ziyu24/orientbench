from orientbench.r009.audit import ALIASES, SIGNATURES
def test_r009_required_aliases_and_signatures():
 assert 'rareplanes-public' in ALIASES
 assert 'rareplanes_public_all_annotations.geojson' in SIGNATURES
