def is_number(value):
    try:
        float(value)
        return True
    except:
        return False


def check_missing(data):
    missing = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                walk(v, new_path)
        else:
            if obj is None or obj == "":
                missing.append(path)

    walk(data)
    return missing


def validate_numbers(data):
    errors = []

    numeric_fields = [
        "academic.total_students",
        "academic.passed_students",
        "academic.failed_students",
        "finance.budget_allocated",
        "finance.budget_used",
        "hr.staff_count",
        "esg.energy_consumption"
    ]

    def get(data, path):
        keys = path.split(".")
        for k in keys:
            if isinstance(data, dict):
                data = data.get(k)
            else:
                return None
        return data

    for f in numeric_fields:
        val = get(data, f)
        if val is not None and val != "":
            if not is_number(val):
                errors.append(f"{f} invalid: {val}")

    return errors


def validate_all(data):
    missing = check_missing(data)
    format_errors = validate_numbers(data)

    return {
        "valid": len(missing) == 0 and len(format_errors) == 0,
        "missing": missing,
        "format_errors": format_errors
    }