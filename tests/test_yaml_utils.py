from openskills.yaml_utils import extract_yaml_field, has_valid_frontmatter


def test_extract_yaml_field_finds_value():
    content = "name: my-skill\ndescription: A skill\n"
    assert extract_yaml_field(content, "name") == "my-skill"
    assert extract_yaml_field(content, "description") == "A skill"


def test_extract_yaml_field_missing_returns_empty():
    content = "name: my-skill\n"
    assert extract_yaml_field(content, "version") == ""


def test_extract_yaml_field_handles_whitespace():
    content = "name:   my-skill  \n"
    assert extract_yaml_field(content, "name") == "my-skill"


def test_extract_yaml_field_multiline():
    content = "---\nname: test\nversion: 1.0\n---\nSome body text\n"
    assert extract_yaml_field(content, "name") == "test"
    assert extract_yaml_field(content, "version") == "1.0"


def test_extract_yaml_field_case_sensitive():
    content = "Name: my-skill\n"
    assert extract_yaml_field(content, "name") == ""
    assert extract_yaml_field(content, "Name") == "my-skill"


def test_has_valid_frontmatter_true():
    assert has_valid_frontmatter("---\nname: test\n---\nbody") is True


def test_has_valid_frontmatter_false():
    assert has_valid_frontmatter("name: test\n") is False


def test_has_valid_frontmatter_strips_whitespace():
    assert has_valid_frontmatter("  ---\nname: test\n") is True


def test_has_valid_frontmatter_empty_string():
    assert has_valid_frontmatter("") is False
